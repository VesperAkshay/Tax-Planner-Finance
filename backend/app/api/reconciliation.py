"""
Reconciliation Flags and Resolution API Endpoints (Task 8.4).

Provides:
- Listing reconciliation flags filtered by status and scoped to authenticated user.
- Triggering full month-level reconciliation matching across user salary slips and bank credits.
- Resolving or ignoring flags with mandatory user notes and timestamp tracking.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.auth import get_current_user
from app.database import get_db_session
from app.models.reconciliation_flag import ReconciliationFlagRead
from app.models.user import User
from app.reconciliation.constants import (
    STATUS_IGNORED,
    STATUS_PENDING,
    STATUS_RESOLVED,
    VALID_STATUSES,
)
from app.reconciliation.schemas import ReconciliationReport
from app.reconciliation.service import (
    get_user_reconciliation_flags,
    resolve_reconciliation_flag,
    run_reconciliation_pipeline,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


class ResolveFlagRequest(BaseModel):
    action: str = Field(description="'resolved' or 'ignored'")
    user_note: str = Field(min_length=1, description="Mandatory note explaining resolution")


@router.get("/flags", response_model=List[ReconciliationFlagRead])
def list_reconciliation_flags(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by pending, resolved, or ignored"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> List[ReconciliationFlagRead]:
    """
    Retrieves all reconciliation flags for the authenticated user (Task 8.4).
    """
    try:
        flags = get_user_reconciliation_flags(session, current_user.id, status=status_filter)
        return [ReconciliationFlagRead.model_validate(f) for f in flags]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/run", response_model=ReconciliationReport)
def run_reconciliation(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ReconciliationReport:
    """
    Runs the month-level salary reconciliation pipeline across user slips and bank transactions.
    Creates any new discrepancy flags.
    """
    report = run_reconciliation_pipeline(session=session, user_id=current_user.id, auto_commit=True)
    return report


@router.post("/flags/{flag_id}/resolve", response_model=ReconciliationFlagRead)
def resolve_flag(
    flag_id: int,
    payload: ResolveFlagRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ReconciliationFlagRead:
    """
    Task 8.4 Resolution Flow:
    Resolves or ignores a flag with a mandatory user note.
    Enforces cross-tenant isolation: rejects requests for flags belonging to other users.
    """
    if payload.action not in (STATUS_RESOLVED, STATUS_IGNORED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action '{payload.action}'. Allowed: '{STATUS_RESOLVED}', '{STATUS_IGNORED}'.",
        )

    if not payload.user_note or not payload.user_note.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A non-empty user_note is mandatory when resolving or ignoring a flag.",
        )

    try:
        updated_flag = resolve_reconciliation_flag(
            session=session,
            flag_id=flag_id,
            user_id=current_user.id,
            action=payload.action,
            user_note=payload.user_note,
        )
        return ReconciliationFlagRead.model_validate(updated_flag)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
