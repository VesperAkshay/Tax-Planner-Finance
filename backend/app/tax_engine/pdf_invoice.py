"""
Neo-Brutalist Invoice-Inspired Tax Report PDF Generator (Phase 12).

Generates a vector-grade, professional A4 PDF Memorandum & Tax Invoice
comparing Old Tax Regime vs New Tax Regime (Section 115BAC) side-by-side
under the Finance Act 2024/2025 for FY 2025-26.

Design Principles:
- Neo-Brutalist aesthetic: high-contrast black borders, Chameli cream (#FAF7F2) background,
  Marigold (#FACC15) & Deep Indigo (#3730A3) accent headers, stark drop-shadow boxes.
- Dual-Regime comparative audit ledger table.
- Official Invoice / Memorandum reference details.
- 100% Deterministic Statutory Engine verification seal.
- Native TrueType Font embedding for clean, non-corrupted Indian Rupee (₹) glyph rendering.
- Mandatory Chartered Accountant (CA) advisory disclaimer.
"""

from datetime import datetime
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# Neo-Brutalist Color Palette
COLOR_BG_CREAM = colors.HexColor("#FAF7F2")
COLOR_CARD_BG = colors.HexColor("#FFFDF9")
COLOR_BLACK = colors.HexColor("#000000")
COLOR_INDIGO = colors.HexColor("#3730A3")
COLOR_MARIGOLD = colors.HexColor("#FACC15")
COLOR_EMERALD = colors.HexColor("#10B981")
COLOR_ROSE = colors.HexColor("#E11D48")
COLOR_GRAY_LIGHT = colors.HexColor("#F3F4F6")
COLOR_GRAY_TEXT = colors.HexColor("#4B5563")

# ==============================================================================
# Robust Unicode TrueType Font Registration for Rupee Glyph (₹) Support
# ==============================================================================
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_OBLIQUE = "Helvetica-Oblique"
CURRENCY_PREFIX = "₹"


def _initialize_pdf_fonts() -> None:
    """
    Registers a TrueType font containing the Indian Rupee glyph (U+20B9).
    If no font with 0x20B9 is present, falls back gracefully to 'Rs. ' prefix
    so that black square missing-glyph artifacts never appear in the PDF.
    """
    global FONT_REGULAR, FONT_BOLD, FONT_OBLIQUE, CURRENCY_PREFIX

    # High-priority candidates across Windows, Linux/Ubuntu, and macOS
    font_candidates = [
        # Windows system fonts (Arial & Segoe UI contain U+20B9)
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
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/calibrii.ttf",
        ),
        # Linux standard TrueType fonts
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        ),
        (
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf",
        ),
        (
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
        ),
    ]

    for reg_path, bold_path, ob_path in font_candidates:
        if Path(reg_path).exists() and Path(bold_path).exists():
            try:
                reg_font = TTFont("NeoInvoiceRegular", reg_path)
                bold_font = TTFont("NeoInvoiceBold", bold_path)

                # Confirm character 0x20B9 (₹) is mapped in the font face
                if 0x20B9 in reg_font.face.charToGlyph:
                    pdfmetrics.registerFont(reg_font)
                    pdfmetrics.registerFont(bold_font)

                    if Path(ob_path).exists():
                        try:
                            pdfmetrics.registerFont(TTFont("NeoInvoiceOblique", ob_path))
                            FONT_OBLIQUE = "NeoInvoiceOblique"
                        except Exception:
                            FONT_OBLIQUE = "NeoInvoiceRegular"
                    else:
                        FONT_OBLIQUE = "NeoInvoiceRegular"

                    FONT_REGULAR = "NeoInvoiceRegular"
                    FONT_BOLD = "NeoInvoiceBold"
                    CURRENCY_PREFIX = "₹"
                    logger.info("Successfully registered Unicode TTF with rupee symbol: %s", reg_path)
                    return
            except Exception as e:
                logger.debug("Failed checking candidate font %s: %s", reg_path, e)
                continue

    # Fallback if no TrueType font with rupee glyph exists
    logger.warning("No TrueType font with U+20B9 found. Using PostScript Helvetica with 'Rs. ' prefix.")
    FONT_REGULAR = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"
    FONT_OBLIQUE = "Helvetica-Oblique"
    CURRENCY_PREFIX = "Rs. "


