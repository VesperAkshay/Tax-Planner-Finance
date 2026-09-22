"""
Career Switch & Offer Letter Decoder Endpoints.
Provides:
- POST /career/decode-offer: Detailed CTC breakdown, real in-hand cash, and trap detection.
- POST /career/simulate-switch: Dual-employer mid-year switch tax simulator (double standard deduction cliff + 234B/C interest).
- POST /career/compare-offers: In-hand cash comparison between current CTC and new offers.
- POST /career/generate-form-12b: Generates statutory Form 12B statement text & particulars.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.career_switch.switch_engine import (
    compare_two_offers,
    decode_offer_ctc,
    simulate_midyear_switch,
)
from app.models.user import User

router = APIRouter(prefix="/career", tags=["Career Switch & Offer Decoder"])


# ==============================================================================
# Request & Response Schemas
# ==============================================================================


class DecodeOfferRequest(BaseModel):
    ctc: float = Field(..., ge=0.0, description="Annual Cost-to-Company (CTC) in INR")
    basic: Optional[float] = Field(None, ge=0.0, description="Annual basic pay (defaults to 40% of CTC)")
    hra: Optional[float] = Field(None, ge=0.0, description="Annual HRA (defaults to 40% of Basic)")
    special_allowance: Optional[float] = Field(None, ge=0.0, description="Annual Special Allowance")
    variable_pay: float = Field(0.0, ge=0.0, description="Performance or annual variable pay")
    joining_bonus: float = Field(0.0, ge=0.0, description="One-time joining or sign-on bonus")
    bonus_clawback_months: int = Field(12, ge=0, le=60, description="Clawback lock-in duration in months")
    esop_annual: float = Field(0.0, ge=0.0, description="Annual vested value of stock options / RSUs")
    gratuity_included: bool = Field(True, description="Whether 4.81% gratuity is included inside CTC")
    employer_pf_included: bool = Field(True, description="Whether 12% employer PF is included inside CTC")
    medical_insurance_annual: float = Field(0.0, ge=0.0, description="Group medical insurance premium in CTC")


class SimulateSwitchRequest(BaseModel):
    company_a_months: int = Field(6, ge=1, le=11, description="Months worked at previous employer (e.g. 6 for Apr-Sep)")
    company_a_gross: float = Field(..., ge=0.0, description="Total gross salary paid by Company A")
    company_a_tds: float = Field(0.0, ge=0.0, description="Total TDS already deducted by Company A")
    company_a_epf: float = Field(0.0, ge=0.0, description="Total Employee PF deducted by Company A")
    company_b_months: int = Field(6, ge=1, le=11, description="Remaining months at new employer (e.g. 6 for Oct-Mar)")
    company_b_monthly_gross: float = Field(..., ge=0.0, description="Offered monthly gross salary at Company B")


class CompareOffersRequest(BaseModel):
    current_ctc: float = Field(..., ge=0.0, description="Current annual CTC in INR")
    offer_a_ctc: float = Field(..., ge=0.0, description="Offer A annual CTC in INR")
    offer_b_ctc: Optional[float] = Field(None, ge=0.0, description="Optional Offer B annual CTC in INR")


class Form12BRequest(BaseModel):
    company_a_name: str = Field(..., description="Name of previous employer (Company A)")
    company_a_tan: Optional[str] = Field("BLRK12345D", description="TAN of previous employer")
    company_a_gross: float = Field(..., ge=0.0)
    company_a_tds: float = Field(0.0, ge=0.0)
    company_a_epf: float = Field(0.0, ge=0.0)
    period_start: str = Field("01-Apr-2024", description="Start of tenure at Company A in FY")
    period_end: str = Field("30-Sep-2024", description="Last working day at Company A")


# ==============================================================================
# Endpoints
# ==============================================================================


@router.post("/decode-offer", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def decode_offer_endpoint(
    payload: DecodeOfferRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Decodes an annual CTC offer into real monthly in-hand take-home pay,
    flags hidden contract traps (gratuity vesting, clawbacks, Special Allowance penalty),
    and generates an AI salary restructuring counter-proposal.
    """
    return decode_offer_ctc(
        ctc=payload.ctc,
        basic=payload.basic,
        hra=payload.hra,
        special_allowance=payload.special_allowance,
        variable_pay=payload.variable_pay,
        joining_bonus=payload.joining_bonus,
        bonus_clawback_months=payload.bonus_clawback_months,
        esop_annual=payload.esop_annual,
        gratuity_included=payload.gratuity_included,
        employer_pf_included=payload.employer_pf_included,
        medical_insurance_annual=payload.medical_insurance_annual,
    )


