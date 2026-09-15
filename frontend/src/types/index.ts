export interface User {
  id: number;
  email: string;
  name: string;
}

export interface StatementUploadResponse {
  upload_id: number;
  account_id: number;
  file_name: string;
  file_type: string;
  parse_status: string;
  parse_confidence: number;
  balance_reconciled: boolean;
  opening_balance: number | null;
  closing_balance: number | null;
  statement_start_date: string | null;
  statement_end_date: string | null;
  transactions_parsed: number;
  needs_review: boolean;
}

export interface SalarySlipUploadResponse {
  salary_slip_id: number;
  file_name: string;
  month: number;
  year: number;
  gross_salary: number;
  net_pay: number;
  basic_pay: number | null;
  hra: number | null;
  provident_fund: number | null;
  tax_deducted: number | null;
  parse_confidence: number;
  matched_to_statement: boolean;
}

export interface CategorySpending {
  category_name: string;
  amount: number;
  percentage_of_total: number;
}

export interface FinancialSnapshot {
  total_income: number;
  total_expenses: number;
  net_savings: number;
  savings_rate: number;
  category_spending: CategorySpending[];
  total_transactions_analyzed: number;
  date_range: {
    start: string | null;
    end: string | null;
  };
}

export interface ReconciliationFlag {
  id: number;
  user_id: number;
  salary_slip_id: number | null;
  transaction_id: number | null;
  flag_type: string;
  discrepancy_amount: number;
  reason: string;
  status: 'pending' | 'resolved' | 'ignored';
  resolved_at: string | null;
  created_at: string;
}

export interface AgentChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface TaxRegimeBreakdown {
  regime: 'new' | 'old';
  gross_income: number;
  exemptions_and_deductions: number;
  standard_deduction: number;
  taxable_income: number;
  gross_tax: number;
  rebate_87a: number;
  marginal_relief_87a: number;
  net_tax_before_cess: number;
  cess: number;
  total_tax_liability: number;
  effective_tax_rate: number;
}

export interface DeductionItem {
  section: string;
  name: string;
  amount_declared: number;
  max_allowed_limit: number;
  citation: string;
}

export interface TaxComparisonReport {
  user_id: number;
  financial_year: string;
  assessment_year: string;
  recommended_regime: 'new' | 'old';
  tax_savings: number;
  new_regime: TaxRegimeBreakdown;
  old_regime: TaxRegimeBreakdown;
  declared_deductions: DeductionItem[];
  missing_deductions_suggestions: string[];
}
