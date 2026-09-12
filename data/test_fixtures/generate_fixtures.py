"""
Deterministic fixture generator for Phase 2 test suite.

Generates:
- 3 Text Bank Statement PDFs (HDFC, ICICI, SBI)
- 2 Scanned Bank Statement PDFs (HDFC, ICICI)
- 2 CSV Statements (HDFC separate columns, Kotak type indicator)
- 3 Salary Slips (April 2024, May 2025, June 2025)
- 10 Hand-verified .expected.json files matching pipeline schemas
"""

import json
from pathlib import Path
import pypdfium2 as pdfium
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FIXTURES_DIR = Path(__file__).resolve().parent


# =====================================================================
# 1. TEXT BANK STATEMENT GENERATORS
# =====================================================================

def generate_hdfc_statement(output_path: Path):
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=14, spaceAfter=8)
    story.append(Paragraph("HDFC BANK LIMITED - ACCOUNT STATEMENT", title_style))
    story.append(Paragraph("Account No: 50100234567890 | Currency: INR | Branch: Bangalore Indiranagar", styles["Normal"]))
    story.append(Paragraph("Statement Period: 01/04/2025 to 30/04/2025 | Opening Balance: 30,000.00", styles["Normal"]))
    story.append(Spacer(1, 14))

    table_data = [
        ["Date", "Narration", "Chq/Ref No", "Withdrawal (Dr)", "Deposit (Cr)", "Balance"],
        ["01/04/2025", "SALARY CREDIT - ACME CORP", "SAL20250401", "", "85,000.00", "1,15,000.00"],
        ["03/04/2025", "UPI-SWIGGY-BANGALORE", "UPI987654", "450.00", "", "1,14,550.00"],
        ["05/04/2025", "NEFT-RENT PAYMENT TO LANDLORD", "NEFT112233", "25,000.00", "", "89,550.00"],
        ["10/04/2025", "ELECTRICITY BILL TNEB", "ELEC5544", "2,100.00", "", "87,450.00"],
        ["15/04/2025", "UPI-AMAZON-SHOPPING", "UPI443322", "3,499.00", "", "83,951.00"],
        ["20/04/2025", "DIVIDEND CREDIT - TCS", "DIV8899", "", "1,200.00", "85,151.00"],
    ]

    t = Table(table_data, colWidths=[65, 200, 80, 80, 70, 75])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B4C7E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    doc.build(story)


def generate_icici_statement(output_path: Path):
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("ICICITitle", parent=styles["Heading1"], fontSize=14, spaceAfter=8, textColor=colors.HexColor("#8C1D40"))
    story.append(Paragraph("ICICI BANK LIMITED - STATEMENT OF ACCOUNT", title_style))
    story.append(Paragraph("Account No: 001205012345 | Currency: INR | Branch: Koramangala Bengaluru", styles["Normal"]))
    story.append(Paragraph("Statement Period: 01/05/2025 to 25/05/2025 | Opening Balance: 45,000.00", styles["Normal"]))
    story.append(Spacer(1, 14))

    table_data = [
        ["Date", "Particulars", "Chq/Ref No", "Withdrawals", "Deposits", "Balance"],
        ["01/05/2025", "CONSULTING INCOME CLIENT ALPHA", "REF-CONS-01", "", "75,000.00", "1,20,000.00"],
        ["05/05/2025", "NATURES BASKET GROCERIES", "POS-99881", "4,250.00", "", "1,15,750.00"],
        ["12/05/2025", "BESCOM ELECTRICITY BILL", "BIL-44552", "1,850.00", "", "1,13,900.00"],
        ["18/05/2025", "HDFC MUTUAL FUND SIP", "SIP-00911", "15,000.00", "", "98,900.00"],
        ["25/05/2025", "SAVINGS INTEREST CREDIT", "INT-202505", "", "620.00", "99,520.00"],
    ]

    t = Table(table_data, colWidths=[65, 200, 80, 80, 70, 75])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8C1D40")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    doc.build(story)


