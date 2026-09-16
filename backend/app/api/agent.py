"""
Tax Planning Agent Conversation Endpoints (Task 8.5).

Wired directly to Phase 7 LangGraph state machine, Phase 6 RAG citations,
and Phase 5 tax engine comparator. Automatically persists elicited deductions
into the user_declared_deductions table.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.agent.graph import run_tax_planning_agent
from app.agent.llm_client import extract_deductions_from_text, generate_llm_explanation
from app.agent.persistence import persist_all_elicited_deductions
from app.api.auth import get_current_user
from app.database import get_db_session
from app.models.account import Account
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


@router.post("/chat", response_model=AgentChatResponse)
def chat_with_tax_agent(
    payload: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> AgentChatResponse:
    """
    Starts or continues a conversation with the Tax Planning Agent (Task 8.5).
    Pulls salary slip data from DB, runs LangGraph state machine, retrieves RAG citations,
    delegates calculation to Phase 5, and persists elicited deductions into the database.
    """
    # 1. Fetch user's salary slips to extract baseline compensation & HRA
    slips = session.exec(
        select(SalarySlip)
        .where(SalarySlip.user_id == current_user.id)
        .order_by(SalarySlip.year.desc(), SalarySlip.month.desc())
    ).all()

    salary_slip_data: Optional[Dict[str, Any]] = None
    derived_gross = payload.gross_income

    if slips:
        # Sum or annualize latest slip if 1 month
        if len(slips) >= 12:
            annual_basic = sum(s.basic for s in slips[:12])
            annual_hra = sum(s.hra for s in slips[:12])
            annual_gross = sum(s.gross_pay for s in slips[:12])
            annual_pf = sum(s.employee_pf for s in slips[:12])
        else:
            # Annualize from recent slip
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
            select(Transaction)
            .where(Transaction.transaction_type == "credit")
        ).all()
        user_salary_txns = [t for t in salary_txns if t.account and t.account.user_id == current_user.id]
        if user_salary_txns:
            derived_gross = sum(t.amount for t in user_salary_txns)
        else:
            derived_gross = 0.0

    # 2. Extract deductions from user message & merge with existing inputs
    extracted = extract_deductions_from_text(payload.message or "")
    combined_responses = dict(payload.user_responses or {})
    combined_responses.update(extracted)

    # Pre-populate any existing deductions already saved in DB
    existing_deductions = session.exec(
        select(UserDeclaredDeduction).where(UserDeclaredDeduction.user_id == current_user.id)
    ).all()
    section_to_key = {
        "80C": "80c",
        "80D": "80d",
        "80CCD(1B)": "80ccd_1b",
        "80G": "80g",
        "24B": "24b",
        "HRA": "hra",
    }
    for ed in existing_deductions:
        clean_sec = (ed.section or "").strip().upper()
        sec_key = section_to_key.get(clean_sec, clean_sec.lower().replace("-", "_").replace(" ", "_"))
        if sec_key not in combined_responses:
            if ed.metadata_json and isinstance(ed.metadata_json, dict):
                combined_responses[sec_key] = ed.metadata_json
            else:
                combined_responses[sec_key] = ed.amount

    # 3. Run LangGraph Tax Planning Agent (Phase 7)
    final_state = run_tax_planning_agent(
        gross_income=derived_gross,
        user_responses=combined_responses,
        salary_slip_data=salary_slip_data,
        is_salaried=payload.is_salaried,
        user_id=current_user.id,
    )

    # 4. Persist elicited deductions into user_declared_deductions (Task 7.3)
    if final_state.declared_deductions:
        persist_all_elicited_deductions(
            session=session,
            user_id=current_user.id,
            declared_deductions=final_state.declared_deductions,
            financial_year=final_state.financial_year,
        )

    # 5. Fetch bank cashflow stats to equip assistant with full financial profile
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

    # 6. Generate conversational explanation via OpenRouter / LLM with deterministic fallback
    llm_message = None
    if payload.message and payload.message.strip():
        llm_message = generate_llm_explanation(
            user_query=payload.message,
            history=payload.history or [],
            comparison=final_state.comparison_result or {},
            citations=final_state.citations,
            declared_deductions=final_state.declared_deductions,
            gross_income=derived_gross,
            financial_profile=financial_profile,
        )

    ca_disclaimer = (
        "\n\n⚠️ **Disclaimer**: *This analysis is an automated suggestion based on your uploaded records "
        "and Income Tax Act rules (FY 2025–26). Please consult a certified Chartered Accountant (CA) "
        "or tax professional for official tax filing and personalized planning.*"
    )

    if llm_message:
        bot_message = llm_message
    else:
        report = final_state.final_report
        if report:
            rec = report.get("recommended_regime", "new").upper()
            savings = report.get("tax_savings", 0.0)
            bot_message = (
                f"Based on your profile and deductions, the **{rec} Regime** is recommended. "
                f"You save ₹{savings:,.2f} in taxes. "
                f"{report.get('summary', '')}"
                f"{ca_disclaimer}"
            )
        else:
            bot_message = f"Your financial inputs have been processed.{ca_disclaimer}"

    return AgentChatResponse(
        session_id=payload.session_id or "default_session",
        visited_nodes=final_state.visited_nodes,
        skipped_nodes=final_state.skipped_nodes,
        has_hra_component=final_state.has_hra_component,
        declared_deductions=final_state.declared_deductions,
        comparison_result=final_state.comparison_result,
        citations=final_state.citations,
        final_report=final_state.final_report,
        message=bot_message,
    )
