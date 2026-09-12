import datetime
import pytest
from app.parsing.csv_adapter_schema import BankAdapterConfig, SignConvention
from app.parsing.csv_parser import CSVBankAdapterRegistry, CSVBankParser


@pytest.fixture
def parser():
    return CSVBankParser()


def test_hdfc_csv_explicit_and_sniff(parser: CSVBankParser):
    hdfc_csv = """HDFC Bank Statement
Date,Narration,Chq./Ref.No.,Value Dt,Withdrawal Amt.,Deposit Amt.,Closing Balance
01/04/24,SALARY CREDIT INFOSYS,REF123456,01/04/24,,150000.00,150000.00
05/04/24,AMAZON INDIA RETAIL,REF789012,05/04/24,4500.50,,145499.50
10/04/24,ELECTRICITY BILL MSEB,REF345678,10/04/24,2300.00,,143199.50
"""
    # 1. Test explicit bank_id
    res_explicit = parser.parse_content(hdfc_csv, bank_id="hdfc")
    assert len(res_explicit.rows) == 3
    assert res_explicit.total_credits == 150000.00
    assert res_explicit.total_debits == 6800.50
    assert res_explicit.opening_balance == 0.00  # 150000 - 150000
    assert res_explicit.closing_balance == 143199.50
    assert res_explicit.statement_start_date == datetime.date(2024, 4, 1)
    assert res_explicit.statement_end_date == datetime.date(2024, 4, 10)
    assert not res_explicit.needs_review

    # Check row specifics
    r1 = res_explicit.rows[0]
    assert r1.date == datetime.date(2024, 4, 1)
    assert r1.description == "SALARY CREDIT INFOSYS"
    assert r1.amount == 150000.00
    assert r1.transaction_type == "credit"
    assert r1.reference_number == "REF123456"
    assert r1.balance == 150000.00

    r2 = res_explicit.rows[1]
    assert r2.transaction_type == "debit"
    assert r2.amount == 4500.50

    # 2. Test auto-sniffing without bank_id
    res_sniff = parser.parse_content(hdfc_csv)
    assert len(res_sniff.rows) == 3
    assert res_sniff.total_credits == 150000.00
    assert res_sniff.total_debits == 6800.50


def test_icici_csv_auto_sniff(parser: CSVBankParser):
    icici_csv = """ICICI Bank Account Statement
Account Number: 000123456789
Customer Name: John Doe
Statement Period: 01-04-2024 to 30-04-2024
Generated on: 01-05-2024
Notes: Please review your statement carefully
Transaction Date,Transaction Remarks,Cheque Number,Withdrawal Amount (INR ),Deposit Amount (INR ),Balance (INR )
02/04/2024,DIVIDEND TCS LTD,CHQ001,,2500.00,52500.00
08/04/2024,SWIGGY BANGALORE,CHQ002,450.00,,52050.00
15/04/2024,RENT TRANSFER TO OWNER,CHQ003,25000.00,,27050.00
"""
    res = parser.parse_content(icici_csv)
    assert len(res.rows) == 3
    assert res.statement_start_date == datetime.date(2024, 4, 2)
    assert res.statement_end_date == datetime.date(2024, 4, 15)
    assert res.total_credits == 2500.00
    assert res.total_debits == 25450.00
    assert res.closing_balance == 27050.00
    assert not res.needs_review


def test_sbi_csv_auto_sniff(parser: CSVBankParser):
    sbi_csv = """State Bank of India
Account Name: Ramesh Kumar
Branch: New Delhi Main Branch
Line 4
Line 5
Line 6
Line 7
Line 8
Line 9
Line 10
Line 11
Line 12
Line 13
Line 14
Line 15
Line 16
Line 17
Line 18
Line 19
Txn Date,Description,Ref No./Cheque No.,Debit,Credit,Balance
10 Apr 2024,INTEREST CREDIT,REF001,,120.00,10120.00
14 Apr 2024,UPI-GROCERIES-998877,REF002,1500.00,,8620.00
"""
    res = parser.parse_content(sbi_csv)
    assert len(res.rows) == 2
    assert res.rows[0].date == datetime.date(2024, 4, 10)
    assert res.rows[0].transaction_type == "credit"
    assert res.rows[0].amount == 120.00
    assert res.rows[1].date == datetime.date(2024, 4, 14)
    assert res.rows[1].transaction_type == "debit"
    assert res.rows[1].amount == 1500.00
    assert res.closing_balance == 8620.00
    assert not res.needs_review


def test_kotak_csv_type_indicator(parser: CSVBankParser):
    kotak_csv = """Kotak Mahindra Bank Account Statement
Account details line 2
Account details line 3
Account details line 4
Account details line 5
Account details line 6
Account details line 7
Account details line 8
Account details line 9
Account details line 10
Account details line 11
Transaction Date,Narration,Transaction Type,Amount,Balance,Reference Number
05-04-2024,SALARY CREDIT,CR,85000.00,105000.00,KOTAK001
12-04-2024,SIP MUTUAL FUND,DR,10000.00,95000.00,KOTAK002
"""
    res = parser.parse_content(kotak_csv)
    assert len(res.rows) == 2
    assert res.rows[0].transaction_type == "credit"
    assert res.rows[0].amount == 85000.00
    assert res.rows[1].transaction_type == "debit"
    assert res.rows[1].amount == 10000.00
    assert res.closing_balance == 95000.00
    assert not res.needs_review


def test_signed_amount_custom_adapter():
    custom_adapter = BankAdapterConfig(
        bank_id="custom_fintech",
        bank_name="Fintech Bank",
        header_signatures=["Date", "Description", "Net Amount", "Running Balance"],
        sign_convention=SignConvention.SIGNED_AMOUNT,
        positive_is_credit=True,
        date_column="Date",
        date_format="%Y-%m-%d",
        description_column="Description",
        amount_column="Net Amount",
        balance_column="Running Balance",
    )
    registry = CSVBankAdapterRegistry()
    registry.adapters[custom_adapter.bank_id] = custom_adapter
    parser = CSVBankParser(registry=registry)

    csv_data = """Date,Description,Net Amount,Running Balance
2024-05-01,Freelance Payment,25000.00,25000.00
2024-05-03,Laptop Purchase,-45000.00,-20000.00
"""
    res = parser.parse_content(csv_data, bank_id="custom_fintech")
    assert len(res.rows) == 2
    assert res.rows[0].transaction_type == "credit"
    assert res.rows[0].amount == 25000.00
    assert res.rows[1].transaction_type == "debit"
    assert res.rows[1].amount == 45000.00
    assert not res.needs_review


def test_unrecognized_csv(parser: CSVBankParser):
    unrecognized = """Some,Random,Headers,Not,Matching
1,2,3,4,5
foo,bar,baz,qux,quux
"""
    res = parser.parse_content(unrecognized)
    assert res.needs_review is True
    assert res.parse_confidence == 0.0
    assert len(res.rows) == 0
    assert any("Could not identify bank CSV format" in w for w in res.warnings)
