from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generate_sample_salary_slip(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
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
        fontSize=11,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#4A5568"),
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
    )

    story = []

    # Header
    story.append(Paragraph("Acme Tech Solutions India Pvt Ltd", title_style))
    story.append(Paragraph("Outer Ring Road, Bengaluru, Karnataka - 560103", subtitle_style))
    story.append(Paragraph("<b>Payslip for the month of April 2024</b>", subtitle_style))
    story.append(Spacer(1, 15))

    # Employee Details Table
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
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2D3748")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4A5568")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#4A5568")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 15))

    # Earnings and Deductions Table
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
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1A202C")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F7FAFC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 15))

    # Net Pay Summary Table
    summary_data = [
        ["Net Pay:", "INR 1,00,000.00 (Rupees One Lakh Only)"],
    ]
    summary_table = Table(summary_data, colWidths=[100, 420])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2B6CB0")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3182CE")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 25))

    story.append(Paragraph("<i>Note: This is a system-generated payslip and does not require a physical signature.</i>", subtitle_style))

    doc.build(story)
    print(f"Generated sample salary slip at: {output_path}")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "sample_salary_slip.pdf"
    generate_sample_salary_slip(out)
