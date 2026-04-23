from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlmodel import Session, select

from app.models import (
    DepositRecord,
    EvidenceDocument,
    HistoryImport,
    MaintenanceTicket,
    Organization,
    OrganizationMembership,
    PaymentRecord,
    Tenancy,
    TrustScoreRecalculationBatch,
    TrustScoreRecalculationRequest,
    TrustScoreHistory,
    TrustScoreSnapshot,
    User,
)
from app.models.common import utcnow
from app.schemas.score import (
    TrustScoreRecalculationBatchResponse,
    TrustScoreRecalculationRequestResponse,
    TrustScoreHistoryResponse,
    TrustScoreInputsResponse,
    TrustScoreSummaryResponse,
)
from trustledger_domain import (
    DepositStatus,
    EvidenceDocumentType,
    EvidenceReviewStatus,
    HistoryImportStatus,
    MaintenanceTicketStatus,
    PaymentRecordStatus,
    ScoreCalculationReason,
    ScoreRecalculationScope,
    ScoreRecalculationStatus,
    VerificationStatus,
)


SCORING_VERSION = "v1"
BASE_SCORE = 500
MAX_SCORE = 1000
MAX_VERIFICATION_STRENGTH = 100


@dataclass
class TrustScoreInputs:
    tenant_counterparty_confirmed_tenancies: int
    tenant_verified_tenancies: int
    landlord_counterparty_confirmed_tenancies: int
    landlord_verified_tenancies: int
    accepted_tenant_evidence_documents: int
    accepted_landlord_evidence_documents: int
    accepted_tenant_counterparty_references: int
    accepted_landlord_counterparty_references: int
    accepted_history_imports: int
    tenant_adjudication_adjustment: int
    landlord_adjudication_adjustment: int


@dataclass
class TrustScoreComputation:
    user_id: object
    tenant_score: int
    landlord_score: int
    verification_strength: int
    scoring_version: str
    calculated_at: object
    inputs: TrustScoreInputs


@dataclass
class TrustScoreRecalculationBatchCounts:
    pending_request_count: int
    processing_request_count: int
    completed_request_count: int
    failed_request_count: int
    request_ids: list[object]


def clamp(value: int, *, lower: int, upper: int) -> int:
    return max(lower, min(value, upper))