def generate_sbi_statement(output_path: Path):
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("SBITitle", parent=styles["Heading1"], fontSize=14, spaceAfter=8, textColor=colors.HexColor("#1A5F7A"))
    story.append(Paragraph("STATE BANK OF INDIA - ACCOUNT STATEMENT", title_style))
    story.append(Paragraph("Account No: 20491827364 | Branch: MG Road Bengaluru | CIF: 8812736412", styles["Normal"]))
    story.append(Paragraph("Statement Period: 01/06/2025 to 28/06/2025 | Opening Balance: 20,000.00", styles["Normal"]))
    story.append(Spacer(1, 14))

    table_data = [
        ["Txn Date", "Narration", "Ref No", "Debit", "Credit", "Balance"],
        ["01/06/2025", "SALARY CREDIT TECHCORP", "SAL-202506", "", "95,000.00", "1,15,000.00"],
        ["04/06/2025", "UPI-ZOMATO-FOOD", "UPI-334411", "680.00", "", "1,14,320.00"],
        ["10/06/2025", "APOLLO PHARMACY BANGALORE", "POS-112233", "2,450.00", "", "1,11,870.00"],
        ["15/06/2025", "AIRTEL BROADBAND BILL", "BIL-88771", "1,199.00", "", "1,10,671.00"],
        ["20/06/2025", "FIXED DEPOSIT INTEREST", "INT-99221", "", "4,500.00", "1,15,171.00"],
        ["28/06/2025", "ZARA CLOTHING RETAIL", "POS-55441", "5,600.00", "", "1,09,571.00"],
    ]

    t = Table(table_data, colWidths=[65, 200, 80, 80, 70, 75])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A5F7A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    doc.build(story)


# =====================================================================
# 2. SCANNED BANK STATEMENT GENERATOR (RASTERIZED IMAGE IN PDF)
# =====================================================================

def generate_scanned_pdf(source_pdf: Path, output_pdf: Path, dpi_scale: float = 3.0):
    pdf = pdfium.PdfDocument(str(source_pdf))
    page = pdf[0]
    img = page.render(scale=dpi_scale).to_pil()
    # Save as image-only PDF
    img.save(str(output_pdf), "PDF", resolution=150.0)


# =====================================================================
# 3. CSV BANK STATEMENT GENERATORS
# =====================================================================

def generate_hdfc_csv(output_path: Path):
    content = (
        "Date,Narration,Chq/Ref No,Withdrawal Amount (INR ),Deposit Amount (INR ),Closing Balance\n"
        "01/04/2025,SALARY CREDIT ACME CORP,SAL001,,90000.00,120000.00\n"
        "03/04/2025,SWIGGY BANGALORE,UPI101,550.00,,119450.00\n"
        "07/04/2025,RENT TRANSFER TO OWNER,NEFT102,28000.00,,91450.00\n"
        "14/04/2025,AMAZON INDIA,UPI103,4200.00,,87250.00\n"
        "22/04/2025,MUTUAL FUND DIVIDEND,DIV104,,1500.00,88750.00\n"
    )
    output_path.write_text(content, encoding="utf-8")


def generate_kotak_csv(output_path: Path):
    content = (
        "Date,Transaction Details,Ref No,Amount,Dr / Cr,Balance\n"
        "02/05/2025,FREELANCE PAYMENT CLIENT X,TXN-901,65000.00,CR,95000.00\n"
        "05/05/2025,GROCERY BLINKIT,TXN-902,1250.00,DR,93750.00\n"
        "11/05/2025,TATA POWER ELECTRICITY,TXN-903,2400.00,DR,91350.00\n"
        "16/05/2025,NETFLIX SUBSCRIPTION,TXN-904,649.00,DR,90701.00\n"
        "24/05/2025,BANK INTEREST,TXN-905,420.00,CR,91121.00\n"
    )
    output_path.write_text(content, encoding="utf-8")


# =====================================================================
# 4. SALARY SLIP GENERATORS
# =====================================================================

