"""
Tax Planning Agent Conversation Endpoints (Task 8.5 & v1.1 Phase 13).

Wired directly to Phase 13 Proactive Stateful Elicitation, LangGraph state machine,
Phase 6 RAG citations, and Phase 5 tax engine comparator. Automatically persists
elicited deductions into the user_declared_deductions and elicitation_progress tables.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.agent.elicitation import CANONICAL_SECTIONS_ORDER
from app.agent.graph import run_tax_planning_agent, step_tax_planning_agent
from app.agent.llm_client import extract_deductions_from_text, generate_llm_explanation
from app.agent.persistence import (
    load_elicitation_state,
    persist_all_elicited_deductions,
    record_elicited_deduction,
    save_elicitation_step,
)
from app.agent.state import TaxPlanningState
from app.api.auth import get_current_user
from app.database import get_db_session
from app.models.account import Account
from app.models.elicitation_progress import ElicitationProgress, ElicitationStateEnum
from app.models.salary_slip import SalarySlip
from app.models.transaction import Transaction
from app.models.user import User
from app.models.user_declared_deduction import UserDeclaredDeduction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Tax Agent"])


class AgentChatRequest(BaseModel):
    message: Optional[str] = Field(default="", description="User natural language message or query")
    user_responses: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Elicited deductions payload")
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Conversation history")
    session_id: Optional[str] = Field(default="default_session", description="Conversation session ID")
    gross_income: Optional[float] = Field(default=None, ge=0.0, description="Gross annual income in INR")
    is_salaried: bool = Field(default=True, description="Whether standard deduction applies")


class AgentChatResponse(BaseModel):
    session_id: str
    visited_nodes: List[str]
    skipped_nodes: List[str]
    has_hra_component: bool
    declared_deductions: Dict[str, Any]
    comparison_result: Optional[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    message: str
    current_section: Optional[str] = None
    sections_pending: Optional[List[str]] = None
    is_completed: bool = False


@router.post("/chat", response_model=AgentChatResponse)
def chat_with_tax_agent(
    payload: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> AgentChatResponse:
    """
    Starts or continues a conversation with the Tax Planning Agent (Task 8.5 & Task 13.3).
    Pulls salary slip data from DB, runs stateful proactive LangGraph state machine,
    retrieves RAG citations, delegates deterministic calculations to Phase 5,
    and persists progress and elicited deductions to DB.
    """
    fy = "2025-2026"

    # 1. Fetch user's salary slips to extract baseline compensation & HRA
    slips = session.exec(
        select(SalarySlip)
        .where(SalarySlip.user_id == current_user.id)
        .order_by(SalarySlip.year.desc(), SalarySlip.month.desc())
    ).all()

    salary_slip_data: Optional[Dict[str, Any]] = None
    derived_gross = payload.gross_income

    if slips:
        if len(slips) >= 12:
            annual_basic = sum(s.basic for s in slips[:12])
            annual_hra = sum(s.hra for s in slips[:12])
            annual_gross = sum(s.gross_pay for s in slips[:12])
            annual_pf = sum(s.employee_pf for s in slips[:12])
        else:
            latest = slips[0]
            annual_basic = latest.basic * 12.0
            annual_hra = latest.hra * 12.0
            annual_gross = latest.gross_pay * 12.0
            annual_pf = latest.employee_pf * 12.0

        salary_slip_data = {
            "basic": annual_basic,
            "hra": annual_hra,
            "gross_pay": annual_gross,
            "employee_pf": annual_pf,
        }
        if derived_gross is None:
            derived_gross = annual_gross

    # If gross income still not available, check credited salary transactions
    if derived_gross is None:
        salary_txns = session.exec(
            select(Transaction).where(Transaction.transaction_type == "credit")
        ).all()
        user_salary_txns = [t for t in salary_txns if t.account and t.account.user_id == current_user.id]
        if user_salary_txns:
            derived_gross = sum(t.amount for t in user_salary_txns)
        else:
            derived_gross = 0.0

    # 2. Load persistent elicitation progress for this user (Task 13.7)
    elicitation = load_elicitation_state(session=session, user_id=current_user.id, financial_year=fy)

    # Pre-populate any existing deductions already saved in DB
    existing_deductions = session.exec(
        select(UserDeclaredDeduction)
        .where(UserDeclaredDeduction.user_id == current_user.id)
        .where(UserDeclaredDeduction.financial_year == fy)
    ).all()

    combined_responses = dict(payload.user_responses or {})
    for ed in existing_deductions:
        sec = ed.section or ""
        if sec not in combined_responses:
            combined_responses[sec] = ed.metadata_json if ed.metadata_json else ed.amount

    user_msg = (payload.message or "").strip()

    # 3. Execution: batch evaluation vs proactive step
    if payload.user_responses:
        stepped_state = run_tax_planning_agent(
            gross_income=derived_gross,
            user_responses=combined_responses,
            salary_slip_data=salary_slip_data,
            is_salaried=payload.is_salaried,
            user_id=current_user.id,
            interactive_mode=False,
        )
    else:
        initial_state = TaxPlanningState(
            user_id=current_user.id,
            financial_year=fy,
            gross_income=derived_gross,
            salary_slip_data=salary_slip_data,
            is_salaried=payload.is_salaried,
            user_responses=combined_responses,
            elicitation=elicitation,
            messages=payload.history or [],
            is_interactive=True,
        )
        stepped_state = step_tax_planning_agent(initial_state, user_message=user_msg if user_msg else None)

    # 4. Persist newly answered or skipped sections into DB (Task 13.4)
    for sec, ans in stepped_state.elicitation.sections_answered.items():
        if sec not in elicitation.sections_answered:
            amt = float(ans.get("amount", 0.0) if isinstance(ans.get("amount"), (int, float)) else 0.0)
            meta = ans.get("metadata") if isinstance(ans.get("metadata"), dict) else None
            record_elicited_deduction(
                session=session,
                user_id=current_user.id,
                section=sec,
                amount=amt,
                status=ans.get("status", "declared"),
                financial_year=fy,
                metadata_json=meta,
                source="agent_elicited",
            )

    for sec, reason in stepped_state.elicitation.sections_skipped.items():
        if sec not in elicitation.sections_skipped:
            save_elicitation_step(
                session=session,
                user_id=current_user.id,
                section_code=sec,
                state=ElicitationStateEnum.skipped,
                financial_year=fy,
                skip_reason=reason,
            )

    # Persist all declared deductions
    if stepped_state.declared_deductions:
        persist_all_elicited_deductions(
            session=session,
            user_id=current_user.id,
            declared_deductions=stepped_state.declared_deductions,
            financial_year=fy,
        )

    # 5. Fetch bank cashflow stats to equip assistant with full financial context
    user_txns = session.exec(
        select(Transaction).join(Account).where(Account.user_id == current_user.id)
    ).all()
    total_credits = sum(t.amount for t in user_txns if t.transaction_type == "credit")
    total_debits = sum(t.amount for t in user_txns if t.transaction_type == "debit")
    net_cashflow = total_credits - total_debits

    financial_profile = {
        "monthly_gross": slips[0].gross_pay if slips else (derived_gross / 12.0 if derived_gross else 0.0),
        "monthly_net": slips[0].net_pay if slips else 0.0,
        "monthly_basic": slips[0].basic if slips else (annual_basic / 12.0 if slips else 0.0),
        "monthly_hra": slips[0].hra if slips else (annual_hra / 12.0 if slips else 0.0),
        "monthly_pf": slips[0].employee_pf if slips else (annual_pf / 12.0 if slips else 0.0),
        "monthly_pt": slips[0].professional_tax if slips and slips[0].professional_tax is not None else 200.0,
        "annual_gross": derived_gross or 0.0,
        "total_credits": total_credits,
        "total_debits": total_debits,
        "net_cashflow": net_cashflow,
        "txns_count": len(user_txns),
    }

    # 6. Formulate bot message
    ca_disclaimer = (
        "\n\n⚠️ **Disclaimer**: *This analysis is an automated suggestion based on your uploaded records "
        "and Income Tax Act rules (FY 2025–26). Please consult a certified Chartered Accountant (CA) "
        "or tax professional for official tax filing and personalized planning.*"
    )

    is_completed = len(stepped_state.elicitation.sections_pending) == 0

    if stepped_state.redirect_message:
        bot_message = stepped_state.redirect_message
    elif not is_completed:
        bot_message = stepped_state.current_agent_message or "Let's review your eligible statutory deductions."
    else:
        report = stepped_state.final_report
        if report:
            rec = report.get("recommended_regime", "new").upper()
            savings = report.get("tax_savings", 0.0)
            bot_message = (
                f"🎉 **Deduction Audit Complete!**\n\n"
                f"Based on your profile and declared deductions, the **{rec} Regime** is recommended. "
                f"You save ₹{savings:,.2f} in taxes.\n\n"
                f"{report.get('summary', '')}"
                f"{ca_disclaimer}"
            )
        else:
            bot_message = f"Your deduction audit is complete.{ca_disclaimer}"

    return AgentChatResponse(
        session_id=payload.session_id or "default_session",
        visited_nodes=stepped_state.visited_nodes,
        skipped_nodes=stepped_state.skipped_nodes,
        has_hra_component=stepped_state.has_hra_component,
        declared_deductions=stepped_state.declared_deductions,
        comparison_result=stepped_state.comparison_result,
        citations=stepped_state.citations,
        final_report=stepped_state.final_report,
        message=bot_message,
        current_section=stepped_state.elicitation.current_section,
        sections_pending=stepped_state.elicitation.sections_pending,
        is_completed=is_completed,
    )


@router.get("/progress")
def get_elicitation_progress(
    financial_year: str = "2025-2026",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Returns the user's current proactive elicitation audit progress (Task 13.1).
    """
    state = load_elicitation_state(session=session, user_id=current_user.id, financial_year=financial_year)
    total = len(CANONICAL_SECTIONS_ORDER)
    resolved = len(state.sections_answered) + len(state.sections_skipped)
    return {
        "financial_year": financial_year,
        "total_sections": total,
        "resolved_count": resolved,
        "pending_count": len(state.sections_pending),
        "answered_count": len(state.sections_answered),
        "skipped_count": len(state.sections_skipped),
        "completion_percentage": round((resolved / total) * 100, 1) if total > 0 else 100.0,
        "current_section": state.current_section,
        "sections_pending": state.sections_pending,
        "sections_answered": state.sections_answered,
        "sections_skipped": state.sections_skipped,
        "is_completed": len(state.sections_pending) == 0,
    }


@router.post("/reset")
def reset_elicitation_progress(
    financial_year: str = "2025-2026",
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Resets elicitation progress and agent-elicited deductions for the specified FY.
    """
    prog_records = session.exec(
        select(ElicitationProgress)
        .where(ElicitationProgress.user_id == current_user.id)
        .where(ElicitationProgress.financial_year == financial_year)
    ).all()
    for p in prog_records:
        session.delete(p)

    ded_records = session.exec(
        select(UserDeclaredDeduction)
        .where(UserDeclaredDeduction.user_id == current_user.id)
        .where(UserDeclaredDeduction.financial_year == financial_year)
    ).all()
    for d in ded_records:
        session.delete(d)

    session.commit()
    return {"success": True, "message": f"Deduction elicitation progress reset for FY {financial_year}."}
