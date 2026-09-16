import React, { useState } from 'react';
import {
  Upload,
  FileSpreadsheet,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
import type { StatementUploadResponse, SalarySlipUploadResponse } from '../types';

interface UploadViewProps {
  onUploadSuccess: () => void;
}

export const UploadView: React.FC<UploadViewProps> = ({ onUploadSuccess }) => {
  const [statementFile, setStatementFile] = useState<File | null>(null);
  const [bankFormat, setBankFormat] = useState<string>('auto');
  const [salaryFile, setSalaryFile] = useState<File | null>(null);
  const [salaryMonth, setSalaryMonth] = useState<number>(10);
  const [salaryYear, setSalaryYear] = useState<number>(2025);

  const [isUploadingStmt, setIsUploadingStmt] = useState(false);
  const [isUploadingSalary, setIsUploadingSalary] = useState(false);

  const [stmtResult, setStmtResult] = useState<StatementUploadResponse | null>(null);
  const [salaryResult, setSalaryResult] = useState<SalarySlipUploadResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleUploadStatement = async () => {
    if (!statementFile) return;
    setIsUploadingStmt(true);
    setErrorMsg(null);
    try {
      const res = await api.uploadStatement(
        statementFile,
        bankFormat === 'auto' ? undefined : bankFormat
      );
      setStmtResult(res);
      onUploadSuccess();
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setIsUploadingStmt(false);
    }
  };

  const handleUploadSalarySlip = async () => {
    if (!salaryFile) return;
    setIsUploadingSalary(true);
    setErrorMsg(null);
    try {
      const res = await api.uploadSalarySlip(salaryFile, salaryMonth, salaryYear);
      setSalaryResult(res);
      onUploadSuccess();
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setIsUploadingSalary(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero Banner with Neo-Brutalist Sticker Graphics */}
      <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000] relative overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div className="inline-flex items-center gap-2 bg-[#FACC15] px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase">
            <Sparkles className="w-4 h-4" />
            <span>DOCUMENT INTAKE // VERIFIED FINANCIAL PARSER</span>
          </div>
          <div className="font-mono text-xs font-bold text-gray-700 bg-white px-3 py-1 border border-black shadow-[2px_2px_0px_0px_#000]">
            SECURE DOCUMENT INGESTION
          </div>
        </div>

        <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none mb-3">
          INGEST STATEMENTS &amp; SALARY SLIPS
        </h2>
        <p className="text-sm md:text-base font-medium text-gray-800 max-w-2xl leading-relaxed font-['Plus_Jakarta_Sans']">
          Intelligent document intake reads multi-bank statements, extracts salary slip components, and
          checks balance continuity within ₹1.00 tolerance.
        </p>
      </div>

      {errorMsg && (
        <div className="bg-red-100 border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000] text-red-900 font-bold flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Grid: Statement Upload & Salary Slip Upload */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Card 1: Bank Statement */}
        <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000000] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b-2 border-black pb-3 mb-4">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="w-6 h-6 text-[#3730A3]" />
                <h3 className="font-black text-lg tracking-wide uppercase font-['Space_Grotesk']">
                  1. Bank Statement
                </h3>
              </div>
              <span className="bg-[#F59E0B] text-black text-xs font-mono font-bold px-2 py-0.5 border border-black">
                CSV / PDF
              </span>
            </div>

            <p className="text-xs text-gray-700 mb-4 font-semibold">
              Supported banks: HDFC, ICICI, SBI, Axis, or auto-detected formats.
            </p>

            <div className="mb-4">
              <label className="block text-xs font-black uppercase tracking-wider text-gray-700 mb-1">
                Bank Adapter / Format:
              </label>
              <select
                value={bankFormat}
                onChange={(e) => setBankFormat(e.target.value)}
                className="w-full bg-[#FAF7F2] border-2 border-black p-2 font-mono font-bold text-xs shadow-[2px_2px_0px_0px_#000] outline-none"
              >
                <option value="auto">Auto-Detect Format (Recommended)</option>
                <option value="hdfc">HDFC Bank</option>
                <option value="icici">ICICI Bank</option>
                <option value="sbi">State Bank of India (SBI)</option>
                <option value="axis">Axis Bank</option>
              </select>
            </div>

            {/* Brutalist File Dropzone */}
            <div className="border-3 border-dashed border-black bg-[#FAF7F2] p-6 text-center shadow-[3px_3px_0px_0px_#000] mb-4 relative">
              <input
                type="file"
                accept=".csv,.pdf"
                onChange={(e) => setStatementFile(e.target.files?.[0] || null)}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
              <Upload className="w-8 h-8 mx-auto text-[#3730A3] mb-2" />
              <p className="font-black text-sm uppercase">
                {statementFile ? statementFile.name : 'DRAG & DROP BANK STATEMENT OR CLICK'}
              </p>
              <p className="text-xs text-gray-600 font-mono mt-1">
                {statementFile ? `${(statementFile.size / 1024).toFixed(1)} KB` : 'CSV or PDF up to 25MB'}
              </p>
            </div>
          </div>

          <button
            onClick={handleUploadStatement}
            disabled={!statementFile || isUploadingStmt}
            className={`w-full py-3 border-3 border-black font-black text-sm tracking-wider uppercase flex items-center justify-center gap-2 transition-all ${
              !statementFile || isUploadingStmt
                ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                : 'bg-[#FACC15] text-black shadow-[4px_4px_0px_0px_#000] hover:shadow-[5px_5px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none'
            }`}
          >
            {isUploadingStmt ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>PARSING &amp; RECONCILING...</span>
              </>
            ) : (
              <>
                <span>PARSE STATEMENT</span>
                <ArrowRight className="w-4 h-4 stroke-[3]" />
              </>
            )}
          </button>
        </div>

        {/* Card 2: Salary Slip */}
        <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000000] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b-2 border-black pb-3 mb-4">
              <div className="flex items-center gap-2">
                <FileText className="w-6 h-6 text-[#F59E0B]" />
                <h3 className="font-black text-lg tracking-wide uppercase font-['Space_Grotesk']">
                  2. Salary Slip
                </h3>
              </div>
              <span className="bg-[#3730A3] text-white text-xs font-mono font-bold px-2 py-0.5 border border-black">
                PDF / PNG
              </span>
            </div>

            <p className="text-xs text-gray-700 mb-4 font-semibold">
              Extracts Basic Pay, HRA, Provident Fund, Professional Tax, and TDS.
            </p>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-xs font-black uppercase text-gray-700 mb-1">
                  Salary Month:
                </label>
                <select
                  value={salaryMonth}
                  onChange={(e) => setSalaryMonth(Number(e.target.value))}
                  className="w-full bg-[#FAF7F2] border-2 border-black p-2 font-mono font-bold text-xs shadow-[2px_2px_0px_0px_#000] outline-none"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                    <option key={m} value={m}>
                      Month {m} ({new Date(2025, m - 1).toLocaleString('default', { month: 'short' })})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-black uppercase text-gray-700 mb-1">
                  Financial Year:
                </label>
                <input
                  type="number"
                  value={salaryYear}
                  onChange={(e) => setSalaryYear(Number(e.target.value))}
                  className="w-full bg-[#FAF7F2] border-2 border-black p-2 font-mono font-bold text-xs shadow-[2px_2px_0px_0px_#000] outline-none"
                />
              </div>
            </div>

            {/* Dropzone */}
            <div className="border-3 border-dashed border-black bg-[#FAF7F2] p-6 text-center shadow-[3px_3px_0px_0px_#000] mb-4 relative">
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => setSalaryFile(e.target.files?.[0] || null)}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
              <Upload className="w-8 h-8 mx-auto text-[#F59E0B] mb-2" />
              <p className="font-black text-sm uppercase">
                {salaryFile ? salaryFile.name : 'DRAG & DROP SALARY SLIP OR CLICK'}
              </p>
              <p className="text-xs text-gray-600 font-mono mt-1">
                {salaryFile ? `${(salaryFile.size / 1024).toFixed(1)} KB` : 'PDF or Scanned Image'}
              </p>
            </div>
          </div>

          <button
            onClick={handleUploadSalarySlip}
            disabled={!salaryFile || isUploadingSalary}
            className={`w-full py-3 border-3 border-black font-black text-sm tracking-wider uppercase flex items-center justify-center gap-2 transition-all ${
              !salaryFile || isUploadingSalary
                ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                : 'bg-[#F59E0B] text-black shadow-[4px_4px_0px_0px_#000] hover:shadow-[5px_5px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none'
            }`}
          >
            {isUploadingSalary ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>EXTRACTING SALARY DETAILS...</span>
              </>
            ) : (
              <>
                <span>PARSE SALARY SLIP</span>
                <ArrowRight className="w-4 h-4 stroke-[3]" />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Real-time Ingestion & Reconciliation Status (Task 8.2) */}
      {(stmtResult || salaryResult) && (
        <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[8px_8px_0px_0px_#000000]">
          <div className="flex items-center gap-3 border-b-3 border-black pb-3 mb-6">
            <ShieldCheck className="w-7 h-7 text-emerald-600 stroke-[2.5]" />
            <div>
              <h3 className="font-black text-xl uppercase font-['Space_Grotesk'] tracking-tight">
                INGESTION &amp; PARSER STATUS
              </h3>
              <p className="text-xs font-mono text-gray-700">
                Verified against parsed document records and balance reconciliation engine.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
            {stmtResult && (
              <>
                <div className="bg-[#FAF7F2] border-2 border-black p-3 shadow-[3px_3px_0px_0px_#000]">
                  <span className="text-[10px] uppercase font-bold text-gray-600 block">
                    TRANSACTIONS PARSED
                  </span>
                  <span className="text-2xl font-black text-[#3730A3]">
                    {stmtResult.transactions_parsed}
                  </span>
                </div>

                <div className="bg-[#FAF7F2] border-2 border-black p-3 shadow-[3px_3px_0px_0px_#000]">
                  <span className="text-[10px] uppercase font-bold text-gray-600 block">
                    PARSE CONFIDENCE
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-black text-black">
                      {(stmtResult.parse_confidence * 100).toFixed(1)}%
                    </span>
                    <span className="bg-emerald-300 text-emerald-950 text-[10px] font-black px-1.5 py-0.5 border border-black">
                      HIGH
                    </span>
                  </div>
                </div>

                <div className="bg-[#FAF7F2] border-2 border-black p-3 shadow-[3px_3px_0px_0px_#000]">
                  <span className="text-[10px] uppercase font-bold text-gray-600 block">
                    BALANCE RECONCILED
                  </span>
                  <div className="flex items-center gap-1.5 mt-1">
                    {stmtResult.balance_reconciled ? (
                      <>
                        <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                        <span className="font-black text-sm text-emerald-900">VERIFIED (Δ ≤ ₹1.00)</span>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-5 h-5 text-amber-600" />
                        <span className="font-black text-sm text-amber-900">DISCREPANCY DETECTED</span>
                      </>
                    )}
                  </div>
                </div>
              </>
            )}

            {salaryResult && (
              <div className="bg-[#FAF7F2] border-2 border-black p-3 shadow-[3px_3px_0px_0px_#000]">
                <span className="text-[10px] uppercase font-bold text-gray-600 block">
                  MONTHLY NET PAY
                </span>
                <span className="text-2xl font-black text-[#F59E0B]">
                  ₹{salaryResult.net_pay.toLocaleString('en-IN')}
                </span>
                <span className="text-[10px] block text-gray-600 font-bold">
                  Basic: ₹{(salaryResult.basic_pay || 0).toLocaleString('en-IN')} | HRA: ₹{(salaryResult.hra || 0).toLocaleString('en-IN')}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
