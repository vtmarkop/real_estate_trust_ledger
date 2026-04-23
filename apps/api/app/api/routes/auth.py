from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlmodel import select

from app.api.deps import CurrentSessionDep, CurrentUserDep, SessionDep, SettingsDep
from app.core.security import generate_session_token, hash_password, hash_token, verify_password
from app.models import AuditLog, AuthSession, User
from app.models.common import utcnow
from app.schemas.audit_log import AuditLogResponse
from app.schemas.auth import (
    AuthSessionBulkRevokeResponse,
    AuthSessionResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.services.audit_logs import append_audit_log, build_audit_log_response
from trustledger_domain import AuditActionType, AuditOutcomeStatus


router = APIRouter(prefix="/auth", tags=["auth"])


MAX_FAILED_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION = timedelta(minutes=15)


def build_auth_session_response(
    auth_session: AuthSession,
    *,
    current_session_id: UUID,
) -> AuthSessionResponse:
    return AuthSessionResponse(
        id=auth_session.id,
        is_current=auth_session.id == current_session_id,
        is_active=auth_session.is_active(),
        expires_at=auth_session.expires_at,
        revoked_at=auth_session.revoked_at,
        last_seen_at=auth_session.last_seen_at,
        ip_address=auth_session.ip_address,
        user_agent=auth_session.user_agent,
        created_at=auth_session.created_at,
    )


def append_auth_login_denied_audit(
    *,
    session: SessionDep,
    user: User,
    details: str,
) -> None:
    append_audit_log(
        session=session,
        action_type=AuditActionType.AUTH_LOGIN_DENIED,
        outcome_status=AuditOutcomeStatus.DENIED,
        actor_user_id=user.id,
        subject_user_id=user.id,
        target_type="user",
        target_id=user.id,
        details=details,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterRequest,
    session: SessionDep,
) -> UserResponse:
    email = payload.email.lower().strip()
    existing_user = session.exec(select(User).where(User.email == email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use.",
        )

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserResponse)
def login_user(
    payload: LoginRequest,
    response: Response,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> UserResponse:
    email = payload.email.lower().strip()
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    current_time = utcnow()
    if user.is_login_locked(now=current_time):
        user.last_login_attempt_at = current_time
        user.updated_at = current_time
        session.add(user)
        append_auth_login_denied_audit(
            session=session,
            user=user,
            details="Login attempt denied because the account is temporarily locked.",
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Login is temporarily locked after repeated failed attempts.",
        )

    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempt_count += 1
        user.last_login_attempt_at = current_time
        user.updated_at = current_time
        if user.failed_login_attempt_count >= MAX_FAILED_LOGIN_ATTEMPTS:
            user.login_locked_until = current_time + LOGIN_LOCKOUT_DURATION
            session.add(user)
            append_auth_login_denied_audit(
                session=session,
                user=user,
                details="Login attempt denied and the account was temporarily locked after repeated invalid passwords.",
            )
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Login is temporarily locked after repeated failed attempts.",
            )
        session.add(user)
        append_auth_login_denied_audit(
            session=session,
            user=user,
            details="Login attempt denied because the password was invalid.",
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        append_auth_login_denied_audit(
            session=session,
            user=user,
            details="Login attempt denied because the user account is inactive.",
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    user.failed_login_attempt_count = 0
    user.last_login_attempt_at = current_time
    user.login_locked_until = None
    user.last_login_at = current_time
    user.updated_at = current_time
    session.add(user)

    raw_session_token = generate_session_token()
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(raw_session_token),
        expires_at=current_time + timedelta(minutes=settings.session_ttl_minutes),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    session.add(auth_session)
    session.commit()
    session.refresh(auth_session)
    append_audit_log(
        session=session,
        action_type=AuditActionType.AUTH_SESSION_CREATED,
        outcome_status=AuditOutcomeStatus.SUCCEEDED,
        actor_user_id=user.id,
        subject_user_id=user.id,
        target_type="auth_session",
        target_id=auth_session.id,
        details="User authenticated and a new session was created.",
    )
    session.commit()

    response.set_cookie(
        key=settings.cookie_name,
        value=raw_session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_minutes * 60,
        path="/",
    )
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(
    response: Response,
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> Response:
    raw_session_token = request.cookies.get(settings.cookie_name)
    if raw_session_token:
        session_token_hash = hash_token(raw_session_token)
        auth_session = session.exec(
            select(AuthSession).where(AuthSession.token_hash == session_token_hash)
        ).first()
        if auth_session and auth_session.revoked_at is None:
            auth_session.revoked_at = utcnow()
            auth_session.updated_at = utcnow()
            session.add(auth_session)
            append_audit_log(
                session=session,
                action_type=AuditActionType.AUTH_SESSION_REVOKED,
                outcome_status=AuditOutcomeStatus.CANCELED,
                actor_user_id=auth_session.user_id,
                subject_user_id=auth_session.user_id,
                target_type="auth_session",
                target_id=auth_session.id,
                details="User logged out and revoked the current session.",
            )
            session.commit()

    response.delete_cookie(
        key=settings.cookie_name,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: CurrentUserDep) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/security-events", response_model=list[AuditLogResponse])
def list_auth_security_events(
    current_user: CurrentUserDep,
    session: SessionDep,
    limit: int = 20,
) -> list[AuditLogResponse]:
    audit_logs = session.exec(
        select(AuditLog)
        .where(
            AuditLog.subject_user_id == current_user.id,
            AuditLog.action_type.in_(
                [
                    AuditActionType.AUTH_SESSION_CREATED,
                    AuditActionType.AUTH_SESSION_REVOKED,
                    AuditActionType.AUTH_LOGIN_DENIED,
                ]
            ),
        )
        .order_by(AuditLog.created_at.desc())
    ).all()[: max(1, min(limit, 100))]
    return [
        build_audit_log_response(session=session, audit_log=audit_log)
        for audit_log in audit_logs
    ]


@router.get("/sessions", response_model=list[AuthSessionResponse])
def list_auth_sessions(
    current_user: CurrentUserDep,
    current_session: CurrentSessionDep,
    session: SessionDep,
) -> list[AuthSessionResponse]:
    auth_sessions = session.exec(
        select(AuthSession)
        .where(AuthSession.user_id == current_user.id)
        .order_by(AuthSession.last_seen_at.desc(), AuthSession.created_at.desc())
    ).all()
    return [
        build_auth_session_response(
            auth_session,
            current_session_id=current_session.id,
        )
        for auth_session in auth_sessions
    ]


@router.post("/sessions/revoke-others", response_model=AuthSessionBulkRevokeResponse)
def revoke_other_auth_sessions(
    current_user: CurrentUserDep,
    current_session: CurrentSessionDep,
    session: SessionDep,
) -> AuthSessionBulkRevokeResponse:
    auth_sessions = session.exec(
        select(AuthSession).where(
            AuthSession.user_id == current_user.id,
            AuthSession.id != current_session.id,
        )
    ).all()

    revoked_session_ids: list[UUID] = []
    revocation_time = utcnow()
    for auth_session in auth_sessions:
        if auth_session.revoked_at is None and auth_session.is_active(now=revocation_time):
            auth_session.revoked_at = revocation_time
            auth_session.updated_at = revocation_time
            session.add(auth_session)
            revoked_session_ids.append(auth_session.id)

    if revoked_session_ids:
        append_audit_log(
            session=session,
            action_type=AuditActionType.AUTH_SESSION_REVOKED,
            outcome_status=AuditOutcomeStatus.CANCELED,
            actor_user_id=current_user.id,
            subject_user_id=current_user.id,
            target_type="auth_session_bulk",
            target_id=current_session.id,
            details=f"User revoked {len(revoked_session_ids)} other active sessions.",
        )
    session.commit()
    return AuthSessionBulkRevokeResponse(
        current_session_id=current_session.id,
        revoked_session_count=len(revoked_session_ids),
        revoked_session_ids=revoked_session_ids,
    )


@router.post("/sessions/{session_id}/revoke", response_model=AuthSessionResponse)
def revoke_auth_session(
    session_id: UUID,
    response: Response,
    current_user: CurrentUserDep,
    current_session: CurrentSessionDep,
    session: SessionDep,
    settings: SettingsDep,
) -> AuthSessionResponse:
    auth_session = session.exec(
        select(AuthSession).where(
            AuthSession.id == session_id,
            AuthSession.user_id == current_user.id,
        )
    ).first()
    if not auth_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auth session not found.",
        )

    if auth_session.revoked_at is None:
        revocation_time = utcnow()
        auth_session.revoked_at = revocation_time
        auth_session.updated_at = revocation_time
        session.add(auth_session)
        append_audit_log(
            session=session,
            action_type=AuditActionType.AUTH_SESSION_REVOKED,
            outcome_status=AuditOutcomeStatus.CANCELED,
            actor_user_id=current_user.id,
            subject_user_id=current_user.id,
            target_type="auth_session",
            target_id=auth_session.id,
            details="User revoked an auth session from the session management surface.",
        )
        session.commit()
        session.refresh(auth_session)

    if auth_session.id == current_session.id:
        response.delete_cookie(
            key=settings.cookie_name,
            path="/",
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
        )

    return build_auth_session_response(
        auth_session,
        current_session_id=current_session.id,
    )
