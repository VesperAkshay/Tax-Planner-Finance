"""
Tax Planning Agent LangGraph State Machine (Tasks 7.1, 7.2, 7.4, 7.5).

Implements:
- 7.1 LangGraph state machine skeleton covering 80C, 80D, 80CCD(1B), 80G, Section 24b, HRA.
- 7.2 Conditional branching based on salary slip (skipping HRA node if salary slip shows no HRA).
- 7.4 Wiring end-of-conversation to Phase 5 compare_regimes (strictly zero LLM arithmetic).
- 7.5 Wiring Phase 6 RAG citations to agent output.
"""

import logging
from typing import Any, Dict, List, Optional
from langgraph.graph import END, START, StateGraph

from app.agent.state import TaxPlanningState
from app.rag.retriever import retrieve_tax_rules
from app.tax_engine.comparator import compare_regimes

logger = logging.getLogger(__name__)


# ==============================================================================
# Node Implementations
# ==============================================================================


def init_node(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Initializes conversation context and inspects salary slip data (Task 7.2).
    Determines whether the employee receives HRA and has an EPF baseline.
    """
    visited = list(state.visited_nodes)
    visited.append("init_node")

    has_hra = state.has_hra_component
    declared = dict(state.declared_deductions)

    if state.salary_slip_data:
        slip = state.salary_slip_data
        slip_hra = float(slip.get("hra", 0.0))
        # Task 7.2: If HRA is absent or zero on the slip, mark HRA as not applicable
        if slip_hra <= 0.0:
            has_hra = False
        else:
            has_hra = True

        # Pre-populate employee PF into 80C if reported on slip and not already declared
        emp_pf = float(slip.get("employee_pf", 0.0))
        if emp_pf > 0.0 and "section_80c" not in declared:
            declared["section_80c"] = emp_pf

    return {
        "visited_nodes": visited,
        "has_hra_component": has_hra,
        "declared_deductions": declared,
    }


def node_80c(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Elicits and records Section 80C deductions (PPF, EPF, ELSS, tuition fees, principal).
    """
    visited = list(state.visited_nodes)
    visited.append("node_80c")

    declared = dict(state.declared_deductions)
    # Check if user provided 80C response
    user_val = state.user_responses.get("80c", state.user_responses.get("section_80c"))
    if user_val is not None:
        declared["section_80c"] = float(user_val)

    return {
        "visited_nodes": visited,
        "declared_deductions": declared,
    }


def node_80d(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Elicits and records Section 80D medical insurance deductions (self, family, parents).
    """
    visited = list(state.visited_nodes)
    visited.append("node_80d")

    declared = dict(state.declared_deductions)
    user_val = state.user_responses.get("80d", state.user_responses.get("section_80d"))
    if user_val is not None:
        if isinstance(user_val, dict):
            declared["section_80d"] = user_val
        else:
            declared["section_80d"] = float(user_val)

    return {
        "visited_nodes": visited,
        "declared_deductions": declared,
    }


def node_80ccd_1b(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Elicits and records Section 80CCD(1B) additional NPS contributions.
    """
    visited = list(state.visited_nodes)
    visited.append("node_80ccd_1b")

    declared = dict(state.declared_deductions)
    user_val = state.user_responses.get("80ccd_1b", state.user_responses.get("nps"))
    if user_val is not None:
        declared["section_80ccd_1b"] = float(user_val)

    return {
        "visited_nodes": visited,
        "declared_deductions": declared,
    }


def node_80g(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Elicits and records Section 80G charitable donations.
    """
    visited = list(state.visited_nodes)
    visited.append("node_80g")

    declared = dict(state.declared_deductions)
    user_val = state.user_responses.get("80g", state.user_responses.get("donations"))
    if user_val is not None:
        declared["section_80g"] = float(user_val)

    return {
        "visited_nodes": visited,
        "declared_deductions": declared,
    }


def node_24b(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Elicits and records Section 24(b) housing loan interest.
    """
    visited = list(state.visited_nodes)
    visited.append("node_24b")

    declared = dict(state.declared_deductions)
    user_val = state.user_responses.get("24b", state.user_responses.get("home_loan_interest"))
    if user_val is not None:
        declared["section_24b"] = float(user_val)

    return {
        "visited_nodes": visited,
        "declared_deductions": declared,
    }


def route_after_24b(state: TaxPlanningState) -> str:
    """
    Conditional routing edge (Task 7.2):
    Skips the HRA node entirely if salary slip shows no HRA component.
    """
    if not state.has_hra_component:
        logger.info("Salary slip indicates no HRA component. Skipping node_hra.")
        return "node_tax_computation"
    return "node_hra"


def node_hra(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Elicits and records Section 10(13A) House Rent Allowance parameters.
    Only executed if has_hra_component is True (Task 7.2).
    """
    visited = list(state.visited_nodes)
    visited.append("node_hra")

    declared = dict(state.declared_deductions)
    user_val = state.user_responses.get("hra")

    if user_val is not None and isinstance(user_val, dict):
        # Extract basic salary from slip if not explicitly passed
        if "basic_salary" not in user_val and state.salary_slip_data:
            user_val["basic_salary"] = float(state.salary_slip_data.get("basic", 0.0))
        if "hra_received" not in user_val and state.salary_slip_data:
            user_val["hra_received"] = float(state.salary_slip_data.get("hra", 0.0))
        declared["hra"] = user_val

    return {
        "visited_nodes": visited,
        "declared_deductions": declared,
    }


def node_tax_computation(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Delegates tax calculation strictly to Phase 5 pure function compare_regimes (Task 7.4).
    CRITICAL ARCHITECTURAL DIRECTIVE: Zero LLM Arithmetic.
    The agent performs no currency arithmetic; pure deterministic math is used.
    """
    visited = list(state.visited_nodes)
    visited.append("node_tax_computation")

    skipped = list(state.skipped_nodes)
    if not state.has_hra_component and "node_hra" not in skipped:
        skipped.append("node_hra")

    # Pure function invocation
    comparison = compare_regimes(
        gross_income=state.gross_income,
        deductions=state.declared_deductions,
        is_salaried=state.is_salaried,
    )

    return {
        "visited_nodes": visited,
        "skipped_nodes": skipped,
        "comparison_result": comparison,
    }


def node_rag_citation(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Retrieves grounded statutory citations from Phase 6 ChromaDB RAG layer (Task 7.5).
    Attaches official citations and source URLs for each active deduction.
    """
    visited = list(state.visited_nodes)
    visited.append("node_rag_citation")

    citations: List[Dict[str, Any]] = []
    declared = state.declared_deductions

    # Standard deduction citation
    std_results = retrieve_tax_rules("standard deduction for salaried employees", top_k=1, section_filter="Standard Deduction")
    if std_results:
        citations.append({
            "section": "Standard Deduction",
            "title": std_results[0]["title"],
            "source_url": std_results[0]["source_url"],
            "citation_markdown": f"[{std_results[0]['title']}]({std_results[0]['source_url']})",
        })

    # 80C citation
    if declared.get("section_80c", 0) > 0:
        c_res = retrieve_tax_rules("80C deduction limit and investments", top_k=1, section_filter="80C")
        if c_res:
            citations.append({
                "section": "80C",
                "title": c_res[0]["title"],
                "source_url": c_res[0]["source_url"],
                "citation_markdown": f"[{c_res[0]['title']}]({c_res[0]['source_url']})",
            })

    # 80D citation
    if declared.get("section_80d"):
        d_res = retrieve_tax_rules("80D medical insurance limit", top_k=1, section_filter="80D")
        if d_res:
            citations.append({
                "section": "80D",
                "title": d_res[0]["title"],
                "source_url": d_res[0]["source_url"],
                "citation_markdown": f"[{d_res[0]['title']}]({d_res[0]['source_url']})",
            })

    # 80CCD(1B) citation
    if declared.get("section_80ccd_1b", 0) > 0:
        nps_res = retrieve_tax_rules("80CCD 1B NPS deduction", top_k=1, section_filter="80CCD(1B)")
        if nps_res:
            citations.append({
                "section": "80CCD(1B)",
                "title": nps_res[0]["title"],
                "source_url": nps_res[0]["source_url"],
                "citation_markdown": f"[{nps_res[0]['title']}]({nps_res[0]['source_url']})",
            })

    # 80G citation
    if declared.get("section_80g", 0) > 0:
        g_res = retrieve_tax_rules("80G donation limit", top_k=1, section_filter="80G")
        if g_res:
            citations.append({
                "section": "80G",
                "title": g_res[0]["title"],
                "source_url": g_res[0]["source_url"],
                "citation_markdown": f"[{g_res[0]['title']}]({g_res[0]['source_url']})",
            })

    # Section 24(b) citation
    if declared.get("section_24b", 0) > 0:
        loan_res = retrieve_tax_rules("home loan interest deduction 24b", top_k=1, section_filter="Section 24(b)")
        if loan_res:
            citations.append({
                "section": "Section 24(b)",
                "title": loan_res[0]["title"],
                "source_url": loan_res[0]["source_url"],
                "citation_markdown": f"[{loan_res[0]['title']}]({loan_res[0]['source_url']})",
            })

    # HRA citation
    if declared.get("hra"):
        hra_res = retrieve_tax_rules("HRA exemption calculation rule", top_k=1, section_filter="Section 10(13A)")
        if hra_res:
            citations.append({
                "section": "Section 10(13A)",
                "title": hra_res[0]["title"],
                "source_url": hra_res[0]["source_url"],
                "citation_markdown": f"[{hra_res[0]['title']}]({hra_res[0]['source_url']})",
            })

    # Section 87A rebate citation
    r87_res = retrieve_tax_rules("Section 87A rebate and marginal relief", top_k=1, section_filter="Section 87A")
    if r87_res:
        citations.append({
            "section": "Section 87A",
            "title": r87_res[0]["title"],
            "source_url": r87_res[0]["source_url"],
            "citation_markdown": f"[{r87_res[0]['title']}]({r87_res[0]['source_url']})",
        })

    return {
        "visited_nodes": visited,
        "citations": citations,
    }


def node_final_recommendation(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Assembles final user-facing comparison report combining Phase 5 calculations
    and Phase 6 statutory citations.
    """
    visited = list(state.visited_nodes)
    visited.append("node_final_recommendation")

    comparison = state.comparison_result or {}
    recommended = comparison.get("recommended", "new")
    savings = comparison.get("savings", 0.0)
    breakeven = comparison.get("breakeven_deductions", 0.0)
    summary_text = comparison.get("summary", "")

    citation_md_list = [c["citation_markdown"] for c in state.citations]

    final_report = {
        "user_id": state.user_id,
        "financial_year": state.financial_year,
        "gross_income": state.gross_income,
        "is_salaried": state.is_salaried,
        "recommended_regime": recommended,
        "tax_savings": savings,
        "breakeven_deductions": breakeven,
        "summary": summary_text,
        "comparison": comparison,
        "citations": state.citations,
        "citation_links": citation_md_list,
        "visited_nodes": visited,
        "skipped_nodes": state.skipped_nodes,
    }

    return {
        "visited_nodes": visited,
        "final_report": final_report,
    }


# ==============================================================================
# Graph Construction & Compilation
# ==============================================================================


def build_tax_planning_graph() -> StateGraph:
    """
    Builds and compiles the LangGraph StateGraph for the Tax Planning Agent.
    """
    builder = StateGraph(TaxPlanningState)

    # 1. Register nodes
    builder.add_node("init_node", init_node)
    builder.add_node("node_80c", node_80c)
    builder.add_node("node_80d", node_80d)
    builder.add_node("node_80ccd_1b", node_80ccd_1b)
    builder.add_node("node_80g", node_80g)
    builder.add_node("node_24b", node_24b)
    builder.add_node("node_hra", node_hra)
    builder.add_node("node_tax_computation", node_tax_computation)
    builder.add_node("node_rag_citation", node_rag_citation)
    builder.add_node("node_final_recommendation", node_final_recommendation)

    # 2. Register linear edges
    builder.add_edge(START, "init_node")
    builder.add_edge("init_node", "node_80c")
    builder.add_edge("node_80c", "node_80d")
    builder.add_edge("node_80d", "node_80ccd_1b")
    builder.add_edge("node_80ccd_1b", "node_80g")
    builder.add_edge("node_80g", "node_24b")

    # 3. Register conditional edge after 24b based on salary slip HRA component (Task 7.2)
    builder.add_conditional_edges(
        "node_24b",
        route_after_24b,
        {
            "node_hra": "node_hra",
            "node_tax_computation": "node_tax_computation",
        },
    )

    # 4. Remaining edges to completion
    builder.add_edge("node_hra", "node_tax_computation")
    builder.add_edge("node_tax_computation", "node_rag_citation")
    builder.add_edge("node_rag_citation", "node_final_recommendation")
    builder.add_edge("node_final_recommendation", END)

    return builder.compile()


def run_tax_planning_agent(
    gross_income: float,
    user_responses: Optional[Dict[str, Any]] = None,
    salary_slip_data: Optional[Dict[str, Any]] = None,
    is_salaried: bool = True,
    user_id: int = 1,
) -> TaxPlanningState:
    """
    Convenience function to execute the full Tax Planning Agent workflow end-to-end.
    """
    app = build_tax_planning_graph()

    initial_state = TaxPlanningState(
        user_id=user_id,
        gross_income=gross_income,
        is_salaried=is_salaried,
        salary_slip_data=salary_slip_data,
        user_responses=user_responses or {},
    )

    final_state_dict = app.invoke(initial_state)
    if isinstance(final_state_dict, dict):
        return TaxPlanningState(**final_state_dict)
    return final_state_dict
