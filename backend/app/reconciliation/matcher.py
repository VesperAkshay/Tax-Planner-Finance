"""
Month-Level Salary Slip vs Bank Credit Matching Engine (Tasks 4.1 - 4.3).

Implements:
- Task 4.1: Month-level matching comparing net_pay to actual credited transaction(s).
- Task 4.2: Tolerance-based flagging (max(₹500, 1% net_pay)) on mismatch.
- Task 4.3: Explicit edge cases: missing slip, missing credit, bonus/variable pay, unexplained credit.
"""

from calendar import monthrange
from datetime import date
import re
from typing import Dict, List, Optional, Set, Tuple

from app.reconciliation.constants import (
    BONUS_RATIO_THRESHOLD,
    DEFAULT_RECONCILIATION_TOLERANCE_ABSOLUTE,
    DEFAULT_RECONCILIATION_TOLERANCE_PERCENT,
    FLAG_TYPE_BONUS_VARIABLE_PAY,
    FLAG_TYPE_MISMATCHED_AMOUNT,
    FLAG_TYPE_MISSING_BANK_CREDIT,
    FLAG_TYPE_MISSING_SALARY_SLIP,
    FLAG_TYPE_UNEXPLAINED_CREDIT,
    SALARY_CREDIT_DAY_WINDOW_END,
    SALARY_CREDIT_DAY_WINDOW_START,
    STATUS_PENDING,
)
from app.reconciliation.schemas import (
    BankCreditItem,
    MonthReconciliationResult,
    ReconciliationFlagItem,
    ReconciliationReport,
    SalarySlipItem,
)

SALARY_KEYWORDS = [
    r"\bSALARY\b",
    r"\bPAYROLL\b",
    r"\bSAL\b",
    r"\bTECHCORP\b",
    r"\bACME CORP\b",
    r"\bSTIPEND\b",
]


def is_salary_credit_narration(description: str) -> bool:
    """Detects whether a transaction narration signifies a salary or payroll credit."""
    if not description:
        return False
    upper = description.upper()
    for pattern in SALARY_KEYWORDS:
        if re.search(pattern, upper):
            return True
    return False


def compute_reconciliation_tolerance(
    net_pay: float,
    abs_tolerance: float = DEFAULT_RECONCILIATION_TOLERANCE_ABSOLUTE,
    pct_tolerance: float = DEFAULT_RECONCILIATION_TOLERANCE_PERCENT,
) -> float:
    """
    Computes dynamic tolerance per Task 4.2:
    e.g. ₹500 or 1% of net pay, whichever is greater.
    """
    return round(max(abs_tolerance, net_pay * pct_tolerance), 2)


def get_month_credit_window(month: int, year: int) -> Tuple[date, date]:
    """
    Returns the date range where salary for (month, year) is expected to be credited:
    From the 20th of `month` through the 10th of `month + 1`.
    """
    start_date = date(year, month, SALARY_CREDIT_DAY_WINDOW_START)

    if month == 12:
        end_date = date(year + 1, 1, SALARY_CREDIT_DAY_WINDOW_END)
    else:
        end_date = date(year, month + 1, SALARY_CREDIT_DAY_WINDOW_END)

    return start_date, end_date


def filter_credits_for_month(
    credits: List[BankCreditItem],
    month: int,
    year: int,
) -> List[BankCreditItem]:
    """
    Finds bank credits associated with a given month's salary.
    Matches credits falling into the window (20th of month to 10th of next month)
    or explicitly mentioning the month in their narration.
    """
    window_start, window_end = get_month_credit_window(month, year)
    month_name = date(year, month, 1).strftime("%B").upper()
    month_short = date(year, month, 1).strftime("%b").upper()

    matched: List[BankCreditItem] = []
    for c in credits:
        # Check window range
        in_window = window_start <= c.date <= window_end
        # Check explicit narration token
        desc_upper = c.description.upper()
        mentions_month = month_name in desc_upper or month_short in desc_upper

        if in_window or mentions_month:
            matched.append(c)

    return matched