def calculate_user_trust_scores(
    *,
    session: Session,
    user: User,
) -> TrustScoreComputation:
    tenant_tenancies = session.exec(
        select(Tenancy).where(Tenancy.tenant_user_id == user.id)
    ).all()
    landlord_tenancies = session.exec(
        select(Tenancy).where(Tenancy.landlord_user_id == user.id)
    ).all()
    evidence_documents = session.exec(
        select(EvidenceDocument).where(
            EvidenceDocument.subject_user_id == user.id,
            EvidenceDocument.review_status == EvidenceReviewStatus.ACCEPTED,
        )
    ).all()
    accepted_history_imports = session.exec(
        select(HistoryImport).where(
            HistoryImport.subject_user_id == user.id,
            HistoryImport.status == HistoryImportStatus.ACCEPTED,
        )
    ).all()
    adjudicated_payment_records = session.exec(
        select(PaymentRecord).where(PaymentRecord.payment_status == PaymentRecordStatus.VERDICT_ISSUED)
    ).all()
    adjudicated_deposit_records = session.exec(
        select(DepositRecord).where(DepositRecord.deposit_status == DepositStatus.VERDICT_ISSUED)
    ).all()
    adjudicated_maintenance_tickets = session.exec(
        select(MaintenanceTicket).where(
            MaintenanceTicket.ticket_status == MaintenanceTicketStatus.VERDICT_ISSUED
        )
    ).all()

    tenant_adjudication_adjustment = 0
    landlord_adjudication_adjustment = 0
    for payment_record in adjudicated_payment_records:
        if payment_record.tenancy and payment_record.tenancy.tenant_user_id == user.id:
            tenant_adjudication_adjustment += payment_record.verdict_tenant_score_delta
        if payment_record.tenancy and payment_record.tenancy.landlord_user_id == user.id:
            landlord_adjudication_adjustment += payment_record.verdict_landlord_score_delta

    for deposit_record in adjudicated_deposit_records:
        if deposit_record.tenancy and deposit_record.tenancy.tenant_user_id == user.id:
            tenant_adjudication_adjustment += deposit_record.verdict_tenant_score_delta
        if deposit_record.tenancy and deposit_record.tenancy.landlord_user_id == user.id:
            landlord_adjudication_adjustment += deposit_record.verdict_landlord_score_delta

    for maintenance_ticket in adjudicated_maintenance_tickets:
        if maintenance_ticket.tenancy and maintenance_ticket.tenancy.tenant_user_id == user.id:
            tenant_adjudication_adjustment += maintenance_ticket.verdict_tenant_score_delta
        if maintenance_ticket.tenancy and maintenance_ticket.tenancy.landlord_user_id == user.id:
            landlord_adjudication_adjustment += maintenance_ticket.verdict_landlord_score_delta

    inputs = TrustScoreInputs(
        tenant_counterparty_confirmed_tenancies=sum(
            1
            for tenancy in tenant_tenancies
            if tenancy.verification_status
            in {
                VerificationStatus.COUNTERPARTY_CONFIRMED,
                VerificationStatus.REVIEWED,
                VerificationStatus.VERIFIED,
            }
        ),
        tenant_verified_tenancies=sum(
            1 for tenancy in tenant_tenancies if tenancy.verification_status == VerificationStatus.VERIFIED
        ),
        landlord_counterparty_confirmed_tenancies=sum(
            1
            for tenancy in landlord_tenancies
            if tenancy.verification_status
            in {
                VerificationStatus.COUNTERPARTY_CONFIRMED,
                VerificationStatus.REVIEWED,
                VerificationStatus.VERIFIED,
            }
        ),
        landlord_verified_tenancies=sum(
            1 for tenancy in landlord_tenancies if tenancy.verification_status == VerificationStatus.VERIFIED
        ),
        accepted_tenant_evidence_documents=sum(
            1
            for evidence_document in evidence_documents
            if evidence_document.tenancy
            and evidence_document.tenancy.tenant_user_id == user.id
            and evidence_document.document_type != EvidenceDocumentType.LANDLORD_REFERENCE
        ),
        accepted_landlord_evidence_documents=sum(
            1
            for evidence_document in evidence_documents
            if evidence_document.tenancy
            and evidence_document.tenancy.landlord_user_id == user.id
            and evidence_document.document_type != EvidenceDocumentType.LANDLORD_REFERENCE
        ),
        accepted_tenant_counterparty_references=sum(
            1
            for evidence_document in evidence_documents
            if evidence_document.tenancy
            and evidence_document.tenancy.tenant_user_id == user.id
            and evidence_document.document_type == EvidenceDocumentType.LANDLORD_REFERENCE
            and evidence_document.reference_request_id is not None
        ),
        accepted_landlord_counterparty_references=sum(
            1
            for evidence_document in evidence_documents
            if evidence_document.tenancy
            and evidence_document.tenancy.landlord_user_id == user.id
            and evidence_document.document_type == EvidenceDocumentType.LANDLORD_REFERENCE
            and evidence_document.reference_request_id is not None
        ),
        accepted_history_imports=len(accepted_history_imports),
        tenant_adjudication_adjustment=tenant_adjudication_adjustment,
        landlord_adjudication_adjustment=landlord_adjudication_adjustment,
    )

    tenant_score = clamp(
        BASE_SCORE
        + (inputs.tenant_counterparty_confirmed_tenancies * 25)
        + (inputs.tenant_verified_tenancies * 50)
        + (inputs.accepted_tenant_evidence_documents * 10)
        + (inputs.accepted_tenant_counterparty_references * 25)
        + inputs.tenant_adjudication_adjustment,
        lower=0,
        upper=MAX_SCORE,
    )
    landlord_score = clamp(
        BASE_SCORE
        + (inputs.landlord_counterparty_confirmed_tenancies * 25)
        + (inputs.landlord_verified_tenancies * 50)
        + (inputs.accepted_landlord_evidence_documents * 10)
        + (inputs.accepted_landlord_counterparty_references * 25)
        + inputs.landlord_adjudication_adjustment,
        lower=0,
        upper=MAX_SCORE,
    )
    verification_strength = clamp(
        (inputs.accepted_history_imports * 10)
        + ((inputs.accepted_tenant_evidence_documents + inputs.accepted_landlord_evidence_documents) * 8)
        + (
            (
                inputs.accepted_tenant_counterparty_references
                + inputs.accepted_landlord_counterparty_references
            )
            * 15
        )
        + ((inputs.tenant_verified_tenancies + inputs.landlord_verified_tenancies) * 12)
        + (
            (
                inputs.tenant_counterparty_confirmed_tenancies
                + inputs.landlord_counterparty_confirmed_tenancies
            )
            * 6
        ),
        lower=0,
        upper=MAX_VERIFICATION_STRENGTH,
    )

    return TrustScoreComputation(
        user_id=user.id,
        tenant_score=tenant_score,
        landlord_score=landlord_score,
        verification_strength=verification_strength,
        scoring_version=SCORING_VERSION,
        calculated_at=utcnow(),
        inputs=inputs,
    )


