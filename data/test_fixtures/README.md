# Test Fixtures & Hand-Verified Expected Outputs (Task 2.10)

This directory contains deterministic test fixtures and their corresponding hand-verified `.expected.json` ground truth files used to evaluate the document parsing pipeline.

## Fixture Inventory

### 1. Text Bank Statement PDFs (3 fixtures)
- **`sample_hdfc_statement.pdf`** | Expected: `sample_hdfc_statement.expected.json`
  - Bank: HDFC Bank Limited (Account: 50100234567890)
  - Period: 01/04/2025 to 30/04/2025 | Opening: ₹30,000.00 | Closing: ₹85,151.00
  - 6 transactions (1 salary credit, 4 debits, 1 dividend credit)
- **`sample_icici_statement.pdf`** | Expected: `sample_icici_statement.expected.json`
  - Bank: ICICI Bank Limited (Account: 001205012345)
  - Period: 01/05/2025 to 25/05/2025 | Opening: ₹45,000.00 | Closing: ₹99,520.00
  - 5 transactions (1 consulting credit, 3 debits, 1 interest credit)
- **`sample_sbi_statement.pdf`** | Expected: `sample_sbi_statement.expected.json`
  - Bank: State Bank of India (Account: 20491827364)
  - Period: 01/06/2025 to 28/06/2025 | Opening: ₹20,000.00 | Closing: ₹1,09,571.00
  - 6 transactions (1 salary credit, 4 debits, 1 FD interest credit)

### 2. Scanned / OCR Bank Statement PDFs (2 fixtures)
- **`scanned_hdfc_statement.pdf`** | Expected: `scanned_hdfc_statement.expected.json`
  - Pure image-only PDF rasterized at 300 DPI from `sample_hdfc_statement.pdf`.
  - Processed through Docling RapidOCR OCR pipeline.
- **`scanned_icici_statement.pdf`** | Expected: `scanned_icici_statement.expected.json`
  - Pure image-only PDF rasterized at 300 DPI from `sample_icici_statement.pdf`.
  - Processed through Docling RapidOCR OCR pipeline.

### 3. Bank Statement CSVs (2 fixtures, different bank formats)
- **`sample_hdfc_statement.csv`** | Expected: `sample_hdfc_statement.csv.expected.json`
  - Format: HDFC format (`SEPARATE_COLUMNS` sign convention for Withdrawal / Deposit).
  - 5 transactions, Opening: ₹30,000.00 | Closing: ₹88,750.00.
- **`sample_kotak_statement.csv`** | Expected: `sample_kotak_statement.csv.expected.json`
  - Format: Kotak format (`TYPE_INDICATOR` convention with `Dr / Cr` indicator column).
  - 5 transactions, Opening: ₹30,000.00 | Closing: ₹91,121.00.

### 4. Salary Slips (3 fixtures)
- **`sample_salary_slip.pdf`** | Expected: `sample_salary_slip.expected.json`
  - Employer: Acme Tech Solutions India Pvt Ltd | Period: April 2024 (FY 2024-25)
  - Gross: ₹1,20,000.00 | Deductions: ₹20,000.00 | Net: ₹1,00,000.00
- **`sample_salary_slip_may.pdf`** | Expected: `sample_salary_slip_may.expected.json`
  - Employer: Infosys Technologies Limited | Period: May 2025 (FY 2025-26)
  - Gross: ₹1,50,000.00 | Deductions: ₹29,000.00 | Net: ₹1,21,000.00
- **`sample_salary_slip_june.pdf`** | Expected: `sample_salary_slip_june.expected.json`
  - Employer: Tata Consultancy Services Limited | Period: June 2025 (FY 2025-26)
  - Gross: ₹80,000.00 | Deductions: ₹10,000.00 | Net: ₹70,000.00

## How to Regenerate Fixtures

All fixtures and ground-truth JSON files can be deterministically regenerated at any time:

```bash
uv run python data/test_fixtures/generate_fixtures.py
```
