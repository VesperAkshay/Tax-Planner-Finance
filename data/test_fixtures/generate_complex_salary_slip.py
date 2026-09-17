"""
Generate Complex Enterprise Salary Slip PDF with Statutory Tax Declarations Annexure.

Features:
- Page 1: Monthly Payslip & Earnings/Deductions Matrix (May 2025)
  - 12 Itemized Earnings components (Total Gross: INR 3,87,000.00)
  - 9 Itemized Deductions components (Total Deductions: INR 1,21,270.00)
  - Net Take-Home Pay: INR 2,65,730.00
  - Attendance & Leave Accounting Ledger (Calendar 31, Payable 30, LOP 1.0)
  - Employer Statutory Contributions & Monthly CTC
  - Year-To-Date (YTD) Cumulative Ledger
- Page 2: Annexure - Statutory Tax Declarations & Regime Audit Worksheet
  - 01. Standard Deduction (- ₹50,000.00 vs - ₹75,000.00)
  - 02. Section 80CCD(2) Employer NPS Contribution
  - 03. Section 80C (EPF, PPF, ELSS, Insurance)     - ₹0.00    N/A (Disallowed)    Sec 80C (Cap ₹1.5L)
  - 04. Section 80D (Health Insurance)              - ₹0.00    N/A (Disallowed)    Sec 80D
  - 05. Section 80CCD(1B) (National Pension Scheme) - ₹0.00    N/A (Disallowed)    Sec 80CCD(1B)
  - 06. Section 10(13A) (HRA Exemption)             - ₹0.00    N/A (Disallowed)    Rule 2A / Sec 10(13A)
  - Comparative Old vs New (Sec 115BAC) projected tax liability
  - Vector TrueType Unicode font registration for native Indian Rupee symbol (₹)
"""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Global font & currency configuration
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_OBLIQUE = "Helvetica-Oblique"
CURRENCY_PREFIX = "₹"


def _initialize_pdf_fonts() -> None:
    """Registers TrueType font containing the Indian Rupee glyph (U+20B9)."""
    global FONT_REGULAR, FONT_BOLD, FONT_OBLIQUE, CURRENCY_PREFIX

    candidates = [
        (
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/ariali.ttf",
        ),
        (
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/segoeuii.ttf",
        ),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        ),
    ]

    for reg_path, bold_path, ob_path in candidates:
        if Path(reg_path).exists() and Path(bold_path).exists():
            try:
                reg_font = TTFont("SalaryTTFRegular", reg_path)
                bold_font = TTFont("SalaryTTFBold", bold_path)
                if 0x20B9 in reg_font.face.charToGlyph:
                    pdfmetrics.registerFont(reg_font)
                    pdfmetrics.registerFont(bold_font)
                    if Path(ob_path).exists():
                        pdfmetrics.registerFont(TTFont("SalaryTTFOblique", ob_path))
                        FONT_OBLIQUE = "SalaryTTFOblique"
                    else:
                        FONT_OBLIQUE = "SalaryTTFRegular"
                    FONT_REGULAR = "SalaryTTFRegular"
                    FONT_BOLD = "SalaryTTFBold"
                    CURRENCY_PREFIX = "₹"
                    return
            except Exception:
                continue

    FONT_REGULAR = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"
    FONT_OBLIQUE = "Helvetica-Oblique"
    CURRENCY_PREFIX = "Rs. "


def fmt_inr(val: float) -> str:
    """Format numeric value in Indian numbering style with currency prefix."""
    return f"{CURRENCY_PREFIX}{val:,.2f}"