def persist_user_trust_score_computation(
    *,
    session: Session,
    user: User,
    computation: TrustScoreComputation,
    calculation_reason: ScoreCalculationReason,
) -> None:
    snapshot = session.exec(
        select(TrustScoreSnapshot).where(TrustScoreSnapshot.user_id == user.id)
    ).first()
    score_changed = (
        snapshot is None
        or snapshot.tenant_score != computation.tenant_score
        or snapshot.landlord_score != computation.landlord_score
        or snapshot.verification_strength != computation.verification_strength
        or snapshot.scoring_version != computation.scoring_version
    )

    if snapshot is None:
        snapshot = TrustScoreSnapshot(
            user_id=user.id,
            tenant_score=computation.tenant_score,
            landlord_score=computation.landlord_score,
            verification_strength=computation.verification_strength,
            scoring_version=computation.scoring_version,
            calculated_at=computation.calculated_at,
        )
    else:
        snapshot.tenant_score = computation.tenant_score
        snapshot.landlord_score = computation.landlord_score
        snapshot.verification_strength = computation.verification_strength
        snapshot.scoring_version = computation.scoring_version
        snapshot.calculated_at = computation.calculated_at
        snapshot.updated_at = utcnow()
    session.add(snapshot)

    if score_changed:
        session.add(
            TrustScoreHistory(
                user_id=user.id,
                tenant_score=computation.tenant_score,
                landlord_score=computation.landlord_score,
                verification_strength=computation.verification_strength,
                scoring_version=computation.scoring_version,
                calculation_reason=calculation_reason.value,
                calculated_at=computation.calculated_at,
            )
        )


def refresh_user_trust_score(
    *,
    session: Session,
    user: User,
    calculation_reason: ScoreCalculationReason,
) -> TrustScoreComputation:
    computation = calculate_user_trust_scores(session=session, user=user)
    persist_user_trust_score_computation(
        session=session,
        user=user,
        computation=computation,
        calculation_reason=calculation_reason,
    )
    return computation


def create_user_score_recalculation_request(
    *,
    session: Session,
    user: User,
    calculation_reason: ScoreCalculationReason,
    requested_by_user: User | None,
    scheduled_for: datetime | None = None,
    batch: TrustScoreRecalculationBatch | None = None,
) -> TrustScoreRecalculationRequest:
    request = TrustScoreRecalculationRequest(
        user_id=user.id,
        batch_id=batch.id if batch else None,
        requested_by_user_id=requested_by_user.id if requested_by_user else None,
        calculation_reason=calculation_reason.value,
        status=ScoreRecalculationStatus.PENDING,
        scheduled_for=scheduled_for or utcnow(),
    )
    session.add(request)
    session.flush()
    return request


def resolve_batch_calculation_reason(
    *,
    scope_type: ScoreRecalculationScope,
) -> ScoreCalculationReason:
    if scope_type == ScoreRecalculationScope.ORGANIZATION_MEMBERS:
        return ScoreCalculationReason.ORGANIZATION_BATCH_REFRESH
    return ScoreCalculationReason.NIGHTLY_BATCH_REFRESH


def resolve_batch_target_users(
    *,
    session: Session,
    scope_type: ScoreRecalculationScope,
    organization: Organization | None,
) -> list[User]:
    if scope_type == ScoreRecalculationScope.ORGANIZATION_MEMBERS:
        if organization is None:
            return []
        memberships = session.exec(
            select(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == organization.id,
                OrganizationMembership.is_active == True,  # noqa: E712
            )
            .order_by(OrganizationMembership.created_at.asc())
        ).all()
        users: list[User] = []
        for membership in memberships:
            user = session.get(User, membership.user_id)
            if user and user.is_active:
                users.append(user)
        return users

    return session.exec(
        select(User)
        .where(User.is_active == True)  # noqa: E712
        .order_by(User.created_at.asc())
    ).all()


