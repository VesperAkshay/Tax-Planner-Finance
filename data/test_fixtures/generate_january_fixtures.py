"""
Generates January 2026 test fixtures:
1. january_hdfc_statement.pdf (HDFC text bank statement PDF)
2. january_hdfc_statement.csv (HDFC bank statement CSV)
3. january_salary_slip.pdf (Acme Tech Solutions salary slip PDF)
"""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FIXTURES_DIR = Path(__file__).resolve().parent


def generate_january_hdfc_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "HDFCTitle",
        parent=styles["Heading1"],
        fontSize=15,
        leading=18,
        spaceAfter=6,
        textColor=colors.HexColor("#004C8F"),
    )
    normal_bold = ParagraphStyle(
        "NormalBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1A202C"),
    )
    normal_gray = ParagraphStyle(
        "NormalGray",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#4A5568"),
    )

    story.append(Paragraph("<b>HDFC BANK LIMITED</b> - STATEMENT OF ACCOUNT", title_style))
    story.append(
        Paragraph(
            "Account No: <b>50100234567890</b> | Customer: <b>Rahul Sharma</b> | Currency: <b>INR</b> | Branch: <b>Bangalore Indiranagar</b>",
            normal_bold,
        )
    )
    story.append(
        Paragraph(
            "Statement Period: <b>01/01/2026 to 31/01/2026</b> | Opening Balance: <b>₹85,000.00</b> | Closing Balance: <b>₹1,39,100.00</b>",
            normal_gray,
        )
    )
    story.append(Spacer(1, 15))

    table_data = [
        ["Date", "Narration", "Chq/Ref No", "Withdrawal (Dr)", "Deposit (Cr)", "Balance"],
        ["02/01/2026", "NEFT-RENT PAYMENT TO LANDLORD", "NEFTJAN01", "25,000.00", "", "60,000.00"],
        ["05/01/2026", "UPI-SWIGGY-BANGALORE", "UPIJAN101", "1,450.00", "", "58,550.00"],
        ["10/01/2026", "UPI-AMAZON-RETAIL-INDIA", "UPIJAN102", "3,200.00", "", "55,350.00"],
        ["15/01/2026", "BESCOM ELECTRICITY BILL", "BBPSJAN103", "2,100.00", "", "53,250.00"],
        ["20/01/2026", "HDFC MUTUAL FUND SIP", "SIPJAN104", "15,000.00", "", "38,250.00"],
        ["25/01/2026", "DIVIDEND CREDIT - TCS", "DIVJAN105", "", "850.00", "39,100.00"],
        ["31/01/2026", "SALARY CREDIT - ACME TECH SOLUTIONS", "SAL202601", "", "1,00,000.00", "1,39,100.00"],
    ]

    t = Table(table_data, colWidths=[65, 205, 80, 75, 75, 75])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#004C8F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (3, 1), (5, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ])
    )
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "<i>Summary: Total Debits: ₹46,750.00 | Total Credits: ₹1,00,850.00 | Net Growth: +₹54,100.00</i>",
            normal_gray,
        )
    )

    doc.build(story)
    print(f"Generated HDFC PDF statement: {output_path}")


def generate_january_hdfc_csv(output_path: Path):
    content = (
        "Date,Narration,Chq./Ref.No.,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        "02/01/2026,RENT TRANSFER TO LANDLORD,NEFTJAN01,25000.00,,60000.00\n"
        "05/01/2026,SWIGGY BANGALORE,UPIJAN101,1450.00,,58550.00\n"
        "10/01/2026,AMAZON RETAIL INDIA,UPIJAN102,3200.00,,55350.00\n"
        "15/01/2026,BESCOM ELECTRICITY BILL,BBPSJAN103,2100.00,,53250.00\n"
        "20/01/2026,MUTUAL FUND SIP HDFC EQUITY,SIPJAN104,15000.00,,38250.00\n"
        "25/01/2026,DIVIDEND CREDIT TCS,DIVJAN105,,850.00,39100.00\n"
        "31/01/2026,SALARY CREDIT ACME TECH SOLUTIONS,SAL202601,,100000.00,139100.00\n"
    )
    output_path.write_text(content, encoding="utf-8")
    print(f"Generated HDFC CSV statement: {output_path}")


def generate_january_salary_slip_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "CompanyHeader",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        alignment=1,  # Center
        textColor=colors.HexColor("#1A365D"),
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#4A5568"),
    )
    month_style = ParagraphStyle(
        "MonthHeader",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        alignment=1,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#2B6CB0"),
    )

    story.append(Paragraph("<b>Acme Tech Solutions India Pvt Ltd</b>", title_style))
    story.append(Paragraph("Outer Ring Road, Bellandur, Bengaluru, Karnataka - 560103", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Payslip for the month of January 2026</b>", month_style))
    story.append(Spacer(1, 15))

    # Employee Details
    emp_data = [
        ["Employee Name:", "Rahul Sharma", "Employee ID:", "ACM-10492"],
        ["Designation:", "Senior Software Engineer", "Department:", "Engineering"],
        ["PAN:", "ABCDE1234F", "UAN:", "100987654321"],
        ["Bank A/C:", "50100234567890", "Bank Name:", "HDFC Bank Ltd"],
        ["Date of Joining:", "15/07/2021", "Days Worked:", "31 / 31"],
    ]
    emp_table = Table(emp_data, colWidths=[100, 170, 95, 175])
    emp_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2D3748")),
            ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#2D3748")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(emp_table)
    story.append(Spacer(1, 15))

    # Earnings & Deductions
    comp_data = [
        ["Earnings", "Amount (INR)", "Deductions", "Amount (INR)"],
        ["Basic Salary", "65,000.00", "Provident Fund (Employee PF)", "7,800.00"],
        ["House Rent Allowance (HRA)", "26,000.00", "Employer PF Contribution", "7,800.00"],
        ["Special Allowance", "20,000.00", "Professional Tax (PT)", "200.00"],
        ["Leave Travel Allowance (LTA)", "5,000.00", "Income Tax (TDS)", "12,000.00"],
        ["Conveyance Allowance", "4,000.00", "", ""],
        ["Total Gross Pay", "1,20,000.00", "Total Deductions", "20,000.00"],
    ]
    comp_table = Table(comp_data, colWidths=[180, 90, 180, 90])
    comp_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 9),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F7FAFC")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(comp_table)
    story.append(Spacer(1, 15))

    # Net Salary Summary Banner
    net_data = [
        ["Net Salary Payable:", "INR 1,00,000.00 (Rupees One Lakh Only)"],
        ["Disbursement Mode:", "Direct Bank Transfer to HDFC Bank A/C 50100234567890"],
    ]
    net_table = Table(net_data, colWidths=[140, 400])
    net_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2B6CB0")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3182CE")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(net_table)
    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "<i>Note: This document is an electronically generated salary voucher issued by Acme Tech Solutions. No physical signature is required.</i>",
            subtitle_style,
        )
    )

    doc.build(story)
    print(f"Generated January Salary Slip PDF: {output_path}")


if __name__ == "__main__":
    generate_january_hdfc_pdf(FIXTURES_DIR / "january_hdfc_statement.pdf")
    generate_january_hdfc_csv(FIXTURES_DIR / "january_hdfc_statement.csv")
    generate_january_salary_slip_pdf(FIXTURES_DIR / "january_salary_slip.pdf")