def generate_salary_slip_april(output_path: Path):
    """April 2024 salary slip for Acme Tech Solutions."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor("#1A365D"))
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, leading=14, alignment=1, textColor=colors.HexColor("#4A5568"))

    story = [
        Paragraph("Acme Tech Solutions India Pvt Ltd", title_style),
        Paragraph("Outer Ring Road, Bengaluru, Karnataka - 560103", subtitle_style),
        Paragraph("<b>Payslip for the month of April 2024</b>", subtitle_style),
        Spacer(1, 15),
    ]

    emp_data = [
        ["Employee Name:", "Rahul Sharma", "Employee ID:", "ACM-10492"],
        ["Designation:", "Senior Software Engineer", "Department:", "Engineering"],
        ["PAN:", "ABCDE1234F", "UAN:", "100987654321"],
        ["Bank A/C:", "987654321012", "Date of Joining:", "15/07/2021"],
    ]
    emp_table = Table(emp_data, colWidths=[100, 160, 100, 160])
    emp_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 15))

    comp_data = [
        ["Earnings", "Amount (INR)", "Deductions", "Amount (INR)"],
        ["Basic Salary", "65,000.00", "Provident Fund (PF)", "7,800.00"],
        ["House Rent Allowance (HRA)", "26,000.00", "Employer PF", "7,800.00"],
        ["Leave Travel Allowance (LTA)", "5,000.00", "Professional Tax", "200.00"],
        ["Special Allowance", "20,000.00", "Income Tax (TDS)", "12,000.00"],
        ["Conveyance Allowance", "4,000.00", "", ""],
        ["Total Gross Pay", "1,20,000.00", "Total Deductions", "20,000.00"],
    ]
    comp_table = Table(comp_data, colWidths=[170, 90, 170, 90])
    comp_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F7FAFC")),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 15))

    net_data = [
        ["Net Salary Payable (INR):", "1,00,000.00"],
        ["Net Pay in Words:", "One Lakh Rupees Only"],
    ]
    net_table = Table(net_data, colWidths=[200, 320])
    net_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
    ]))
    story.append(net_table)
    doc.build(story)


def generate_salary_slip_may(output_path: Path):
    """May 2025 salary slip for Infosys Technologies."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor("#003366"))
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, leading=14, alignment=1, textColor=colors.HexColor("#4A5568"))

    story = [
        Paragraph("Infosys Technologies Limited", title_style),
        Paragraph("Electronics City, Hosur Road, Bengaluru, Karnataka - 560100", subtitle_style),
        Paragraph("<b>Payslip for the month of May 2025</b>", subtitle_style),
        Spacer(1, 15),
    ]

    emp_data = [
        ["Employee Name:", "Priya Patel", "Employee ID:", "INF-55821"],
        ["Designation:", "Lead Consultant", "Department:", "Cloud & AI"],
        ["PAN:", "ABCDE9876G", "UAN:", "100123456789"],
        ["Bank A/C:", "401099887766", "Date of Joining:", "01/03/2020"],
    ]
    emp_table = Table(emp_data, colWidths=[100, 160, 100, 160])
    emp_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 15))

    comp_data = [
        ["Earnings", "Amount (INR)", "Deductions", "Amount (INR)"],
        ["Basic Salary", "85,000.00", "Provident Fund (PF)", "10,200.00"],
        ["House Rent Allowance (HRA)", "34,000.00", "Employer PF", "10,200.00"],
        ["Leave Travel Allowance (LTA)", "6,000.00", "Professional Tax", "200.00"],
        ["Special Allowance", "25,000.00", "Income Tax (TDS)", "18,600.00"],
        ["Total Gross Pay", "1,50,000.00", "Total Deductions", "29,000.00"],
    ]
    comp_table = Table(comp_data, colWidths=[170, 90, 170, 90])
    comp_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F7FAFC")),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 15))

    net_data = [
        ["Net Salary Payable (INR):", "1,21,000.00"],
        ["Net Pay in Words:", "One Lakh Twenty One Thousand Rupees Only"],
    ]
    net_table = Table(net_data, colWidths=[200, 320])
    net_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
    ]))
    story.append(net_table)
    doc.build(story)