def create_score_recalculation_batch(
    *,
    session: Session,
    scope_type: ScoreRecalculationScope,
    requested_by_user: User | None,
    organization: Organization | None = None,
    scheduled_for: datetime | None = None,
) -> tuple[TrustScoreRecalculationBatch, list[TrustScoreRecalculationRequest]]:
    calculation_reason = resolve_batch_calculation_reason(scope_type=scope_type)
    batch = TrustScoreRecalculationBatch(
        requested_by_user_id=requested_by_user.id if requested_by_user else None,
        organization_id=organization.id if organization else None,
        scope_type=scope_type,
        calculation_reason=calculation_reason.value,
        status=ScoreRecalculationStatus.PENDING,
        scheduled_for=scheduled_for or utcnow(),
    )
    session.add(batch)
    session.flush()

    target_users = resolve_batch_target_users(
        session=session,
        scope_type=scope_type,
        organization=organization,
    )
    requests: list[TrustScoreRecalculationRequest] = []
    for user in target_users:
        requests.append(
            create_user_score_recalculation_request(
                session=session,
                user=user,
                calculation_reason=calculation_reason,
                requested_by_user=requested_by_user,
                scheduled_for=batch.scheduled_for,
                batch=batch,
            )
        )

    batch.requested_user_count = len(requests)
    if batch.requested_user_count == 0:
        batch.status = ScoreRecalculationStatus.COMPLETED
        batch.completed_at = utcnow()
    batch.updated_at = utcnow()
    session.add(batch)
    session.flush()
    return batch, requests


def build_score_recalculation_batch_counts(
    *,
    session: Session,
    batch: TrustScoreRecalculationBatch,
) -> TrustScoreRecalculationBatchCounts:
    requests = session.exec(
        select(TrustScoreRecalculationRequest)
        .where(TrustScoreRecalculationRequest.batch_id == batch.id)
        .order_by(TrustScoreRecalculationRequest.created_at.asc())
    ).all()
    return TrustScoreRecalculationBatchCounts(
        pending_request_count=sum(
            1 for request in requests if request.status == ScoreRecalculationStatus.PENDING
        ),
        processing_request_count=sum(
            1 for request in requests if request.status == ScoreRecalculationStatus.PROCESSING
        ),
        completed_request_count=sum(
            1 for request in requests if request.status == ScoreRecalculationStatus.COMPLETED
        ),
        failed_request_count=sum(
            1 for request in requests if request.status == ScoreRecalculationStatus.FAILED
        ),
        request_ids=[request.id for request in requests],
    )


def sync_score_recalculation_batch_status(
    *,
    session: Session,
    batch: TrustScoreRecalculationBatch,
) -> TrustScoreRecalculationBatch:
    counts = build_score_recalculation_batch_counts(session=session, batch=batch)
    requests = session.exec(
        select(TrustScoreRecalculationRequest)
        .where(TrustScoreRecalculationRequest.batch_id == batch.id)
        .order_by(TrustScoreRecalculationRequest.created_at.asc())
    ).all()

    if counts.processing_request_count > 0:
        batch.status = ScoreRecalculationStatus.PROCESSING
        batch.started_at = batch.started_at or utcnow()
        batch.completed_at = None
        batch.last_error = None
    elif counts.pending_request_count == 0:
        batch.started_at = batch.started_at or utcnow()
        batch.completed_at = utcnow()
        if counts.failed_request_count > 0:
            batch.status = ScoreRecalculationStatus.FAILED
            failed_request = next(
                (
                    request
                    for request in requests
                    if request.status == ScoreRecalculationStatus.FAILED and request.last_error
                ),
                None,
            )
            batch.last_error = failed_request.last_error if failed_request else batch.last_error
        else:
            batch.status = ScoreRecalculationStatus.COMPLETED
            batch.last_error = None
    else:
        batch.status = ScoreRecalculationStatus.PENDING
        batch.completed_at = None

    batch.updated_at = utcnow()
    session.add(batch)
    session.flush()
    return batch


