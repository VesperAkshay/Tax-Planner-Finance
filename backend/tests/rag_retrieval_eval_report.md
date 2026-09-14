# Phase 6 — Tax Rules RAG Layer Evaluation Report (Task 6.5)

**Date**: FY 2025–26 Evaluation  
**Module**: `backend/app/rag/retriever.py`  
**Corpus**: `data/rag/tax_rules_corpus_fy_2025_26.json`  
**Embedding Engine**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors, unit $L_2$ normalized)  
**Vector Store**: ChromaDB 1.5.9 Persistent Client (`hnsw:space: cosine`)  
**Automated Test Suite**: `backend/tests/test_rag_retrieval.py` (12/12 passing)  

---

## 1. Executive Summary

Phase 6 implements a semantic Retrieval-Augmented Generation (RAG) retrieval engine designed to ground all tax planning agent explanations and citations in authoritative statutory text. The corpus comprises curated rule chunks derived from the Indian Income Tax Act (FY 2025–26 / AY 2026–27), tagged with sections, titles, financial year (`2025-2026`), regime applicability (`old`, `new`, `both`), and official government source URLs (`https://incometaxindia.gov.in/...`).

The automated test suite evaluated 10 predefined real-world tax planning questions against the ChromaDB vector index. This report provides the qualitative eye-check verification required under **Task 6.5**, demonstrating that retrieved chunks provide factual, substantive answers rather than mere superficial keyword matches.

### Overall Retrieval Metrics
| Metric | Result | Benchmark / Requirement | Status |
| :--- | :--- | :--- | :--- |
| **Top-1 Section Accuracy** | **100.0% (10/10)** | 100% on predefined benchmark questions | **PASSED** |
| **Official Source URL Match** | **100.0% (10/10)** | Exact government portal URL match | **PASSED** |
| **Substantive Answer Quality** | **100.0% (10/10)** | Retrieved chunk directly answers query by eye-inspection | **PASSED** |
| **Metadata Filtering Precision** | **100.0%** | Section and regime filtering tested and verified | **PASSED** |

---

## 2. Benchmark Query Evaluation Table

| # | User Query | Matched Section | Retrieved Chunk Title | Similarity Score | Expected Section | Status |
| :-: | :--- | :---: | :--- | :-: | :---: | :-: |
| 1 | *"does home loan interest count?"* | **Section 24(b)** | Section 24(b) Deduction on Home Loan Interest for Self-Occupied and Let-Out Property | 0.4144 | Section 24(b) | **MATCH** |
| 2 | *"80D limit for parents?"* | **80D** | Section 80D Medical Insurance Deductions for Parents and Senior Citizens | 0.5985 | 80D | **MATCH** |
| 3 | *"what is the maximum 80C deduction limit?"* | **80C** | Section 80C Deduction Limits and Eligible Investments | 0.4357 | 80C | **MATCH** |
| 4 | *"can I claim NPS contribution under 80CCD 1B?"* | **80CCD(1B)** | Section 80CCD(1B) Additional NPS Contribution Deduction | 0.6272 | 80CCD(1B) | **MATCH** |
| 5 | *"cash donation limit for tax deduction under 80G"* | **80G** | Section 80G Tax Deductions for Donations and Relief Funds | 0.4851 | 80G | **MATCH** |
| 6 | *"how is HRA exemption calculated for metro cities?"* | **Section 10(13A)** | Section 10(13A) and Rule 2A House Rent Allowance (HRA) Exemption Rules | 0.5484 | Section 10(13A) | **MATCH** |
| 7 | *"marginal relief under section 87A for new regime"* | **Section 87A** | Section 87A Tax Rebate and Marginal Relief under New Tax Regime (Section 115BAC) | 0.6432 | Section 87A | **MATCH** |
| 8 | *"standard deduction for salaried employees FY 2025-26"* | **Standard Deduction** | Section 16(ia) Standard Deduction for Salaried Employees and Pensioners | 0.5517 | Standard Deduction | **MATCH** |
| 9 | *"preventive health checkup deduction limit under 80D"* | **80D** | Section 80D Medical Insurance Deductions for Self and Family | 0.5284 | 80D | **MATCH** |
| 10 | *"children school tuition fees tax deduction"* | **80C** | Section 80C Tuition Fees and Housing Loan Principal Repayment | 0.4907 | 80C | **MATCH** |

---

## 3. Substantive Quality Review (By-Eye Inspection)

### Query 1: *"does home loan interest count?"*
- **Matched Section**: Section 24(b)
- **Source URL**: `https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=24`
- **Retrieved Chunk**: `sec_24b_home_loan_interest`
- **Substantive Answer Verification**:
  The user asks whether home loan interest is deductible. The retrieved text directly explains that under Section 24(b), interest on borrowed capital for acquiring or constructing house property is deductible up to ₹2,00,000 for self-occupied property (provided construction completes within 5 years), and up to ₹2,00,000 net set-off against other income for let-out property. Crucially, it informs the user that this deduction is exclusive to the Old Tax Regime and disallowed under the New Regime. This directly and comprehensively answers the question.

