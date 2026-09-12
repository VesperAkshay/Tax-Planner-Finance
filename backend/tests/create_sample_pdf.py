from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_sample_bank_statement_pdf(output_path: Path) -> Path:
    """Generates a text-based bank statement PDF fixture for parser testing."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=14, spaceAfter=8)
    story.append(Paragraph("HDFC BANK LIMITED - ACCOUNT STATEMENT", title_style))
    story.append(Paragraph("Account No: 50100234567890 | Currency: INR | Branch: Bangalore Indiranagar", styles["Normal"]))
    story.append(Paragraph("Statement Period: 01/04/2025 to 30/04/2025 | Opening Balance: 30,000.00", styles["Normal"]))
    story.append(Spacer(1, 14))

    # Transactions Table
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
    return output_path


if __name__ == "__main__":
    p = generate_sample_bank_statement_pdf(Path("data/test_fixtures/sample_hdfc_statement.pdf"))
    print(f"Sample PDF created at: {p}")