def generate_complex_salary_slip(output_path: Path):
    _initialize_pdf_fonts()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=28,
        leftMargin=28,
        topMargin=22,
        bottomMargin=22,
    )

    styles = getSampleStyleSheet()

    # Typography styles
    corp_title_style = ParagraphStyle(
        "CorpTitle",
        parent=styles["Heading1"],
        fontName=FONT_BOLD,
        fontSize=12.5,
        leading=15,
        alignment=1,
        textColor=colors.HexColor("#0F172A"),
    )
    corp_sub_style = ParagraphStyle(
        "CorpSub",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7.5,
        leading=10,
        alignment=1,
        textColor=colors.HexColor("#475569"),
    )
    period_title_style = ParagraphStyle(
        "PeriodTitle",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#1E3A8A"),
    )
    th_style = ParagraphStyle(
        "TableHead",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
    )
    td_bold = ParagraphStyle(
        "TDBold",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#0F172A"),
    )
    td_reg = ParagraphStyle(
        "TDReg",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#334155"),
    )
    td_right_bold = ParagraphStyle(
        "TDRB",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=7,
        leading=9,
        alignment=2,
        textColor=colors.HexColor("#0F172A"),
    )
    td_right_reg = ParagraphStyle(
        "TDRR",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7,
        leading=9,
        alignment=2,
        textColor=colors.HexColor("#334155"),
    )
    td_muted = ParagraphStyle(
        "TDMuted",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7,
        leading=9,
        alignment=2,
        textColor=colors.HexColor("#64748B"),
    )
    td_muted_left = ParagraphStyle(
        "TDMutedLeft",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#64748B"),
    )
    annex_title_style = ParagraphStyle(
        "AnnexTitle",
        parent=styles["Heading1"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=15,
        alignment=1,
        textColor=colors.HexColor("#1E3A8A"),
    )
    annex_sub_style = ParagraphStyle(
        "AnnexSub",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=7.5,
        leading=10,
        alignment=1,
        textColor=colors.HexColor("#475569"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName=FONT_OBLIQUE,
        fontSize=6.5,
        leading=8.5,
        alignment=1,
        textColor=colors.HexColor("#64748B"),
    )

    story = []

    # ==========================================================================
    # PAGE 1: MONTHLY SALARY SLIP (COMPREHENSIVE ENTERPRISE COMPENSATION)
    # ==========================================================================

    # Header
    story.append(Paragraph("APEX GLOBAL TECHNOLOGIES (INDIA) PRIVATE LIMITED", corp_title_style))
    story.append(
        Paragraph(
            "Embassy TechVillage, Outer Ring Road, Devarabeesanahalli, Bengaluru, Karnataka - 560103",
            corp_sub_style,
        )
    )
    story.append(
        Paragraph(
            "CIN: U72200KA2015PTC082341 &nbsp;|&nbsp; GSTIN: 29AABCA8392K1ZX &nbsp;|&nbsp; TAN: BLRA12345B",
            corp_sub_style,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>PAYSLIP FOR THE MONTH OF MAY 2025</b>",
            period_title_style,
        )
    )
    story.append(Spacer(1, 5))

    # Employee Details Matrix (4-column grid)
    emp_info = [
        ["Employee Name:", "Vikramaditya Singhania", "Employee ID:", "AGT-DIR-9082"],
        ["Designation:", "Principal Architect & Engineering Director", "Department:", "Cloud Systems & AI Platform"],
        ["Date of Joining:", "15/06/2019", "Location / Cost Center:", "Bengaluru / CC-IND-BLR-04"],
        ["PAN:", "ABCPS1234K", "UAN:", "101482910382"],
        ["Bank Name:", "HDFC Bank Limited", "Bank A/C:", "50100482910384"],
        ["IFSC Code:", "HDFC0000240", "Tax Regime:", "Section 115BAC (New Tax Regime)"],
    ]
    emp_table = Table(emp_info, colWidths=[90, 195, 105, 166])
    emp_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#334155")),
            ("FONTNAME", (0, 0), (0, -1), FONT_BOLD),
            ("FONTNAME", (2, 0), (2, -1), FONT_BOLD),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#1E293B")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ])
    )
    story.append(emp_table)
    story.append(Spacer(1, 5))

    # Attendance & Leave Summary
    attendance_data = [
        ["Calendar Days: 31.0", "Payable Days: 30.0", "Loss of Pay (LOP): 1.0", "Earned Leave: 13.5", "Sick Leave: 6.0", "Casual Leave: 4.0"]
    ]
    attendance_table = Table(attendance_data, colWidths=[90, 90, 110, 90, 85, 91])
    attendance_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF2F6")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )
    story.append(attendance_table)
    story.append(Spacer(1, 5))

    # Detailed Itemized Earnings & Deductions Table (12 rows)
    comp_data = [
        ["Earnings", "Amount (INR)", "Deductions", "Amount (INR)"],
        ["Basic Salary", "1,85,000.00", "Provident Fund (PF)", "22,200.00"],
        ["House Rent Allowance (HRA)", "74,000.00", "Employer PF", "22,200.00"],
        ["Special Allowance", "48,500.00", "Professional Tax", "200.00"],
        ["Leave Travel Allowance (LTA)", "15,000.00", "Income Tax (TDS)", "68,500.00"],
        ["Performance Bonus", "45,000.00", "Voluntary PF", "10,000.00"],
        ["Conveyance Allowance", "5,000.00", "Group Insurance", "2,850.00"],
        ["Telephone Allowance", "3,500.00", "Labour Welfare Fund", "20.00"],
        ["Books & Periodicals", "2,500.00", "Salary Advance", "5,000.00"],
        ["Uniform Allowance", "2,000.00", "Other Deductions", "12,500.00"],
        ["Meal Allowance", "3,000.00", "", ""],
        ["Shift Allowance", "2,500.00", "", ""],
        ["Child Education Allowance", "1,000.00", "", ""],
        ["Total Gross Pay", "3,87,000.00", "Total Deductions", "1,21,270.00"],
    ]

    comp_table = Table(comp_data, colWidths=[185, 93, 185, 93])
    comp_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, 0), 7.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("ALIGN", (2, 0), (2, -1), "LEFT"),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("FONTNAME", (0, 1), (-1, -2), FONT_REGULAR),
            ("FONTSIZE", (0, 1), (-1, -2), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFFFF")),
            ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#FFFFFF")),
            ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#FFFFFF")),
            ("BACKGROUND", (0, 6), (-1, 6), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (0, 7), (-1, 7), colors.HexColor("#FFFFFF")),
            ("BACKGROUND", (0, 8), (-1, 8), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (0, 9), (-1, 9), colors.HexColor("#FFFFFF")),
            ("BACKGROUND", (0, 10), (-1, 10), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (0, 11), (-1, 11), colors.HexColor("#FFFFFF")),
            ("BACKGROUND", (0, 12), (-1, 12), colors.HexColor("#F8FAFC")),
            ("FONTNAME", (0, -1), (-1, -1), FONT_BOLD),
            ("FONTSIZE", (0, -1), (-1, -1), 7.5),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E2E8F0")),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#0F172A")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#64748B")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ])
    )
    story.append(comp_table)
    story.append(Spacer(1, 5))

    # Net Pay Banner Table
    net_pay_data = [
        [
            "Net Take-Home Pay:",
            "INR 2,65,730.00",
            "In Words:",
            "Indian Rupees Two Lakh Sixty-Five Thousand Seven Hundred Thirty Only",
        ],
    ]
    net_table = Table(net_pay_data, colWidths=[110, 105, 55, 286])
    net_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (0, 0), FONT_BOLD),
            ("FONTNAME", (1, 0), (1, 0), FONT_BOLD),
            ("FONTNAME", (2, 0), (2, 0), FONT_BOLD),
            ("FONTNAME", (3, 0), (3, 0), FONT_REGULAR),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("TEXTCOLOR", (0, 0), (1, 0), colors.HexColor("#1E3A8A")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3B82F6")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ])
    )
    story.append(net_table)
    story.append(Spacer(1, 5))

    # YTD & Employer Contributions Split Grid
    ytd_and_ctc_data = [
        ["Year-To-Date (YTD) Summary (FY 2025–26)", "", "Employer Statutory Contributions (Monthly)", ""],
        ["YTD Gross Earnings:", "INR 7,74,000.00", "Employer EPF Contribution (12%):", "INR 22,200.00"],
        ["YTD Employee PF:", "INR 44,400.00", "Employer EPS Contribution:", "INR 1,250.00"],
        ["YTD Professional Tax:", "INR 400.00", "Employer NPS (Sec 80CCD(2)):", "INR 18,500.00"],
        ["YTD Income Tax (TDS):", "INR 1,37,000.00", "Monthly Cost to Company (CTC):", "INR 4,38,198.00"],
        ["YTD Net Disbursed:", "INR 5,31,460.00", "Payment Mode / Ref:", "NEFT: HDFC-20250531-984210382"],
    ]
    ytd_table = Table(ytd_and_ctc_data, colWidths=[165, 113, 175, 103])
    ytd_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#F1F5F9")),
            ("BACKGROUND", (2, 0), (3, 0), colors.HexColor("#F1F5F9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("FONTNAME", (0, 1), (0, -1), FONT_REGULAR),
            ("FONTNAME", (1, 1), (1, -1), FONT_BOLD),
            ("FONTNAME", (2, 1), (2, -1), FONT_REGULAR),
            ("FONTNAME", (3, 1), (3, -1), FONT_BOLD),
            ("FONTSIZE", (0, 1), (-1, -1), 6.5),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )
    story.append(ytd_table)
    story.append(Spacer(1, 6))

    story.append(
        Paragraph(
            "<b>DIGITAL AUTHENTICATION:</b> Document electronically verified via SHA-256 Digest "
            "<code>7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069</code>",
            disclaimer_style,
        )
    )
    story.append(
        Paragraph(
            "<i>Note: System-generated confidential payroll advice issued by Apex Global Technologies Ltd. Page 1 of 2.</i>",
            disclaimer_style,
        )
    )

    # ==========================================================================
    # PAGE 2: ANNEXURE - STATUTORY TAX DECLARATIONS & REGIME AUDIT WORKSHEET
    # ==========================================================================
    story.append(PageBreak())

    story.append(
        Paragraph(
            "APEX GLOBAL TECHNOLOGIES (INDIA) PRIVATE LIMITED",
            corp_title_style,
        )
    )
    story.append(
        Paragraph(
            "<b>ANNEXURE: STATUTORY TAX DEDUCTION DECLARATIONS & COMPARATIVE REGIME AUDIT</b>",
            annex_title_style,
        )
    )
    story.append(
        Paragraph(
            "Financial Year: 2025–2026 &nbsp;|&nbsp; Assessment Year: 2026–2027 &nbsp;|&nbsp; "
            "Form 12BB Statutory Compliance (CBDT Notification No. 11/2024)",
            annex_sub_style,
        )
    )
    story.append(Spacer(1, 6))

    # Employee Tax Summary Card
    tax_emp_info = [
        ["Employee Name:", "Vikramaditya Singhania", "Employee ID:", "AGT-DIR-9082", "PAN:", "ABCPS1234K"],
        ["Opted Tax Regime:", "Section 115BAC (New Regime)", "Residential Status:", "Resident Individual", "Metro Rent:", "Yes (Bangalore)"],
    ]
    tax_emp_table = Table(tax_emp_info, colWidths=[95, 125, 85, 110, 60, 81])
    tax_emp_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR),
            ("FONTSIZE", (0, 0), (-1, -1), 6.5),
            ("FONTNAME", (0, 0), (0, -1), FONT_BOLD),
            ("FONTNAME", (2, 0), (2, -1), FONT_BOLD),
            ("FONTNAME", (4, 0), (4, -1), FONT_BOLD),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )
    story.append(tax_emp_table)
    story.append(Spacer(1, 8))

    # User-Requested Chapter VI-A & Section 10 Deductions Comparison Table
    tax_table_rows = [
        [
            Paragraph("<b>ITEMIZED STATUTORY DEDUCTION / EXEMPTION</b>", th_style),
            Paragraph("<b>OLD REGIME (CH. VI-A)</b>", th_style),
            Paragraph("<b>NEW REGIME (SEC 115BAC)</b>", th_style),
            Paragraph("<b>STATUTORY CITATION / CAP</b>", th_style),
        ],
        [
            Paragraph("01. Standard Deduction (Salaried Employees)", td_bold),
            Paragraph(f"- {fmt_inr(50000.0)}", td_right_bold),
            Paragraph(f"- {fmt_inr(75000.0)}", td_right_bold),
            Paragraph("Section 16(ia) (Finance Act 2025)", td_reg),
        ],
        [
            Paragraph("02. Section 80CCD(2) (Employer NPS Contribution)", td_bold),
            Paragraph(f"- {fmt_inr(222000.0)}", td_right_bold),
            Paragraph(f"- {fmt_inr(222000.0)}", td_right_bold),
            Paragraph("Sec 80CCD(2) (Eligible Both Regimes)", td_reg),
        ],
        # 03. Section 80C (EPF, PPF, ELSS, Insurance)
        [
            Paragraph("03. Section 80C (EPF, PPF, ELSS, Insurance)", td_bold),
            Paragraph(f"- {fmt_inr(0.0)}", td_muted),
            Paragraph("N/A (Disallowed)", td_muted),
            Paragraph("Sec 80C (Cap ₹1.5L)", td_reg),
        ],
        # 04. Section 80D (Health Insurance)
        [
            Paragraph("04. Section 80D (Health Insurance)", td_bold),
            Paragraph(f"- {fmt_inr(0.0)}", td_muted),
            Paragraph("N/A (Disallowed)", td_muted),
            Paragraph("Sec 80D", td_reg),
        ],
        # 05. Section 80CCD(1B) (National Pension Scheme)
        [
            Paragraph("05. Section 80CCD(1B) (National Pension Scheme)", td_bold),
            Paragraph(f"- {fmt_inr(0.0)}", td_muted),
            Paragraph("N/A (Disallowed)", td_muted),
            Paragraph("Sec 80CCD(1B)", td_reg),
        ],
        # 06. Section 10(13A) (HRA Exemption)
        [
            Paragraph("06. Section 10(13A) (HRA Exemption)", td_bold),
            Paragraph(f"- {fmt_inr(0.0)}", td_muted),
            Paragraph("N/A (Disallowed)", td_muted),
            Paragraph("Rule 2A / Sec 10(13A)", td_reg),
        ],
        [
            Paragraph("07. Total Deductions & Exemptions Claimed", td_bold),
            Paragraph(f"- {fmt_inr(272000.0)}", td_right_bold),
            Paragraph(f"- {fmt_inr(297000.0)}", td_right_bold),
            Paragraph("Statutory Total Chapter VI-A", td_reg),
        ],
        [
            Paragraph("08. Annual Gross Salary (Projected 12 Months)", td_bold),
            Paragraph(fmt_inr(4644000.0), td_right_bold),
            Paragraph(fmt_inr(4644000.0), td_right_bold),
            Paragraph("Gross Salary Base u/s 17(1)", td_reg),
        ],
        [
            Paragraph("09. Net Taxable Income", td_bold),
            Paragraph(fmt_inr(4372000.0), td_right_bold),
            Paragraph(fmt_inr(4347000.0), td_right_bold),
            Paragraph("Base for Slab Computation", td_reg),
        ],
        [
            Paragraph("10. Health & Education Cess (4%)", td_reg),
            Paragraph(f"+ {fmt_inr(45667.0)}", td_right_reg),
            Paragraph(f"+ {fmt_inr(37800.0)}", td_right_reg),
            Paragraph("Finance Act Mandatory Levy", td_reg),
        ],
        [
            Paragraph("11. TOTAL ANNUAL TAX LIABILITY", td_bold),
            Paragraph(fmt_inr(1187347.0), td_right_bold),
            Paragraph(fmt_inr(982800.0), td_right_bold),
            Paragraph("<b>NEW REGIME SAVES ₹2,04,547!</b>", td_bold),
        ],
        [
            Paragraph("12. Monthly TDS Deduction Required", td_bold),
            Paragraph(fmt_inr(98946.0), td_right_bold),
            Paragraph(fmt_inr(68500.0), td_right_bold),
            Paragraph("Actual Monthly TDS Deducted", td_bold),
        ],
    ]

    tax_table = Table(tax_table_rows, colWidths=[200, 105, 110, 141])
    tax_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, 0), 7.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            # Alternating row background
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFFFF")),
            ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#FEF2F2")),  # 03 Highlighted
            ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#FEF2F2")),  # 04 Highlighted
            ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#FEF2F2")),  # 05 Highlighted
            ("BACKGROUND", (0, 6), (-1, 6), colors.HexColor("#FEF2F2")),  # 06 Highlighted
            ("BACKGROUND", (0, 7), (-1, 7), colors.HexColor("#F1F5F9")),
            ("BACKGROUND", (0, 8), (-1, 8), colors.HexColor("#FFFFFF")),
            ("BACKGROUND", (0, 9), (-1, 9), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (0, 10), (-1, 10), colors.HexColor("#FFFFFF")),
            ("BACKGROUND", (0, 11), (-1, 11), colors.HexColor("#FEF3C7")),  # Total Tax Winner
            ("BACKGROUND", (0, 12), (-1, 12), colors.HexColor("#EFF6FF")),  # Monthly TDS
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#64748B")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ])
    )
    story.append(tax_table)
    story.append(Spacer(1, 8))

    # Detailed Statutory Tax Strategy & Breakeven Insight Box
    advisory_notes = [
        [
            Paragraph(
                "<b>PAYROLL TAX ADVISORY NOTE & STATUTORY DECLARATION AUDIT:</b><br/>"
                "1. Under <b>Section 115BAC(2)</b> of the Income Tax Act, 1961, salaried employees opting for the "
                "New Tax Regime cannot claim deductions under Chapter VI-A (such as Section 80C, 80D, 80CCD(1B)) "
                "or house rent allowance exemption under Section 10(13A). These are statutorily marked <b>N/A (Disallowed)</b>.<br/>"
                "2. <b>Section 80CCD(2)</b> (Employer NPS Contribution) remains fully exempt under both regimes up to 14% of Basic.<br/>"
                "3. <b>Standard Deduction</b> is enhanced to <b>₹75,000</b> under Section 115BAC (vs ₹50,000 under Old Regime).<br/>"
                "4. <b>Breakeven Deduction Threshold:</b> For the Old Regime to match the New Regime at your annual gross salary "
                "of ₹46,44,000.00, you must claim eligible deductions exceeding <b>₹4,75,000.00</b>. With your declared deductions at ₹0.00, "
                "the New Tax Regime provides guaranteed savings of <b>₹2,04,547.00 per annum</b>.<br/>"
                "5. Monthly TDS of <b>₹68,500.00</b> is deducted strictly pursuant to Section 192 based on Section 115BAC rates.",
                ParagraphStyle(
                    "Advisory",
                    parent=styles["Normal"],
                    fontName=FONT_REGULAR,
                    fontSize=6.5,
                    leading=9,
                    textColor=colors.HexColor("#1E293B"),
                ),
            )
        ]
    ]
    advisory_table = Table(advisory_notes, colWidths=[556])
    advisory_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#94A3B8")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(advisory_table)
    story.append(Spacer(1, 8))

    # Formal Chartered Accountant & Payroll Officer Sign-off Block
    sign_block = [
        [
            Paragraph("<b>PREPARED & VERIFIED BY:</b>", td_bold),
            Paragraph("<b>PAYROLL AUDITOR:</b>", td_bold),
            Paragraph("<b>EMPLOYEE ACKNOWLEDGEMENT:</b>", td_bold),
        ],
        [
            Paragraph("Central Payroll Services Division<br/>Apex Global Technologies India Ltd", td_reg),
            Paragraph("Internal Audit & Tax Compliance Cell<br/>Membership No: ACA-584920", td_reg),
            Paragraph("Digitally Verified via PAN ABCPS1234K<br/>Opted Regime: Section 115BAC", td_reg),
        ],
    ]
    sign_table = Table(sign_block, colWidths=[185, 185, 186])
    sign_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(sign_table)
    story.append(Spacer(1, 6))

    story.append(
        Paragraph(
            "<i>Statutory Note: This statement is an official annexure to Form 16 / Form 12BB for Assessment Year 2026–27. "
            "Issued in compliance with Rule 26A of the Indian Income Tax Rules, 1962. Page 2 of 2.</i>",
            disclaimer_style,
        )
    )

    doc.build(story)
    print(f"Generated complex salary slip with tax annexure at: {output_path}")


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    out_pdf = out_dir / "complex_salary_slip_may_2025.pdf"
    generate_complex_salary_slip(out_pdf)
