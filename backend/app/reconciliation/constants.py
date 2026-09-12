"""
Constants for the Salary vs Bank Credit Reconciliation Engine (Phase 4).
"""

# Tolerance Defaults (Task 4.2)
DEFAULT_RECONCILIATION_TOLERANCE_ABSOLUTE: float = 500.0  # ₹500 tolerance
DEFAULT_RECONCILIATION_TOLERANCE_PERCENT: float = 0.01   # 1% tolerance

# Reconciliation Flag Types (Task 4.1 - 4.3)
FLAG_TYPE_MISMATCHED_AMOUNT = "mismatched_amount"
FLAG_TYPE_MISSING_BANK_CREDIT = "missing_bank_credit"
FLAG_TYPE_MISSING_SALARY_SLIP = "missing_salary_slip"
FLAG_TYPE_BONUS_VARIABLE_PAY = "bonus_unmatched"
FLAG_TYPE_UNEXPLAINED_CREDIT = "unexplained_salary_credit"

VALID_FLAG_TYPES = [
    FLAG_TYPE_MISMATCHED_AMOUNT,
    FLAG_TYPE_MISSING_BANK_CREDIT,
    FLAG_TYPE_MISSING_SALARY_SLIP,
    FLAG_TYPE_BONUS_VARIABLE_PAY,
    FLAG_TYPE_UNEXPLAINED_CREDIT,
]

# Resolution Statuses (Task 4.4)
STATUS_PENDING = "pending"
STATUS_RESOLVED = "resolved"
STATUS_IGNORED = "ignored"

VALID_STATUSES = [STATUS_PENDING, STATUS_RESOLVED, STATUS_IGNORED]

# Matching Window Parameters
# Salary for month M can be credited between the 20th of month M and the 10th of month M+1
SALARY_CREDIT_DAY_WINDOW_START = 20
SALARY_CREDIT_DAY_WINDOW_END = 10

# Bonus / Variable Pay Ratio Threshold
# If credited amount exceeds net pay by this ratio, or multiple credits occur, handle via separate bonus path
BONUS_RATIO_THRESHOLD: float = 1.25