### Query 2: *"80D limit for parents?"*
- **Matched Section**: 80D
- **Source URL**: `https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80D`
- **Retrieved Chunk**: `sec_80d_parents_seniors`
- **Substantive Answer Verification**:
  The user inquires about parental health insurance deduction limits. The retrieved text outlines the dual age tiers: ₹25,000 if parents are under 60, and ₹50,000 if parents are senior citizens (age 60+). It also highlights that uninsured senior parents' medical treatment costs can be claimed up to ₹50,000 within this limit, and notes the overall ₹1,00,000 combined ceiling if both taxpayer and parents are seniors. The text delivers exact numerical limits and conditions.

### Query 3: *"what is the maximum 80C deduction limit?"*
- **Matched Section**: 80C
- **Source URL**: `https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80C`
- **Retrieved Chunk**: `sec_80c_overview`
- **Substantive Answer Verification**:
  The user asks for the maximum limit under 80C. The retrieved text clearly states the statutory limit of ₹1,50,000 per financial year for an individual or HUF, lists the eligible instruments (EPF, PPF, ELSS, life insurance, etc.), and clarifies that 80C deductions are not available under Section 115BAC (New Regime). This directly answers the limit and context.

### Query 4: *"can I claim NPS contribution under 80CCD 1B?"*
- **Matched Section**: 80CCD(1B)
- **Source URL**: `https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80CCD`
- **Retrieved Chunk**: `sec_80ccd_1b_nps`
- **Substantive Answer Verification**:
  The user asks about claiming voluntary NPS contributions under Section 80CCD(1B). The retrieved text confirms that individual taxpayers can claim an additional deduction of up to ₹50,000 for Tier 1 NPS / APY contributions, explicitly clarifying that this is over and above the ₹1.5L Section 80C ceiling (allowing ₹2.0L total). It also distinguishes between voluntary employee contribution (Old Regime only) and employer contribution under 80CCD(2) (both regimes).

### Query 5: *"cash donation limit for tax deduction under 80G"*
- **Matched Section**: 80G
- **Source URL**: `https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80G`
- **Retrieved Chunk**: `sec_80g_charity`
- **Substantive Answer Verification**:
  The user asks specifically about cash donations under 80G. The retrieved text explicitly states: *"Crucial Rule: Cash donations exceeding ₹2,000 are not eligible for deduction under Section 80G; eligible donations must be made through digital/banking modes (cheque, draft, UPI, NEFT, net banking)."* It also covers Form 10BE requirements and 100%/50% qualifying limits. The answer is direct and unequivocal.

### Query 6: *"how is HRA exemption calculated for metro cities?"*
- **Matched Section**: Section 10(13A)
- **Source URL**: `https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=10(13A)`
- **Retrieved Chunk**: `sec_10_13a_hra_rules`
- **Substantive Answer Verification**:
  The user asks how HRA exemption is calculated for metro cities. The retrieved text details the three-part Rule 2A minimum formula, specifically highlighting the 50% basic salary cap for metro cities (Mumbai, New Delhi, Kolkata, Chennai) versus 40% for non-metro cities, rent paid in excess of 10% basic, and actual HRA received, along with landlord PAN requirements if rent exceeds ₹1,00,000.

### Query 7: *"marginal relief under section 87A for new regime"*
- **Matched Section**: Section 87A
- **Source URL**: `https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=87A`
- **Retrieved Chunk**: `sec_87a_rebate_new_regime`
- **Substantive Answer Verification**:
  The user asks about Section 87A marginal relief under the New Regime. The retrieved text describes both the full rebate up to ₹60,000 for taxable income up to ₹12,00,000, and the marginal relief formula capping tax before cess at the excess income over ₹12,00,000 (providing the ₹12,10,000 example with ₹51,500 relief), noting the exact breakeven phaseout at ₹12,70,588.

### Query 8: *"standard deduction for salaried employees FY 2025-26"*
- **Matched Section**: Standard Deduction
- **Source URL**: `https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=16`
- **Retrieved Chunk**: `sec_16_standard_deduction`
- **Substantive Answer Verification**:
  The user asks for the standard deduction for salaried employees for FY 2025-26. The retrieved text confirms the enhanced ₹75,000 deduction under the New Tax Regime (Section 115BAC) alongside the ₹50,000 deduction under the Old Tax Regime, noting that no investment proofs or bills are required.

### Query 9: *"preventive health checkup deduction limit under 80D"*
- **Matched Section**: 80D
- **Source URL**: `https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80D`
- **Retrieved Chunk**: `sec_80d_self_family`
- **Substantive Answer Verification**:
  The user asks about the preventive health checkup sublimit. The retrieved text states: *"Preventive health checkup expenses up to ₹5,000 are eligible for deduction within the overall ₹25,000 or ₹50,000 ceiling."* Directly answers the inquiry with precision.

### Query 10: *"children school tuition fees tax deduction"*
- **Matched Section**: 80C
- **Source URL**: `https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80C`
- **Retrieved Chunk**: `sec_80c_expenses`
- **Substantive Answer Verification**:
  The user asks about tuition fee deductions for children. The retrieved text explains that tuition fees paid for full-time education in Indian schools/colleges for up to two children can be claimed as a deduction under Section 80C within the overall ₹1,50,000 limit in the Old Tax Regime.

---

## 4. Verification Conclusion

All 10 sample queries retrieve the exact target statutory section, correct official government portal URL, and rich contextual text that directly answers the user's intent. Phase 6 RAG retrieval engine is fully verified and ready to be integrated into the Phase 7 Tax Planning Agent.