def reconcile_month(
    month: int,
    year: int,
    slip: Optional[SalarySlipItem],
    credits: List[BankCreditItem],
    abs_tolerance: float = DEFAULT_RECONCILIATION_TOLERANCE_ABSOLUTE,
    pct_tolerance: float = DEFAULT_RECONCILIATION_TOLERANCE_PERCENT,
) -> MonthReconciliationResult:
    """
    Reconciles salary slip and bank credits for a specific month (Tasks 4.1 - 4.3).
    Handles exact matching, tolerance comparison, and explicit edge cases.
    """
    flags: List[ReconciliationFlagItem] = []

    # Edge Case 1: Missing Salary Slip (salary credit exists in bank, but no slip uploaded)
    if slip is None:
        for c in credits:
            flags.append(
                ReconciliationFlagItem(
                    salary_slip_id=None,
                    transaction_id=c.id,
                    month=month,
                    year=year,
                    flag_type=FLAG_TYPE_MISSING_SALARY_SLIP,
                    expected_amount=None,
                    actual_amount=c.amount,
                    difference=c.amount,
                    tolerance_applied=0.0,
                    status=STATUS_PENDING,
                    details=f"Bank credit of ₹{c.amount:,.2f} on {c.date} has no corresponding salary slip for {month}/{year}.",
                )
            )
        return MonthReconciliationResult(
            month=month,
            year=year,
            status="missing_slip",
            slip=None,
            credits=credits,
            flags=flags,
            is_reconciled=False,
        )

    # Edge Case 2: Missing Bank Credit (slip exists, but zero matching credits in bank)
    if not credits:
        flags.append(
            ReconciliationFlagItem(
                salary_slip_id=slip.id,
                transaction_id=None,
                month=month,
                year=year,
                flag_type=FLAG_TYPE_MISSING_BANK_CREDIT,
                expected_amount=slip.net_pay,
                actual_amount=0.0,
                difference=slip.net_pay,
                tolerance_applied=compute_reconciliation_tolerance(slip.net_pay, abs_tolerance, pct_tolerance),
                status=STATUS_PENDING,
                details=f"Salary slip shows net pay of ₹{slip.net_pay:,.2f}, but no bank credit was found for {month}/{year}.",
            )
        )
        return MonthReconciliationResult(
            month=month,
            year=year,
            status="missing_credit",
            slip=slip,
            credits=[],
            flags=flags,
            is_reconciled=False,
        )

    tolerance = compute_reconciliation_tolerance(slip.net_pay, abs_tolerance, pct_tolerance)

    # 1. Check if any single credit matches slip.net_pay within tolerance (Task 4.1 & 4.2)
    matching_credit = None
    for c in credits:
        if abs(c.amount - slip.net_pay) <= tolerance:
            matching_credit = c
            break

    if matching_credit is not None:
        # Primary salary credit matched!
        # Check for additional unexpected credits in the same month (Edge Case 4)
        if len(credits) > 1:
            for extra in credits:
                if extra.id != matching_credit.id:
                    flags.append(
                        ReconciliationFlagItem(
                            salary_slip_id=slip.id,
                            transaction_id=extra.id,
                            month=month,
                            year=year,
                            flag_type=FLAG_TYPE_UNEXPLAINED_CREDIT,
                            expected_amount=None,
                            actual_amount=extra.amount,
                            difference=extra.amount,
                            tolerance_applied=0.0,
                            status=STATUS_PENDING,
                            details=f"Extra unexplained salary credit of ₹{extra.amount:,.2f} on {extra.date} alongside reconciled regular salary.",
                        )
                    )

        is_reconciled = len(flags) == 0
        return MonthReconciliationResult(
            month=month,
            year=year,
            status="matched" if is_reconciled else "flagged",
            slip=slip,
            credits=credits,
            flags=flags,
            is_reconciled=is_reconciled,
        )

    # 2. No credit individually matched within tolerance.
    # Check if this is a Bonus / Variable Pay scenario (Edge Case 3, Task 4.3):
    total_credit = sum(c.amount for c in credits)
    is_bonus_scenario = (
        (len(credits) == 1 and credits[0].amount >= slip.net_pay * BONUS_RATIO_THRESHOLD)
        or any("BONUS" in c.description.upper() or "VARIABLE" in c.description.upper() for c in credits)
        or (len(credits) > 1 and total_credit >= slip.net_pay * BONUS_RATIO_THRESHOLD)
    )

    if is_bonus_scenario:
        diff = round(abs(total_credit - slip.net_pay), 2)
        flags.append(
            ReconciliationFlagItem(
                salary_slip_id=slip.id,
                transaction_id=credits[0].id if credits else None,
                month=month,
                year=year,
                flag_type=FLAG_TYPE_BONUS_VARIABLE_PAY,
                expected_amount=slip.net_pay,
                actual_amount=total_credit,
                difference=diff,
                tolerance_applied=tolerance,
                status=STATUS_PENDING,
                details=(
                    f"Bonus/Variable pay detected: Total credit ₹{total_credit:,.2f} across {len(credits)} transaction(s) "
                    f"differs from slip net pay ₹{slip.net_pay:,.2f} by ₹{diff:,.2f}. Must not be force-averaged."
                ),
            )
        )
        return MonthReconciliationResult(
            month=month,
            year=year,
            status="bonus_detected",
            slip=slip,
            credits=credits,
            flags=flags,
            is_reconciled=False,
        )

    # 3. Standard Mismatched Amount (Task 4.2)
    primary_credit = max(credits, key=lambda c: c.amount)
    diff = round(abs(slip.net_pay - primary_credit.amount), 2)
    flags.append(
        ReconciliationFlagItem(
            salary_slip_id=slip.id,
            transaction_id=primary_credit.id,
            month=month,
            year=year,
            flag_type=FLAG_TYPE_MISMATCHED_AMOUNT,
            expected_amount=slip.net_pay,
            actual_amount=primary_credit.amount,
            difference=diff,
            tolerance_applied=tolerance,
            status=STATUS_PENDING,
            details=(
                f"Amount mismatch for {month}/{year}: Slip net pay is ₹{slip.net_pay:,.2f}, "
                f"Bank credit is ₹{primary_credit.amount:,.2f} (diff ₹{diff:,.2f} > tolerance ₹{tolerance:,.2f})."
            ),
        )
    )
    return MonthReconciliationResult(
        month=month,
        year=year,
        status="mismatched",
        slip=slip,
        credits=credits,
        flags=flags,
        is_reconciled=False,
    )


