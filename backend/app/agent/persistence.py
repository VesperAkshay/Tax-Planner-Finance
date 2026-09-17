"""
Persistence helper for user-declared deductions and proactive elicitation state (Tasks 7.3, 13.1, 13.4, 13.7).

Writes or updates rows in:
- `user_declared_deductions` with `source = 'agent_elicited'` and `status = 'declared' | 'not_applicable'`
- `elicitation_progress` tracking section states across sessions (`pending`, `answered`, `skipped`)
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlmodel import Session, select

from app.agent.elicitation import CANONICAL_SECTIONS_ORDER
from app.agent.state import ElicitationState
from app.models.elicitation_progress import ElicitationProgress, ElicitationStateEnum
from app.models.user_declared_deduction import DeductionSource, DeductionStatus, UserDeclaredDeduction

logger = logging.getLogger(__name__)


def load_elicitation_state(
    session: Session,
    user_id: int,
    financial_year: str = "2025-2026",
) -> ElicitationState:
    """
    Loads saved elicitation progress from DB to enable cross-session resumption (Task 13.7).
    Reconstructs sections_pending, sections_answered, sections_skipped.
    """
    progress_records = session.exec(
        select(ElicitationProgress)
        .where(ElicitationProgress.user_id == user_id)
        .where(ElicitationProgress.financial_year == financial_year)
    ).all()

    answered: Dict[str, Any] = {}
    skipped: Dict[str, str] = {}

    for p in progress_records:
        sec = p.section_code
        if p.state == ElicitationStateEnum.answered:
            ded_rec = session.exec(
                select(UserDeclaredDeduction)
                .where(UserDeclaredDeduction.user_id == user_id)
                .where(UserDeclaredDeduction.financial_year == financial_year)
                .where(UserDeclaredDeduction.section == sec)
            ).first()
            if ded_rec:
                answered[sec] = {
                    "amount": ded_rec.amount,
                    "status": ded_rec.status.value if hasattr(ded_rec.status, "value") else str(ded_rec.status),
                    "metadata": ded_rec.metadata_json,
                }
            else:
                answered[sec] = {"amount": 0.0, "status": "not_applicable"}
        elif p.state == ElicitationStateEnum.skipped:
            skipped[sec] = p.skip_reason or "Automatically skipped by rule"

    pending = [
        sec for sec in CANONICAL_SECTIONS_ORDER
        if sec not in answered and sec not in skipped
    ]

    current_sec = pending[0] if pending else None

    return ElicitationState(
        financial_year=financial_year,
        sections_pending=pending,
        sections_answered=answered,
        sections_skipped=skipped,
        current_section=current_sec,
    )


def save_elicitation_step(
    session: Session,
    user_id: int,
    section_code: str,
    state: ElicitationStateEnum,
    financial_year: str = "2025-2026",
    skip_reason: Optional[str] = None,
) -> ElicitationProgress:
    """
    Updates or inserts a record into elicitation_progress (Task 13.1 & 13.4).
    """
    existing = session.exec(
        select(ElicitationProgress)
        .where(ElicitationProgress.user_id == user_id)
        .where(ElicitationProgress.financial_year == financial_year)
        .where(ElicitationProgress.section_code == section_code)
    ).first()

    now_utc = datetime.now(timezone.utc)
    if existing:
        existing.state = state
        existing.skip_reason = skip_reason
        existing.updated_at = now_utc
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        new_record = ElicitationProgress(
            user_id=user_id,
            financial_year=financial_year,
            section_code=section_code,
            state=state,
            skip_reason=skip_reason,
            updated_at=now_utc,
        )
        session.add(new_record)
        session.commit()
        session.refresh(new_record)
        return new_record


def record_elicited_deduction(
    session: Session,
    user_id: int,
    section: str,
    amount: float,
    status: str = "declared",
    financial_year: str = "2025-2026",
    metadata_json: Optional[Dict[str, Any]] = None,
    source: str = "agent_elicited",
) -> UserDeclaredDeduction:
    """
    Saves an elicited deduction with source ('agent_elicited') and status ('declared' | 'not_applicable') (Task 13.4).
    Also updates elicitation_progress to 'answered'.
    """
    ded_source = DeductionSource.agent_elicited if source == "agent_elicited" else DeductionSource.catalog_self_added
    ded_status = DeductionStatus.declared if status == "declared" else DeductionStatus.not_applicable

    statement = (
        select(UserDeclaredDeduction)
        .where(UserDeclaredDeduction.user_id == user_id)
        .where(UserDeclaredDeduction.financial_year == financial_year)
        .where(UserDeclaredDeduction.section == section)
    )
    existing = session.exec(statement).first()

    if existing:
        existing.amount = amount
        existing.source = ded_source
        existing.status = ded_status
        existing.metadata_json = metadata_json
        session.add(existing)
        session.commit()
        session.refresh(existing)
        rec = existing
    else:
        rec = UserDeclaredDeduction(
            user_id=user_id,
            financial_year=financial_year,
            section=section,
            amount=amount,
            source=ded_source,
            status=ded_status,
            metadata_json=metadata_json,
        )
        session.add(rec)
        session.commit()
        session.refresh(rec)

    # Mark progress as answered
    save_elicitation_step(
        session=session,
        user_id=user_id,
        section_code=section,
        state=ElicitationStateEnum.answered,
        financial_year=financial_year,
    )

    return rec


def persist_elicited_deduction(
    session: Session,
    user_id: int,
    section: str,
    amount: float,
    financial_year: str = "2025-2026",
    metadata_json: Optional[Dict[str, Any]] = None,
) -> UserDeclaredDeduction:
    """Backward-compatible helper for v1 calls."""
    return record_elicited_deduction(
        session=session,
        user_id=user_id,
        section=section,
        amount=amount,
        status="declared",
        financial_year=financial_year,
        metadata_json=metadata_json,
        source="agent_elicited",
    )


def persist_all_elicited_deductions(
    session: Session,
    user_id: int,
    declared_deductions: Dict[str, Any],
    financial_year: str = "2025-2026",
) -> List[UserDeclaredDeduction]:
    """Backward-compatible helper for saving all deductions in a dictionary."""
    records: List[UserDeclaredDeduction] = []
    section_code_map = {
        "section_80c": "80C",
        "80c": "80C",
        "section_80d": "80D",
        "80d": "80D",
        "section_80ccd_1b": "80CCD(1B)",
        "80ccd_1b": "80CCD(1B)",
        "section_80ccd_2": "80CCD(2)",
        "80ccd_2": "80CCD(2)",
        "section_80g": "80G",
        "80g": "80G",
        "section_24b": "24b",
        "24b": "24b",
        "24(b)": "24b",
        "hra": "HRA",
        "80gg": "80GG",
    }

    for section_key, val in declared_deductions.items():
        if val is None:
            continue
        clean_key = section_key.lower().replace("-", "_").replace(" ", "_")
        sec_code = section_code_map.get(clean_key, section_key)
        amt = 0.0
        meta = None

        if isinstance(val, (int, float)):
            amt = float(val)
        elif isinstance(val, dict):
            amt = float(val.get("rent_paid_annual", val.get("allowed", val.get("amount", 0.0))))
            meta = val

        if amt > 0.0:
            rec = record_elicited_deduction(
                session=session,
                user_id=user_id,
                section=sec_code,
                amount=amt,
                status="declared",
                financial_year=financial_year,
                metadata_json=meta,
                source="agent_elicited",
            )
            records.append(rec)

    return records
