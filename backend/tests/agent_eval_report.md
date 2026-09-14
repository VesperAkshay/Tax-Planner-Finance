# Phase 7 — Tax Planning Agent Evaluation Report (Tasks 7.7 & 7.8)

**Date**: FY 2025–26 Evaluation  
**Module**: `backend/app/agent/` (`graph.py`, `state.py`, `persistence.py`)  
**State Machine**: LangGraph `StateGraph`  
**Automated Test Suite**: `backend/tests/test_tax_planning_agent.py` (5/5 passing)  
**Strict Design Directive**: Zero LLM Tax Arithmetic  

---

## 1. Executive Summary

Phase 7 implements the Tax Planning Agent as an elicitation and decision-support state machine built with LangGraph. The agent interrogates the user's financial profile across Chapter VI-A deductions (80C, 80D, 80CCD(1B), 80G), Section 24(b) housing loan interest, and Section 10(13A) House Rent Allowance (HRA).

Crucially, **the agent does not perform any mathematical tax calculations itself**. All tax computation, regime comparisons, and savings calculations are delegated to the pure functions developed in Phase 5 (`backend/app/tax_engine/comparator.py`), while all explanation citations are retrieved from the ChromaDB RAG layer developed in Phase 6 (`backend/app/rag/retriever.py`).

---

## 2. Architectural Verification: Zero LLM Tax Arithmetic (Task 7.7)

### Verification Methodology
To ensure compliance with the **"Zero LLM Tax Arithmetic"** directive, `test_zero_currency_arithmetic_in_agent_code` performs an automated AST scan across all Python modules in `backend/app/agent/` (`state.py`, `graph.py`, `persistence.py`), searching for binary arithmetic expressions operating on currency or tax fields (e.g. `* 0.04`, `* 0.10`, `taxable_income *`, `cess *`).

### Findings
1. **No currency arithmetic** was found in any node function or prompt template.
2. The state machine strictly gathers input data into `declared_deductions` and invokes:
   ```python
   comparison = compare_regimes(
       gross_income=state.gross_income,
       deductions=state.declared_deductions,
       is_salaried=state.is_salaried,
   )
   ```
3. All tax numbers in the agent's output originate directly from deterministic pure Python math grounded in `data/tax_rules/fy_2025_26.json`.

---

## 3. Conditional Branching Verification (Task 7.2)

The agent implements dynamic conditional branching based on the user's salary slip:
- If `salary_slip_data.hra <= 0` or missing: The routing function `route_after_24b` intercepts the flow and directs execution directly to `node_tax_computation`, appending `"node_hra"` to `state.skipped_nodes`.
- If `salary_slip_data.hra > 0`: The agent visits `node_hra`, eliciting rent paid, metro status, and computing eligible Section 10(13A) exemption under Rule 2A.

---

## 4. Synthetic User Profiles & Hand-Calculation Matching (Tasks 7.6 & 7.8)

### Profile 1: No HRA / No Investments (₹6,00,000 Salaried Gross)
- **Salary Slip**: Basic ₹40,000/mo, HRA ₹0.0/mo, Gross ₹50,000/mo (No HRA).
- **Visited Nodes**: `init_node`, `node_80c`, `node_80d`, `node_80ccd_1b`, `node_80g`, `node_24b`, `node_tax_computation`, `node_rag_citation`, `node_final_recommendation`.
- **Skipped Nodes**: `node_hra` (skipped due to zero HRA on slip).
- **Hand-Calculation**:
  - *New Regime*: Gross ₹6,00,000 - ₹75,000 standard deduction = ₹5,25,000 taxable income. Since ₹5.25L $\le$ ₹12,00,000 threshold, Section 87A rebate wipes out 100% of tax liability $\rightarrow$ **₹0.00 (NIL)**.
  - *Old Regime*: Gross ₹6,00,000 - ₹50,000 standard deduction = ₹5,50,000 taxable income.
    - Slab: 0–2.5L: ₹0; 2.5L–5L @ 5%: ₹12,500; 5L–5.5L (50k @ 20%): ₹10,000.
    - Tax before cess: ₹22,500. No 87A rebate (income > ₹5L).
    - 4% Cess: ₹900.
    - Old Regime Total: ₹22,500 + ₹900 = **₹23,400.00**.
  - *Recommendation*: **New Regime** (Savings = **₹23,400.00**).
- **Agent Output**: New Regime ₹0.00, Old Regime ₹23,400.00, Recommended: New, Savings: ₹23,400.00.
- **Discrepancy**: **₹0.00 (Exact Match)**.

---

