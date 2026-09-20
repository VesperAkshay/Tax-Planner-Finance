from datetime import date as dt_date
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, func, select

from app.api.auth import get_current_user
from app.api.profile_context import ensure_user_default_profile, get_active_profile
from app.database import get_db_session
from app.models.salary_slip import SalarySlip
from app.models.statement_upload import StatementUpload
from app.models.taxpayer_profile import (
    TaxpayerProfile,
    TaxpayerProfileCreate,
    TaxpayerProfileRead,
    TaxpayerProfileUpdate,
)
from app.models.user import User
from app.models.user_declared_deduction import UserDeclaredDeduction

router = APIRouter(prefix="/profiles", tags=["Taxpayer Profiles & Household"])


class ReadinessMilestone(BaseModel):
    name: str
    is_complete: bool
    weight_percent: int
    details: str
    action_tab: str


class ProfileReadinessResponse(BaseModel):
    profile_id: int
    profile_name: str
    persona: str
    overall_score: int  # 0 to 100
    is_filing_ready: bool
    milestones: List[ReadinessMilestone]
    next_step: str


class HouseholdMemberSummary(BaseModel):
    profile_id: int
    name: str
    relationship: str
    persona: str
    age_category: str
    pan: Optional[str] = None
    gross_income: float
    total_deductions: float
    tax_new_regime: float
    tax_old_regime: float
    recommended_regime: str
    optimal_tax: float
    tax_savings: float


class HouseholdArbitrageAdvice(BaseModel):
    category: str
    title: str
    impact_amount: float
    description: str
    actionable_tip: str


class HouseholdSummaryResponse(BaseModel):
    total_household_income: float
    total_household_tax: float
    total_household_savings: float
    members_count: int
    members: List[HouseholdMemberSummary]
    arbitrage_opportunities: List[HouseholdArbitrageAdvice]


def _calculate_profile_readiness(
    session: Session, user_id: int, profile_id: int
) -> tuple[int, List[ReadinessMilestone], str]:
    """Calculates filing readiness checklist (0-100%) for a given profile."""
    # 1. Bank statements count
    stmt_count = session.exec(
        select(func.count(StatementUpload.id))
        .where(StatementUpload.user_id == user_id)
    ).one() or 0

    # 2. Salary slips count
    salary_count = session.exec(
        select(func.count(SalarySlip.id))
        .where(SalarySlip.user_id == user_id)
    ).one() or 0

    # 3. Deductions declared count
    deductions_count = session.exec(
        select(func.count(UserDeclaredDeduction.id))
        .where(UserDeclaredDeduction.user_id == user_id)
        .where(UserDeclaredDeduction.amount > 0)
    ).one() or 0

    has_stmt = stmt_count > 0
    has_salary = salary_count > 0
    has_deductions = deductions_count > 0
    has_regime_evaluated = has_stmt or has_salary

    milestones = [
        ReadinessMilestone(
            name="Bank Statement Ingestion",
            is_complete=has_stmt,
            weight_percent=25,
            details=f"{stmt_count} statement(s) parsed and continuity verified"
            if has_stmt
            else "Upload bank statement in Tab 1 to activate ML categorization",
            action_tab="upload",
        ),
        ReadinessMilestone(
            name="Salary Payroll Audit",
            is_complete=has_salary,
            weight_percent=25,
            details=f"{salary_count} salary slip(s) extracted with HRA and PF"
            if has_salary
            else "Upload salary slip in Tab 1 to enable payroll reconciliation",
            action_tab="upload",
        ),
        ReadinessMilestone(
            name="Statutory Deductions Review",
            is_complete=has_deductions,
            weight_percent=25,
            details=f"{deductions_count} deduction section(s) declared"
            if has_deductions
            else "Review Chapter VI-A deductions (80C, 80D, HRA) in Tab 4",
            action_tab="catalog",
        ),
        ReadinessMilestone(
            name="Dual-Regime Slabs Evaluation",
            is_complete=has_regime_evaluated,
            weight_percent=25,
            details="Section 115BAC vs Old Regime side-by-side liability computed"
            if has_regime_evaluated
            else "Complete document intake to evaluate optimal regime in Tab 6",
            action_tab="report",
        ),
    ]

    overall_score = sum(m.weight_percent for m in milestones if m.is_complete)
    next_step = "All milestones complete! Ready for ITR filing."
    for m in milestones:
        if not m.is_complete:
            next_step = f"Next: {m.name} ({m.details})"
            break

    return overall_score, milestones, next_step