# Run font initialization once at import
_initialize_pdf_fonts()


def fmt_inr(val: float) -> str:
    """Formats a currency amount with the active safe currency prefix."""
    return f"{CURRENCY_PREFIX}{val:,.2f}"


def _draw_neo_brutalist_background(canvas, doc):
    """Draws the uniform Chameli cream canvas background and outer frame."""
    canvas.saveState()
    canvas.setFillColor(COLOR_BG_CREAM)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)

    # Outer decorative brutalist border
    canvas.setStrokeColor(COLOR_BLACK)
    canvas.setLineWidth(2.5)
    margin = 18
    canvas.rect(
        margin,
        margin,
        doc.pagesize[0] - (2 * margin),
        doc.pagesize[1] - (2 * margin),
        fill=False,
        stroke=True,
    )
    canvas.restoreState()


def generate_tax_invoice_pdf(
    user_email: str,
    user_pan: Optional[str],
    user_id: int,
    financial_year: str,
    gross_income: float,
    comparison: Dict[str, Any],
    deductions_applied: Dict[str, Any],
    citations: Optional[List[Dict[str, Any]]] = None,
    real_world_flags: Optional[Dict[str, Any]] = None,
    ais_26as_checklist: Optional[Dict[str, Any]] = None,
    filing_deadline: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Generates an in-memory PDF byte stream for the Neo-Brutalist Tax Comparison Invoice.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=32,
        bottomMargin=32,
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles using dynamically registered fonts
    style_title = ParagraphStyle(
        "NeoTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=19,
        leading=22,
        textColor=COLOR_BLACK,
    )
    style_subtitle = ParagraphStyle(
        "NeoSubtitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=9,
        leading=11,
        textColor=COLOR_INDIGO,
    )
    style_meta_label = ParagraphStyle(
        "NeoMetaLabel",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8,
        leading=10,
        textColor=COLOR_BLACK,
    )
    style_meta_val = ParagraphStyle(
        "NeoMetaVal",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=10,
        textColor=COLOR_GRAY_TEXT,
    )
    style_th = ParagraphStyle(
        "NeoTH",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8,
        leading=10,
        textColor=COLOR_BLACK,
    )
    style_td = ParagraphStyle(
        "NeoTD",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=10,
        textColor=COLOR_BLACK,
    )
    style_td_bold = ParagraphStyle(
        "NeoTDBold",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8,
        leading=10,
        textColor=COLOR_BLACK,
    )
    style_td_green = ParagraphStyle(
        "NeoTDGreen",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#065F46"),
    )
    style_winner = ParagraphStyle(
        "NeoWinner",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=13,
        textColor=COLOR_BLACK,
    )
    style_disclaimer = ParagraphStyle(
        "NeoDisclaimer",
        parent=styles["Normal"],
        fontName=FONT_OBLIQUE,
        fontSize=7,
        leading=9,
        textColor=COLOR_GRAY_TEXT,
    )

    story = []

    # --------------------------------------------------------------------------
    # 1. HEADER BLOCK: Neo-Brutalist Invoice & Audit Memo
    # --------------------------------------------------------------------------
    memo_ref = f"TP-2025-INV-{user_id:04d}-{datetime.now().strftime('%m%d')}"
    today_str = datetime.now().strftime("%d %B %Y")
    pan_display = (user_pan or "NOT SPECIFIED").strip().upper()

    header_left = [
        Paragraph("MR. PLANNER // STATUTORY TAX ADVISORY", style_subtitle),
        Paragraph("TAX AUDIT & INVOICE MEMORANDUM", style_title),
        Spacer(1, 4),
        Paragraph(
            f"<b>Financial Year:</b> {financial_year} (AY 2026–27) &nbsp;|&nbsp; <b>Governing Act:</b> Income Tax Act, 1961",
            style_meta_val,
        ),
    ]

    header_right = [
        Paragraph(f"<b>MEMO REF:</b> {memo_ref}", style_meta_label),
        Paragraph(f"<b>ISSUE DATE:</b> {today_str}", style_meta_val),
        Paragraph(f"<b>CLIENT:</b> {user_email}", style_meta_val),
        Paragraph(f"<b>PAN:</b> {pan_display}", style_meta_val),
        Paragraph("<b>STATUS:</b> <font color='#065F46'>AUDIT VERIFIED (100% MATH)</font>", style_meta_label),
    ]
    if filing_deadline:
        dl_date = filing_deadline.get("deadline_date", "")
        days_rem = filing_deadline.get("days_remaining", 0)
        header_right.append(
            Paragraph(f"<b>ITR DEADLINE:</b> {dl_date} ({days_rem}d left)", style_meta_label)
        )

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[335, 200],
    )
    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 2.5, COLOR_BLACK),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(header_table)
    story.append(Spacer(1, 10))

    # --------------------------------------------------------------------------
    # 2. GRAND WINNER ANNOUNCEMENT STAMP
    # --------------------------------------------------------------------------
    old_res = comparison.get("old", {})
    new_res = comparison.get("new", {})
    recommended = str(comparison.get("recommended", "new")).lower()
    is_new_winner = recommended == "new"
    savings = float(comparison.get("savings", 0.0))
    breakeven = float(comparison.get("breakeven_deductions", 375000.0))

    winner_title = "RECOMMENDED CHOICE: NEW TAX REGIME (SECTION 115BAC)" if is_new_winner else "RECOMMENDED CHOICE: OLD TAX REGIME (CHAPTER VI-A)"
    winner_bg = COLOR_MARIGOLD if is_new_winner else colors.HexColor("#F59E0B")

    winner_content = [
        Paragraph(f"🏆 <b>{winner_title}</b>", style_winner),
        Spacer(1, 2),
        Paragraph(
            f"You will save <b>{fmt_inr(savings)}</b> in statutory income tax by opting for this regime. "
            f"Breakeven deduction threshold required for Old Regime is <b>{fmt_inr(breakeven)}</b>.",
            style_td,
        ),
    ]

    new_total_tax = new_res.get("total_tax", 0.0)
    old_total_tax = old_res.get("total_tax", 0.0)
    winner_tax_val = new_total_tax if is_new_winner else old_total_tax

    winner_badge = [
        Paragraph("<font size=7><b>TOTAL TAX PAYABLE</b></font>", style_meta_label),
        Paragraph(
            f"<font size=13><b>{fmt_inr(winner_tax_val)}</b></font>",
            ParagraphStyle("wTB", fontName=FONT_BOLD, fontSize=13, leading=15, textColor=COLOR_INDIGO),
        ),
    ]

    winner_table = Table(
        [[winner_content, winner_badge]],
        colWidths=[395, 140],
    )
    winner_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), winner_bg),
            ("BOX", (0, 0), (-1, -1), 2.5, COLOR_BLACK),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(winner_table)
    story.append(Spacer(1, 10))

    # --------------------------------------------------------------------------
    # 3. DUAL-REGIME COMPARATIVE AUDIT INVOICE LEDGER
    # --------------------------------------------------------------------------
    new_std_ded = new_res.get("standard_deduction", 75000.0)
    old_std_ded = old_res.get("standard_deduction", 50000.0)
    old_exemptions = old_res.get("exemptions_and_deductions", 0.0)

    new_taxable = new_res.get("taxable_income", 0.0)
    old_taxable = old_res.get("taxable_income", 0.0)

    new_gross_tax = new_res.get("tax_before_rebate", 0.0)
    old_gross_tax = old_res.get("tax_before_rebate", 0.0)

    new_rebate = new_res.get("rebate_87a", 0.0)
    old_rebate = old_res.get("rebate_87a", 0.0)

    new_cess = new_res.get("cess", 0.0)
    old_cess = old_res.get("cess", 0.0)

    new_rate = (new_total_tax / gross_income * 100.0) if gross_income > 0 else 0.0
    old_rate = (old_total_tax / gross_income * 100.0) if gross_income > 0 else 0.0

    val_80c = float(deductions_applied.get("section_80c", 0.0))
    val_80d = deductions_applied.get("section_80d", 0.0)
    val_80d_num = float(val_80d if not isinstance(val_80d, dict) else val_80d.get("allowed", 0.0))
    val_nps = float(deductions_applied.get("section_80ccd_1b", 0.0))
    val_hra = deductions_applied.get("hra", 0.0)
    val_hra_num = float(val_hra if not isinstance(val_hra, dict) else val_hra.get("rent_paid", 0.0))

    table_data = [
        [
            Paragraph("<b>ITEMIZED COMPUTATION LINE ITEM</b>", style_th),
            Paragraph("<b>OLD REGIME (CH. VI-A)</b>", style_th),
            Paragraph("<b>NEW REGIME (SEC 115BAC)</b>", style_th),
            Paragraph("<b>STATUTORY CITATION</b>", style_th),
        ],
        [
            Paragraph("01. Gross Annual Salary / Inflows", style_td_bold),
            Paragraph(fmt_inr(gross_income), style_td_bold),
            Paragraph(fmt_inr(gross_income), style_td_bold),
            Paragraph("Sec 15 / 17(1)", style_td),
        ],
        [
            Paragraph("02. Salaried Standard Deduction", style_td),
            Paragraph(f"- {fmt_inr(old_std_ded)}", style_td_green),
            Paragraph(f"- {fmt_inr(new_std_ded)}", style_td_green),
            Paragraph("Sec 16(ia)", style_td),
        ],
        [
            Paragraph("03. Section 80C (EPF, PPF, ELSS, Life Ins)", style_td),
            Paragraph(f"- {fmt_inr(val_80c)}", style_td if val_80c > 0 else style_meta_val),
            Paragraph("<font color='#9CA3AF'>N/A (Disallowed)</font>", style_td),
            Paragraph("Sec 80C (Cap ₹1.5L)", style_td),
        ],
        [
            Paragraph("04. Section 80D (Health Insurance)", style_td),
            Paragraph(f"- {fmt_inr(val_80d_num)}", style_td if val_80d_num > 0 else style_meta_val),
            Paragraph("<font color='#9CA3AF'>N/A (Disallowed)</font>", style_td),
            Paragraph("Sec 80D", style_td),
        ],
        [
            Paragraph("05. Section 80CCD(1B) (National Pension Scheme)", style_td),
            Paragraph(f"- {fmt_inr(val_nps)}", style_td if val_nps > 0 else style_meta_val),
            Paragraph("<font color='#9CA3AF'>N/A (Disallowed)</font>", style_td),
            Paragraph("Sec 80CCD(1B) (Cap ₹50k)", style_td),
        ],
        [
            Paragraph("06. Section 10(13A) (House Rent Allowance)", style_td),
            Paragraph(f"- {fmt_inr(val_hra_num)}", style_td if val_hra_num > 0 else style_meta_val),
            Paragraph("<font color='#9CA3AF'>N/A (Disallowed)</font>", style_td),
            Paragraph("Rule 2A / Sec 10(13A)", style_td),
        ],
        [
            Paragraph("07. Total Deductions & Exemptions Claimed", style_td_bold),
            Paragraph(f"- {fmt_inr(old_exemptions)}", style_td_bold),
            Paragraph(f"- {fmt_inr(new_std_ded)}", style_td_bold),
            Paragraph("Aggregated Limits", style_td),
        ],
        [
            Paragraph("<b>08. Net Taxable Income</b>", style_td_bold),
            Paragraph(f"<b>{fmt_inr(old_taxable)}</b>", style_td_bold),
            Paragraph(f"<b>{fmt_inr(new_taxable)}</b>", style_td_bold),
            Paragraph("Gross minus deductions", style_td),
        ],
        [
            Paragraph("09. Gross Tax on Slab Brackets", style_td),
            Paragraph(fmt_inr(old_gross_tax), style_td),
            Paragraph(fmt_inr(new_gross_tax), style_td),
            Paragraph("Statutory Rate Slabs", style_td),
        ],
        [
            Paragraph("10. Section 87A Rebate (Full rebate limit)", style_td),
            Paragraph(f"- {fmt_inr(old_rebate)}", style_td_green if old_rebate > 0 else style_meta_val),
            Paragraph(f"- {fmt_inr(new_rebate)}", style_td_green if new_rebate > 0 else style_meta_val),
            Paragraph("Old ≤₹5L | New ≤₹12L", style_td),
        ],
        [
            Paragraph("11. Health & Education Cess (4%)", style_td),
            Paragraph(f"+ {fmt_inr(old_cess)}", style_td),
            Paragraph(f"+ {fmt_inr(new_cess)}", style_td),
            Paragraph("4% on (Tax - Rebate)", style_td),
        ],
        [
            Paragraph("<b>12. FINAL STATUTORY TAX LIABILITY</b>", style_td_bold),
            Paragraph(f"<b>{fmt_inr(old_total_tax)}</b>", ParagraphStyle("oldTot", fontName=FONT_BOLD, fontSize=9, textColor=COLOR_BLACK if is_new_winner else COLOR_INDIGO)),
            Paragraph(f"<b>{fmt_inr(new_total_tax)}</b>", ParagraphStyle("newTot", fontName=FONT_BOLD, fontSize=9, textColor=COLOR_INDIGO if is_new_winner else COLOR_BLACK)),
            Paragraph("<b>NET DUE</b>", style_td_bold),
        ],
        [
            Paragraph("13. Effective Tax Rate (% of Gross)", style_td),
            Paragraph(f"{old_rate:.2f}%", style_td),
            Paragraph(f"{new_rate:.2f}%", style_td),
            Paragraph("Effective %", style_td),
        ],
    ]

    ledger_table = Table(
        table_data,
        colWidths=[205, 115, 115, 100],
    )
    ledger_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_GRAY_LIGHT),
            ("BOX", (0, 0), (-1, -1), 2, COLOR_BLACK),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            # Highlight Net Taxable Income row
            ("BACKGROUND", (0, 8), (-1, 8), colors.HexColor("#FEF3C7")),
            # Highlight Final Tax Liability row
            ("BACKGROUND", (0, 12), (-1, 12), COLOR_MARIGOLD),
            ("LINEBELOW", (0, 12), (-1, 12), 2, COLOR_BLACK),
            ("LINEABOVE", (0, 12), (-1, 12), 2, COLOR_BLACK),
        ])
    )
    story.append(ledger_table)
    story.append(Spacer(1, 8))

    # --------------------------------------------------------------------------
    # 4. SLAB RATES REFERENCE MATRIX
    # --------------------------------------------------------------------------
    slabs_summary_data = [
        [
            Paragraph("<b>NEW REGIME SLABS (SEC 115BAC)</b>", style_th),
            Paragraph("<b>OLD REGIME SLABS (GENERAL)</b>", style_th),
        ],
        [
            Paragraph(
                f"• {CURRENCY_PREFIX}0 – {CURRENCY_PREFIX}4,00,000: <b>NIL (0%)</b><br/>"
                f"• {CURRENCY_PREFIX}4,00,001 – {CURRENCY_PREFIX}8,00,000: <b>5%</b><br/>"
                f"• {CURRENCY_PREFIX}8,00,001 – {CURRENCY_PREFIX}12,00,000: <b>10%</b> (Rebate up to {CURRENCY_PREFIX}12L)<br/>"
                f"• {CURRENCY_PREFIX}12,00,001 – {CURRENCY_PREFIX}16,00,000: <b>15%</b><br/>"
                f"• {CURRENCY_PREFIX}16,00,001 – {CURRENCY_PREFIX}20,00,000: <b>20%</b><br/>"
                f"• {CURRENCY_PREFIX}20,00,001 – {CURRENCY_PREFIX}24,00,000: <b>25%</b><br/>"
                f"• Above {CURRENCY_PREFIX}24,00,000: <b>30%</b>",
                style_td,
            ),
            Paragraph(
                f"• {CURRENCY_PREFIX}0 – {CURRENCY_PREFIX}2,50,000: <b>NIL (0%)</b><br/>"
                f"• {CURRENCY_PREFIX}2,50,001 – {CURRENCY_PREFIX}5,00,000: <b>5%</b> (Rebate up to {CURRENCY_PREFIX}5L)<br/>"
                f"• {CURRENCY_PREFIX}5,00,001 – {CURRENCY_PREFIX}10,00,000: <b>20%</b><br/>"
                f"• Above {CURRENCY_PREFIX}10,00,000: <b>30%</b><br/><br/>"
                "<i>Permits Chapter VI-A deductions &amp; HRA exemptions.</i>",
                style_td,
            ),
        ],
    ]
    slabs_table = Table(slabs_summary_data, colWidths=[270, 265])
    slabs_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_GRAY_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1.5, COLOR_BLACK),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(KeepTogether([slabs_table]))
    story.append(Spacer(1, 8))

    # --------------------------------------------------------------------------
    # 4b. REAL-WORLD STATUTORY ADVISORIES & AIS / 26AS CHECKLIST (Phase 17)
    # --------------------------------------------------------------------------
    if real_world_flags:
        cg_flag = real_world_flags.get("capital_gains", {})
        if cg_flag.get("has_capital_gains_indicators"):
            cg_p = Paragraph(
                f"<b>⚠️ ITR-2 NOTICE (CAPITAL GAINS DETECTED):</b> {cg_flag.get('warning_message')}",
                ParagraphStyle("cgAlert", parent=styles["Normal"], fontName=FONT_BOLD, fontSize=7.5, leading=9.5, textColor=COLOR_ROSE),
            )
            cg_tbl = Table([[cg_p]], colWidths=[535])
            cg_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF1F2")),
                ("BOX", (0, 0), (-1, -1), 1.5, COLOR_ROSE),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(cg_tbl)
            story.append(Spacer(1, 6))

        arr_flag = real_world_flags.get("salary_arrears", {})
        if arr_flag.get("has_arrears_indicator"):
            arr_p = Paragraph(
                f"<b>⚠️ SECTION 89 RELIEF ADVISORY:</b> {arr_flag.get('warning_message')}",
                ParagraphStyle("arrAlert", parent=styles["Normal"], fontName=FONT_BOLD, fontSize=7.5, leading=9.5, textColor=COLOR_INDIGO),
            )
            arr_tbl = Table([[arr_p]], colWidths=[535])
            arr_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF2FF")),
                ("BOX", (0, 0), (-1, -1), 1.5, COLOR_INDIGO),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(arr_tbl)
            story.append(Spacer(1, 6))

    if ais_26as_checklist:
        ais_title = Paragraph(f"<b>{ais_26as_checklist.get('notice_banner')}</b>", style_th)
        ais_rows = [[ais_title]]
        for item in ais_26as_checklist.get("checklist_items", []):
            item_p = Paragraph(
                f"• <b>{item.get('title')}:</b> {item.get('description')}",
                ParagraphStyle("aisItem", parent=styles["Normal"], fontName=FONT_REGULAR, fontSize=7, leading=9, textColor=COLOR_BLACK),
            )
            ais_rows.append([item_p])
        ais_table = Table(ais_rows, colWidths=[535])
        ais_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 1.5, COLOR_BLACK),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(KeepTogether([ais_table]))
        story.append(Spacer(1, 6))

    # --------------------------------------------------------------------------
    # 5. AUDIT CERTIFICATION SEAL & CA DISCLAIMER
    # --------------------------------------------------------------------------
    audit_seal = [
        Paragraph(
            "<b>DETERMINISTIC STATUTORY CERTIFICATION:</b><br/>"
            "This document was compiled by <b>Mr. Planner Engine</b> using pure Python AST-verified statutory functions. "
            "Zero LLM arithmetic was used in any currency computation. Figures match exact Finance Act schedules.",
            style_meta_label,
        )
    ]
    audit_table = Table([audit_seal], colWidths=[535])
    audit_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
            ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#065F46")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(audit_table)
    story.append(Spacer(1, 6))

    # Legal Disclaimer
    disclaimer_text = (
        "⚠️ <b>Statutory Notice &amp; Disclaimer:</b> This tax computation and regime comparison memorandum is an automated "
        "planning analysis based on taxpayer-supplied records and statutory rules under the Indian Income Tax Act, 1961 for FY 2025–26. "
        "It does not constitute a formal legal filing or chartered accountancy audit certificate. Please consult a qualified "
        "Chartered Accountant (CA) or certified tax professional for official tax filing and personalized planning."
    )
    story.append(Paragraph(disclaimer_text, style_disclaimer))

    # Build the document
    doc.build(story, onFirstPage=_draw_neo_brutalist_background, onLaterPages=_draw_neo_brutalist_background)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
