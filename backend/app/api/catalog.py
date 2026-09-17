"""
Deduction Catalog API Router (v1.1 Phase 14: Tasks 14.1 - 14.7).

Provides:
- 14.1: List all statutory deduction rows from deduction_catalog with caps and user status.
- 14.2: Edit affordance for existing agent-elicited or self-added deductions without duplication.
- 14.3: Self-add deduction endpoint setting source = 'catalog_self_added'.
- 14.4: Eligibility verification enforcement for requires_eligibility_check = True sections.
- 14.5: Live cap tracking (cap amount, used amount, remaining headroom, utilization percentage).
- 14.7: Completion checkpoint tracking (catalog viewed confirmation for final report).
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.agent.persistence import save_elicitation_step
from app.api.auth import get_current_user
from app.database import get_db_session
from app.models.deduction_catalog import DeductionCatalog
from app.models.elicitation_progress import ElicitationProgress, ElicitationStateEnum
from app.models.user import User
from app.models.user_declared_deduction import DeductionSource, DeductionStatus, UserDeclaredDeduction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalog", tags=["Deduction Catalog"])

CATALOG_VIEWED_SECTION_CODE = "__CATALOG_VIEWED__"


class DeductionCatalogItemResponse(BaseModel):
    id: str
    section_code: str
    display_name: str
    description: str
    applicable_regimes: str
    cap_type: str
    cap_amount: Optional[float] = None
    cap_formula: Optional[str] = None
    requires_eligibility_check: bool
    # User's current declared status
    declared_amount: Optional[float] = None
    declared_status: Optional[str] = None
    source: Optional[str] = None
    elicitation_state: Optional[str] = None
    skip_reason: Optional[str] = None
    # Live cap tracking (Task 14.5)
    remaining_cap: Optional[float] = None
    used_percentage: Optional[float] = None
    is_editable: bool = True


class CatalogListResponse(BaseModel):
    financial_year: str
    total_sections: int
    declared_count: int
    total_declared_deductions: float
    catalog_viewed: bool
    catalog_viewed_at: Optional[datetime] = None
    sections: List[DeductionCatalogItemResponse]


class SelfAddDeductionRequest(BaseModel):
    section_code: str = Field(description="Statutory section code, e.g. 80C, 80G, 80D")
    amount: float = Field(ge=0.0, description="Deduction amount in INR")
    financial_year: str = Field(default="2025-2026", description="Financial year")
    eligibility_confirmed: bool = Field(default=False, description="User confirmation of statutory eligibility criteria")
    metadata_json: Optional[Dict[str, Any]] = Field(default=None, description="Detailed sub-limits, institution info, or breakdown")


class SelfAddDeductionResponse(BaseModel):
    success: bool
    message: str
    section_code: str
    amount: float
    source: str
    remaining_cap: Optional[float] = None
    cap_amount: Optional[float] = None


@router.get("", response_model=CatalogListResponse)
def get_deduction_catalog(
    financial_year: str = Query(default="2025-2026"),
    mark_viewed: bool = Query(default=True, description="Record catalog viewed checkpoint (Task 14.7)"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> CatalogListResponse:
    """
    Lists the complete statutory deduction catalog with live cap tracking,
    user declarations, and satisfies the completion checkpoint (Tasks 14.1, 14.2, 14.5, 14.7).
    """
    # 1. Fetch all catalog rows
    catalog_items = session.exec(select(DeductionCatalog)).all()

    # 2. Fetch user's declarations for this FY
    declarations = session.exec(
        select(UserDeclaredDeduction)
        .where(UserDeclaredDeduction.user_id == current_user.id)
        .where(UserDeclaredDeduction.financial_year == financial_year)
    ).all()
    decl_map: Dict[str, UserDeclaredDeduction] = {
        d.section.strip().upper(): d for d in declarations if d.section
    }

    # 3. Fetch user's elicitation progress
    progress_records = session.exec(
        select(ElicitationProgress)
        .where(ElicitationProgress.user_id == current_user.id)
        .where(ElicitationProgress.financial_year == financial_year)
    ).all()
    prog_map: Dict[str, ElicitationProgress] = {
        p.section_code.strip().upper(): p for p in progress_records if p.section_code
    }

    # 4. Checkpoint tracking: check and optionally mark catalog as viewed (Task 14.7)
    checkpoint = prog_map.get(CATALOG_VIEWED_SECTION_CODE)
    catalog_viewed = checkpoint is not None
    catalog_viewed_at = checkpoint.updated_at if checkpoint else None

    if mark_viewed and not catalog_viewed:
        checkpoint = save_elicitation_step(
            session=session,
            user_id=current_user.id,
            section_code=CATALOG_VIEWED_SECTION_CODE,
            state=ElicitationStateEnum.answered,
            financial_year=financial_year,
            skip_reason="Catalog view checkpoint satisfied",
        )
        catalog_viewed = True
        catalog_viewed_at = checkpoint.updated_at

    # 5. Build enriched response with live cap tracking (Task 14.5)
    sections_response: List[DeductionCatalogItemResponse] = []
    total_declared = 0.0
    declared_count = 0

    for item in catalog_items:
        clean_code = item.section_code.strip().upper()
        user_decl = decl_map.get(clean_code)
        prog = prog_map.get(clean_code)

        decl_amt = float(user_decl.amount) if user_decl else None
        decl_status = user_decl.status.value if user_decl and hasattr(user_decl.status, "value") else (str(user_decl.status) if user_decl else None)
        decl_source = user_decl.source.value if user_decl and hasattr(user_decl.source, "value") else (str(user_decl.source) if user_decl else None)

        if decl_amt and decl_amt > 0 and decl_status == "declared":
            total_declared += decl_amt
            declared_count += 1

        elicit_state = prog.state.value if prog and hasattr(prog.state, "value") else (str(prog.state) if prog else "pending")
        skip_reason = prog.skip_reason if prog else None

        # Live cap tracking
        remaining_cap = None
        used_pct = None
        if item.cap_amount is not None and item.cap_amount > 0:
            claimed = decl_amt or 0.0
            remaining_cap = max(0.0, round(item.cap_amount - claimed, 2))
            used_pct = min(100.0, round((claimed / item.cap_amount) * 100.0, 1))

        sections_response.append(
            DeductionCatalogItemResponse(
                id=str(item.id),
                section_code=item.section_code,
                display_name=item.display_name,
                description=item.description,
                applicable_regimes=item.applicable_regimes,
                cap_type=item.cap_type,
                cap_amount=item.cap_amount,
                cap_formula=item.cap_formula,
                requires_eligibility_check=item.requires_eligibility_check,
                declared_amount=decl_amt,
                declared_status=decl_status,
                source=decl_source,
                elicitation_state=elicit_state,
                skip_reason=skip_reason,
                remaining_cap=remaining_cap,
                used_percentage=used_pct,
                is_editable=True,
            )
        )

    return CatalogListResponse(
        financial_year=financial_year,
        total_sections=len(catalog_items),
        declared_count=declared_count,
        total_declared_deductions=round(total_declared, 2),
        catalog_viewed=catalog_viewed,
        catalog_viewed_at=catalog_viewed_at,
        sections=sections_response,
    )


@router.post("/declare", response_model=SelfAddDeductionResponse)
def self_add_deduction(
    payload: SelfAddDeductionRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> SelfAddDeductionResponse:
    """
    Self-adds or updates a deduction entry from the catalog view (Tasks 14.2, 14.3, 14.4, 14.9).
    - Enforces eligibility confirmation check if required (Task 14.4).
    - Updates existing record if already declared to avoid duplicates (Task 14.2 & 14.9).
    - Sets source = 'catalog_self_added' when newly created (Task 14.3).
    - Updates elicitation progress to 'answered'.
    """
    clean_code = payload.section_code.strip()

    # 1. Validate section exists in catalog
    catalog_item = session.exec(
        select(DeductionCatalog).where(DeductionCatalog.section_code == clean_code)
    ).first()

    if not catalog_item:
        # Check case-insensitive match
        all_items = session.exec(select(DeductionCatalog)).all()
        for item in all_items:
            if item.section_code.upper() == clean_code.upper():
                catalog_item = item
                clean_code = item.section_code
                break

    if not catalog_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section '{clean_code}' does not exist in the statutory deduction catalog.",
        )

    # 2. Eligibility check enforcement (Task 14.4)
    if catalog_item.requires_eligibility_check and not payload.eligibility_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Statutory eligibility confirmation is required for Section {clean_code}. "
                "Please confirm eligibility criteria before submitting."
            ),
        )

    # 3. Duplicate protection / Edit affordance (Task 14.2 & 14.9)
    existing = session.exec(
        select(UserDeclaredDeduction)
        .where(UserDeclaredDeduction.user_id == current_user.id)
        .where(UserDeclaredDeduction.financial_year == payload.financial_year)
        .where(UserDeclaredDeduction.section == clean_code)
    ).first()

    now_utc = datetime.now(timezone.utc)
    target_status = DeductionStatus.declared if payload.amount > 0 else DeductionStatus.not_applicable

    if existing:
        # Update existing record — NEVER create duplicate (Task 14.9)
        existing.amount = payload.amount
        existing.status = target_status
        existing.metadata_json = payload.metadata_json
        existing.updated_at = now_utc
        session.add(existing)
        session.commit()
        session.refresh(existing)
        rec = existing
        msg = f"Deduction for Section {clean_code} updated successfully to ₹{payload.amount:,.2f}."
    else:
        # Create new record with source = catalog_self_added (Task 14.3)
        rec = UserDeclaredDeduction(
            user_id=current_user.id,
            financial_year=payload.financial_year,
            section=clean_code,
            amount=payload.amount,
            source=DeductionSource.catalog_self_added,
            status=target_status,
            metadata_json=payload.metadata_json,
            created_at=now_utc,
            updated_at=now_utc,
        )
        session.add(rec)
        session.commit()
        session.refresh(rec)
        msg = f"Deduction for Section {clean_code} self-added successfully with amount ₹{payload.amount:,.2f}."

    # 4. Mark elicitation progress as answered
    save_elicitation_step(
        session=session,
        user_id=current_user.id,
        section_code=clean_code,
        state=ElicitationStateEnum.answered,
        financial_year=payload.financial_year,
    )

    # Calculate remaining cap
    remaining = None
    if catalog_item.cap_amount is not None:
        remaining = max(0.0, round(catalog_item.cap_amount - payload.amount, 2))

    return SelfAddDeductionResponse(
        success=True,
        message=msg,
        section_code=clean_code,
        amount=payload.amount,
        source=rec.source.value if hasattr(rec.source, "value") else str(rec.source),
        remaining_cap=remaining,
        cap_amount=catalog_item.cap_amount,
    )


@router.post("/viewed")
def mark_catalog_viewed(
    financial_year: str = "2025-2026",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Explicitly satisfies the catalog completion checkpoint for the financial year (Task 14.7).
    """
    checkpoint = save_elicitation_step(
        session=session,
        user_id=current_user.id,
        section_code=CATALOG_VIEWED_SECTION_CODE,
        state=ElicitationStateEnum.answered,
        financial_year=financial_year,
        skip_reason="Catalog view checkpoint satisfied",
    )
    return {
        "success": True,
        "catalog_viewed": True,
        "financial_year": financial_year,
        "viewed_at": checkpoint.updated_at.isoformat(),
    }


@router.get("/checkpoint")
def get_catalog_checkpoint(
    financial_year: str = "2025-2026",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Checks if the user has satisfied the catalog viewing checkpoint for this FY (Task 14.7).
    """
    rec = session.exec(
        select(ElicitationProgress)
        .where(ElicitationProgress.user_id == current_user.id)
        .where(ElicitationProgress.financial_year == financial_year)
        .where(ElicitationProgress.section_code == CATALOG_VIEWED_SECTION_CODE)
    ).first()
    return {
        "financial_year": financial_year,
        "catalog_viewed": rec is not None,
        "viewed_at": rec.updated_at.isoformat() if rec else None,
    }
