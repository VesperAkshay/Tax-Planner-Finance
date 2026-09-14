"""
State schema for the Tax Planning Agent (Task 7.1).

Represents conversational context, user financial inputs, salary slip data,
elicited deductions, visited/skipped node execution history, and Phase 5/6 results.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


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

    # Salary slip information (from Phase 2 document parsing)
    salary_slip_data: Optional[Dict[str, Any]] = None
    has_hra_component: bool = True

    # User-declared inputs collected across deduction topics
    user_responses: Dict[str, Any] = Field(default_factory=dict)

    # Normalized deductions dictionary passed to Phase 5 compare_regimes
    declared_deductions: Dict[str, Any] = Field(default_factory=dict)

    # Execution traceability: list of node names visited or explicitly skipped
    visited_nodes: List[str] = Field(default_factory=list)
    skipped_nodes: List[str] = Field(default_factory=list)

    # Conversational messages log
    messages: List[Dict[str, str]] = Field(default_factory=list)

    # Pure function calculation outputs (Phase 5 - strictly zero LLM arithmetic)
    comparison_result: Optional[Dict[str, Any]] = None

    # Grounded citations retrieved from ChromaDB (Phase 6 RAG)
    citations: List[Dict[str, Any]] = Field(default_factory=list)

    # Final report generated for user
    final_report: Optional[Dict[str, Any]] = None
