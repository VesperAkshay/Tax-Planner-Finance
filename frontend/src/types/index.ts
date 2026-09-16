export interface User {
  id: number;
  email: string;
  full_name?: string | null;
  pan?: string | null;
  is_active?: boolean;
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
  total_amount?: number;
  percentage?: number;
  transaction_count?: number;
  amount?: number;
  percentage_of_total?: number;
}

export interface BudgetRuleDiagnostic {
  needs_amount: number;
  needs_pct: number;
  wants_amount: number;
  wants_pct: number;
  savings_amount: number;
  savings_pct: number;
  status: string;
  advice: string;
}

export interface TopMerchantItem {
  merchant: string;
  total_spent: number;
  transaction_count: number;
  category: string;
}

export interface RecurringSubscriptionItem {
  name: string;
  amount: number;
  category: string;
  frequency: string;
}

export interface TaxDeductibleSpendItem {
  section: string;
  title: string;
  amount: number;
  transaction_count: number;
  description: string;
}

export interface SnapshotTransactionItem {
  id: number;
  date: string;
  description: string;
  merchant: string;
  amount: number;
  transaction_type: string;
  category: string;
  needs_review: boolean;
}

export interface FinancialSnapshot {
  user_id?: number;
  total_income: number;
  total_expenses: number;
  net_savings: number;
  savings_rate: number;
  daily_burn_rate?: number;
  category_spending: CategorySpending[];
  top_categories?: CategorySpending[];
  budget_rule_diagnostic?: BudgetRuleDiagnostic;
  top_merchants?: TopMerchantItem[];
  recurring_subscriptions?: RecurringSubscriptionItem[];
  tax_deductible_spends?: TaxDeductibleSpendItem[];
  uncategorized_count?: number;
  needs_review_count?: number;
  total_transactions_analyzed: number;
  recent_transactions?: SnapshotTransactionItem[];
  date_range?: {
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
  financial_year?: string;
  gross_income: number;
  standard_deduction: number;
  taxable_income: number;
  tax_before_rebate?: number;
  rebate_87a?: number;
  marginal_relief?: number;
  tax_after_rebate?: number;
  cess: number;
  cess_rate?: number;
  total_tax?: number;
  effective_tax_rate?: number;
  total_deductions?: number;
  slab_breakdown?: Array<{
    min: number;
    max: number | null;
    rate: number;
    taxable_in_slab?: number;
    slab_tax?: number;
  }>;
  // Fallback aliases:
  total_tax_liability?: number;
  gross_tax?: number;
  exemptions_and_deductions?: number;
  marginal_relief_87a?: number;
  net_tax_before_cess?: number;
}

export interface DeductionItem {
  section: string;
  name?: string;
  amount_declared?: number;
  max_allowed_limit?: number;
  citation?: string;
}

export interface TaxComparisonReport {
  user_id: number;
  financial_year: string;
  gross_income: number;
  is_salaried: boolean;
  recommended_regime: 'new' | 'old' | string;
  tax_savings: number;
  breakeven_deductions?: number;
  old_regime: TaxRegimeBreakdown;
  new_regime: TaxRegimeBreakdown;
  deductions_applied?: Record<string, any>;
  citations?: Array<{
    section: string;
    title: string;
    source_url: string;
    citation_markdown?: string;
  }>;
  summary?: string;
  assessment_year?: string;
  declared_deductions?: DeductionItem[];
  missing_deductions_suggestions?: string[];
}