def begin_score_recalculation_request_processing(
    *,
    session: Session,
    recalculation_request: TrustScoreRecalculationRequest,
    processed_by_user: User | None = None,
) -> TrustScoreRecalculationRequest:
    if recalculation_request.status == ScoreRecalculationStatus.PROCESSING:
        if processed_by_user:
            recalculation_request.processed_by_user_id = processed_by_user.id
            recalculation_request.updated_at = utcnow()
            session.add(recalculation_request)
            session.flush()
        return recalculation_request

    current_time = utcnow()
    recalculation_request.status = ScoreRecalculationStatus.PROCESSING
    recalculation_request.started_at = recalculation_request.started_at or current_time
    recalculation_request.completed_at = None
    recalculation_request.last_error = None
    recalculation_request.attempt_count += 1
    recalculation_request.updated_at = current_time
    if processed_by_user:
        recalculation_request.processed_by_user_id = processed_by_user.id
    session.add(recalculation_request)
    session.flush()

    if recalculation_request.batch_id:
        batch = session.get(TrustScoreRecalculationBatch, recalculation_request.batch_id)
        if batch:
            sync_score_recalculation_batch_status(session=session, batch=batch)
    return recalculation_request


def process_score_recalculation_request(
    *,
    session: Session,
    recalculation_request: TrustScoreRecalculationRequest,
    processed_by_user: User | None = None,
) -> TrustScoreRecalculationRequest:
    if recalculation_request.status == ScoreRecalculationStatus.COMPLETED:
        if recalculation_request.batch_id:
            batch = session.get(TrustScoreRecalculationBatch, recalculation_request.batch_id)
            if batch:
                sync_score_recalculation_batch_status(session=session, batch=batch)
        return recalculation_request

    begin_score_recalculation_request_processing(
        session=session,
        recalculation_request=recalculation_request,
        processed_by_user=processed_by_user,
    )

    user = session.get(User, recalculation_request.user_id)
    if not user or not user.is_active:
        recalculation_request.status = ScoreRecalculationStatus.FAILED
        recalculation_request.completed_at = utcnow()
        recalculation_request.last_error = "User is inactive or unavailable."
        recalculation_request.updated_at = utcnow()
        session.add(recalculation_request)
        if recalculation_request.batch_id:
            batch = session.get(TrustScoreRecalculationBatch, recalculation_request.batch_id)
            if batch:
                sync_score_recalculation_batch_status(session=session, batch=batch)
        return recalculation_request

    calculation_reason = ScoreCalculationReason(recalculation_request.calculation_reason)
    computation = calculate_user_trust_scores(session=session, user=user)
    persist_user_trust_score_computation(
        session=session,
        user=user,
        computation=computation,
        calculation_reason=calculation_reason,
    )

    recalculation_request.status = ScoreRecalculationStatus.COMPLETED
    recalculation_request.completed_at = utcnow()
    recalculation_request.last_error = None
    recalculation_request.result_tenant_score = computation.tenant_score
    recalculation_request.result_landlord_score = computation.landlord_score
    recalculation_request.result_verification_strength = computation.verification_strength
    recalculation_request.result_scoring_version = computation.scoring_version
    recalculation_request.result_calculated_at = computation.calculated_at
    recalculation_request.updated_at = utcnow()
    session.add(recalculation_request)

    if recalculation_request.batch_id:
        batch = session.get(TrustScoreRecalculationBatch, recalculation_request.batch_id)
        if batch:
            sync_score_recalculation_batch_status(session=session, batch=batch)

    return recalculation_request


def list_due_score_recalculation_requests(
    *,
    session: Session,
    limit: int = 100,
    due_before: datetime | None = None,
) -> list[TrustScoreRecalculationRequest]:
    due_boundary = due_before or utcnow()
    requests = session.exec(
        select(TrustScoreRecalculationRequest)
        .where(
            TrustScoreRecalculationRequest.status == ScoreRecalculationStatus.PENDING,
            TrustScoreRecalculationRequest.scheduled_for <= due_boundary,
        )
        .order_by(
            TrustScoreRecalculationRequest.scheduled_for.asc(),
            TrustScoreRecalculationRequest.created_at.asc(),
        )
    ).all()
    return requests[:limit]


def claim_due_score_recalculation_requests(
    *,
    session: Session,
    processed_by_user: User,
    limit: int = 100,
    due_before: datetime | None = None,
) -> list[TrustScoreRecalculationRequest]:
    due_boundary = due_before or utcnow()
    requests = list_due_score_recalculation_requests(
        session=session,
        limit=limit,
        due_before=due_boundary,
    )

    claimed_requests: list[TrustScoreRecalculationRequest] = []
    for recalculation_request in requests:
        claimed_requests.append(
            begin_score_recalculation_request_processing(
                session=session,
                recalculation_request=recalculation_request,
                processed_by_user=processed_by_user,
            )
        )
    return claimed_requests


