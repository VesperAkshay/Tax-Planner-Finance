# Document Parsing Pipeline Accuracy Report (Task 2.11 & Gate 2.12)

**Evaluation Date**: Automated Test Suite Execution

**Scope**: All test fixtures in `data/test_fixtures/` evaluated against hand-verified `.expected.json` ground truths.

## Executive Summary & Gate Evaluation

| Category | Fixtures | Fields Tested | Matched | Accuracy | Gate Requirement | Gate Status |
|---|---|---|---|---|---|---|
| Text PDF Bank Statements | 3 | 63 | 63 | **100.00%** | > 90.0% | **PASSED** |
| Scanned PDF Bank Statements (OCR) | 2 | 41 | 41 | **100.00%** | > 75.0% | **PASSED** |
| CSV Bank Statements | 2 | 38 | 38 | **100.00%** | > 90.0% | **PASSED** |
| Salary Slips | 3 | 39 | 39 | **100.00%** | > 85.0% | **PASSED** |

**Combined Text/CSV Accuracy**: **100.00%** (Gate: > 90.0%)

**Scanned PDF (OCR) Accuracy**: **100.00%** (Gate: > 75.0%)

**Overall Pipeline Accuracy**: **100.00%**

**Phase 2 Gate Verdict**: **PASSED**

---

## Per-Fixture Detailed Breakdown

| # | Fixture File | Type / Bank / Employer | Matched / Total | Accuracy | Status |
|---|---|---|---|---|---|
| 1 | `sample_hdfc_statement.pdf` | HDFC Bank (Text PDF) | 22/22 | **100.00%** | PASSED |
| 2 | `sample_icici_statement.pdf` | ICICI Bank (Text PDF) | 19/19 | **100.00%** | PASSED |
| 3 | `sample_sbi_statement.pdf` | SBI (Text PDF) | 22/22 | **100.00%** | PASSED |
| 4 | `scanned_hdfc_statement.pdf` | HDFC Bank (Scanned OCR PDF) | 22/22 | **100.00%** | PASSED |
| 5 | `scanned_icici_statement.pdf` | ICICI Bank (Scanned OCR PDF) | 19/19 | **100.00%** | PASSED |
| 6 | `sample_hdfc_statement.csv` | HDFC Bank (Separate Columns CSV) | 19/19 | **100.00%** | PASSED |
| 7 | `sample_kotak_statement.csv` | Kotak Mahindra Bank (Type Indicator CSV) | 19/19 | **100.00%** | PASSED |
| 8 | `sample_salary_slip.pdf` | Acme Tech Solutions (April 2024) | 13/13 | **100.00%** | PASSED |
| 9 | `sample_salary_slip_may.pdf` | Infosys Technologies (May 2025) | 13/13 | **100.00%** | PASSED |
| 10 | `sample_salary_slip_june.pdf` | TCS (June 2025) | 13/13 | **100.00%** | PASSED |

---

## Field-Level Extraction Observations

### `sample_hdfc_statement.pdf` (100.00% accuracy)
- **Category**: text_pdf
- **Fields Evaluated**: 22 / 22
- **Verification Notes**:
  - Row count matched (6/6)
  - Total credits matched (₹86,200.00)
  - Total debits matched (₹31,049.00)
  - Closing balance matched (₹85,151.00)

### `sample_icici_statement.pdf` (100.00% accuracy)
- **Category**: text_pdf
- **Fields Evaluated**: 19 / 19
- **Verification Notes**:
  - Row count matched (5/5)
  - Total credits matched (₹75,620.00)
  - Total debits matched (₹21,100.00)
  - Closing balance matched (₹99,520.00)

### `sample_sbi_statement.pdf` (100.00% accuracy)
- **Category**: text_pdf
- **Fields Evaluated**: 22 / 22
- **Verification Notes**:
  - Row count matched (6/6)
  - Total credits matched (₹99,500.00)
  - Total debits matched (₹9,929.00)
  - Closing balance matched (₹109,571.00)

### `scanned_hdfc_statement.pdf` (100.00% accuracy)
- **Category**: scanned_pdf
- **Fields Evaluated**: 22 / 22
- **Verification Notes**:
  - Row count matched (6/6)
  - Total credits matched (₹86,200.00)
  - Total debits matched (₹31,049.00)
  - Closing balance matched (₹85,151.00)

### `scanned_icici_statement.pdf` (100.00% accuracy)
- **Category**: scanned_pdf
- **Fields Evaluated**: 19 / 19
- **Verification Notes**:
  - Row count matched (5/5)
  - Total credits matched (₹75,620.00)
  - Total debits matched (₹21,100.00)
  - Closing balance matched (₹99,520.00)

### `sample_hdfc_statement.csv` (100.00% accuracy)
- **Category**: csv
- **Fields Evaluated**: 19 / 19
- **Verification Notes**:
  - Row count matched (5/5)
  - Total credits matched (₹91,500.00)
  - Total debits matched (₹32,750.00)
  - Closing balance matched (₹88,750.00)

### `sample_kotak_statement.csv` (100.00% accuracy)
- **Category**: csv
- **Fields Evaluated**: 19 / 19
- **Verification Notes**:
  - Row count matched (5/5)
  - Total credits matched (₹65,420.00)
  - Total debits matched (₹4,299.00)
  - Closing balance matched (₹91,121.00)

### `sample_salary_slip.pdf` (100.00% accuracy)
- **Category**: salary_slip
- **Fields Evaluated**: 13 / 13
- **Verification Notes**:
  - month matched (4)
  - year matched (2024)
  - financial_year matched ('2024-2025')
  - basic_salary matched (₹65,000.00)
  - hra matched (₹26,000.00)
  - lta matched (₹5,000.00)
  - ... (7 additional fields verified)

### `sample_salary_slip_may.pdf` (100.00% accuracy)
- **Category**: salary_slip
- **Fields Evaluated**: 13 / 13
- **Verification Notes**:
  - month matched (5)
  - year matched (2025)
  - financial_year matched ('2025-2026')
  - basic_salary matched (₹85,000.00)
  - hra matched (₹34,000.00)
  - lta matched (₹6,000.00)
  - ... (7 additional fields verified)

### `sample_salary_slip_june.pdf` (100.00% accuracy)
- **Category**: salary_slip
- **Fields Evaluated**: 13 / 13
- **Verification Notes**:
  - month matched (6)
  - year matched (2025)
  - financial_year matched ('2025-2026')
  - basic_salary matched (₹45,000.00)
  - hra matched (₹18,000.00)
  - lta matched (₹3,500.00)
  - ... (7 additional fields verified)
