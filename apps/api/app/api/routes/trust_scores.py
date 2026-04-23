from __future__ import annotations

from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import CurrentUserDep, SessionDep
from app.models import TrustScoreHistory
from app.schemas.score import TrustScoreHistoryResponse, TrustScoreSummaryResponse
from app.services.scoring import (
    build_trust_score_history_response,
    build_trust_score_summary_response,
    refresh_user_trust_score,
)
from trustledger_domain import ScoreCalculationReason


router = APIRouter(prefix="/trust-scores", tags=["trust-scores"])


@router.get("/mine", response_model=TrustScoreSummaryResponse)
def get_my_trust_score(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> TrustScoreSummaryResponse:
    computation = refresh_user_trust_score(
        session=session,
        user=current_user,
        calculation_reason=ScoreCalculationReason.SELF_SERVICE_REFRESH,
    )
    session.commit()
    return build_trust_score_summary_response(computation=computation)


@router.get("/mine/history", response_model=list[TrustScoreHistoryResponse])
def list_my_trust_score_history(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[TrustScoreHistoryResponse]:
    history_entries = session.exec(
        select(TrustScoreHistory)
        .where(TrustScoreHistory.user_id == current_user.id)
        .order_by(TrustScoreHistory.calculated_at.desc())
    ).all()
    return [
        build_trust_score_history_response(history_entry=history_entry)
        for history_entry in history_entries
    ]