def build_trust_score_summary_response(
    *,
    computation: TrustScoreComputation,
) -> TrustScoreSummaryResponse:
    return TrustScoreSummaryResponse(
        user_id=computation.user_id,
        tenant_score=computation.tenant_score,
        landlord_score=computation.landlord_score,
        verification_strength=computation.verification_strength,
        scoring_version=computation.scoring_version,
        calculated_at=computation.calculated_at,
        inputs=TrustScoreInputsResponse(
            tenant_counterparty_confirmed_tenancies=computation.inputs.tenant_counterparty_confirmed_tenancies,
            tenant_verified_tenancies=computation.inputs.tenant_verified_tenancies,
            landlord_counterparty_confirmed_tenancies=computation.inputs.landlord_counterparty_confirmed_tenancies,
            landlord_verified_tenancies=computation.inputs.landlord_verified_tenancies,
            accepted_tenant_evidence_documents=computation.inputs.accepted_tenant_evidence_documents,
            accepted_landlord_evidence_documents=computation.inputs.accepted_landlord_evidence_documents,
            accepted_tenant_counterparty_references=computation.inputs.accepted_tenant_counterparty_references,
            accepted_landlord_counterparty_references=computation.inputs.accepted_landlord_counterparty_references,
            accepted_history_imports=computation.inputs.accepted_history_imports,
            tenant_adjudication_adjustment=computation.inputs.tenant_adjudication_adjustment,
            landlord_adjudication_adjustment=computation.inputs.landlord_adjudication_adjustment,
        ),
    )


def build_trust_score_history_response(
    *,
    history_entry: TrustScoreHistory,
) -> TrustScoreHistoryResponse:
    return TrustScoreHistoryResponse(
        id=history_entry.id,
        user_id=history_entry.user_id,
        tenant_score=history_entry.tenant_score,
        landlord_score=history_entry.landlord_score,
        verification_strength=history_entry.verification_strength,
        scoring_version=history_entry.scoring_version,
        calculation_reason=history_entry.calculation_reason,
        calculated_at=history_entry.calculated_at,
    )


def build_score_recalculation_request_response(
    *,
    recalculation_request: TrustScoreRecalculationRequest,
) -> TrustScoreRecalculationRequestResponse:
    return TrustScoreRecalculationRequestResponse(
        id=recalculation_request.id,
        user_id=recalculation_request.user_id,
        batch_id=recalculation_request.batch_id,
        requested_by_user_id=recalculation_request.requested_by_user_id,
        processed_by_user_id=recalculation_request.processed_by_user_id,
        calculation_reason=recalculation_request.calculation_reason,
        status=recalculation_request.status.value,
        attempt_count=recalculation_request.attempt_count,
        scheduled_for=recalculation_request.scheduled_for,
        started_at=recalculation_request.started_at,
        completed_at=recalculation_request.completed_at,
        last_error=recalculation_request.last_error,
        result_tenant_score=recalculation_request.result_tenant_score,
        result_landlord_score=recalculation_request.result_landlord_score,
        result_verification_strength=recalculation_request.result_verification_strength,
        result_scoring_version=recalculation_request.result_scoring_version,
        result_calculated_at=recalculation_request.result_calculated_at,
        created_at=recalculation_request.created_at,
    )


def build_score_recalculation_batch_response(
    *,
    session: Session,
    batch: TrustScoreRecalculationBatch,
) -> TrustScoreRecalculationBatchResponse:
    counts = build_score_recalculation_batch_counts(session=session, batch=batch)
    return TrustScoreRecalculationBatchResponse(
        id=batch.id,
        scope_type=batch.scope_type.value,
        organization_id=batch.organization_id,
        requested_by_user_id=batch.requested_by_user_id,
        calculation_reason=batch.calculation_reason,
        status=batch.status.value,
        scheduled_for=batch.scheduled_for,
        requested_user_count=batch.requested_user_count,
        pending_request_count=counts.pending_request_count,
        processing_request_count=counts.processing_request_count,
        completed_request_count=counts.completed_request_count,
        failed_request_count=counts.failed_request_count,
        request_ids=counts.request_ids,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        last_error=batch.last_error,
        created_at=batch.created_at,
    )