@router.post("/simulate-switch", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def simulate_switch_endpoint(
    payload: SimulateSwitchRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Simulates a mid-year job switch across two employers.
    Calculates the surprise tax demand caused by double standard deductions and sequential slabs,
    computes Section 234B/C interest, and provides Form 12B remediation.
    """
    if payload.company_a_months + payload.company_b_months > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total months across Company A and Company B cannot exceed 12 months in a financial year.",
        )

    return simulate_midyear_switch(
        company_a_months=payload.company_a_months,
        company_a_gross=payload.company_a_gross,
        company_a_tds=payload.company_a_tds,
        company_a_epf=payload.company_a_epf,
        company_b_months=payload.company_b_months,
        company_b_monthly_gross=payload.company_b_monthly_gross,
    )


@router.post("/compare-offers", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def compare_offers_endpoint(
    payload: CompareOffersRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Compares current salary against Offer A and optional Offer B
    on guaranteed monthly in-hand take-home cash after statutory taxes.
    """
    return compare_two_offers(
        current_ctc=payload.current_ctc,
        offer_a_ctc=payload.offer_a_ctc,
        offer_b_ctc=payload.offer_b_ctc,
    )


@router.post("/generate-form-12b", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def generate_form_12b_endpoint(
    payload: Form12BRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Generates a statutory Form 12B declaration under Section 192(2) of the Income Tax Act
    for the employee to submit to their new employer.
    """
    user_name = current_user.full_name or "Taxpayer"
    user_pan = current_user.pan or "NOT_SPECIFIED"

    form_text = (
        "================================================================================\n"
        "FORM NO. 12B\n"
        "[See rule 26A of Income Tax Rules, 1962]\n"
        "Form for furnishing details of income under section 192(2) for the year ending 31st March, 2025\n"
        "================================================================================\n\n"
        f"1. Name and address of the employee: {user_name}\n"
        f"2. Permanent Account Number (PAN): {user_pan}\n"
        f"3. Name of Previous Employer: {payload.company_a_name}\n"
        f"4. TAN of Previous Employer: {payload.company_a_tan or 'N/A'}\n"
        f"5. Period of Employment during the year: From {payload.period_start} to {payload.period_end}\n\n"
        "PARTICULARS OF SALARY PAID AND TAX DEDUCTED AT SOURCE BY PREVIOUS EMPLOYER:\n"
        f"  a) Total Amount of Salary Paid: ₹{payload.company_a_gross:,.2f}\n"
        f"  b) Total Amount of Tax Deducted at Source (TDS): ₹{payload.company_a_tds:,.2f}\n"
        f"  c) Total Employee Provident Fund (PF) Deducted: ₹{payload.company_a_epf:,.2f}\n\n"
        "VERIFICATION:\n"
        f"I, {user_name}, do hereby declare that what is stated above is true to the best of my knowledge and belief.\n\n"
        f"Signature of Employee: ___________________________\n"
        f"Date: ___________________________\n"
        "================================================================================\n"
    )

    return {
        "employee_name": user_name,
        "employee_pan": user_pan,
        "company_a_name": payload.company_a_name,
        "company_a_tan": payload.company_a_tan,
        "gross_salary": payload.company_a_gross,
        "tds_deducted": payload.company_a_tds,
        "epf_deducted": payload.company_a_epf,
        "period": f"{payload.period_start} to {payload.period_end}",
        "raw_form_text": form_text,
    }