### Profile 2: Full HRA + Heavy 80C (₹15,00,000 Salaried Gross)
- **Salary Slip**: Basic ₹70,000/mo (₹8.4L/yr), HRA ₹35,000/mo (₹4.2L/yr).
- **Declared Deductions**: 80C claimed ₹1,80,000; HRA rent paid ₹3,60,000 in Mumbai (metro).
- **Visited Nodes**: `init_node`, `node_80c`, `node_80d`, `node_80ccd_1b`, `node_80g`, `node_24b`, `node_hra`, `node_tax_computation`, `node_rag_citation`, `node_final_recommendation`.
- **Skipped Nodes**: None.
- **Hand-Calculation**:
  - *HRA Exemption*: $\min(\text{Actual HRA } 4.2\text{L}, \text{Rent } 3.6\text{L} - 10\% \text{Basic } 84\text{k} = 2.76\text{L}, 50\% \text{Basic } 4.2\text{L}) = \text{₹}2,76,000$.
  - *80C Allowed*: $\min(1,80,000, 1,50,000) = \text{₹}1,50,000$.
  - *Old Regime Deductions*: ₹50,000 (std) + ₹2,76,000 (HRA) + ₹1,50,000 (80C) = ₹4,76,000.
  - *Old Regime Taxable Income*: ₹15,00,000 - ₹4,76,000 = ₹10,24,000.
    - Slab: 0–2.5L: ₹0; 2.5L–5L: ₹12,500; 5L–10L: ₹1,00,000; 10L–10.24L (24k @ 30%): ₹7,200.
    - Tax before cess: ₹1,19,700.
    - 4% Cess: ₹4,788.
    - Old Regime Total: **₹1,24,488.00**.
  - *New Regime*: Gross ₹15,00,000 - ₹75,000 = ₹14,25,000 taxable income.
    - Slab: 0–4L: ₹0; 4L–8L: ₹20,000; 8L–12L: ₹40,000; 12L–14.25L (2.25L @ 15%): ₹33,750.
    - Tax before cess: ₹93,750.
    - 4% Cess: ₹3,750.
    - New Regime Total: **₹97,500.00**.
  - *Recommendation*: **New Regime** (Savings = ₹1,24,488 - ₹97,500 = **₹26,988.00**).
- **Agent Output**: New Regime ₹97,500.00, Old Regime ₹1,24,488.00, Recommended: New, Savings: ₹26,988.00.
- **Discrepancy**: **₹0.00 (Exact Match)**.

---

### Profile 3: NPS + Donations + Health Insurance (₹18,00,000 Salaried Gross)
- **Salary Slip**: Basic ₹1,00,000/mo, HRA ₹0.0/mo (No HRA).
- **Declared Deductions**: 80C ₹1.5L, 80CCD(1B) NPS ₹50k, 80D (Self ₹25k + Senior Parents ₹50k = ₹75k), 80G Donations ₹30k, Section 24(b) Home loan interest ₹2.0L.
- **Visited Nodes**: All nodes except `node_hra`.
- **Skipped Nodes**: `node_hra`.
- **Hand-Calculation**:
  - *Total Deductions (Old Regime)*:
    - Standard deduction: ₹50,000
    - Section 80C: ₹1,50,000
    - Section 80CCD(1B): ₹50,000
    - Section 80D: ₹75,000
    - Section 80G: ₹30,000
    - Section 24(b): ₹2,00,000
    - Total = ₹5,55,000.
  - *Old Regime Taxable Income*: ₹18,00,000 - ₹5,55,000 = ₹12,45,000.
    - Slab: 0–2.5L: ₹0; 2.5L–5L: ₹12,500; 5L–10L: ₹1,00,000; 10L–12.45L (2.45L @ 30%): ₹73,500.
    - Tax before cess: ₹1,86,000.
    - 4% Cess: ₹7,440.
    - Old Regime Total: **₹1,93,440.00**.
  - *New Regime*: Gross ₹18,00,000 - ₹75,000 = ₹17,25,000 taxable income.
    - Slab: 0–4L: ₹0; 4L–8L: ₹20,000; 8L–12L: ₹40,000; 12L–16L: ₹60,000; 16L–17.25L (1.25L @ 20%): ₹25,000.
    - Tax before cess: ₹1,45,000.
    - 4% Cess: ₹5,800.
    - New Regime Total: **₹1,50,800.00**.
  - *Recommendation*: **New Regime** (Savings = ₹1,93,440 - ₹1,50,800 = **₹42,640.00**).
- **Agent Output**: New Regime ₹1,50,800.00, Old Regime ₹1,93,440.00, Recommended: New, Savings: ₹42,640.00.
- **Discrepancy**: **₹0.00 (Exact Match)**.

---

## 5. Summary Table of Hand-Calculation Verification

| Profile | Description | Hand-Calc New Tax | Agent New Tax | Hand-Calc Old Tax | Agent Old Tax | Hand-Calc Savings | Agent Savings | Discrepancy |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Profile 1** | ₹6L Salaried, No HRA, No Investments | ₹0.00 | ₹0.00 | ₹23,400.00 | ₹23,400.00 | ₹23,400.00 | ₹23,400.00 | **₹0.00** |
| **Profile 2** | ₹15L Salaried, Full Metro HRA, 80C | ₹97,500.00 | ₹97,500.00 | ₹1,24,488.00 | ₹1,24,488.00 | ₹26,988.00 | ₹26,988.00 | **₹0.00** |
| **Profile 3** | ₹18L Salaried, NPS, 80D, 80G, 24(b) | ₹1,50,800.00 | ₹1,50,800.00 | ₹1,93,440.00 | ₹1,93,440.00 | ₹42,640.00 | ₹42,640.00 | **₹0.00** |

---

## 6. Conclusion

Phase 7 Tax Planning Agent satisfies all architectural and functional criteria:
- **Zero LLM tax arithmetic** verified programmatically.
- **Conditional branching** reliably skips unneeded nodes (e.g. HRA).
- **User-declared deductions** persist correctly with `source = agent_elicited`.
- **RAG citations** ground all recommendations with official government URLs.
- **100% mathematical equality** across all benchmark synthetic profiles.
Phase 7 is 100% complete!