def reconcile_salary_and_bank(
    slips: List[SalarySlipItem],
    credits: List[BankCreditItem],
    user_id: int = 1,
    abs_tolerance: float = DEFAULT_RECONCILIATION_TOLERANCE_ABSOLUTE,
    pct_tolerance: float = DEFAULT_RECONCILIATION_TOLERANCE_PERCENT,
) -> ReconciliationReport:
    """
    Executes full multi-month reconciliation between all salary slips and bank credits.
    """
    # Group slips by (month, year)
    slips_by_month: Dict[Tuple[int, int], SalarySlipItem] = {
        (s.month, s.year): s for s in slips
    }

    # Discover all relevant (month, year) combinations
    all_months: Set[Tuple[int, int]] = set(slips_by_month.keys())

    # Map credits to their respective salary months
    credits_by_month: Dict[Tuple[int, int], List[BankCreditItem]] = {}
    assigned_credit_ids: Set[Optional[int]] = set()

    for (m, y) in all_months:
        month_credits = filter_credits_for_month(credits, m, y)
        credits_by_month[(m, y)] = month_credits
        for c in month_credits:
            assigned_credit_ids.add(c.id)

    # Check for unassigned salary credits in bank (which indicates missing slip)
    for c in credits:
        if c.id not in assigned_credit_ids and (c.is_salary or is_salary_credit_narration(c.description)):
            # Determine likely month
            # If credited 1st-10th, relates to previous month; else current month
            if c.date.day <= SALARY_CREDIT_DAY_WINDOW_END:
                c_month = 12 if c.date.month == 1 else c.date.month - 1
                c_year = c.date.year - 1 if c.date.month == 1 else c.date.year
            else:
                c_month = c.date.month
                c_year = c.date.year

            all_months.add((c_month, c_year))
            if (c_month, c_year) not in credits_by_month:
                credits_by_month[(c_month, c_year)] = []
            credits_by_month[(c_month, c_year)].append(c)

    # Reconcile each month in chronological order
    sorted_months = sorted(list(all_months), key=lambda item: (item[1], item[0]))
    results: List[MonthReconciliationResult] = []
    all_flags: List[ReconciliationFlagItem] = []
    matched_count = 0
    flagged_count = 0

    for (m, y) in sorted_months:
        slip = slips_by_month.get((m, y))
        m_credits = credits_by_month.get((m, y), [])
        m_res = reconcile_month(
            month=m,
            year=y,
            slip=slip,
            credits=m_credits,
            abs_tolerance=abs_tolerance,
            pct_tolerance=pct_tolerance,
        )
        results.append(m_res)
        all_flags.extend(m_res.flags)
        if m_res.is_reconciled:
            matched_count += 1
        else:
            flagged_count += 1

    return ReconciliationReport(
        user_id=user_id,
        months_evaluated=len(sorted_months),
        matched_months_count=matched_count,
        flagged_months_count=flagged_count,
        total_flags=len(all_flags),
        flags=all_flags,
        month_results=results,
    )