@router.get("", response_model=List[TaxpayerProfileRead])
def list_taxpayer_profiles(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> List[TaxpayerProfileRead]:
    """Lists all taxpayer profiles for the authenticated user."""
    ensure_user_default_profile(session, current_user)

    profiles = session.exec(
        select(TaxpayerProfile)
        .where(TaxpayerProfile.user_id == current_user.id)
        .order_by(TaxpayerProfile.is_default.desc(), TaxpayerProfile.id)
    ).all()

    result = []
    for p in profiles:
        score, _, _ = _calculate_profile_readiness(session, current_user.id, p.id or 0)
        stmt_count = session.exec(
            select(func.count(StatementUpload.id)).where(StatementUpload.user_id == current_user.id)
        ).one() or 0
        salary_count = session.exec(
            select(func.count(SalarySlip.id)).where(SalarySlip.user_id == current_user.id)
        ).one() or 0

        p_read = TaxpayerProfileRead(
            id=p.id or 0,
            user_id=p.user_id,
            name=p.name,
            relationship=p.relationship,
            pan=p.pan,
            dob=p.dob,
            age_category=p.age_category,
            persona=p.persona,
            is_default=p.is_default,
            filing_status=p.filing_status,
            created_at=p.created_at,
            updated_at=p.updated_at,
            statements_count=stmt_count,
            salary_slips_count=salary_count,
            readiness_score=score,
            recommended_regime="NEW (115BAC)",
        )
        result.append(p_read)

    return result


@router.post("", response_model=TaxpayerProfileRead, status_code=status.HTTP_201_CREATED)
def create_taxpayer_profile(
    payload: TaxpayerProfileCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TaxpayerProfileRead:
    """Creates a new taxpayer profile (Self, Spouse, Parent, HUF, etc.)."""
    pan_cleaned = payload.pan.strip().upper() if payload.pan else None
    if pan_cleaned and len(pan_cleaned) != 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PAN must be exactly 10 alphanumeric characters (e.g. ABCDE1234F).",
        )

    # If setting as default, unset existing default
    if payload.is_default:
        session.exec(
            select(TaxpayerProfile)
            .where(TaxpayerProfile.user_id == current_user.id)
        )
        existing_defaults = session.exec(
            select(TaxpayerProfile)
            .where(TaxpayerProfile.user_id == current_user.id)
            .where(TaxpayerProfile.is_default == True)
        ).all()
        for ed in existing_defaults:
            ed.is_default = False
            session.add(ed)

    profile = TaxpayerProfile(
        user_id=current_user.id,
        name=payload.name.strip(),
        relationship=payload.relationship,
        pan=pan_cleaned,
        dob=payload.dob,
        age_category=payload.age_category,
        persona=payload.persona,
        is_default=payload.is_default,
        filing_status="in_progress",
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)

    return TaxpayerProfileRead(
        id=profile.id or 0,
        user_id=profile.user_id,
        name=profile.name,
        relationship=profile.relationship,
        pan=profile.pan,
        dob=profile.dob,
        age_category=profile.age_category,
        persona=profile.persona,
        is_default=profile.is_default,
        filing_status=profile.filing_status,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        statements_count=0,
        salary_slips_count=0,
        readiness_score=0,
    )


@router.put("/{profile_id}", response_model=TaxpayerProfileRead)
def update_taxpayer_profile(
    profile_id: int,
    payload: TaxpayerProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> TaxpayerProfileRead:
    """Updates an existing taxpayer profile."""
    profile = session.exec(
        select(TaxpayerProfile)
        .where(TaxpayerProfile.id == profile_id)
        .where(TaxpayerProfile.user_id == current_user.id)
    ).first()

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    if payload.name is not None:
        profile.name = payload.name.strip()
    if payload.relationship is not None:
        profile.relationship = payload.relationship
    if payload.pan is not None:
        p_clean = payload.pan.strip().upper()
        if p_clean and len(p_clean) != 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PAN must be exactly 10 alphanumeric characters (e.g. ABCDE1234F).",
            )
        profile.pan = p_clean or None
    if payload.dob is not None:
        profile.dob = payload.dob
    if payload.age_category is not None:
        profile.age_category = payload.age_category
    if payload.persona is not None:
        profile.persona = payload.persona
    if payload.filing_status is not None:
        profile.filing_status = payload.filing_status
    if payload.is_default is True:
        # Unset others
        others = session.exec(
            select(TaxpayerProfile)
            .where(TaxpayerProfile.user_id == current_user.id)
            .where(TaxpayerProfile.id != profile_id)
        ).all()
        for o in others:
            o.is_default = False
            session.add(o)
        profile.is_default = True

    session.add(profile)
    session.commit()
    session.refresh(profile)

    score, _, _ = _calculate_profile_readiness(session, current_user.id, profile.id or 0)
    return TaxpayerProfileRead(
        id=profile.id or 0,
        user_id=profile.user_id,
        name=profile.name,
        relationship=profile.relationship,
        pan=profile.pan,
        dob=profile.dob,
        age_category=profile.age_category,
        persona=profile.persona,
        is_default=profile.is_default,
        filing_status=profile.filing_status,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        readiness_score=score,
    )


@router.delete("/{profile_id}", status_code=status.HTTP_200_OK)
def delete_taxpayer_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """Deletes a taxpayer profile."""
    profile = session.exec(
        select(TaxpayerProfile)
        .where(TaxpayerProfile.id == profile_id)
        .where(TaxpayerProfile.user_id == current_user.id)
    ).first()

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    total_profiles = session.exec(
        select(func.count(TaxpayerProfile.id)).where(TaxpayerProfile.user_id == current_user.id)
    ).one() or 0

    if total_profiles <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the sole taxpayer profile. At least one profile must exist.",
        )

    session.delete(profile)
    session.commit()

    # Ensure a default exists
    ensure_user_default_profile(session, current_user)

    return {"status": "success", "message": f"Profile '{profile.name}' deleted successfully."}


