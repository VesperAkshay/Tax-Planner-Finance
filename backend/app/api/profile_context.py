from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session, select

from app.api.auth import get_current_user
from app.database import get_db_session
from app.models.taxpayer_profile import TaxpayerProfile
from app.models.user import User


def ensure_user_default_profile(session: Session, user: User) -> TaxpayerProfile:
    """
    Guarantees that every user has at least one default TaxpayerProfile (Self).
    Automatically migrates legacy accounts on first access with zero data loss.
    """
    profile = session.exec(
        select(TaxpayerProfile)
        .where(TaxpayerProfile.user_id == user.id)
        .where(TaxpayerProfile.is_default == True)
    ).first()

    if profile:
        return profile

    # Check if user has any profile at all
    any_profile = session.exec(
        select(TaxpayerProfile).where(TaxpayerProfile.user_id == user.id)
    ).first()

    if any_profile:
        any_profile.is_default = True
        session.add(any_profile)
        session.commit()
        session.refresh(any_profile)
        return any_profile

    # Create default 'Self' profile from user account details
    display_name = user.full_name.strip() if user.full_name else user.email.split("@")[0]
    default_profile = TaxpayerProfile(
        user_id=user.id,
        name=display_name,
        relationship="self",
        pan=user.pan,
        age_category="general",
        persona="salaried",
        is_default=True,
        filing_status="in_progress",
    )
    session.add(default_profile)
    session.commit()
    session.refresh(default_profile)
    return default_profile


def get_active_profile(
    x_taxpayer_profile_id: Optional[str] = Header(None, alias="X-Taxpayer-Profile-Id"),
    session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TaxpayerProfile:
    """
    FastAPI dependency to resolve the active TaxpayerProfile for the current request.
    Scopes all statements, transactions, salary slips, deductions, and tax reports.
    """
    if x_taxpayer_profile_id:
        try:
            profile_id = int(x_taxpayer_profile_id)
            profile = session.exec(
                select(TaxpayerProfile)
                .where(TaxpayerProfile.id == profile_id)
                .where(TaxpayerProfile.user_id == current_user.id)
            ).first()

            if profile:
                return profile
        except (ValueError, TypeError):
            pass

    # Fallback to default or auto-created profile
    return ensure_user_default_profile(session, current_user)
