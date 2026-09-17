"""
Tax Planning Agent LangGraph State Machine (Tasks 7.1, 7.2, 7.4, 7.5 & v1.1 Phase 13).

Implements:
- 13.1 ElicitationState tracking (sections_pending, sections_answered, sections_skipped).
- 13.2 Automatic conditional skip rules (e.g. skip 80GG if salary slip has HRA).
- 13.3 Proactive question formulation: agent initiates each topic on its turn.
- 13.4 Response resolution: maps answers to 'declared' or 'not_applicable'.
- 13.5 Completion gate: cannot transition to tax computation until all sections are resolved.
  Redirects short-circuit attempts back to the pending section.
- 13.6 Wire RAG citations into opening questions and explanations.
- 13.7 Supports cross-session resumption.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from langgraph.graph import END, START, StateGraph

from app.agent.elicitation import (
    CANONICAL_SECTIONS_ORDER,
    SECTION_QUESTIONS,
    evaluate_auto_skips,
    is_short_circuit_attempt,
    parse_elicitation_response,
)
from app.agent.state import ElicitationAnswer, ElicitationState, TaxPlanningState
from app.rag.retriever import retrieve_tax_rules
from app.tax_engine.comparator import compare_regimes

logger = logging.getLogger(__name__)


# Section code to internal deduction key mapping & aliases
SECTION_ALIAS_MAP: Dict[str, Tuple[str, str, List[str]]] = {
    "80C": ("80C", "section_80c", ["80c", "section_80c", "ppf", "epf", "elss"]),
    "80CCD(1B)": ("80CCD(1B)", "section_80ccd_1b", ["80ccd_1b", "80ccd(1b)", "80ccd1b", "nps", "section_80ccd_1b"]),
    "80CCD(2)": ("80CCD(2)", "section_80ccd_2", ["80ccd_2", "80ccd(2)", "80ccd2", "section_80ccd_2"]),
    "80D": ("80D", "section_80d", ["80d", "section_80d", "health_insurance"]),
    "80D (parents)": ("80D (parents)", "section_80d_parents", ["80d_parents", "80d (parents)", "section_80d_parents"]),
    "10(13A)": ("10(13A)", "hra", ["hra", "10(13a)", "10_13a", "section_10_13a", "section_10(13a)"]),
    "80GG": ("80GG", "section_80gg", ["80gg", "section_80gg"]),
    "24(b)": ("24(b)", "section_24b", ["24b", "24(b)", "section_24b", "section_24(b)", "home_loan_interest"]),
    "80EEA": ("80EEA", "section_80eea", ["80eea", "section_80eea"]),
    "80E": ("80E", "section_80e", ["80e", "section_80e", "education_loan"]),
    "80G": ("80G", "section_80g", ["80g", "section_80g", "donations"]),
    "80GGC": ("80GGC", "section_80ggc", ["80ggc", "section_80ggc"]),
    "80TTA": ("80TTA", "section_80tta", ["80tta", "section_80tta"]),
    "80TTB": ("80TTB", "section_80ttb", ["80ttb", "section_80ttb"]),
    "80DD": ("80DD", "section_80dd", ["80dd", "section_80dd"]),
    "80DDB": ("80DDB", "section_80ddb", ["80ddb", "section_80ddb"]),
    "80U": ("80U", "section_80u", ["80u", "section_80u"]),
    "10(5)": ("10(5)", "section_10_5", ["10(5)", "10_5", "section_10_5", "lta"]),
}


def resolve_user_response_key(raw_key: str) -> Tuple[Optional[str], str]:
    """
    Resolves an input response key to (statutory_section_code, canonical_internal_key).
    """
    clean_k = (
        raw_key.strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
    )
    for sec_code, (_, internal_key, aliases) in SECTION_ALIAS_MAP.items():
        alias_cleaned = [
            a.lower().replace("-", "_").replace(" ", "_").replace("(", "").replace(")", "")
            for a in aliases
        ]
        if (
            clean_k in alias_cleaned
            or clean_k == internal_key
            or clean_k == sec_code.lower().replace("(", "").replace(")", "")
        ):
            return sec_code, internal_key
    return None, raw_key


SECTION_TO_KEY = {sec: info[1] for sec, info in SECTION_ALIAS_MAP.items()}


# ==============================================================================
# Node Implementations
# ==============================================================================


def init_node(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Initializes conversation context, salary slip baseline, and elicitation queue (Tasks 7.2 & 13.2).
    Applies conditional skip rules automatically (e.g. skip 80GG if salary slip has HRA).
    """
    visited = list(state.visited_nodes)
    if "init_node" not in visited:
        visited.append("init_node")

    skipped = list(state.skipped_nodes)
    declared = dict(state.declared_deductions)
    has_hra = state.has_hra_component

    # 1. Salary slip inspection
    if state.salary_slip_data:
        slip = state.salary_slip_data
        slip_hra = float(slip.get("hra", 0.0))
        if slip_hra <= 0.0:
            has_hra = False
            if "node_hra" not in skipped:
                skipped.append("node_hra")
            if "node_hra" in visited:
                visited.remove("node_hra")
        else:
            has_hra = True
            if "node_hra" not in visited:
                visited.append("node_hra")
            if "node_hra" in skipped:
                skipped.remove("node_hra")

        # Pre-populate employee PF into 80C if reported and not yet declared
        emp_pf = float(slip.get("employee_pf", 0.0))
        if emp_pf > 0.0 and "section_80c" not in declared and "80c" not in declared:
            declared["section_80c"] = emp_pf
            declared["80c"] = emp_pf
    else:
        if has_hra:
            if "node_hra" not in visited:
                visited.append("node_hra")
        else:
            if "node_hra" not in skipped:
                skipped.append("node_hra")

    # 2. Initialize or merge ElicitationState (Task 13.1 & 13.2)
    elicitation = state.elicitation.model_copy()

    # Pre-populate any declarations provided via user_responses (e.g. from batch test profiles)
    if state.user_responses:
        for k, v in state.user_responses.items():
            if v is None:
                continue
            sec_code, internal_key = resolve_user_response_key(k)
            # If HRA dict provided, augment with slip data if available
            if internal_key == "hra" and isinstance(v, dict) and state.salary_slip_data:
                if "basic_salary" not in v and "basic" in state.salary_slip_data:
                    v["basic_salary"] = float(state.salary_slip_data["basic"])
                if "hra_received" not in v and "hra" in state.salary_slip_data:
                    v["hra_received"] = float(state.salary_slip_data["hra"])

            # Store in declared using canonical internal key and original key
            declared[internal_key] = v
            declared[k] = v

            if sec_code:
                elicitation.sections_answered[sec_code] = {"amount": v, "status": "declared"}

    # Evaluate conditional skip rules automatically (Task 13.2)
    auto_skips = evaluate_auto_skips(state, CANONICAL_SECTIONS_ORDER)
    for sec, reason in auto_skips.items():
        if sec not in elicitation.sections_answered and sec not in elicitation.sections_skipped:
            elicitation.sections_skipped[sec] = reason

    # In batch non-interactive mode:
    # Mark remaining unmentioned sections as not_applicable so synthetic profiles evaluate end-to-end tax calculation cleanly.
    is_interactive = bool(state.is_interactive or getattr(state, "_is_interactive", False))

    if not is_interactive:
        for sec in CANONICAL_SECTIONS_ORDER:
            if sec not in elicitation.sections_answered and sec not in elicitation.sections_skipped:
                elicitation.sections_answered[sec] = {"amount": 0.0, "status": "not_applicable"}

    # Determine pending sections (Task 13.2)
    if is_interactive and state.elicitation.sections_pending:
        pending = [
            s for s in state.elicitation.sections_pending
            if s not in elicitation.sections_answered and s not in elicitation.sections_skipped
        ]
    else:
        pending = [
            sec for sec in CANONICAL_SECTIONS_ORDER
            if sec not in elicitation.sections_answered and sec not in elicitation.sections_skipped
        ]

    elicitation.sections_pending = pending
    elicitation.current_section = pending[0] if pending else None

    # Include section node identifiers in visited_nodes for traceability and backward compatibility
    for sec_code in elicitation.sections_answered:
        node_name = f"node_{sec_code.lower().replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '')}"
        if node_name not in visited:
            visited.append(node_name)

    return {
        "visited_nodes": visited,
        "skipped_nodes": skipped,
        "has_hra_component": has_hra,
        "declared_deductions": declared,
        "elicitation": elicitation,
    }


