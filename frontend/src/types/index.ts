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
  statement_start_date?: string | null;
  statement_end_date?: string | null;
  transactions_parsed?: number;
  transactions_count?: number;
  needs_review: boolean;
  has_forex?: boolean;
  forex_count?: number;
  warning?: string | null;
}

export interface SalarySlipUploadResponse {
  id?: number;
  salary_slip_id?: number;
  file_name: string;
  month: number;
  year: number;
  financial_year?: string;
  gross_salary?: number;
  gross_pay?: number;
  net_pay: number;
  basic_pay?: number | null;
  basic?: number | null;
  hra?: number | null;
  lta?: number | null;
  special_allowance?: number | null;
  other_allowances?: number | null;
  provident_fund?: number | null;
  employee_pf?: number | null;
  employer_pf?: number | null;
  professional_tax?: number | null;
  tax_deducted?: number | null;
  tds?: number | null;
  total_deductions?: number | null;
  parse_confidence?: number;
  extraction_confidence?: number | null;
  is_gross_valid?: boolean;
  needs_review?: boolean;
  matched_to_statement?: boolean;
}

export interface UnifiedUploadResult {
  document_type: 'salary_slip' | 'bank_statement';
  statement?: StatementUploadResponse;
  salary_slip?: SalarySlipUploadResponse;
  message: string;
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

export interface FilingDeadlineInfo {
  deadline_date: string;
  days_remaining: number;
  assessment_year: string;
  is_overdue: boolean;
  warning_level: 'green' | 'amber' | 'red';
}

export interface RealWorldFlags {
  savings_interest?: {
    total_interest: number;
    interest_transactions_count: number;
    eligible_deduction: number;
    section: string;
    is_senior_citizen: boolean;
  };
  capital_gains?: {
    has_capital_gains_activity: boolean;
    detected_sources: string[];
    transaction_count: number;
    advisory_warning: string;
    itr_form_recommendation: string;
  };
  salary_arrears?: {
    has_arrears: boolean;
    arrears_transactions_count: number;
    section_89_relief_advisory: string;
  };
  forex_transactions?: {
    count: number;
  };
  sample_insufficiency?: {
    is_insufficient: boolean;
    transaction_count: number;
  };
}

export interface AISChecklistItem {
  id: string;
  name: string;
  description: string;
  status: 'matched' | 'action_needed' | 'verified' | string;
  action_needed: string;
}

export interface TaxComparisonReport {
  user_id: number;
  financial_year: string;
  gross_income: number;
  salary_income?: number;
  savings_interest_income?: number;
  gross_income_extrapolated?: boolean;
  gross_income_slip_count?: number | null;
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
  // v1.1 Statutory Governance & Real-World Features
  catalog_viewed?: boolean;
  is_final?: boolean;
  report_status?: 'draft' | 'final' | string;
  real_world_flags?: RealWorldFlags;
  ais_26as_checklist?: {
    title: string;
    items: AISChecklistItem[];
  };
  filing_deadline?: FilingDeadlineInfo;
}

export interface DeductionCatalogItem {
  id: string;
  section_code: string;
  display_name: string;
  description: string;
  applicable_regimes: 'old_only' | 'both' | string;
  cap_type: 'fixed' | 'percentage' | 'formula' | string;
  cap_amount: number | null;
  cap_formula: string | null;
  requires_eligibility_check: boolean;
  declared_amount: number | null;
  declared_status: string | null;
  source: string | null;
  elicitation_state: string | null;
  skip_reason: string | null;
  remaining_cap: number | null;
  used_percentage: number | null;
  is_editable: boolean;
}

export interface CatalogListResponse {
  financial_year: string;
  total_sections: number;
  declared_count: number;
  total_declared_deductions: number;
  catalog_viewed: boolean;
  catalog_viewed_at: string | null;
  sections: DeductionCatalogItem[];
}

export interface SelfAddDeductionResponse {
  success: boolean;
  message: string;
  section_code: string;
  amount: number;
  source: string;
  remaining_cap: number | null;
  cap_amount: number | null;
}

export interface YearOverYearComparison {
  current_year: {
    financial_year: string;
    gross_income: number;
    old_regime_total_liability: number;
    new_regime_total_liability: number;
    recommended_regime: string;
    tax_savings: number;
  };
  prior_year: {
    financial_year: string;
    gross_income: number;
    old_regime_total_liability: number;
    new_regime_total_liability: number;
    recommended_regime: string;
    tax_savings: number;
  } | null;
  deltas?: {
    gross_income_delta: number;
    gross_income_pct_change: number;
    tax_liability_delta: number;
    tax_liability_pct_change: number;
  };
  has_prior_year_data: boolean;
  analysis_summary: string;
}

export interface CustomBankMapping {
  date_col: string;
  narration_col: string;
  debit_col?: string;
  credit_col?: string;
  amount_col?: string;
  balance_col?: string;
}

export interface BYOKConfig {
  has_key: boolean;
  provider?: string;
  model_name?: string;
  masked_key?: string;
  custom_base_url?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  storage_mode?: 'vault' | 'local';
}

export interface BYOKValidateRequest {
  provider: string;
  api_key: string;
  model_name?: string;
  custom_base_url?: string;
}

export interface BYOKValidateResponse {
  valid: boolean;
  provider: string;
  model_name: string;
  latency_ms?: number;
  message: string;
  error?: string | null;
}

export interface BYOKSaveRequest {
  provider: string;
  api_key: string;
  model_name?: string;
  custom_base_url?: string;
  validate_before_save?: boolean;
}

export interface UploadedFileItem {
  id: number;
  type: 'statement' | 'salary_slip';
  file_name: string;
  file_type: string;
  created_at: string;
  parse_status: string;
  transaction_count?: number | null;
  date_range?: string | null;
  details?: Record<string, any> | null;
}

export interface UserUploadedFilesResponse {
  files: UploadedFileItem[];
  total: number;
}

export interface TaxpayerProfile {
  id: number;
  user_id: number;
  name: string;
  relationship: 'self' | 'spouse' | 'parent' | 'child' | 'huf' | 'client' | string;
  pan?: string | null;
  dob?: string | null;
  age_category: 'general' | 'senior' | 'super_senior' | string;
  persona: 'salaried' | 'freelancer_44ada' | 'investor' | 'senior_citizen' | 'huf' | string;
  is_default: boolean;
  filing_status: 'in_progress' | 'ready' | 'filed' | string;
  created_at: string;
  updated_at: string;
  statements_count?: number;
  salary_slips_count?: number;
  readiness_score?: number;
  estimated_tax?: number | null;
  recommended_regime?: string | null;
}

export interface ReadinessMilestone {
  name: string;
  is_complete: boolean;
  weight_percent: number;
  details: string;
  action_tab: string;
}

export interface ProfileReadinessResponse {
  profile_id: number;
  profile_name: string;
  persona: string;
  overall_score: number;
  is_filing_ready: boolean;
  milestones: ReadinessMilestone[];
  next_step: string;
}

export interface HouseholdMemberSummary {
  profile_id: number;
  name: string;
  relationship: string;
  persona: string;
  age_category: string;
  pan?: string | null;
  gross_income: number;
  total_deductions: number;
  tax_new_regime: number;
  tax_old_regime: number;
  recommended_regime: string;
  optimal_tax: number;
  tax_savings: number;
}

export interface HouseholdArbitrageAdvice {
  category: string;
  title: string;
  impact_amount: number;
  description: string;
  actionable_tip: string;
}

export interface HouseholdSummaryResponse {
  total_household_income: number;
  total_household_tax: number;
  total_household_savings: number;
  members_count: number;
  members: HouseholdMemberSummary[];
  arbitrage_opportunities: HouseholdArbitrageAdvice[];
}

// ==============================================================================
// Career Switch & Offer Letter Decoder Types
// ==============================================================================

export interface TrapDetected {
  code: string;
  title: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
  amount: number;
}

export interface NegotiationPlaybook {
  suggested_80ccd2_monthly: number;
  suggested_broadband_monthly: number;
  annual_tax_saved: number;
  counter_proposal_email: string;
}

export interface OfferComponents {
  basic: number;
  hra: number;
  special_allowance: number;
  gratuity_annual: number;
  employer_pf_annual: number;
  employee_pf_annual: number;
  medical_insurance_annual: number;
  variable_pay: number;
  joining_bonus: number;
  esop_annual: number;
}

export interface MonthlyBreakdown {
  fixed_gross: number;
  basic: number;
  hra: number;
  special_allowance: number;
  employee_pf_deduction: number;
  professional_tax: number;
  monthly_tds_tax: number;
  guaranteed_in_hand: number;
}

export interface AnnualTotals {
  guaranteed_fixed_gross: number;
  annual_in_hand: number;
  annual_tax: number;
  effective_tax_rate_pct: number;
  retirals_total: number;
  at_risk_total: number;
}

export interface DecodeOfferRequest {
  ctc: number;
  basic?: number;
  hra?: number;
  special_allowance?: number;
  variable_pay?: number;
  joining_bonus?: number;
  bonus_clawback_months?: number;
  esop_annual?: number;
  gratuity_included?: boolean;
  employer_pf_included?: boolean;
  medical_insurance_annual?: number;
}

export interface DecodeOfferResponse {
  annual_ctc: number;
  components: OfferComponents;
  monthly_breakdown: MonthlyBreakdown;
  annual_totals: AnnualTotals;
  traps_detected: TrapDetected[];
  negotiation_playbook: NegotiationPlaybook;
}

export interface SimulateSwitchRequest {
  company_a_months: number;
  company_a_gross: number;
  company_a_tds: number;
  company_a_epf: number;
  company_b_months: number;
  company_b_monthly_gross: number;
}

export interface SimulateSwitchResponse {
  timeline: {
    company_a_months: number;
    company_b_months: number;
  };
  incomes: {
    company_a_gross: number;
    company_b_gross: number;
    total_combined_gross: number;
  };
  without_form_12b: {
    company_a_tds: number;
    company_b_projected_tds: number;
    total_tds_collected: number;
  };
  true_statutory_liability: {
    total_tax_due: number;
    effective_tax_rate_pct: number;
  };
  the_tax_shock: {
    tds_shortfall: number;
    section_234b_interest: number;
    section_234c_interest: number;
    total_july_demand: number;
    has_critical_shortfall: boolean;
  };
  with_form_12b: {
    remaining_tax_for_company_b: number;
    adjusted_monthly_tds: number;
    july_tax_surprise: number;
    interest_saved: number;
  };
  form_12b_particulars: {
    statement_period: string;
    gross_salary_company_a: number;
    tds_deducted_company_a: number;
    provident_fund_company_a: number;
    gross_salary_company_b_expected: number;
    total_annual_combined_income: number;
    statutory_form_12b_rule: string;
  };
}

export interface CompareOffersRequest {
  current_ctc: number;
  offer_a_ctc: number;
  offer_b_ctc?: number;
}

export interface OfferComparisonItem {
  ctc: number;
  monthly_in_hand: number;
  annual_in_hand: number;
  annual_tax: number;
  paper_ctc_hike_pct?: number;
  real_in_hand_hike_pct?: number;
  monthly_cash_gain?: number;
}

export interface CompareOffersResponse {
  current: OfferComparisonItem;
  offer_a: OfferComparisonItem;
  offer_b?: OfferComparisonItem;
}

export interface Form12BRequest {
  company_a_name: string;
  company_a_tan?: string;
  company_a_gross: number;
  company_a_tds: number;
  company_a_epf: number;
  period_start: string;
  period_end: string;
}

export interface Form12BResponse {
  employee_name: string;
  employee_pan: string;
  company_a_name: string;
  company_a_tan?: string;
  gross_salary: number;
  tds_deducted: number;
  epf_deducted: number;
  period: string;
  raw_form_text: string;
}

