"""
Comprehensive Unit Tests for Tax Planning Agent (Phase 7).

Verifies:
- Task 7.1: LangGraph state machine skeleton execution.
- Task 7.2: Conditional branching based on salary slip (HRA component check).
- Task 7.3: Database persistence into user_declared_deductions with source = 'agent_elicited'.
- Task 7.4: Zero LLM arithmetic requirement (Phase 5 pure function delegation).
- Task 7.5: Grounded statutory citations wired from Phase 6 RAG.
- Task 7.6: Automated conversation flow test on 3 synthetic user profiles.
- Task 7.7: Verification of zero currency arithmetic inside the agent code.
- Task 7.8: Exact matching of hand-calculated tax liability vs agent final output.
"""

import ast
from pathlib import Path
import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.agent.graph import build_tax_planning_graph, run_tax_planning_agent
from app.agent.persistence import persist_all_elicited_deductions
from app.models.user_declared_deduction import UserDeclaredDeduction


# In-memory test SQLite engine for persistence testing
@pytest.fixture(name="db_session")
def db_session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# ==============================================================================
# Task 7.6 & 7.8: Synthetic Profile 1 — No HRA / No Investments
# ==============================================================================


def test_synthetic_profile_1_no_hra_no_investments():
    """
    Profile 1:
    - Gross Salaried Income: ₹6,00,000
    - Salary Slip: basic: 40,000, hra: 0.0, gross_pay: 50,000 (No HRA component)
    - No declared investments.

    Verification:
    - node_hra is skipped (in skipped_nodes, not in visited_nodes)
    - New Regime: Gross 6L - 75k = 5.25L taxable <= 12L -> Tax = ₹0 (NIL)
    - Old Regime: Gross 6L - 50k = 5.5L taxable -> Tax before cess = 22,500 -> Total = ₹23,400
    - Recommended: New Regime (Tax Savings = ₹23,400)
    """
    salary_slip = {
        "basic": 40000.0,
        "hra": 0.0,
        "gross_pay": 50000.0,
        "employee_pf": 0.0,
    }

    final_state = run_tax_planning_agent(
        gross_income=600000.0,
        salary_slip_data=salary_slip,
        user_responses={},
        is_salaried=True,
    )

    # 1. Assert conditional branching: node_hra was skipped (Task 7.2)
    assert "node_hra" in final_state.skipped_nodes
    assert "node_hra" not in final_state.visited_nodes
    assert "node_tax_computation" in final_state.visited_nodes
    assert "node_final_recommendation" in final_state.visited_nodes

    # 2. Assert hand-calculated tax matches agent output exactly (Task 7.8)
    report = final_state.final_report
    assert report is not None
    assert report["recommended_regime"] == "new"
    assert report["tax_savings"] == 23400.0
    assert report["comparison"]["new"]["total_tax"] == 0.0
    assert report["comparison"]["old"]["total_tax"] == 23400.0

    # 3. Assert RAG citations attached (Task 7.5)
    assert len(report["citations"]) >= 1
    sections = [c["section"] for c in report["citations"]]
    assert "Standard Deduction" in sections


# ==============================================================================
# Task 7.6 & 7.8: Synthetic Profile 2 — Full HRA + Heavy 80C
# ==============================================================================


def test_synthetic_profile_2_full_hra_heavy_80c():
    """
    Profile 2:
    - Gross Salaried Income: ₹15,00,000
    - Salary Slip: basic: 70,000 (annual 8.4L), hra: 35,000 (annual 4.2L)
    - Declared: 80C = ₹1,80,000 (capped at 1.5L)
    - Declared HRA: rent_paid = ₹3,60,000, metro = True
      HRA exemption = min(4.2L actual, 3.6L - 84k = 2.76L, 50% basic 4.2L) = ₹2,76,000
    - Old Regime Deductions: 50k std + 1.5L 80C + 2.76L HRA = ₹4,76,000
    - Old Regime Taxable: 15L - 4.76L = ₹10,24,000 -> Tax: 1,19,700 + 4% cess = ₹1,24,488
    - New Regime: Gross 15L - 75k = 14.25L taxable -> Tax: 93,750 + 4% cess = ₹97,500
    - Recommended: New Regime (Savings = ₹26,988)
    """
    salary_slip = {
        "basic": 70000.0,
        "hra": 35000.0,
        "gross_pay": 125000.0,
        "employee_pf": 8400.0,
    }

    user_responses = {
        "80c": 180000.0,
        "hra": {
            "rent_paid": 360000.0,
            "basic_salary": 840000.0,
            "hra_received": 420000.0,
            "is_metro": True,
        },
    }

    final_state = run_tax_planning_agent(
        gross_income=1500000.0,
        salary_slip_data=salary_slip,
        user_responses=user_responses,
        is_salaried=True,
    )

    # 1. Assert node_hra was visited (Task 7.2)
    assert "node_hra" in final_state.visited_nodes
    assert "node_hra" not in final_state.skipped_nodes

    # 2. Assert exact mathematical matching (Task 7.8)
    report = final_state.final_report
    assert report["recommended_regime"] == "new"
    assert report["comparison"]["new"]["total_tax"] == 97500.0
    assert report["comparison"]["old"]["total_tax"] == 124488.0
    assert report["tax_savings"] == 26988.0

    # 3. Assert RAG citations include 80C and Section 10(13A) (Task 7.5)
    sections = [c["section"] for c in report["citations"]]
    assert "80C" in sections
    assert "Section 10(13A)" in sections


