from typing import Optional
from app.parsing.constants import DEFAULT_REVIEW_THRESHOLD
from app.parsing.schemas import StatementParseResult

# Default balance reconciliation tolerance in INR
DEFAULT_BALANCE_TOLERANCE: float = 1.0


def reconcile_statement_balance(
    result: StatementParseResult,
    tolerance: float = DEFAULT_BALANCE_TOLERANCE,
) -> StatementParseResult:
    """
    Post-parse balance reconciliation check (Task 2.7).
    Compares the statement's stated opening and closing balances against
    the sum of parsed transaction debits and credits:
        Expected Closing = Opening + Total Credits - Total Debits

    Sets `balance_reconciled`, `parse_status`, `expected_closing_balance`,
    `balance_discrepancy`, and updates `parse_confidence` and `needs_review` accordingly.
    """
    if not result.rows:
        result.parse_status = "failed"
        result.balance_reconciled = False
        result.needs_review = True
        result.parse_confidence = 0.0
        if "No valid transactions found in statement." not in result.warnings:
            result.warnings.append("No valid transactions found in statement.")
        return result

    # Sort rows by date and calculate totals
    result.rows.sort(key=lambda r: r.date)
    result.statement_start_date = result.rows[0].date
    result.statement_end_date = result.rows[-1].date

    result.total_credits = round(
        sum(r.amount for r in result.rows if r.transaction_type == "credit"), 2
    )
    result.total_debits = round(
        sum(r.amount for r in result.rows if r.transaction_type == "debit"), 2
    )

    if not result.parse_confidence or result.parse_confidence == 0.0:
        result.parse_confidence = round(
            sum(r.parse_confidence for r in result.rows) / len(result.rows), 3
        )

    # 1. Resolve missing opening or closing balance from transaction running balances
    first_bal = result.rows[0].balance
    last_bal = result.rows[-1].balance

    if result.opening_balance is None and first_bal is not None:
        if result.rows[0].transaction_type == "credit":
            result.opening_balance = round(first_bal - result.rows[0].amount, 2)
        else:
            result.opening_balance = round(first_bal + result.rows[0].amount, 2)

    if result.closing_balance is None and last_bal is not None:
        result.closing_balance = round(last_bal, 2)

    # 2. Check running balance continuity across individual transaction rows
    running_balance_mismatches = 0
    for idx in range(len(result.rows) - 1):
        curr_r = result.rows[idx]
        next_r = result.rows[idx + 1]
        if curr_r.balance is not None and next_r.balance is not None:
            if next_r.transaction_type == "credit":
                expected_next = round(curr_r.balance + next_r.amount, 2)
            else:
                expected_next = round(curr_r.balance - next_r.amount, 2)

            step_diff = round(abs(expected_next - next_r.balance), 2)
            if step_diff > tolerance:
                running_balance_mismatches += 1
                result.warnings.append(
                    f"Row {idx + 1} -> {idx + 2} balance discontinuity: "
                    f"expected {expected_next}, found {next_r.balance} (diff: {step_diff})"
                )

    # 3. Overall Statement Balance Reconciliation
    if result.opening_balance is not None:
        expected_closing = round(
            result.opening_balance + result.total_credits - result.total_debits, 2
        )
        result.expected_closing_balance = expected_closing

        if result.closing_balance is not None:
            discrepancy = round(abs(result.closing_balance - expected_closing), 2)
            result.balance_discrepancy = discrepancy

            if discrepancy <= tolerance and running_balance_mismatches == 0:
                result.balance_reconciled = True
                if result.parse_confidence >= DEFAULT_REVIEW_THRESHOLD:
                    result.parse_status = "completed"
                    result.needs_review = False
                else:
                    result.parse_status = "needs_review"
                    result.needs_review = True
            else:
                # Discrepancy detected
                result.balance_reconciled = False
                result.needs_review = True
                result.parse_status = "needs_review"
                # Penalize confidence when stated balance doesn't match parsed sum
                result.parse_confidence = round(min(result.parse_confidence, 0.60), 3)
                result.warnings.append(
                    f"Balance reconciliation mismatch: Stated opening ({result.opening_balance}) "
                    f"+ Credits ({result.total_credits}) - Debits ({result.total_debits}) "
                    f"= Expected closing ({expected_closing}), but stated closing is {result.closing_balance} "
                    f"(diff: {discrepancy})"
                )
        else:
            # Closing balance not stated on statement; infer it
            result.closing_balance = expected_closing
            result.balance_discrepancy = 0.0
            result.balance_reconciled = (running_balance_mismatches == 0)
            if result.balance_reconciled and result.parse_confidence >= DEFAULT_REVIEW_THRESHOLD:
                result.parse_status = "completed"
                result.needs_review = False
            else:
                result.parse_status = "needs_review"
                result.needs_review = True
            result.warnings.append(
                f"Closing balance not stated on statement; computed from transactions as {expected_closing}."
            )
    else:
        # Opening balance not available
        if result.closing_balance is not None:
            inferred_opening = round(
                result.closing_balance - result.total_credits + result.total_debits, 2
            )
            result.opening_balance = inferred_opening
            result.expected_closing_balance = result.closing_balance
            result.balance_discrepancy = 0.0
            result.balance_reconciled = (running_balance_mismatches == 0)
            if result.balance_reconciled and result.parse_confidence >= DEFAULT_REVIEW_THRESHOLD:
                result.parse_status = "completed"
                result.needs_review = False
            else:
                result.parse_status = "needs_review"
                result.needs_review = True
            result.warnings.append(
                f"Opening balance not stated on statement; computed from transactions as {inferred_opening}."
            )
        else:
            # Neither opening nor closing balance available
            result.balance_reconciled = False
            result.expected_closing_balance = None
            result.balance_discrepancy = None
            if result.parse_confidence >= DEFAULT_REVIEW_THRESHOLD:
                result.parse_status = "completed"
                result.needs_review = False
            else:
                result.parse_status = "needs_review"
                result.needs_review = True
            result.warnings.append(
                "Statement lacks opening and closing balances for reconciliation."
            )

    return result
