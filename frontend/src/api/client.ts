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

    const res = await fetch(`${API_BASE}/statement`, {
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

    const res = await fetch(`${API_BASE}/salary-slip`, {
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

  async getReconciliationFlags(): Promise<ReconciliationFlag[]> {
    const res = await fetch(`${API_BASE}/flags`, {
      headers: this.headers(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch reconciliation flags (${res.status})`);
    }
    return await res.json();
  }

  async resolveFlag(
    flagId: number,
    resolution: string,
    note?: string
  ): Promise<{ success: boolean; flag: ReconciliationFlag }> {
    const res = await fetch(`${API_BASE}/flags/${flagId}/resolve`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ resolution, note }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to resolve flag (${res.status})`);
    }
    return await res.json();
  }

  async sendChatMessage(
    message: string,
    history: { role: string; content: string }[]
  ): Promise<{ reply: string; deductions_updated?: Record<string, number> }> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ message, history }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Agent communication failed (${res.status})`);
    }
    return await res.json();
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
}

export const api = new ApiClient();
