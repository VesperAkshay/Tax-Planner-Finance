import type {
  FinancialSnapshot,
  ReconciliationFlag,
  StatementUploadResponse,
  SalarySlipUploadResponse,
  UnifiedUploadResult,
  TaxComparisonReport,
  User,
  CatalogListResponse,
  SelfAddDeductionResponse,
  YearOverYearComparison,
  BYOKConfig,
  BYOKValidateRequest,
  BYOKValidateResponse,
  BYOKSaveRequest,
  UserUploadedFilesResponse,
  TaxpayerProfile,
  ProfileReadinessResponse,
  HouseholdSummaryResponse,
} from '../types';

const BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const API_BASE = `${BASE_URL}/api/v1`;

export class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('taxplanner_token');
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('taxplanner_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('taxplanner_token');
  }

  getToken(): string | null {
    return this.token;
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  private headers(isFormData: boolean = false): Record<string, string> {
    const h: Record<string, string> = {};
    if (!isFormData) {
      h['Content-Type'] = 'application/json';
    }
    if (this.token) {
      h['Authorization'] = `Bearer ${this.token}`;
    }

    // Attach local browser BYOK credentials if active
    const localByok = localStorage.getItem('taxplanner_byok_local');
    if (localByok) {
      try {
        const parsed = JSON.parse(localByok);
        if (parsed.api_key) {
          h['X-BYOK-Key'] = parsed.api_key;
          if (parsed.provider) h['X-BYOK-Provider'] = parsed.provider;
          if (parsed.model_name) h['X-BYOK-Model'] = parsed.model_name;
          if (parsed.custom_base_url) h['X-BYOK-Base-Url'] = parsed.custom_base_url;
        }
      } catch {}
    }

    // Attach active taxpayer profile context if selected
    const activeProfileId = localStorage.getItem('taxplanner_active_profile_id');
    if (activeProfileId) {
      h['X-Taxpayer-Profile-Id'] = activeProfileId;
    }

    return h;
  }

  async register(
    email: string,
    password: string,
    fullName: string,
    pan?: string
  ): Promise<{ token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        pan: pan || undefined,
        is_active: true,
      }),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Registration failed (${res.status})`);
    }

    const data = await res.json();
    this.setToken(data.access_token);
    return { token: data.access_token, user: data.user };
  }

  async login(email: string, password: string): Promise<{ token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Login failed (${res.status})`);
    }

    const data = await res.json();
    this.setToken(data.access_token);
    return { token: data.access_token, user: data.user };
  }

  async getCurrentUser(): Promise<User | null> {
    if (!this.token) {
      return null;
    }
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: this.headers(),
      });
      if (!res.ok) {
        if (res.status === 401) {
          this.clearToken();
        }
        return null;
      }
      return await res.json();
    } catch {
      return null;
    }
  }

  async uploadStatement(
    file: File,
    bankFormat?: string,
    columnMapping?: Record<string, string>,
    confirmOverlap: boolean = true,
    password?: string
  ): Promise<StatementUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (bankFormat && bankFormat !== 'auto') {
      formData.append('bank_format', bankFormat);
    }
    if (columnMapping && Object.keys(columnMapping).length > 0) {
      formData.append('column_mapping', JSON.stringify(columnMapping));
    }
    formData.append('confirm_overlap', String(confirmOverlap));
    if (password) {
      formData.append('password', password);
    }

    const res = await fetch(`${API_BASE}/upload/statement`, {
      method: 'POST',
      headers: this.headers(true),
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = typeof err.detail === 'string' ? err.detail : (err.detail?.message || err.detail?.code || `Statement upload failed (${res.status})`);
      throw new Error(msg);
    }
    return await res.json();
  }

  async uploadSalarySlip(file: File, month?: number, year?: number, password?: string): Promise<SalarySlipUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (month && month > 0) formData.append('month', String(month));
    if (year && year > 0) formData.append('year', String(year));
    if (password) formData.append('password', password);

    const res = await fetch(`${API_BASE}/upload/salary-slip`, {
      method: 'POST',
      headers: this.headers(true),
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = typeof err.detail === 'string' ? err.detail : (err.detail?.message || err.detail?.code || `Salary slip upload failed (${res.status})`);
      throw new Error(msg);
    }
    return await res.json();
  }

  async uploadAutoDocument(
    file: File,
    password?: string,
    bankFormat?: string,
    confirmOverlap: boolean = true
  ): Promise<UnifiedUploadResult> {
    const formData = new FormData();
    formData.append('file', file);
    if (password) formData.append('password', password);
    if (bankFormat && bankFormat !== 'auto') formData.append('bank_format', bankFormat);
    formData.append('confirm_overlap', String(confirmOverlap));

    const res = await fetch(`${API_BASE}/upload/auto`, {
      method: 'POST',
      headers: this.headers(true),
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = typeof err.detail === 'string' ? err.detail : (err.detail?.message || err.detail?.code || `Document upload failed (${res.status})`);
      throw new Error(msg);
    }
    return await res.json();
  }

  async getFinancialSnapshot(): Promise<FinancialSnapshot> {
    const res = await fetch(`${API_BASE}/financial-snapshot`, {
      headers: this.headers(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to retrieve financial snapshot (${res.status})`);
    }
    return await res.json();
  }

  async reCategorizeTransactions(): Promise<{ total_processed: number; updated_count: number; message: string }> {
    const res = await fetch(`${API_BASE}/financial-snapshot/re-categorize`, {
      method: 'POST',
      headers: this.headers(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Re-categorization failed (${res.status})`);
    }
    return await res.json();
  }

  async getReconciliationFlags(): Promise<ReconciliationFlag[]> {
    const res = await fetch(`${API_BASE}/reconciliation/flags`, {
      headers: this.headers(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch reconciliation flags (${res.status})`);
    }
    return await res.json();
  }

  async runReconciliation(): Promise<unknown> {
    const res = await fetch(`${API_BASE}/reconciliation/run`, {
      method: 'POST',
      headers: this.headers(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to run reconciliation pipeline (${res.status})`);
    }
    return await res.json();
  }

  async resolveFlag(
    flagId: number,
    resolution: string,
    note?: string
  ): Promise<{ success: boolean; flag: ReconciliationFlag }> {
    const action = resolution === 'resolve' || resolution === 'resolved' ? 'resolved' : 'ignored';
    const userNote = note && note.trim().length > 0 ? note : 'User marked as resolved in UI';

    const res = await fetch(`${API_BASE}/reconciliation/flags/${flagId}/resolve`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ action, user_note: userNote }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to resolve flag (${res.status})`);
    }
    const data = await res.json();
    return { success: true, flag: data };
  }

  async sendChatMessage(
    message: string,
    history: { role: string; content: string }[]
  ): Promise<{ reply: string; deductions_updated?: Record<string, number> }> {
    const res = await fetch(`${API_BASE}/agent/chat`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({
        message,
        history,
        user_responses: {},
        session_id: 'default_session',
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Agent communication failed (${res.status})`);
    }
    const data = await res.json();
    return {
      reply: data.message || data.reply || 'Calculations updated.',
      deductions_updated: data.declared_deductions || data.deductions_updated,
    };
  }

  async getTaxComparisonReport(): Promise<TaxComparisonReport> {
    const res = await fetch(`${API_BASE}/tax/comparison-report`, {
      headers: this.headers(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to generate tax comparison report (${res.status})`);
    }
    return await res.json();
  }

  async downloadTaxReportPdf(): Promise<void> {
    const res = await fetch(`${API_BASE}/tax/comparison-report/pdf`, {
      headers: this.headers(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to download tax report PDF (${res.status})`);
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Mr_Planner_Tax_Invoice_FY2025-26.pdf';
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }

  // ==========================================
  // Statutory Deduction Catalog (Phase 14)
  // ==========================================

  async getCatalog(financialYear: string = '2025-2026', markViewed: boolean = true): Promise<CatalogListResponse> {
    const res = await fetch(
      `${API_BASE}/catalog?financial_year=${encodeURIComponent(financialYear)}&mark_viewed=${markViewed}`,
      { headers: this.headers() }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch deduction catalog (${res.status})`);
    }
    return await res.json();
  }

  async declareDeduction(
    sectionCode: string,
    amount: number,
    eligibilityConfirmed: boolean = true,
    financialYear: string = '2025-2026',
    metadataJson?: Record<string, any>
  ): Promise<SelfAddDeductionResponse> {
    const res = await fetch(`${API_BASE}/catalog/declare`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({
        section_code: sectionCode,
        amount,
        financial_year: financialYear,
        eligibility_confirmed: eligibilityConfirmed,
        metadata_json: metadataJson || null,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to declare deduction for Section ${sectionCode} (${res.status})`);
    }
    return await res.json();
  }

  async markCatalogViewed(financialYear: string = '2025-2026'): Promise<{
    success: boolean;
    catalog_viewed: boolean;
    financial_year: string;
    viewed_at: string;
  }> {
    const res = await fetch(`${API_BASE}/catalog/viewed?financial_year=${encodeURIComponent(financialYear)}`, {
      method: 'POST',
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to satisfy catalog checkpoint (${res.status})`);
    }
    return await res.json();
  }

  async getCatalogCheckpoint(financialYear: string = '2025-2026'): Promise<{
    financial_year: string;
    catalog_viewed: boolean;
    viewed_at: string | null;
  }> {
    const res = await fetch(`${API_BASE}/catalog/checkpoint?financial_year=${encodeURIComponent(financialYear)}`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to check catalog checkpoint (${res.status})`);
    }
    return await res.json();
  }

  // ==========================================
  // Real-World YoY Comparison (Phase 17)
  // ==========================================

  async getYearOverYearComparison(
    currentFy: string = '2025-2026',
    priorFy?: string
  ): Promise<YearOverYearComparison> {
    let url = `${API_BASE}/tax/year-over-year?current_fy=${encodeURIComponent(currentFy)}`;
    if (priorFy) {
      url += `&prior_fy=${encodeURIComponent(priorFy)}`;
    }
    const res = await fetch(url, { headers: this.headers() });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch Year-Over-Year comparison (${res.status})`);
    }
    return await res.json();
  }

  // ==========================================
  // Account & Data Lifecycle (Phase 15)
  // ==========================================

  async exportDataArchive(financialYear: string = '2025-2026'): Promise<void> {
    const res = await fetch(`${API_BASE}/lifecycle/export?financial_year=${encodeURIComponent(financialYear)}`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to generate export archive (${res.status})`);
    }
    const blob = await res.blob();
    const cleanFy = financialYear.replace('-', '_');
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tax_planner_export_FY${cleanFy}.zip`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }

  async getUserUploadedFiles(): Promise<UserUploadedFilesResponse> {
    const res = await fetch(`${API_BASE}/lifecycle/files?_t=${Date.now()}`, {
      headers: {
        ...this.headers(),
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
      },
      cache: 'no-store',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch uploaded files (${res.status})`);
    }
    return await res.json();
  }

  async deleteSalarySlip(salarySlipId: number): Promise<{ success: boolean; message: string; details?: any }> {
    const res = await fetch(`${API_BASE}/lifecycle/salary-slip/${salarySlipId}?confirm=true`, {
      method: 'DELETE',
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to delete salary slip ${salarySlipId} (${res.status})`);
    }
    return await res.json();
  }

  async deleteUpload(uploadId: number): Promise<{ success: boolean; message: string; details?: any }> {
    const res = await fetch(`${API_BASE}/lifecycle/upload/${uploadId}?confirm=true`, {
      method: 'DELETE',
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to delete upload ${uploadId} (${res.status})`);
    }
    return await res.json();
  }

  async deleteFinancialYear(financialYear: string): Promise<{ success: boolean; message: string; details?: any }> {
    const res = await fetch(
      `${API_BASE}/lifecycle/financial-year/${encodeURIComponent(financialYear)}?confirm=true`,
      {
        method: 'DELETE',
        headers: this.headers(),
      }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to delete financial year data (${res.status})`);
    }
    return await res.json();
  }

  async deleteAccount(): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/lifecycle/account?confirm=true`, {
      method: 'DELETE',
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to erase account (${res.status})`);
    }
    this.clearToken();
    return await res.json();
  }

  // ==========================================
  // BYOK (Bring Your Own Key) (v1.2)
  // ==========================================

  async validateBYOK(payload: BYOKValidateRequest): Promise<BYOKValidateResponse> {
    const res = await fetch(`${API_BASE}/byok/validate`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Validation failed (${res.status})`);
    }
    return await res.json();
  }

  async saveBYOK(payload: BYOKSaveRequest): Promise<BYOKConfig> {
    const res = await fetch(`${API_BASE}/byok`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to save API key (${res.status})`);
    }
    return await res.json();
  }

  async getBYOK(): Promise<BYOKConfig> {
    // Check if local storage mode is active first
    const localByok = localStorage.getItem('taxplanner_byok_local');
    if (localByok) {
      try {
        const parsed = JSON.parse(localByok);
        if (parsed.api_key) {
          const raw = String(parsed.api_key);
          const masked = raw.length > 8 ? `${raw.slice(0, 7)}••••••••${raw.slice(-4)}` : '••••••••';
          return {
            has_key: true,
            provider: parsed.provider,
            model_name: parsed.model_name,
            masked_key: masked,
            custom_base_url: parsed.custom_base_url,
            is_active: true,
            storage_mode: 'local',
          };
        }
      } catch {}
    }

    const res = await fetch(`${API_BASE}/byok`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to load BYOK configuration (${res.status})`);
    }
    const data = await res.json();
    return { ...data, storage_mode: data.has_key ? 'vault' : undefined };
  }

  async deleteBYOK(): Promise<{ success: boolean; message: string }> {
    // Remove local browser storage if present
    localStorage.removeItem('taxplanner_byok_local');

    const res = await fetch(`${API_BASE}/byok`, {
      method: 'DELETE',
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to delete BYOK configuration (${res.status})`);
    }
    return await res.json();
  }

  // ============================================================================
  // Taxpayer Profiles & Household Hub (Multi-Taxpayer Switcher)
  // ============================================================================

  setActiveProfileId(id: number | null) {
    if (id !== null) {
      localStorage.setItem('taxplanner_active_profile_id', String(id));
    } else {
      localStorage.removeItem('taxplanner_active_profile_id');
    }
  }

  getActiveProfileId(): number | null {
    const id = localStorage.getItem('taxplanner_active_profile_id');
    return id ? parseInt(id, 10) : null;
  }

  async getProfiles(): Promise<TaxpayerProfile[]> {
    const res = await fetch(`${API_BASE}/profiles`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to load taxpayer profiles');
    }
    return await res.json();
  }

  async createProfile(payload: Partial<TaxpayerProfile>): Promise<TaxpayerProfile> {
    const res = await fetch(`${API_BASE}/profiles`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create taxpayer profile');
    }
    return await res.json();
  }

  async updateProfile(id: number, payload: Partial<TaxpayerProfile>): Promise<TaxpayerProfile> {
    const res = await fetch(`${API_BASE}/profiles/${id}`, {
      method: 'PUT',
      headers: this.headers(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update taxpayer profile');
    }
    return await res.json();
  }

  async deleteProfile(id: number): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/profiles/${id}`, {
      method: 'DELETE',
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete taxpayer profile');
    }
    return await res.json();
  }

  async getProfileReadiness(): Promise<ProfileReadinessResponse> {
    const res = await fetch(`${API_BASE}/profiles/readiness`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to load filing readiness scorecard');
    }
    return await res.json();
  }

  async getHouseholdSummary(): Promise<HouseholdSummaryResponse> {
    const res = await fetch(`${API_BASE}/profiles/household-summary`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to compute household tax summary');
    }
    return await res.json();
  }
}

export const api = new ApiClient();