def node_proactive_elicitation(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Handles proactive turn-by-turn deduction elicitation (Tasks 13.3, 13.4, 13.5, 13.6).
    - Checks for short-circuit attempts (Completion Gate enforcement).
    - Resolves user responses into 'declared' or 'not_applicable'.
    - Formulates next proactive question grounded in statutory citations.
    """
    visited = list(state.visited_nodes)
    if "node_proactive_elicitation" not in visited:
        visited.append("node_proactive_elicitation")

    elicitation = state.elicitation.model_copy()
    declared = dict(state.declared_deductions)
    citations = list(state.citations)
    current_sec = elicitation.current_section

    # Check the latest user message (if any)
    latest_user_message = ""
    for m in reversed(state.messages):
        if m.get("role") == "user":
            latest_user_message = m.get("content", "")
            break

    redirect_msg = None
    agent_msg = None

    # 1. Completion Gate: Intercept short-circuit attempts (Task 13.5)
    if latest_user_message and is_short_circuit_attempt(latest_user_message):
        if elicitation.sections_pending:
            redirect_msg = (
                f"Before we calculate your final tax liability and recommend the optimal regime, "
                f"we must systematically audit each statutory deduction to ensure you don't miss out on eligible tax relief.\n\n"
                f"Let's continue with **Section {current_sec}**:\n"
                f"{SECTION_QUESTIONS.get(current_sec, f'Do you have any deductions under Section {current_sec}?')}"
            )
            return {
                "visited_nodes": visited,
                "elicitation": elicitation,
                "redirect_message": redirect_msg,
                "current_agent_message": redirect_msg,
            }

    # 2. Process user answer for current_section (Task 13.4)
    if latest_user_message and current_sec and current_sec in elicitation.sections_pending:
        status, amount, meta = parse_elicitation_response(latest_user_message, current_sec)

        if status in ("declared", "not_applicable"):
            elicitation.sections_answered[current_sec] = {
                "amount": amount,
                "status": status,
                "metadata": meta,
            }
            if status == "declared":
                key = SECTION_TO_KEY.get(current_sec, current_sec.lower())
                declared[key] = meta if meta else amount

            elicitation.sections_pending = [s for s in elicitation.sections_pending if s != current_sec]
            current_sec = elicitation.sections_pending[0] if elicitation.sections_pending else None
            elicitation.current_section = current_sec

    # 3. Formulate the next proactive opening question (Task 13.3 & 13.6)
    if current_sec:
        try:
            sec_citations = retrieve_tax_rules(query=f"Section {current_sec} deduction rules", top_k=2)
            for c in sec_citations:
                if c not in citations:
                    citations.append(c)
        except Exception as e:
            logger.debug(f"RAG retrieval skipped for {current_sec}: {e}")

        q_text = SECTION_QUESTIONS.get(
            current_sec,
            f"Do you have any eligible deductions to declare under **Section {current_sec}**? Reply with the amount or 'No'."
        )
        if current_sec in ("80TTA", "80TTB") and getattr(state, "detected_savings_interest", 0.0) > 0:
            interest_amt = getattr(state, "detected_savings_interest", 0.0)
            cap = 50000.0 if current_sec == "80TTB" else 10000.0
            sec_name = "80TTB" if current_sec == "80TTB" else "80TTA"
            q_text = (
                f"You received approximately ₹{interest_amt:,.2f} in savings interest this year — "
                f"this must be reported as income, and you can claim up to ₹{cap:,.0f} "
                f"({'₹50,000 if senior citizen' if current_sec == '80TTA' else 'under Section 80TTB'}) "
                f"under {sec_name}. Would you like to declare this amount?"
            )
        agent_msg = q_text

    for sec_code in elicitation.sections_answered:
        node_name = f"node_{sec_code.lower().replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '')}"
        if node_name not in visited:
            visited.append(node_name)

    return {
        "visited_nodes": visited,
        "elicitation": elicitation,
        "declared_deductions": declared,
        "citations": citations,
        "current_agent_message": agent_msg,
        "redirect_message": redirect_msg,
    }


def node_tax_computation(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Computes tax liabilities under Section 115BAC vs Old Regime (Task 7.4).
    Gated strictly: only accessible when all pending sections are resolved (Task 13.5).
    """
    visited = list(state.visited_nodes)
    if "node_tax_computation" not in visited:
        visited.append("node_tax_computation")

    comparison = compare_regimes(
        gross_income=state.gross_income,
        deductions=state.declared_deductions,
        is_salaried=state.is_salaried,
    )

    return {
        "visited_nodes": visited,
        "comparison_result": comparison,
    }


def node_rag_citation(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Retrieves grounded statutory citations from Phase 6 ChromaDB RAG layer (Task 7.5).
    Attaches official citations and source URLs for each active deduction.
    """
    visited = list(state.visited_nodes)
    if "node_rag_citation" not in visited:
        visited.append("node_rag_citation")

    citations: List[Dict[str, Any]] = list(state.citations)
    declared = state.declared_deductions

    # 1. Standard deduction citation
    std_results = retrieve_tax_rules(
        "standard deduction for salaried employees",
        top_k=1,
        section_filter="Standard Deduction",
    )
    if std_results:
        citations.append({
            "section": "Standard Deduction",
            "title": std_results[0]["title"],
            "source_url": std_results[0]["source_url"],
            "citation_markdown": f"[{std_results[0]['title']}]({std_results[0]['source_url']})",
        })

    # 2. 80C citation
    val_80c = declared.get("section_80c", declared.get("80c", 0.0))
    if float(val_80c or 0.0) > 0:
        c_res = retrieve_tax_rules("80C deduction limit and investments", top_k=1, section_filter="80C")
        if c_res:
            citations.append({
                "section": "80C",
                "title": c_res[0]["title"],
                "source_url": c_res[0]["source_url"],
                "citation_markdown": f"[{c_res[0]['title']}]({c_res[0]['source_url']})",
            })

    # 3. 80D citation
    val_80d = declared.get("section_80d", declared.get("80d"))
    if val_80d:
        d_res = retrieve_tax_rules("80D medical insurance limit", top_k=1, section_filter="80D")
        if d_res:
            citations.append({
                "section": "80D",
                "title": d_res[0]["title"],
                "source_url": d_res[0]["source_url"],
                "citation_markdown": f"[{d_res[0]['title']}]({d_res[0]['source_url']})",
            })

    # 4. 80CCD(1B) citation
    val_80ccd_1b = declared.get(
        "section_80ccd_1b",
        declared.get("80ccd_1b", declared.get("nps", 0.0)),
    )
    if float(val_80ccd_1b or 0.0) > 0:
        nps_res = retrieve_tax_rules("80CCD 1B NPS deduction", top_k=1, section_filter="80CCD(1B)")
        if nps_res:
            citations.append({
                "section": "80CCD(1B)",
                "title": nps_res[0]["title"],
                "source_url": nps_res[0]["source_url"],
                "citation_markdown": f"[{nps_res[0]['title']}]({nps_res[0]['source_url']})",
            })

    # 5. 80G citation
    val_80g = declared.get(
        "section_80g",
        declared.get("80g", declared.get("donations", 0.0)),
    )
    if float(val_80g or 0.0) > 0:
        g_res = retrieve_tax_rules("80G donation limit", top_k=1, section_filter="80G")
        if g_res:
            citations.append({
                "section": "80G",
                "title": g_res[0]["title"],
                "source_url": g_res[0]["source_url"],
                "citation_markdown": f"[{g_res[0]['title']}]({g_res[0]['source_url']})",
            })

    # 6. Section 24(b) citation
    val_24b = declared.get(
        "section_24b",
        declared.get("24b", declared.get("home_loan_interest", 0.0)),
    )
    if float(val_24b or 0.0) > 0:
        loan_res = retrieve_tax_rules("home loan interest deduction 24b", top_k=1, section_filter="Section 24(b)")
        if loan_res:
            citations.append({
                "section": "Section 24(b)",
                "title": loan_res[0]["title"],
                "source_url": loan_res[0]["source_url"],
                "citation_markdown": f"[{loan_res[0]['title']}]({loan_res[0]['source_url']})",
            })

    # 7. HRA Section 10(13A) citation
    if declared.get("hra"):
        hra_res = retrieve_tax_rules("HRA exemption calculation rule", top_k=1, section_filter="Section 10(13A)")
        if hra_res:
            citations.append({
                "section": "Section 10(13A)",
                "title": hra_res[0]["title"],
                "source_url": hra_res[0]["source_url"],
                "citation_markdown": f"[{hra_res[0]['title']}]({hra_res[0]['source_url']})",
            })

    # 8. Section 87A rebate citation
    r87_res = retrieve_tax_rules("Section 87A rebate and marginal relief", top_k=1, section_filter="Section 87A")
    if r87_res:
        citations.append({
            "section": "Section 87A",
            "title": r87_res[0]["title"],
            "source_url": r87_res[0]["source_url"],
            "citation_markdown": f"[{r87_res[0]['title']}]({r87_res[0]['source_url']})",
        })

    # De-duplicate citations by section name preserving original ordering
    seen_sections = set()
    deduped_citations = []
    for c in citations:
        sec = c.get("section")
        if sec and sec not in seen_sections:
            seen_sections.add(sec)
            deduped_citations.append(c)
        elif not sec:
            deduped_citations.append(c)

    return {
        "visited_nodes": visited,
        "citations": deduped_citations,
    }


def node_final_recommendation(state: TaxPlanningState) -> Dict[str, Any]:
    """
    Synthesizes the executive final report and comparison breakdown.
    """
    visited = list(state.visited_nodes)
    if "node_final_recommendation" not in visited:
        visited.append("node_final_recommendation")

    comparison = state.comparison_result or {}
    rec = comparison.get("recommended", "new")
    savings = float(comparison.get("savings", 0.0))
    breakeven = float(comparison.get("breakeven_deductions", 375000.0))

    summary = (
        f"For FY 2025–26, the **{'New' if rec == 'new' else 'Old'} Tax Regime** is recommended for you. "
        f"You will save ₹{savings:,.2f} in tax liability. "
        f"Breakeven deduction threshold required for Old Regime to match New Regime: ₹{breakeven:,.2f}."
    )

    final_report = {
        "user_id": state.user_id,
        "financial_year": state.financial_year,
        "gross_income": state.gross_income,
        "is_salaried": state.is_salaried,
        "recommended_regime": rec,
        "tax_savings": savings,
        "breakeven_deductions": breakeven,
        "comparison": comparison,
        "citations": state.citations,
        "citation_links": [c.get("citation_markdown", "") for c in state.citations if "citation_markdown" in c],
        "summary": summary,
        "deductions_applied": state.declared_deductions,
        "visited_nodes": visited,
        "skipped_nodes": state.skipped_nodes,
    }

    return {
        "visited_nodes": visited,
        "final_report": final_report,
        "current_agent_message": summary,
    }


# ==============================================================================
# Conditional Edge Routers
# ==============================================================================


def route_after_init(state: TaxPlanningState) -> str:
    """
    Routes after init: if all sections are resolved, go straight to computation;
    otherwise enter proactive elicitation.
    """
    if len(state.elicitation.sections_pending) == 0:
        return "node_tax_computation"
    return "node_proactive_elicitation"


def route_after_elicitation(state: TaxPlanningState) -> str:
    """
    Completion gate router (Task 13.5):
    Only transitions to tax computation when sections_pending is empty!
    """
    if len(state.elicitation.sections_pending) == 0:
        return "node_tax_computation"
    return "end"


# ==============================================================================
# Graph Construction & Compilation
# ==============================================================================


def build_tax_planning_graph() -> StateGraph:
    """
    Builds and compiles the proactive stateful LangGraph StateGraph (Task 13.3).
    """
    builder = StateGraph(TaxPlanningState)

    # 1. Register nodes
    builder.add_node("init_node", init_node)
    builder.add_node("node_proactive_elicitation", node_proactive_elicitation)
    builder.add_node("node_tax_computation", node_tax_computation)
    builder.add_node("node_rag_citation", node_rag_citation)
    builder.add_node("node_final_recommendation", node_final_recommendation)

    # 2. Edges
    builder.add_edge(START, "init_node")
    builder.add_conditional_edges(
        "init_node",
        route_after_init,
        {
            "node_proactive_elicitation": "node_proactive_elicitation",
            "node_tax_computation": "node_tax_computation",
        },
    )
    builder.add_conditional_edges(
        "node_proactive_elicitation",
        route_after_elicitation,
        {
            "node_tax_computation": "node_tax_computation",
            "end": END,
        },
    )
    builder.add_edge("node_tax_computation", "node_rag_citation")
    builder.add_edge("node_rag_citation", "node_final_recommendation")
    builder.add_edge("node_final_recommendation", END)

    return builder.compile()


def step_tax_planning_agent(
    state: TaxPlanningState,
    user_message: Optional[str] = None,
) -> TaxPlanningState:
    """
    Executes a single conversational step in the proactive elicitation flow.
    """
    app = build_tax_planning_graph()

    current_state = state.model_copy()
    current_state.is_interactive = True
    if user_message:
        current_state.messages.append({"role": "user", "content": user_message})

    result_dict = app.invoke(current_state)
    if isinstance(result_dict, dict):
        res_state = TaxPlanningState(**result_dict)
    else:
        res_state = result_dict

    if res_state.current_agent_message:
        res_state.messages.append({"role": "assistant", "content": res_state.current_agent_message})

    return res_state


def run_tax_planning_agent(
    gross_income: float,
    user_responses: Optional[Dict[str, Any]] = None,
    salary_slip_data: Optional[Dict[str, Any]] = None,
    is_salaried: bool = True,
    user_id: int = 1,
    elicitation_state: Optional[ElicitationState] = None,
    interactive_mode: bool = False,
) -> TaxPlanningState:
    """
    Executes the tax planning workflow, supporting both batch profile testing
    and cross-session stateful execution.
    """
    app = build_tax_planning_graph()

    initial_elicitation = elicitation_state or ElicitationState()
    initial_state = TaxPlanningState(
        user_id=user_id,
        gross_income=gross_income,
        is_salaried=is_salaried,
        salary_slip_data=salary_slip_data,
        user_responses=user_responses or {},
        elicitation=initial_elicitation,
        is_interactive=interactive_mode,
    )

    final_state_dict = app.invoke(initial_state)
    if isinstance(final_state_dict, dict):
        return TaxPlanningState(**final_state_dict)
    return final_state_dict
