import type {
  FinancialSnapshot,
  ReconciliationFlag,
  StatementUploadResponse,
  SalarySlipUploadResponse,
  TaxComparisonReport,
  User,
} from '../types';

const API_BASE = '/api/v1';

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

  async uploadStatement(file: File, bankFormat?: string): Promise<StatementUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (bankFormat && bankFormat !== 'auto') {
      formData.append('bank_format', bankFormat);
    }

    const res = await fetch(`${API_BASE}/upload/statement`, {
      method: 'POST',
      headers: this.headers(true),
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Statement upload failed (${res.status})`);
    }
    return await res.json();
  }

  async uploadSalarySlip(file: File, month?: number, year?: number): Promise<SalarySlipUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (month) formData.append('month', String(month));
    if (year) formData.append('year', String(year));

    const res = await fetch(`${API_BASE}/upload/salary-slip`, {
      method: 'POST',
      headers: this.headers(true),
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Salary slip upload failed (${res.status})`);
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
}

export const api = new ApiClient();
