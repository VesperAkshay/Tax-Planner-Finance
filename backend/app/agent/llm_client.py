"""
OpenRouter & Multi-Provider LLM Integration for Tax Planning Agent.

Architecture & Compliance Rules:
1. STRICT ZERO LLM ARITHMETIC:
   The LLM NEVER computes tax slabs, liability, or arithmetic.
   All numbers are derived deterministically from Phase 5 pure functions.
2. The LLM is used for:
   - Natural language deduction intent extraction.
   - Conversational explanations grounded in statutory citations (Phase 6 RAG).
3. Seamless fallback:
   If no API key is provided or OpenRouter fails, deterministic rule-based
   formatting and regex extraction take over seamlessly.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


def parse_inr_amount(text: str) -> Optional[float]:
    """
    Parses currency representations like '1.5L', '1.5 lakh', '50k', '₹25,000', '25000'.
    """
    cleaned = text.replace(",", "").replace("₹", "").strip().lower()

    # Match '1.5l' or '1.5 lakh' or '1.5 lakhs'
    m_lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:l|lac|lakh|lakhs)", cleaned)
    if m_lakh:
        return float(m_lakh.group(1)) * 100000.0

    # Match '50k'
    m_k = re.search(r"(\d+(?:\.\d+)?)\s*k", cleaned)
    if m_k:
        return float(m_k.group(1)) * 1000.0

    # Match raw number
    m_num = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if m_num:
        return float(m_num.group(1))

    return None


def extract_deductions_from_text(message: str) -> Dict[str, Any]:
    """
    Deterministic rule-based extractor for tax deductions mentioned in conversational messages.
    Supports Section 80C, 80D, 80CCD(1B) NPS, 80G, Section 24b, and Section 10(13A) HRA.
    """
    if not message:
        return {}

    msg = message.lower()
    deductions: Dict[str, Any] = {}

    # 1. HRA Rent extraction
    if any(k in msg for k in ["rent", "hra", "tenant", "landlord"]):
        # Check monthly rent vs annual
        is_metro = any(city in msg for city in ["mumbai", "delhi", "kolkata", "chennai", "metro"])
        rent_match = re.search(
            r"(?:rent(?:\s+of)?|pay(?:ing)?)\s*(?:₹|inr|rs\.?)?\s*(\d[\d,]*(?:\.\d+)?(?:\s*(?:lakh|lac|k))?)",
            msg,
        )
        if rent_match:
            amount = parse_inr_amount(rent_match.group(1))
            if amount:
                # If amount < 100,000 and user said "monthly rent" or reasonable monthly range, annualize
                if "month" in msg or "pm" in msg or amount <= 100000:
                    annual_rent = amount * 12.0
                else:
                    annual_rent = amount
                deductions["hra"] = {
                    "rent_paid_annual": annual_rent,
                    "is_metro": is_metro,
                }

    # 2. Section 80C extraction (PPF, EPF, ELSS, Life Insurance, Tuition)
    if any(k in msg for k in ["80c", "ppf", "elss", "epf", "provident", "lic", "life insurance", "tuition"]):
        m_80c = re.search(
            r"(?:80c|ppf|elss|epf|lic|invest(?:ed|ment)?)\s*(?:of|is|in)?\s*(?:₹|inr|rs\.?)?\s*(\d[\d,]*(?:\.\d+)?(?:\s*(?:lakh|lac|k))?)",
            msg,
        )
        if m_80c:
            amount = parse_inr_amount(m_80c.group(1))
            if amount:
                deductions["section_80c"] = min(amount, 150000.0)
        elif "1.5" in msg or "150000" in msg or "1.5l" in msg:
            deductions["section_80c"] = 150000.0

    # 3. Section 80D extraction (Health Insurance / Mediclaim)
    if any(k in msg for k in ["80d", "health insurance", "mediclaim", "medical insurance"]):
        m_80d = re.search(
            r"(?:80d|insurance|mediclaim|premium)\s*(?:of|is)?\s*(?:₹|inr|rs\.?)?\s*(\d[\d,]*(?:\.\d+)?(?:\s*(?:lakh|lac|k))?)",
            msg,
        )
        if m_80d:
            amount = parse_inr_amount(m_80d.group(1))
            if amount:
                deductions["section_80d"] = amount

    # 4. Section 80CCD(1B) NPS extraction
    if any(k in msg for k in ["nps", "80ccd", "national pension"]):
        m_nps = re.search(
            r"(?:nps|80ccd(?:\(1b\))?)\s*(?:of|is)?\s*(?:₹|inr|rs\.?)?\s*(\d[\d,]*(?:\.\d+)?(?:\s*(?:lakh|lac|k))?)",
            msg,
        )
        if m_nps:
            amount = parse_inr_amount(m_nps.group(1))
            if amount:
                deductions["section_80ccd_1b"] = min(amount, 50000.0)

    # 5. Section 80G Donations extraction
    if any(k in msg for k in ["80g", "donation", "charity", "pm cares"]):
        m_80g = re.search(
            r"(?:80g|donat(?:ion|ed)|charity)\s*(?:of|is)?\s*(?:₹|inr|rs\.?)?\s*(\d[\d,]*(?:\.\d+)?(?:\s*(?:lakh|lac|k))?)",
            msg,
        )
        if m_80g:
            amount = parse_inr_amount(m_80g.group(1))
            if amount:
                deductions["section_80g"] = amount

    # 6. Section 24(b) Home Loan Interest extraction
    if any(k in msg for k in ["24b", "home loan", "housing loan", "loan interest"]):
        m_24b = re.search(
            r"(?:24b|home loan|interest)\s*(?:of|is)?\s*(?:₹|inr|rs\.?)?\s*(\d[\d,]*(?:\.\d+)?(?:\s*(?:lakh|lac|k))?)",
            msg,
        )
        if m_24b:
            amount = parse_inr_amount(m_24b.group(1))
            if amount:
                deductions["section_24b"] = min(amount, 200000.0)

    return deductions


def get_llm_client_and_model():
    """
    Returns (client, model_name, provider) based on environment configuration.
    Priority: OpenRouter -> OpenAI -> Anthropic -> None.
    """
    settings = get_settings()

    # 1. OpenRouter (Supports free models out-of-the-box)
    if settings.OPENROUTER_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url=settings.OPENROUTER_BASE_URL,
                api_key=settings.OPENROUTER_API_KEY,
                default_headers={
                    "HTTP-Referer": settings.APP_URL,
                    "X-Title": settings.APP_NAME,
                },
            )
            model = settings.OPENROUTER_MODEL or "meta-llama/llama-3.3-70b-instruct:free"
            return client, model, "openrouter"
        except Exception as e:
            logger.warning("Failed to initialize OpenRouter client: %s", e)

    # 2. Standard OpenAI
    if settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            return client, "gpt-4o-mini", "openai"
        except Exception as e:
            logger.warning("Failed to initialize OpenAI client: %s", e)

    # 3. Anthropic
    if settings.ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            return client, "claude-3-haiku-20240307", "anthropic"
        except Exception as e:
            logger.warning("Failed to initialize Anthropic client: %s", e)

    return None, None, None


def answer_direct_financial_query(
    query: str,
    financial_profile: Optional[Dict[str, Any]],
) -> Optional[str]:
    """
    Direct zero-latency answer for factual salary & cashflow queries.
    """
    if not financial_profile:
        return None

    q = query.lower().strip()
    m_gross = financial_profile.get("monthly_gross", 0.0)
    m_net = financial_profile.get("monthly_net", 0.0)
    m_basic = financial_profile.get("monthly_basic", 0.0)
    m_hra = financial_profile.get("monthly_hra", 0.0)
    m_pf = financial_profile.get("monthly_pf", 0.0)
    m_pt = financial_profile.get("monthly_pt", 200.0)
    annual_gross = financial_profile.get("annual_gross", 0.0)
    t_credits = financial_profile.get("total_credits", 0.0)
    t_debits = financial_profile.get("total_debits", 0.0)
    n_cashflow = financial_profile.get("net_cashflow", 0.0)
    tx_count = financial_profile.get("txns_count", 0)

    disclaimer = (
        "\n\n⚠️ **Disclaimer**: *This analysis is an automated suggestion based on your uploaded records "
        "and Income Tax Act rules (FY 2025–26). Please consult a certified Chartered Accountant (CA) "
        "or tax professional for official tax filing and personalized planning.*"
    )

    # 1. Salary / Take-home queries
    salary_keywords = [
        "monthly salary", "monthly gross", "monthly income", "in hand", "in-hand",
        "take home", "take-home", "monthly pay", "net salary", "net pay",
        "what is my salary", "what is my salry", "my salary", "tell me my salary",
        "how much is my salary", "salary details", "salary slip", "gross pay",
        "gross salary", "my earnings", "monthly earnings"
    ]
    if any(k in q for k in salary_keywords):
        return (
            f"Based on your verified records and salary slip:\n\n"
            f"- **Monthly Gross Salary**: ₹{m_gross:,.2f}\n"
            f"- **Net Take-Home Pay (In-Hand)**: ₹{m_net:,.2f}\n"
            f"- **Basic Salary**: ₹{m_basic:,.2f} per month\n"
            f"- **House Rent Allowance (HRA)**: ₹{m_hra:,.2f} per month\n"
            f"- **Provident Fund (PF) Deduction**: ₹{m_pf:,.2f} per month\n"
            f"- **Professional Tax**: ₹{m_pt:,.2f} per month\n\n"
            f"Your annualized gross income is **₹{annual_gross:,.2f}**.{disclaimer}"
        )

    # 2. Basic Salary queries
    if any(k in q for k in ["basic salary", "my basic", "basic pay"]):
        return (
            f"Based on your latest salary slip, your **Basic Salary is ₹{m_basic:,.2f} per month** "
            f"(annualized: ₹{m_basic * 12:,.2f}).{disclaimer}"
        )

    # 3. HRA component queries
    if any(k in q for k in ["my hra", "hra component", "house rent allowance received", "hra allowance"]):
        return (
            f"Based on your latest salary slip, your **HRA is ₹{m_hra:,.2f} per month** "
            f"(annualized: ₹{m_hra * 12:,.2f}). You can claim exemption under Section 10(13A) if you pay rent!{disclaimer}"
        )

    # 4. Provident Fund queries
    if any(k in q for k in ["provident fund", "my pf", "pf deduction", "epf deduction", "employee pf"]):
        return (
            f"Based on your latest salary slip, your **Employee Provident Fund (PF) contribution is ₹{m_pf:,.2f} per month** "
            f"(annualized: ₹{m_pf * 12:,.2f}). This automatically counts towards your Section 80C deduction ceiling (₹1.5 Lakh)!{disclaimer}"
        )

    # 5. Bank Statement & Cash Flow queries
    if any(k in q for k in ["cash flow", "cashflow", "bank statement", "expenses", "spending", "total debits", "total credits", "bank cash"]):
        return (
            f"Based on your verified bank statement records ({tx_count} transactions analyzed):\n\n"
            f"- **Total Inflows (Credits)**: ₹{t_credits:,.2f}\n"
            f"- **Total Outflows (Debits / Expenses)**: ₹{t_debits:,.2f}\n"
            f"- **Net Cash Flow / Savings**: ₹{n_cashflow:,.2f}\n\n"
            f"Would you like recommendations on how to allocate these savings into tax-saving instruments (like ELSS, PPF, or NPS)?{disclaimer}"
        )

    return None


def generate_llm_explanation(
    user_query: str,
    history: List[Dict[str, str]],
    comparison: Dict[str, Any],
    citations: List[Dict[str, Any]],
    declared_deductions: Dict[str, Any],
    gross_income: float,
    financial_profile: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Calls the configured LLM (OpenRouter / OpenAI / Anthropic) to provide
    a natural language response strictly adhering to Zero LLM Arithmetic.
    Includes mandatory CA disclaimer on all tax queries.
    """
    # 1. Check for direct factual queries first (instant, robust)
    direct_ans = answer_direct_financial_query(user_query, financial_profile)
    if direct_ans:
        return direct_ans

    client, model, provider = get_llm_client_and_model()
    if not client or not model:
        return None

    # Format deterministic context
    rec = comparison.get("recommended", "new").upper()
    savings = comparison.get("savings", 0.0)
    old_res = comparison.get("old_regime", {})
    new_res = comparison.get("new_regime", {})
    breakeven = comparison.get("breakeven_deductions", 0.0)

    profile_details = ""
    if financial_profile:
        m_gross = financial_profile.get("monthly_gross", 0.0)
        m_net = financial_profile.get("monthly_net", 0.0)
        m_basic = financial_profile.get("monthly_basic", 0.0)
        m_hra = financial_profile.get("monthly_hra", 0.0)
        m_pf = financial_profile.get("monthly_pf", 0.0)
        m_pt = financial_profile.get("monthly_pt", 200.0)
        t_credits = financial_profile.get("total_credits", 0.0)
        t_debits = financial_profile.get("total_debits", 0.0)
        n_cashflow = financial_profile.get("net_cashflow", 0.0)
        tx_count = financial_profile.get("txns_count", 0)

        profile_details = (
            f"Taxpayer Verified Compensation Profile (from salary slip):\n"
            f"- Monthly Gross Salary: ₹{m_gross:,.2f}\n"
            f"- Monthly Net Take-Home Pay (In-Hand): ₹{m_net:,.2f}\n"
            f"- Monthly Basic Pay: ₹{m_basic:,.2f}\n"
            f"- Monthly HRA: ₹{m_hra:,.2f}\n"
            f"- Monthly Employee PF: ₹{m_pf:,.2f}\n"
            f"- Monthly Professional Tax: ₹{m_pt:,.2f}\n\n"
            f"Taxpayer Verified Banking Cashflow (from {tx_count} bank statement transactions):\n"
            f"- Total Inflows/Credits: ₹{t_credits:,.2f}\n"
            f"- Total Outflows/Debits: ₹{t_debits:,.2f}\n"
            f"- Net Cashflow: ₹{n_cashflow:,.2f}\n\n"
        )

    citation_summary = "\n".join(
        f"- {c.get('section', '')}: {c.get('title', '')} (URL: {c.get('source_url', '')})"
        for c in citations
    )

    ca_disclaimer_text = (
        "\n\n⚠️ **Disclaimer**: *This computation and analysis is an automated tax planning suggestion "
        "based on Indian Income Tax Act rules (FY 2025–26). Please consult a qualified Chartered Accountant (CA) "
        "or certified tax professional for official tax filing and personalized planning.*"
    )

    system_prompt = (
        "You are Mr. Planner, an expert Indian Income Tax & Personal Finance AI Strategist for Financial Year 2025-26 (Assessment Year 2026-27).\n"
        "STRICT ARCHITECTURAL DIRECTIVE: ZERO ARITHMETIC HALLUCINATIONS.\n"
        "All tax figures below are computed by our verified deterministic engine. "
        "DO NOT attempt to calculate or recalculate tax amounts, tax slabs, or savings yourself. "
        "Use ONLY the exact figures provided below in your explanation:\n\n"
        f"{profile_details}"
        f"- Gross Annual Income: ₹{gross_income:,.2f}\n"
        f"- Recommended Tax Regime: {rec} Regime\n"
        f"- Tax Savings: ₹{savings:,.2f}\n"
        f"- Old Regime Tax Liability: ₹{old_res.get('total_tax', 0.0):,.2f} (Taxable Income: ₹{old_res.get('taxable_income', 0.0):,.2f})\n"
        f"- New Regime Tax Liability: ₹{new_res.get('total_tax', 0.0):,.2f} (Taxable Income: ₹{new_res.get('taxable_income', 0.0):,.2f})\n"
        f"- Breakeven Deductions Required for Old Regime: ₹{breakeven:,.2f}\n"
        f"- Active User Deductions: {declared_deductions}\n\n"
        f"Statutory Citations Grounding:\n{citation_summary}\n\n"
        "Instructions:\n"
        "1. Address the taxpayer's question concisely in a professional, friendly, and structured manner.\n"
        "2. When asked about monthly salary, basic pay, take-home pay, or income, refer directly to the verified numbers above.\n"
        "3. State which regime saves more money and quote the exact savings amount.\n"
        "4. Reference statutory sections (like Section 80C, 80D, 10(13A) HRA, Section 87A rebate, standard deduction ₹75,000 for New vs ₹50,000 for Old) where applicable.\n"
        "5. Formatting requirements:\n"
        "   - Use clean Markdown with clear headings (e.g., '### Your Verified Numbers').\n"
        "   - Put every bullet point on its own new line with '- '.\n"
        "   - Always include double newlines before headers and between sections for clean rendering.\n"
        "   - Never collapse headings or bullet points onto a single line.\n"
        "6. MANDATORY CA DISCLAIMER: You MUST ALWAYS conclude tax-related responses with this disclaimer:\n"
        "   '⚠️ **Disclaimer**: *This analysis is an automated suggestion based on Income Tax Act rules (FY 2025–26). Please consult a qualified Chartered Accountant (CA) or certified tax professional for official tax filing.*'\n"
    )

    try:
        if provider in ("openrouter", "openai"):
            messages_payload = [{"role": "system", "content": system_prompt}]
            for h in history[-4:]:
                messages_payload.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            messages_payload.append({"role": "user", "content": user_query})

            completion = client.chat.completions.create(
                model=model,
                messages=messages_payload,
                temperature=0.2,
                max_tokens=4096,
            )
            msg = completion.choices[0].message
            content = msg.content
            if content:
                content = content.strip()
                if "Disclaimer" not in content:
                    content += ca_disclaimer_text
                return content
            return None

        elif provider == "anthropic":
            history_text = "\n".join(f"{h.get('role', 'user')}: {h.get('content', '')}" for h in history[-4:])
            resp = client.messages.create(
                model=model,
                max_tokens=800,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"{history_text}\nTaxpayer: {user_query}"},
                ],
            )
            res_text = resp.content[0].text.strip()
            if "Disclaimer" not in res_text:
                res_text += ca_disclaimer_text
            return res_text
    except Exception as e:
        logger.warning("LLM generation via %s failed: %s. Using deterministic fallback.", provider, e)
        return None

    return None