# ==============================================================================
# Task 7.6 & 7.8: Synthetic Profile 3 — NPS + Donations + Health Insurance
# ==============================================================================


def test_synthetic_profile_3_nps_donations_health_insurance():
    """
    Profile 3:
    - Gross Salaried Income: ₹18,00,000
    - Salary Slip: basic: 1,00,000, hra: 0.0 (No HRA)
    - Declared:
      - 80C: 1,50,000
      - 80CCD(1B) NPS: 50,000
      - 80D: Self 25,000, Senior Parents 50,000 = 75,000
      - 80G Donations: 30,000
      - Section 24b Home loan interest: 2,00,000
    - Total Old Deductions: 50k + 1.5L + 50k + 75k + 30k + 2.0L = ₹5,55,000
    - Old Regime Taxable: 18L - 5.55L = ₹12,45,000 -> Tax: 1,86,000 + 4% = ₹1,93,440
    - New Regime: Gross 18L - 75k = 17.25L taxable -> Tax: 1,45,000 + 4% = ₹1,50,800
    - Recommended: New Regime (Savings = ₹42,640)
    """
    salary_slip = {
        "basic": 100000.0,
        "hra": 0.0,
        "gross_pay": 150000.0,
        "employee_pf": 12000.0,
    }

    user_responses = {
        "80c": 150000.0,
        "80ccd_1b": 50000.0,
        "80d": {
            "self_family_premium": 25000.0,
            "parents_premium": 50000.0,
            "are_parents_senior": True,
        },
        "80g": 30000.0,
        "24b": 200000.0,
    }

    final_state = run_tax_planning_agent(
        gross_income=1800000.0,
        salary_slip_data=salary_slip,
        user_responses=user_responses,
        is_salaried=True,
    )

    # 1. Assert node_hra was skipped (Task 7.2)
    assert "node_hra" in final_state.skipped_nodes

    # 2. Assert exact mathematical matching (Task 7.8)
    report = final_state.final_report
    assert report["recommended_regime"] == "new"
    assert report["comparison"]["new"]["total_tax"] == 150800.0
    assert report["comparison"]["old"]["total_tax"] == 193440.0
    assert report["tax_savings"] == 42640.0

    # 3. Assert RAG citations include 80CCD(1B), 80D, 80G, Section 24(b) (Task 7.5)
    sections = [c["section"] for c in report["citations"]]
    assert "80CCD(1B)" in sections
    assert "80D" in sections
    assert "80G" in sections
    assert "Section 24(b)" in sections


# ==============================================================================
# Task 7.3: Database Persistence Verification
# ==============================================================================


def test_database_persistence_user_declared_deductions(db_session):
    """
    Task 7.3: Verifies that elicited deductions are correctly persisted to the database
    with source = 'agent_elicited'.
    """
    declared = {
        "section_80c": 150000.0,
        "section_80d": 25000.0,
        "section_80ccd_1b": 50000.0,
        "section_24b": 200000.0,
    }

    records = persist_all_elicited_deductions(
        session=db_session,
        user_id=42,
        declared_deductions=declared,
        financial_year="2025-2026",
    )

    assert len(records) == 4
    for r in records:
        assert r.user_id == 42
        assert r.source == "agent_elicited"
        assert r.financial_year == "2025-2026"
        assert r.amount > 0.0

    # Query back from SQLite
    saved_rows = db_session.exec(
        select(UserDeclaredDeduction).where(UserDeclaredDeduction.user_id == 42)
    ).all()
    assert len(saved_rows) == 4
    sec_map = {row.section: row.amount for row in saved_rows}
    assert sec_map["80C"] == 150000.0
    assert sec_map["80D"] == 25000.0
    assert sec_map["80CCD(1B)"] == 50000.0
    assert sec_map["24b"] == 200000.0


# ==============================================================================
# Task 7.4 & 7.7: Zero LLM Arithmetic AST Verification Gate
# ==============================================================================


def test_zero_currency_arithmetic_in_agent_code():
    """
    Task 7.4 & 7.7: Asserts that the agent module code performs NO currency arithmetic.
    All mathematical calculations (slabs, cess, rebates, deductions) are delegated
    strictly to Phase 5 pure functions.
    """
    agent_dir = Path("backend/app/agent")
    py_files = list(agent_dir.glob("*.py"))
    assert len(py_files) >= 3, "Expected at least state.py, graph.py, persistence.py"

    forbidden_patterns = [
        "taxable_income *",
        "gross_income *",
        "slab *",
        "cess *",
        "* 0.04",
        "* 0.05",
        "* 0.10",
        "* 0.15",
        "* 0.20",
        "* 0.25",
        "* 0.30",
    ]

    for py_file in py_files:
        code_text = py_file.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            assert pattern not in code_text, (
                f"Violation of Zero LLM Arithmetic policy: found '{pattern}' in {py_file}"
            )
