"""
Persistence helper for user-declared deductions elicited by the Tax Planning Agent (Task 7.3).

Writes or updates rows in the `user_declared_deductions` table with `source = 'agent_elicited'`.
"""

import logging
from typing import Any, Dict, List, Optional
from sqlmodel import Session, select

from app.models.user_declared_deduction import UserDeclaredDeduction

logger = logging.getLogger(__name__)


def persist_elicited_deduction(
    session: Session,
    user_id: int,
    section: str,
    amount: float,
    financial_year: str = "2025-2026",
    metadata_json: Optional[Dict[str, Any]] = None,
) -> UserDeclaredDeduction:
    """
    Saves or updates an agent-elicited deduction record in user_declared_deductions (Task 7.3).
    """
    statement = (
        select(UserDeclaredDeduction)
        .where(UserDeclaredDeduction.user_id == user_id)
        .where(UserDeclaredDeduction.financial_year == financial_year)
        .where(UserDeclaredDeduction.section == section)
    )
    existing = session.exec(statement).first()

    if existing:
        existing.amount = amount
        existing.source = "agent_elicited"
        existing.metadata_json = metadata_json
        session.add(existing)
        session.commit()
        session.refresh(existing)
        logger.info(f"Updated {section} deduction for user {user_id}: ₹{amount}")
        return existing
    else:
        record = UserDeclaredDeduction(
            user_id=user_id,
            financial_year=financial_year,
            section=section,
            amount=amount,
            source="agent_elicited",
            metadata_json=metadata_json,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        logger.info(f"Created {section} deduction for user {user_id}: ₹{amount}")
        return record


def persist_all_elicited_deductions(
    session: Session,
    user_id: int,
    declared_deductions: Dict[str, Any],
    financial_year: str = "2025-2026",
) -> List[UserDeclaredDeduction]:
    """
    Persists all deductions collected across visited agent nodes into the database.
    """
    records: List[UserDeclaredDeduction] = []

    section_mapping = {
        "section_80c": "80C",
        "80c": "80C",
        "section_80d": "80D",
        "80d": "80D",
        "section_80ccd_1b": "80CCD(1B)",
        "80ccd_1b": "80CCD(1B)",
        "section_80g": "80G",
        "80g": "80G",
        "section_24b": "24b",
        "24b": "24b",
        "hra": "HRA",
    }

    for key, value in declared_deductions.items():
        standard_section = section_mapping.get(key, key)
        amount = 0.0
        meta = None

        if isinstance(value, (int, float)):
            amount = float(value)
        elif isinstance(value, dict):
            # Complex deduction (e.g. HRA, 80D with tiers)
            meta = value
            if "claimed" in value:
                amount = float(value["claimed"])
            elif "rent_paid" in value:
                amount = float(value["rent_paid"])
            elif "self_family_premium" in value or "parents_premium" in value:
                p1 = float(value.get("self_family_premium", 0.0))
                p2 = float(value.get("parents_premium", 0.0))
                c = float(value.get("preventive_health_checkup", 0.0))
                amount = p1 + p2 + c

        if amount > 0.0 or meta:
            rec = persist_elicited_deduction(
                session=session,
                user_id=user_id,
                section=standard_section,
                amount=amount,
                financial_year=financial_year,
                metadata_json=meta,
            )
            records.append(rec)

    return records
