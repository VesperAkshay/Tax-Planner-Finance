import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test.describe.serial('Tax Planner v1.1 End-to-End Test Suite', () => {
  const timestamp = Date.now();
  const apiTestEmail = `e2e_api_${timestamp}@taxplanner.internal`;
  const apiTestPassword = 'Password123!';
  const apiTestName = `E2E Taxpayer ${timestamp}`;

  let authToken = '';

  test.beforeAll(async ({ request }) => {
    // Fast, deterministic API registration for test session
    const res = await request.post('http://127.0.0.1:8000/api/v1/auth/register', {
      data: {
        email: apiTestEmail,
        password: apiTestPassword,
        full_name: apiTestName,
        pan: 'ABCDE1234F',
        is_active: true,
      },
    });
    expect(res.ok()).toBeTruthy();
    const json = await res.json();
    authToken = json.access_token;

    // Ingest FY 2025-26 salary slip so Tab 6 has live calculated tax figures
    const fixturePath = path.resolve(__dirname, '../../data/test_fixtures/complex_salary_slip_may_2025.pdf');
    if (fs.existsSync(fixturePath)) {
      const fileBuffer = fs.readFileSync(fixturePath);
      const slipRes = await request.post('http://127.0.0.1:8000/api/v1/upload/salary-slip', {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
        multipart: {
          file: {
            name: 'complex_salary_slip_may_2025.pdf',
            mimeType: 'application/pdf',
            buffer: fileBuffer,
          },
          month: '5',
          year: '2025',
        },
      });
      expect(slipRes.ok()).toBeTruthy();
    }
  });

  test('01: Landing Page renders correctly with Neo-Brutalist branding', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForLoadState('domcontentloaded');

    // Title & Brand Check
    await expect(page).toHaveTitle(/TaxPlanner/i);
    await expect(page.getByText('STOP GUESSING TAXES.')).toBeVisible();
    await expect(page.getByText('MAXIMIZE REBATE.')).toBeVisible();
    await expect(page.getByText('TAX FACTS')).toBeVisible();
    await expect(page.getByText('100% DETERMINISTIC CALCULATION')).toBeVisible();

    // CTA buttons exist
    const openVaultBtn = page.getByRole('button', { name: /OPEN YOUR TAX VAULT/i });
    await expect(openVaultBtn).toBeVisible();
  });

  test('02: User Registration and Authentication UI Flow', async ({ page }) => {
    const uiEmail = `ui_${Date.now()}@taxplanner.internal`;
    const uiName = `UI User ${Date.now()}`;

    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForLoadState('domcontentloaded');

    // Open Auth Modal
    const openVaultBtn = page.getByRole('button', { name: /OPEN YOUR TAX VAULT/i });
    await openVaultBtn.click();

    // Verify Modal appears
    await expect(page.getByText(/SECURE AUTH/i)).toBeVisible();

    // Switch to Register Mode
    const registerTabBtn = page.getByRole('button', { name: /CREATE NEW ACCOUNT/i });
    await registerTabBtn.click();

    // Fill in registration form
    await page.getByPlaceholder(/e\.g\. Vikram Sharma/i).fill(uiName);
    await page.locator('input[type="email"]').fill(uiEmail);
    await page.locator('input[type="password"]').fill('Password123!');
    await page.getByPlaceholder(/e\.g\. ABCDE1234F/i).fill('ABCDE9999Z');

    // Submit
    const submitBtn = page.getByRole('button', { name: /INITIALIZE REAL VAULT/i });
    await submitBtn.click();

    // Verify authenticated state
    await expect(page.getByText('ACTIVE VAULT')).toBeVisible();
    await expect(page.getByText(uiName)).toBeVisible();
    await expect(page.getByText('VAULT DATA')).toBeVisible();
  });

  test('03: Tab 1 (Ingest Docs) - Custom Bank CSV Mapping Form', async ({ page }) => {
    // Inject auth token and navigate
    await page.addInitScript((token) => {
      localStorage.setItem('taxplanner_token', token);
    }, authToken);

    await page.goto('/');
    await expect(page.getByText('ACTIVE VAULT')).toBeVisible();

    // Verify Tab 1 (Ingest Docs) heading
    await expect(page.getByText('INGEST STATEMENTS & SALARY SLIPS')).toBeVisible();

    // Switch bank format dropdown to Custom Format
    const formatSelect = page.locator('select').first();
    await formatSelect.selectOption('custom');

    // Verify Custom Bank CSV Mapping configuration UI appears
    await expect(page.getByText(/CUSTOM CSV COLUMN MAPPING/i)).toBeVisible();
    await expect(page.getByText(/Date Col:/i)).toBeVisible();
    await expect(page.getByText(/Narration Col:/i)).toBeVisible();
    await expect(page.getByText(/Single Amount \(Balance Delta\)/i)).toBeVisible();
  });

  test('04: Tab 4 (Deduction Catalog) - 18 Statutory Sections & Declaration Flow', async ({ page }) => {
    await page.addInitScript((token) => {
      localStorage.setItem('taxplanner_token', token);
    }, authToken);

    await page.goto('/');
    await expect(page.getByText('ACTIVE VAULT')).toBeVisible();

    // Navigate to Tab 4
    await page.getByRole('button', { name: /4\. Deduction Catalog/i }).click();

    // Verify Catalog Heading and KPIs
    await expect(page.getByText('STATUTORY DEDUCTION CATALOG')).toBeVisible();
    await expect(page.getByText('TOTAL SECTIONS AVAILABLE')).toBeVisible();
    await expect(page.getByText('18 Official Statutory Clauses')).toBeVisible();

    // Verify sections are listed
    await expect(page.getByText('SEC 80C', { exact: true })).toBeVisible();
    await expect(page.getByText('SEC 80D', { exact: true }).first()).toBeVisible();

    // Search filter test: type '80CCD'
    const searchInput = page.getByPlaceholder(/Search section/i);
    await searchInput.fill('80CCD');
    await expect(page.getByText('SEC 80CCD(1B)', { exact: true })).toBeVisible();

    // Clear search
    await searchInput.fill('');

    // Checkpoint confirmation button
    const confirmBtn = page.getByRole('button', { name: /CONFIRM CATALOG REVIEWED/i });
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click();
      await expect(page.getByText(/CHECKPOINT SATISFIED/i)).toBeVisible();
    }
  });

  test('05: Tab 5 (Mr. Planner) - Proactive Elicitation Quick Chips', async ({ page }) => {
    await page.addInitScript((token) => {
      localStorage.setItem('taxplanner_token', token);
    }, authToken);

    await page.goto('/');
    await expect(page.getByText('ACTIVE VAULT')).toBeVisible();

    // Navigate to Tab 5
    await page.getByRole('button', { name: /5\. Mr\. Planner/i }).click();

    // Verify chat UI and Mr. Planner branding
    await expect(page.getByText(/MR\. PLANNER/i).first()).toBeVisible();

    // Verify quick action chips
    await expect(page.getByRole('button', { name: /Not Applicable \(₹0\)/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Claim Maximum Cap/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Calculate Tax/i }).first()).toBeVisible();

    // Verify quick replies label and topics
    await expect(page.getByText(/QUICK REPLIES:/i)).toBeVisible();
    await expect(page.getByText(/TOPICS:/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /🏠 Rent & HRA/i })).toBeVisible();
    await expect(page.getByPlaceholder(/Ask about 80C, 80D, rent HRA/i)).toBeVisible();
  });

  test('06: Tab 6 (Tax Report) - Real-World Compliance & YoY Comparison', async ({ page }) => {
    await page.addInitScript((token) => {
      localStorage.setItem('taxplanner_token', token);
    }, authToken);

    await page.goto('/');
    await expect(page.getByText('ACTIVE VAULT')).toBeVisible();

    // Navigate to Tab 6
    await page.getByRole('button', { name: /6\. Final Tax Report/i }).click();

    // Verify Filing Deadline countdown badge
    await expect(page.getByText(/ITR STATUTORY FILING DEADLINE/i)).toBeVisible();
    await expect(page.getByText(/DAYS REMAINING/i).first()).toBeVisible();

    // Verify Regime Comparison cards
    await expect(page.getByText(/NEW REGIME \(SEC 115BAC\)/i).first()).toBeVisible();
    await expect(page.getByText(/OLD TAX REGIME/i).first()).toBeVisible();

    // Verify Pre-Filing AIS & 26AS Statutory Reconciliation
    await expect(page.getByText(/AIS & FORM 26AS PRE-FILING STATUTORY RECONCILIATION/i)).toBeVisible();

    // Switch to Year-over-Year tab
    const yoyTabBtn = page.getByRole('button', { name: /YEAR-OVER-YEAR/i });
    await yoyTabBtn.click();
    await expect(page.getByText(/MULTI-YEAR TAX & FINANCIAL PROGRESSION/i)).toBeVisible();

    // PDF Download Button presence
    const pdfDownloadBtn = page.getByRole('button', { name: /DOWNLOAD TAX INVOICE \(PDF\)/i });
    await expect(pdfDownloadBtn).toBeVisible();
  });

  test('07: Vault Data & Lifecycle Modal Controls', async ({ page }) => {
    await page.addInitScript((token) => {
      localStorage.setItem('taxplanner_token', token);
    }, authToken);

    await page.goto('/');
    await expect(page.getByText('ACTIVE VAULT')).toBeVisible();

    // Click VAULT DATA button in Navbar
    await page.getByRole('button', { name: /VAULT DATA/i }).click();

    // Verify Lifecycle Modal opens
    await expect(page.getByText(/SECURE DATA VAULT & LIFECYCLE MANAGEMENT/i)).toBeVisible();
    await expect(page.getByText(/EXPORT COMPLETE DATA ARCHIVE/i)).toBeVisible();
    await expect(page.getByText(/DELETE SPECIFIC STATEMENT UPLOAD/i)).toBeVisible();
    await expect(page.getByText(/RESET FINANCIAL YEAR DATA/i)).toBeVisible();
    await expect(page.getByText(/PERMANENT ACCOUNT & DATA PURGE/i)).toBeVisible();

    // Close Modal
    await page.getByRole('button', { name: /CLOSE VAULT/i }).click();
    await expect(page.getByText(/SECURE DATA VAULT & LIFECYCLE MANAGEMENT/i)).not.toBeVisible();
  });
});