def generate_salary_slip_june(output_path: Path):
    """June 2025 salary slip for Tata Consultancy Services."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor("#0F4C81"))
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, leading=14, alignment=1, textColor=colors.HexColor("#4A5568"))

    story = [
        Paragraph("Tata Consultancy Services Limited", title_style),
        Paragraph("Whitefield, Bengaluru, Karnataka - 560066", subtitle_style),
        Paragraph("<b>Payslip for the month of June 2025</b>", subtitle_style),
        Spacer(1, 15),
    ]

    emp_data = [
        ["Employee Name:", "Vikram Malhotra", "Employee ID:", "TCS-89211"],
        ["Designation:", "Software Engineer", "Department:", "Banking Solutions"],
        ["PAN:", "BCDEF1234H", "UAN:", "100456789012"],
        ["Bank A/C:", "501009871234", "Date of Joining:", "10/01/2023"],
    ]
    emp_table = Table(emp_data, colWidths=[100, 160, 100, 160])
    emp_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 15))

    comp_data = [
        ["Earnings", "Amount (INR)", "Deductions", "Amount (INR)"],
        ["Basic Salary", "45,000.00", "Provident Fund (PF)", "5,400.00"],
        ["House Rent Allowance (HRA)", "18,000.00", "Employer PF", "5,400.00"],
        ["Leave Travel Allowance (LTA)", "3,500.00", "Professional Tax", "200.00"],
        ["Special Allowance", "13,500.00", "Income Tax (TDS)", "4,400.00"],
        ["Total Gross Pay", "80,000.00", "Total Deductions", "10,000.00"],
    ]
    comp_table = Table(comp_data, colWidths=[170, 90, 170, 90])
    comp_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F7FAFC")),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 15))

    net_data = [
        ["Net Salary Payable (INR):", "70,000.00"],
        ["Net Pay in Words:", "Seventy Thousand Rupees Only"],
    ]
    net_table = Table(net_data, colWidths=[200, 320])
    net_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
    ]))
    story.append(net_table)
    doc.build(story)


# =====================================================================
# 5. HAND-VERIFIED EXPECTED OUTPUT DEFINITIONS
# =====================================================================

EXPECTED_HDFC_STATEMENT = {
    "fixture_type": "bank_statement",
    "bank_name": "HDFC Bank",
    "opening_balance": 30000.0,
    "closing_balance": 85151.0,
    "statement_start_date": "2025-04-01",
    "statement_end_date": "2025-04-20",
    "total_credits": 86200.0,
    "total_debits": 31049.0,
    "total_rows": 6,
    "rows": [
        {
            "date": "2025-04-01",
            "description": "SALARY CREDIT - ACME CORP",
            "amount": 85000.0,
            "transaction_type": "credit",
            "balance": 115000.0,
            "reference_number": "SAL20250401",
        },
        {
            "date": "2025-04-03",
            "description": "UPI-SWIGGY-BANGALORE",
            "amount": 450.0,
            "transaction_type": "debit",
            "balance": 114550.0,
            "reference_number": "UPI987654",
        },
        {
            "date": "2025-04-05",
            "description": "NEFT-RENT PAYMENT TO LANDLORD",
            "amount": 25000.0,
            "transaction_type": "debit",
            "balance": 89550.0,
            "reference_number": "NEFT112233",
        },
        {
            "date": "2025-04-10",
            "description": "ELECTRICITY BILL TNEB",
            "amount": 2100.0,
            "transaction_type": "debit",
            "balance": 87450.0,
            "reference_number": "ELEC5544",
        },
        {
            "date": "2025-04-15",
            "description": "UPI-AMAZON-SHOPPING",
            "amount": 3499.0,
            "transaction_type": "debit",
            "balance": 83951.0,
            "reference_number": "UPI443322",
        },
        {
            "date": "2025-04-20",
            "description": "DIVIDEND CREDIT - TCS",
            "amount": 1200.0,
            "transaction_type": "credit",
            "balance": 85151.0,
            "reference_number": "DIV8899",
        },
    ],
}

EXPECTED_ICICI_STATEMENT = {
    "fixture_type": "bank_statement",
    "bank_name": "ICICI Bank",
    "opening_balance": 45000.0,
    "closing_balance": 99520.0,
    "statement_start_date": "2025-05-01",
    "statement_end_date": "2025-05-25",
    "total_credits": 75620.0,
    "total_debits": 21100.0,
    "total_rows": 5,
    "rows": [
        {
            "date": "2025-05-01",
            "description": "CONSULTING INCOME CLIENT ALPHA",
            "amount": 75000.0,
            "transaction_type": "credit",
            "balance": 120000.0,
            "reference_number": "REF-CONS-01",
        },
        {
            "date": "2025-05-05",
            "description": "NATURES BASKET GROCERIES",
            "amount": 4250.0,
            "transaction_type": "debit",
            "balance": 115750.0,
            "reference_number": "POS-99881",
        },
        {
            "date": "2025-05-12",
            "description": "BESCOM ELECTRICITY BILL",
            "amount": 1850.0,
            "transaction_type": "debit",
            "balance": 113900.0,
            "reference_number": "BIL-44552",
        },
        {
            "date": "2025-05-18",
            "description": "HDFC MUTUAL FUND SIP",
            "amount": 15000.0,
            "transaction_type": "debit",
            "balance": 98900.0,
            "reference_number": "SIP-00911",
        },
        {
            "date": "2025-05-25",
            "description": "SAVINGS INTEREST CREDIT",
            "amount": 620.0,
            "transaction_type": "credit",
            "balance": 99520.0,
            "reference_number": "INT-202505",
        },
    ],
}

EXPECTED_SBI_STATEMENT = {
    "fixture_type": "bank_statement",
    "bank_name": "State Bank of India",
    "opening_balance": 20000.0,
    "closing_balance": 109571.0,
    "statement_start_date": "2025-06-01",
    "statement_end_date": "2025-06-28",
    "total_credits": 99500.0,
    "total_debits": 9929.0,
    "total_rows": 6,
    "rows": [
        {
            "date": "2025-06-01",
            "description": "SALARY CREDIT TECHCORP",
            "amount": 95000.0,
            "transaction_type": "credit",
            "balance": 115000.0,
            "reference_number": "SAL-202506",
        },
        {
            "date": "2025-06-04",
            "description": "UPI-ZOMATO-FOOD",
            "amount": 680.0,
            "transaction_type": "debit",
            "balance": 114320.0,
            "reference_number": "UPI-334411",
        },
        {
            "date": "2025-06-10",
            "description": "APOLLO PHARMACY BANGALORE",
            "amount": 2450.0,
            "transaction_type": "debit",
            "balance": 111870.0,
            "reference_number": "POS-112233",
        },
        {
            "date": "2025-06-15",
            "description": "AIRTEL BROADBAND BILL",
            "amount": 1199.0,
            "transaction_type": "debit",
            "balance": 110671.0,
            "reference_number": "BIL-88771",
        },
        {
            "date": "2025-06-20",
            "description": "FIXED DEPOSIT INTEREST",
            "amount": 4500.0,
            "transaction_type": "credit",
            "balance": 115171.0,
            "reference_number": "INT-99221",
        },
        {
            "date": "2025-06-28",
            "description": "ZARA CLOTHING RETAIL",
            "amount": 5600.0,
            "transaction_type": "debit",
            "balance": 109571.0,
            "reference_number": "POS-55441",
        },
    ],
}

EXPECTED_HDFC_CSV = {
    "fixture_type": "bank_statement",
    "bank_name": "HDFC Bank",
    "opening_balance": 30000.0,
    "closing_balance": 88750.0,
    "statement_start_date": "2025-04-01",
    "statement_end_date": "2025-04-22",
    "total_credits": 91500.0,
    "total_debits": 32750.0,
    "total_rows": 5,
    "rows": [
        {
            "date": "2025-04-01",
            "description": "SALARY CREDIT ACME CORP",
            "amount": 90000.0,
            "transaction_type": "credit",
            "balance": 120000.0,
            "reference_number": "SAL001",
        },
        {
            "date": "2025-04-03",
            "description": "SWIGGY BANGALORE",
            "amount": 550.0,
            "transaction_type": "debit",
            "balance": 119450.0,
            "reference_number": "UPI101",
        },
        {
            "date": "2025-04-07",
            "description": "RENT TRANSFER TO OWNER",
            "amount": 28000.0,
            "transaction_type": "debit",
            "balance": 91450.0,
            "reference_number": "NEFT102",
        },
        {
            "date": "2025-04-14",
            "description": "AMAZON INDIA",
            "amount": 4200.0,
            "transaction_type": "debit",
            "balance": 87250.0,
            "reference_number": "UPI103",
        },
        {
            "date": "2025-04-22",
            "description": "MUTUAL FUND DIVIDEND",
            "amount": 1500.0,
            "transaction_type": "credit",
            "balance": 88750.0,
            "reference_number": "DIV104",
        },
    ],
}

EXPECTED_KOTAK_CSV = {
    "fixture_type": "bank_statement",
    "bank_name": "Kotak Mahindra Bank",
    "opening_balance": 30000.0,
    "closing_balance": 91121.0,
    "statement_start_date": "2025-05-02",
    "statement_end_date": "2025-05-24",
    "total_credits": 65420.0,
    "total_debits": 4299.0,
    "total_rows": 5,
    "rows": [
        {
            "date": "2025-05-02",
            "description": "FREELANCE PAYMENT CLIENT X",
            "amount": 65000.0,
            "transaction_type": "credit",
            "balance": 95000.0,
            "reference_number": "TXN-901",
        },
        {
            "date": "2025-05-05",
            "description": "GROCERY BLINKIT",
            "amount": 1250.0,
            "transaction_type": "debit",
            "balance": 93750.0,
            "reference_number": "TXN-902",
        },
        {
            "date": "2025-05-11",
            "description": "TATA POWER ELECTRICITY",
            "amount": 2400.0,
            "transaction_type": "debit",
            "balance": 91350.0,
            "reference_number": "TXN-903",
        },
        {
            "date": "2025-05-16",
            "description": "NETFLIX SUBSCRIPTION",
            "amount": 649.0,
            "transaction_type": "debit",
            "balance": 90701.0,
            "reference_number": "TXN-904",
        },
        {
            "date": "2025-05-24",
            "description": "BANK INTEREST",
            "amount": 420.0,
            "transaction_type": "credit",
            "balance": 91121.0,
            "reference_number": "TXN-905",
        },
    ],
}

EXPECTED_SALARY_APRIL = {
    "fixture_type": "salary_slip",
    "employer_name": "Acme Tech Solutions India Pvt Ltd",
    "month": 4,
    "year": 2024,
    "financial_year": "2024-25",
    "basic_salary": 65000.0,
    "hra": 26000.0,
    "lta": 5000.0,
    "special_allowance": 20000.0,
    "employer_pf": 7800.0,
    "employee_pf": 7800.0,
    "professional_tax": 200.0,
    "tds": 12000.0,
    "gross_pay": 120000.0,
    "net_pay": 100000.0,
}

EXPECTED_SALARY_MAY = {
    "fixture_type": "salary_slip",
    "employer_name": "Infosys Technologies Limited",
    "month": 5,
    "year": 2025,
    "financial_year": "2025-26",
    "basic_salary": 85000.0,
    "hra": 34000.0,
    "lta": 6000.0,
    "special_allowance": 25000.0,
    "employer_pf": 10200.0,
    "employee_pf": 10200.0,
    "professional_tax": 200.0,
    "tds": 18600.0,
    "gross_pay": 150000.0,
    "net_pay": 121000.0,
}

EXPECTED_SALARY_JUNE = {
    "fixture_type": "salary_slip",
    "employer_name": "Tata Consultancy Services Limited",
    "month": 6,
    "year": 2025,
    "financial_year": "2025-26",
    "basic_salary": 45000.0,
    "hra": 18000.0,
    "lta": 3500.0,
    "special_allowance": 13500.0,
    "employer_pf": 5400.0,
    "employee_pf": 5400.0,
    "professional_tax": 200.0,
    "tds": 4400.0,
    "gross_pay": 80000.0,
    "net_pay": 70000.0,
}


def build_all_fixtures():
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    print("1. Generating 3 text bank statement PDFs...")
    hdfc_pdf = FIXTURES_DIR / "sample_hdfc_statement.pdf"
    generate_hdfc_statement(hdfc_pdf)
    (FIXTURES_DIR / "sample_hdfc_statement.expected.json").write_text(
        json.dumps(EXPECTED_HDFC_STATEMENT, indent=2), encoding="utf-8"
    )

    icici_pdf = FIXTURES_DIR / "sample_icici_statement.pdf"
    generate_icici_statement(icici_pdf)
    (FIXTURES_DIR / "sample_icici_statement.expected.json").write_text(
        json.dumps(EXPECTED_ICICI_STATEMENT, indent=2), encoding="utf-8"
    )

    sbi_pdf = FIXTURES_DIR / "sample_sbi_statement.pdf"
    generate_sbi_statement(sbi_pdf)
    (FIXTURES_DIR / "sample_sbi_statement.expected.json").write_text(
        json.dumps(EXPECTED_SBI_STATEMENT, indent=2), encoding="utf-8"
    )

    print("2. Generating 2 scanned bank statement PDFs...")
    scanned_hdfc_pdf = FIXTURES_DIR / "scanned_hdfc_statement.pdf"
    generate_scanned_pdf(hdfc_pdf, scanned_hdfc_pdf, dpi_scale=3.0)
    (FIXTURES_DIR / "scanned_hdfc_statement.expected.json").write_text(
        json.dumps(EXPECTED_HDFC_STATEMENT, indent=2), encoding="utf-8"
    )

    scanned_icici_pdf = FIXTURES_DIR / "scanned_icici_statement.pdf"
    generate_scanned_pdf(icici_pdf, scanned_icici_pdf, dpi_scale=3.0)
    (FIXTURES_DIR / "scanned_icici_statement.expected.json").write_text(
        json.dumps(EXPECTED_ICICI_STATEMENT, indent=2), encoding="utf-8"
    )

    print("3. Generating 2 CSV bank statements...")
    hdfc_csv = FIXTURES_DIR / "sample_hdfc_statement.csv"
    generate_hdfc_csv(hdfc_csv)
    (FIXTURES_DIR / "sample_hdfc_statement.csv.expected.json").write_text(
        json.dumps(EXPECTED_HDFC_CSV, indent=2), encoding="utf-8"
    )

    kotak_csv = FIXTURES_DIR / "sample_kotak_statement.csv"
    generate_kotak_csv(kotak_csv)
    (FIXTURES_DIR / "sample_kotak_statement.csv.expected.json").write_text(
        json.dumps(EXPECTED_KOTAK_CSV, indent=2), encoding="utf-8"
    )

    print("4. Generating 3 salary slips...")
    salary_april = FIXTURES_DIR / "sample_salary_slip.pdf"
    generate_salary_slip_april(salary_april)
    (FIXTURES_DIR / "sample_salary_slip.expected.json").write_text(
        json.dumps(EXPECTED_SALARY_APRIL, indent=2), encoding="utf-8"
    )

    salary_may = FIXTURES_DIR / "sample_salary_slip_may.pdf"
    generate_salary_slip_may(salary_may)
    (FIXTURES_DIR / "sample_salary_slip_may.expected.json").write_text(
        json.dumps(EXPECTED_SALARY_MAY, indent=2), encoding="utf-8"
    )

    salary_june = FIXTURES_DIR / "sample_salary_slip_june.pdf"
    generate_salary_slip_june(salary_june)
    (FIXTURES_DIR / "sample_salary_slip_june.expected.json").write_text(
        json.dumps(EXPECTED_SALARY_JUNE, indent=2), encoding="utf-8"
    )

    print("Successfully built all 10 test fixtures and their .expected.json files!")


if __name__ == "__main__":
    build_all_fixtures()