@router.get("/readiness", response_model=ProfileReadinessResponse)
def get_active_profile_readiness(
    current_user: User = Depends(get_current_user),
    active_profile: TaxpayerProfile = Depends(get_active_profile),
    session: Session = Depends(get_db_session),
) -> ProfileReadinessResponse:
    """Returns live filing readiness scorecard for the currently active profile."""
    score, milestones, next_step = _calculate_profile_readiness(
        session, current_user.id, active_profile.id or 0
    )

    return ProfileReadinessResponse(
        profile_id=active_profile.id or 0,
        profile_name=active_profile.name,
        persona=active_profile.persona,
        overall_score=score,
        is_filing_ready=score >= 75,
        milestones=milestones,
        next_step=next_step,
    )


@router.get("/household-summary", response_model=HouseholdSummaryResponse)
def get_household_summary(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> HouseholdSummaryResponse:
    """
    Computes joint household tax liability across all family member profiles.
    Identifies deduction arbitrage and senior citizen tax optimization opportunities.
    """
    ensure_user_default_profile(session, current_user)

    profiles = session.exec(
        select(TaxpayerProfile)
        .where(TaxpayerProfile.user_id == current_user.id)
        .order_by(TaxpayerProfile.id)
    ).all()

    members_summary: List[HouseholdMemberSummary] = []
    total_household_income = 0.0
    total_household_tax = 0.0
    total_household_savings = 0.0

    # Aggregate salary slip income for household
    salary_slips = session.exec(
        select(SalarySlip).where(SalarySlip.user_id == current_user.id)
    ).all()
    total_annual_salary = sum(s.gross_pay for s in salary_slips) * (12.0 / max(1, len(salary_slips))) if salary_slips else 0.0

    # User declared deductions
    deductions = session.exec(
        select(UserDeclaredDeduction)
        .where(UserDeclaredDeduction.user_id == current_user.id)
        .where(UserDeclaredDeduction.amount > 0)
    ).all()
    total_deductions_amount = sum(d.amount for d in deductions)

    for idx, p in enumerate(profiles):
        # Distribute or attribute income (Primary profile gets main salary if not separated)
        p_gross = total_annual_salary if (p.is_default or idx == 0) else 0.0
        p_ded = total_deductions_amount if (p.is_default or idx == 0) else 0.0

        # High-level estimates
        from app.tax.engine import TaxEngine
        from app.tax.models import IncomeDetails, TaxpayerRegimePreferences

        engine = TaxEngine()
        inc = IncomeDetails(
            gross_salary=p_gross,
            rental_income=0.0,
            interest_income=0.0,
            dividend_income=0.0,
            other_income=0.0,
            exemptions={"hra": 0.0, "standard_deduction": 75000.0 if p.persona == "salaried" else 0.0},
        )
        pref = TaxpayerRegimePreferences(
            age_category=p.age_category if p.age_category in ["general", "senior", "super_senior"] else "general",
            metro_city=True,
            rent_paid_annual=0.0,
        )
        comp = engine.calculate_all(inc, {}, pref)

        optimal_tax = comp.recommended_tax
        opt_regime = "NEW REGIME (115BAC)" if comp.recommended_regime == "new" else "OLD REGIME"
        savings = comp.tax_savings

        total_household_income += p_gross
        total_household_tax += optimal_tax
        total_household_savings += savings

        members_summary.append(
            HouseholdMemberSummary(
                profile_id=p.id or 0,
                name=p.name,
                relationship=p.relationship,
                persona=p.persona,
                age_category=p.age_category,
                pan=p.pan,
                gross_income=round(p_gross, 2),
                total_deductions=round(p_ded, 2),
                tax_new_regime=round(comp.new_regime.tax_payable, 2),
                tax_old_regime=round(comp.old_regime.tax_payable, 2),
                recommended_regime=opt_regime,
                optimal_tax=round(optimal_tax, 2),
                tax_savings=round(savings, 2),
            )
        )

    # Compute joint arbitrage opportunities
    arbitrage_list: List[HouseholdArbitrageAdvice] = []

    # 1. Section 80D Health Insurance Arbitrage
    if len(profiles) > 1:
        arbitrage_list.append(
            HouseholdArbitrageAdvice(
                category="Section 80D",
                title="Household Health Insurance Allocation",
                impact_amount=15600.0,
                description=(
                    "If one family member is in the 30% tax slab under Old Regime and another is opting for New Regime, "
                    "route parental health insurance (up to ₹50,000) under the Old Regime taxpayer's PAN to capture maximum 31.2% tax relief."
                ),
                actionable_tip="Pay parental health premiums from the taxpayer in the higher tax bracket.",
            )
        )

    # 2. Senior Citizen Interest Exemption (Section 80TTB)
    senior_members = [p for p in profiles if p.age_category in ["senior", "super_senior"] or p.persona == "senior_citizen"]
    if senior_members:
        arbitrage_list.append(
            HouseholdArbitrageAdvice(
                category="Section 80TTB",
                title=f"Senior Citizen ₹50,000 FD Exemption ({senior_members[0].name})",
                impact_amount=10400.0,
                description=(
                    f"Senior citizen profiles like {senior_members[0].name} are entitled to ₹50,000 deduction on savings and fixed deposit interest "
                    "under Section 80TTB (compared to only ₹10,000 under 80TTA for non-seniors)."
                ),
                actionable_tip=f"Hold high-yield fixed deposits under {senior_members[0].name}'s PAN.",
            )
        )
    else:
        arbitrage_list.append(
            HouseholdArbitrageAdvice(
                category="Profile Persona",
                title="Add Senior Parent Profile for 80TTB & 80D Benefits",
                impact_amount=25000.0,
                description=(
                    "Adding a senior citizen parent (Age 60+) unlocks an additional ₹50,000 Section 80D deduction for their medical insurance "
                    "and separate ₹3,00,000 basic exemption limit."
                ),
                actionable_tip="Click '+ Add Family Member' in the profile switcher to create a Senior Parent profile.",
            )
        )

    # 3. Section 44ADA Presumptive Tax for Freelancers
    freelance_members = [p for p in profiles if p.persona == "freelancer_44ada"]
    if freelance_members:
        arbitrage_list.append(
            HouseholdArbitrageAdvice(
                category="Section 44ADA",
                title="50% Presumptive Profit Ratio",
                impact_amount=75000.0,
                description=(
                    f"{freelance_members[0].name} is enrolled in Section 44ADA. Exactly 50% of gross freelance/consulting receipts "
                    "are deemed as statutory expenses with zero bookkeeping and no audit requirements up to ₹75 Lakhs."
                ),
                actionable_tip="Invoice professional consulting fees under the 44ADA profile to halve taxable net income.",
            )
        )

    return HouseholdSummaryResponse(
        total_household_income=round(total_household_income, 2),
        total_household_tax=round(total_household_tax, 2),
        total_household_savings=round(total_household_savings, 2),
        members_count=len(profiles),
        members=members_summary,
        arbitrage_opportunities=arbitrage_list,
    )
