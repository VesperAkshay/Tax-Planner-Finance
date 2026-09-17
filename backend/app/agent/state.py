"""
State schema for the Tax Planning Agent (Task 7.1 & Task 13.1).

Represents conversational context, user financial inputs, salary slip data,
proactive elicitation state (pending, answered, skipped sections),
visited/skipped node execution history, and Phase 5/6 results.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ElicitationAnswer(BaseModel):
    """Represents a resolved deduction answer for a single catalog section."""
    section_code: str
    status: str = "declared"  # "declared" | "not_applicable"
    amount: float = 0.0
    source: str = "agent_elicited"
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class ElicitationState(BaseModel):
    """
    Tracks stateful, proactive deduction elicitation completeness per user per FY (Task 13.1).
    Backed by the elicitation_progress table.
    """
    financial_year: str = "2025-2026"
    sections_pending: List[str] = Field(default_factory=list)
    sections_answered: Dict[str, Any] = Field(default_factory=dict)
    sections_skipped: Dict[str, str] = Field(default_factory=dict)
    current_section: Optional[str] = None


class TaxPlanningState(BaseModel):
    """
    State object passed between nodes in the LangGraph Tax Planning State Machine.
    """

    user_id: int = 1
    session_id: str = "default_session"
    financial_year: str = "2025-2026"

    # User profile & income
    gross_income: float = 0.0
    is_salaried: bool = True
    is_senior_citizen: bool = False
    has_dependent_parents: bool = True
    user_profile: Optional[Dict[str, Any]] = None
    is_interactive: bool = False

    # Real-world coverage fields (Phase 17)
    detected_savings_interest: float = 0.0
    detected_capital_gains_warning: Optional[str] = None
    detected_arrears_warning: Optional[str] = None

    # Salary slip information (from document parsing)
    salary_slip_data: Optional[Dict[str, Any]] = None
    has_hra_component: bool = True

    # Elicitation state tracking (Task 13.1)
    elicitation: ElicitationState = Field(default_factory=ElicitationState)

    # User-declared inputs collected across deduction topics
    user_responses: Dict[str, Any] = Field(default_factory=dict)

    # Normalized deductions dictionary passed to Phase 5 compare_regimes
    declared_deductions: Dict[str, Any] = Field(default_factory=dict)

    # Execution traceability: list of node names visited or explicitly skipped
    visited_nodes: List[str] = Field(default_factory=list)
    skipped_nodes: List[str] = Field(default_factory=list)

    # Conversational messages log
    messages: List[Dict[str, str]] = Field(default_factory=list)

    # Pure function calculation outputs (strictly zero LLM arithmetic)
    comparison_result: Optional[Dict[str, Any]] = None

    # Grounded citations retrieved from ChromaDB (Phase 6 RAG)
    citations: List[Dict[str, Any]] = Field(default_factory=list)

    # Final report generated for user
    final_report: Optional[Dict[str, Any]] = None

    # Proactive agent question or redirect message
    current_agent_message: Optional[str] = None
    redirect_message: Optional[str] = None
