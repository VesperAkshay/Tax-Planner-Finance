import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  FileSpreadsheet,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Sparkles,
  Lock,
  Trash2,
  Plus,
  Check,
  ChevronDown,
  ChevronUp,
  FolderOpen,
  KeyRound,
  FileQuestion,
} from 'lucide-react';
import { api } from '../api/client';
import type { StatementUploadResponse, SalarySlipUploadResponse } from '../types';
import { UploadedFilesVault } from './UploadedFilesVault';

interface UploadViewProps {
  onUploadSuccess: () => void;
  onNavigateTab?: (tab: string) => void;
}

interface StagedDocument {
  id: string;
  file: File;
  detectedType: 'auto' | 'bank_statement' | 'salary_slip';
  status: 'idle' | 'uploading' | 'needs_password' | 'success' | 'error';
  passwordInput: string;
  errorMessage?: string;
  statementResult?: StatementUploadResponse;
  salaryResult?: SalarySlipUploadResponse;
}

function detectDocumentType(fileName: string): 'auto' | 'bank_statement' | 'salary_slip' {
  const nameLower = fileName.toLowerCase();
  if (nameLower.endsWith('.csv')) {
    return 'bank_statement';
  }
  if (
    nameLower.includes('salary') ||
    nameLower.includes('payslip') ||
    nameLower.includes('pay_slip') ||
    nameLower.includes('pay-slip') ||
    nameLower.includes('wage') ||
    nameLower.includes('earnings') ||
    nameLower.includes('form16') ||
    nameLower.includes('form_16')
  ) {
    return 'salary_slip';
  }
  if (
    nameLower.includes('statement') ||
    nameLower.includes('stmt') ||
    nameLower.includes('passbook') ||
    nameLower.includes('bank') ||
    nameLower.includes('account_statement') ||
    nameLower.includes('ledger') ||
    nameLower.includes('hdfc') ||
    nameLower.includes('icici') ||
    nameLower.includes('sbi') ||
    nameLower.includes('axis') ||
    nameLower.includes('kotak')
  ) {
    return 'bank_statement';
  }
  return 'auto';
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const UploadView: React.FC<UploadViewProps> = ({ onUploadSuccess, onNavigateTab }) => {
  const [queue, setQueue] = useState<StagedDocument[]>([]);
  const [isBatchUploading, setIsBatchUploading] = useState(false);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [refreshVaultCounter, setRefreshVaultCounter] = useState(0);
  const [globalBanner, setGlobalBanner] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // User Profile Metadata for 1-click password autofill
  const [profilePan, setProfilePan] = useState<string>('');

  // Advanced Custom CSV Column Mapping drawer state
  const [showAdvancedMapper, setShowAdvancedMapper] = useState(false);
  const [bankFormat, setBankFormat] = useState<string>('auto');
  const [customDateCol, setCustomDateCol] = useState('Date');
  const [customNarrationCol, setCustomNarrationCol] = useState('Narration');
  const [customSignMode, setCustomSignMode] = useState<'separate' | 'single'>('separate');
  const [customDebitCol, setCustomDebitCol] = useState('Debit');
  const [customCreditCol, setCustomCreditCol] = useState('Credit');
  const [customAmountCol, setCustomAmountCol] = useState('Amount');
  const [customBalanceCol, setCustomBalanceCol] = useState('Balance');

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    // Attempt to load current user PAN for smart password suggestions
    api.getCurrentUser().then((user) => {
      if (user?.pan) {
        setProfilePan(user.pan.toUpperCase());
      }
    }).catch(() => {});
  }, []);

  const handleAddFiles = (incomingFiles: FileList | File[]) => {
    const newItems: StagedDocument[] = Array.from(incomingFiles).map((file, idx) => ({
      id: `${Date.now()}-${idx}-${file.name}`,
      file,
      detectedType: detectDocumentType(file.name),
      status: 'idle',
      passwordInput: '',
    }));

    setQueue((prev) => [...prev, ...newItems]);
    setGlobalBanner(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleAddFiles(e.dataTransfer.files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(true);
  };

  const handleDragLeave = () => {
    setIsDraggingOver(false);
  };

  const handleRemoveItem = (id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const updateItem = (id: string, partial: Partial<StagedDocument>) => {
    setQueue((prev) =>
      prev.map((item) => (item.id === id ? { ...item, ...partial } : item))
    );
  };

  const processSingleDocument = async (item: StagedDocument, customPassword?: string): Promise<boolean> => {
    updateItem(item.id, { status: 'uploading', errorMessage: undefined });
    const pwd = customPassword !== undefined ? customPassword : (item.passwordInput.trim() || undefined);

    let mappingPayload: Record<string, string> | undefined = undefined;
    if (bankFormat === 'custom') {
      mappingPayload = {
        date: customDateCol.trim(),
        description: customNarrationCol.trim(),
      };
      if (customSignMode === 'separate') {
        if (customDebitCol.trim()) mappingPayload.debit = customDebitCol.trim();
        if (customCreditCol.trim()) mappingPayload.credit = customCreditCol.trim();
      } else {
        if (customAmountCol.trim()) mappingPayload.amount = customAmountCol.trim();
      }
      if (customBalanceCol.trim()) mappingPayload.balance = customBalanceCol.trim();
    }

    try {
      if (item.detectedType === 'bank_statement') {
        const res = await api.uploadStatement(
          item.file,
          bankFormat === 'auto' || bankFormat === 'custom' ? undefined : bankFormat,
          mappingPayload,
          true,
          pwd
        );
        updateItem(item.id, {
          status: 'success',
          statementResult: res,
        });
        return true;
      } else if (item.detectedType === 'salary_slip') {
        const res = await api.uploadSalarySlip(item.file, undefined, undefined, pwd);
        updateItem(item.id, {
          status: 'success',
          salaryResult: res,
        });
        return true;
      } else {
        // Auto-detect endpoint
        const unified = await api.uploadAutoDocument(item.file, pwd, bankFormat === 'auto' ? undefined : bankFormat, true);
        if (unified.document_type === 'salary_slip' && unified.salary_slip) {
          updateItem(item.id, {
            status: 'success',
            detectedType: 'salary_slip',
            salaryResult: unified.salary_slip,
          });
        } else if (unified.statement) {
          updateItem(item.id, {
            status: 'success',
            detectedType: 'bank_statement',
            statementResult: unified.statement,
          });
        } else {
          updateItem(item.id, { status: 'success' });
        }
        return true;
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Upload failed';
      const msgLower = msg.toLowerCase();

      if (msgLower.includes('password_required') || msgLower.includes('password-protected') || msgLower.includes('encrypted')) {
        updateItem(item.id, {
          status: 'needs_password',
          errorMessage: '🔒 Password-Protected PDF: Please enter document password to unlock.',
        });
      } else if (msgLower.includes('invalid_password') || msgLower.includes('incorrect password')) {
        updateItem(item.id, {
          status: 'needs_password',
          errorMessage: '❌ Incorrect password. Please check and try again.',
        });
      } else if (msgLower.includes('duplicate') || msgLower.includes('409')) {
        updateItem(item.id, {
          status: 'error',
          errorMessage: '📋 Duplicate File: This exact document was already ingested.',
        });
      } else if (msgLower.includes('non_financial') || msgLower.includes('unrecognized')) {
        updateItem(item.id, {
          status: 'error',
          errorMessage: '🛑 Non-Financial Document: File headers do not match bank statements or payslips.',
        });
      } else {
        updateItem(item.id, {
          status: 'error',
          errorMessage: msg,
        });
      }
      return false;
    }
  };

  const handleUploadAll = async () => {
    const pendingItems = queue.filter((item) => item.status === 'idle' || item.status === 'error');
    if (pendingItems.length === 0) return;

    setIsBatchUploading(true);
    setGlobalBanner(null);

    let successCount = 0;
    let failedCount = 0;

    for (const item of pendingItems) {
      const ok = await processSingleDocument(item);
      if (ok) successCount++;
      else failedCount++;
    }

    setIsBatchUploading(false);
    setRefreshVaultCounter((c) => c + 1);
    onUploadSuccess();

    if (failedCount === 0 && successCount > 0) {
      setGlobalBanner({
        type: 'success',
        message: `🎉 All ${successCount} document${successCount > 1 ? 's' : ''} parsed and ingested successfully! Ready for harvesting.`,
      });
    } else if (successCount > 0 && failedCount > 0) {
      setGlobalBanner({
        type: 'success',
        message: `Processed ${successCount} document${successCount > 1 ? 's' : ''}. ${failedCount} item${failedCount > 1 ? 's' : ''} require attention (e.g. password unlock).`,
      });
    }
  };

  const handleUnlockAndRetry = async (item: StagedDocument) => {
    const ok = await processSingleDocument(item, item.passwordInput);
    if (ok) {
      setRefreshVaultCounter((c) => c + 1);
      onUploadSuccess();
    }
  };

  const handleAutofillPan = (item: StagedDocument) => {
    if (profilePan) {
      updateItem(item.id, { passwordInput: profilePan });
    }
  };

  const clearCompleted = () => {
    setQueue((prev) => prev.filter((item) => item.status !== 'success'));
  };

  // Metrics for parsed documents in active session
  const totalSuccess = queue.filter((q) => q.status === 'success');
  const parsedStatements = queue.filter((q) => q.status === 'success' && q.statementResult);
  const parsedSalaries = queue.filter((q) => q.status === 'success' && q.salaryResult);
  const totalTxns = parsedStatements.reduce(
    (acc, curr) => acc + (curr.statementResult?.transactions_count || curr.statementResult?.transactions_parsed || 0),
    0
  );

  return (
    <div className="space-y-8">
      {/* Header Banner with Neo-Brutalist Accents */}
      <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000] relative overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div className="inline-flex items-center gap-2 bg-[#FACC15] px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase">
            <Sparkles className="w-4 h-4" />
            <span>SMART INTAKE 2.0 // ZERO MANUAL OVERHEAD</span>
          </div>
          <div className="font-mono text-xs font-bold text-gray-700 bg-white px-3 py-1 border border-black shadow-[2px_2px_0px_0px_#000]">
            MULTI-FILE BATCH &amp; IN-MEMORY UNLOCK
          </div>
        </div>

        <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none mb-3">
          UNIFIED DOCUMENT INTAKE HUB
        </h2>
        <p className="text-sm md:text-base font-medium text-gray-800 max-w-3xl leading-relaxed font-['Plus_Jakarta_Sans']">
          Drop all 12 monthly salary slips and multi-bank statements together. The parser automatically detects pay periods, unlocks password-protected PDFs in memory, extracts compensation components, and primes your data for the <strong>Bank Deduction Harvester</strong>.
        </p>
      </div>

      {/* Global Notice Banner */}
      {globalBanner && (
        <div
          className={`p-4 border-3 border-black font-mono font-bold shadow-[4px_4px_0px_0px_#000] flex items-center gap-3 ${
            globalBanner.type === 'success'
              ? 'bg-emerald-100 text-emerald-950 border-emerald-950'
              : 'bg-red-100 text-red-950 border-red-950'
          }`}
        >
          {globalBanner.type === 'success' ? (
            <CheckCircle2 className="w-6 h-6 flex-shrink-0 text-emerald-700 stroke-[2.5]" />
          ) : (
            <AlertTriangle className="w-6 h-6 flex-shrink-0 text-red-700 stroke-[2.5]" />
          )}
          <span className="text-sm">{globalBanner.message}</span>
        </div>
      )}

      {/* Unified Drag & Drop Ingestion Box */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`border-4 border-dashed p-8 md:p-12 text-center transition-all cursor-pointer relative ${
          isDraggingOver
            ? 'bg-[#FEF08A] border-[#18153B] scale-[1.01] shadow-[8px_8px_0px_0px_#000]'
            : 'bg-[#FFFDF9] border-black hover:bg-[#FAF7F2] shadow-[6px_6px_0px_0px_#000]'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.csv,.png,.jpg,.jpeg"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleAddFiles(e.target.files);
            }
          }}
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center pointer-events-none">
          <div className="w-16 h-16 bg-[#FACC15] border-3 border-black shadow-[4px_4px_0px_0px_#000] flex items-center justify-center mb-4 text-[#18153B]">
            <Upload className="w-8 h-8 stroke-[2.5]" />
          </div>

          <h3 className="font-['Space_Grotesk'] font-black text-xl md:text-2xl uppercase text-[#18153B] mb-2 tracking-tight">
            DRAG &amp; DROP ALL TAX DOCUMENTS HERE
          </h3>
          <p className="font-mono text-xs md:text-sm text-gray-700 max-w-xl mb-4 font-semibold">
            Drop Bank Statements (HDFC, ICICI, SBI, Axis, CSV/PDF) and up to 12 Salary Slips at once.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-2">
            <span className="bg-[#3730A3] text-white text-[11px] font-mono font-bold px-2.5 py-1 border border-black shadow-[2px_2px_0px_0px_#000]">
              ✓ AUTO TYPE DETECTION
            </span>
            <span className="bg-[#10B981] text-black text-[11px] font-mono font-bold px-2.5 py-1 border border-black shadow-[2px_2px_0px_0px_#000]">
              ✓ AUTO MONTH &amp; FY EXTRACTION
            </span>
            <span className="bg-[#F59E0B] text-black text-[11px] font-mono font-bold px-2.5 py-1 border border-black shadow-[2px_2px_0px_0px_#000]">
              ✓ IN-MEMORY PDF DECRYPTION
            </span>
          </div>
        </div>
      </div>

      {/* Staged Batch Queue View */}
      {queue.length > 0 && (
        <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[8px_8px_0px_0px_#000000] space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b-3 border-black pb-4">
            <div className="flex items-center gap-3">
              <FolderOpen className="w-6 h-6 text-[#3730A3]" />
              <div>
                <h3 className="font-black text-xl uppercase font-['Space_Grotesk'] tracking-tight">
                  STAGED DOCUMENT QUEUE ({queue.length})
                </h3>
                <p className="font-mono text-xs text-gray-600">
                  Review detected document types or enter passwords for locked PDFs before parsing.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-white hover:bg-gray-100 text-black border-2 border-black px-3 py-1.5 font-mono font-black text-xs uppercase flex items-center gap-1.5 shadow-[2px_2px_0px_0px_#000] cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Add Files</span>
              </button>
              {totalSuccess.length > 0 && (
                <button
                  onClick={clearCompleted}
                  className="bg-gray-100 hover:bg-gray-200 text-gray-800 border-2 border-black px-3 py-1.5 font-mono font-black text-xs uppercase shadow-[2px_2px_0px_0px_#000] cursor-pointer"
                >
                  Clear Completed ({totalSuccess.length})
                </button>
              )}
              <button
                onClick={handleUploadAll}
                disabled={isBatchUploading || queue.every((q) => q.status === 'success')}
                className={`px-4 py-2 border-3 border-black font-black text-xs md:text-sm tracking-wider uppercase flex items-center gap-2 transition-all cursor-pointer ${
                  isBatchUploading || queue.every((q) => q.status === 'success')
                    ? 'bg-gray-300 text-gray-600 cursor-not-allowed shadow-none'
                    : 'bg-[#FACC15] text-black shadow-[4px_4px_0px_0px_#000] hover:shadow-[6px_6px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5'
                }`}
              >
                {isBatchUploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>PARSING BATCH...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>PROCESS ALL ({queue.filter((q) => q.status !== 'success').length})</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Queue Items List */}
          <div className="space-y-3">
            {queue.map((item) => (
              <div
                key={item.id}
                className={`border-3 border-black p-4 transition-all shadow-[3px_3px_0px_0px_#000] ${
                  item.status === 'success'
                    ? 'bg-emerald-50/50'
                    : item.status === 'needs_password'
                    ? 'bg-amber-50'
                    : item.status === 'error'
                    ? 'bg-red-50'
                    : 'bg-[#FAF7F2]'
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  {/* Left: Icon & File Meta */}
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2 border-2 border-black bg-white shadow-[2px_2px_0px_0px_#000] flex-shrink-0">
                      {item.detectedType === 'bank_statement' ? (
                        <FileSpreadsheet className="w-5 h-5 text-[#3730A3]" />
                      ) : item.detectedType === 'salary_slip' ? (
                        <FileText className="w-5 h-5 text-[#F59E0B]" />
                      ) : (
                        <FileQuestion className="w-5 h-5 text-gray-700" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="font-mono font-bold text-sm text-black truncate max-w-xs md:max-w-md">
                        {item.file.name}
                      </p>
                      <p className="font-mono text-[11px] text-gray-600">
                        {formatFileSize(item.file.size)}
                      </p>
                    </div>
                  </div>

                  {/* Right: Controls & Status Badges */}
                  <div className="flex flex-wrap items-center gap-2.5">
                    {/* Document Type Selector */}
                    {item.status !== 'success' && (
                      <select
                        value={item.detectedType}
                        onChange={(e) =>
                          updateItem(item.id, {
                            detectedType: e.target.value as 'auto' | 'bank_statement' | 'salary_slip',
                          })
                        }
                        className="bg-white border-2 border-black px-2 py-1 font-mono font-bold text-xs uppercase shadow-[2px_2px_0px_0px_#000] outline-none cursor-pointer"
                      >
                        <option value="auto">Auto-Detect</option>
                        <option value="bank_statement">Bank Statement</option>
                        <option value="salary_slip">Salary Slip</option>
                      </select>
                    )}

                    {/* Status Pill */}
                    {item.status === 'idle' && (
                      <span className="bg-[#FAF7F2] text-gray-800 font-mono text-[11px] font-black px-2.5 py-1 border border-black">
                        QUEUED
                      </span>
                    )}
                    {item.status === 'uploading' && (
                      <span className="bg-[#FACC15] text-black font-mono text-[11px] font-black px-2.5 py-1 border border-black flex items-center gap-1.5">
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        PARSING...
                      </span>
                    )}
                    {item.status === 'needs_password' && (
                      <span className="bg-amber-300 text-amber-950 font-mono text-[11px] font-black px-2.5 py-1 border border-black flex items-center gap-1">
                        <Lock className="w-3.5 h-3.5" />
                        PASSWORD REQUIRED
                      </span>
                    )}
                    {item.status === 'success' && (
                      <span className="bg-emerald-300 text-emerald-950 font-mono text-[11px] font-black px-2.5 py-1 border border-black flex items-center gap-1">
                        <Check className="w-3.5 h-3.5 stroke-[3]" />
                        INGESTED
                      </span>
                    )}
                    {item.status === 'error' && (
                      <span className="bg-red-200 text-red-950 font-mono text-[11px] font-black px-2.5 py-1 border border-black">
                        ERROR
                      </span>
                    )}

                    {/* Action: Single upload / retry button */}
                    {item.status !== 'success' && item.status !== 'needs_password' && (
                      <button
                        onClick={() => processSingleDocument(item)}
                        disabled={item.status === 'uploading'}
                        className="bg-white hover:bg-gray-100 text-black border-2 border-black px-2.5 py-1 text-xs font-mono font-black uppercase shadow-[2px_2px_0px_0px_#000] cursor-pointer"
                      >
                        Parse
                      </button>
                    )}

                    {/* Remove button */}
                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      className="p-1.5 text-gray-600 hover:text-red-700 hover:bg-red-50 border border-transparent hover:border-black transition-colors cursor-pointer"
                      title="Remove file from queue"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Inline Password Decrypt Prompt */}
                {item.status === 'needs_password' && (
                  <div className="mt-3 p-3 bg-white border-2 border-black shadow-[2px_2px_0px_0px_#000] space-y-2 font-mono">
                    <div className="flex items-center gap-2 text-amber-900 text-xs font-bold">
                      <Lock className="w-4 h-4 text-amber-700" />
                      <span>{item.errorMessage || 'This PDF is password-protected. Enter password below to unlock in-memory:'}</span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <div className="relative flex-1 min-w-[200px]">
                        <input
                          type="password"
                          placeholder="Enter statement/payslip password..."
                          value={item.passwordInput}
                          onChange={(e) => updateItem(item.id, { passwordInput: e.target.value })}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleUnlockAndRetry(item);
                          }}
                          className="w-full bg-[#FAF7F2] border-2 border-black px-3 py-1.5 font-mono text-xs font-bold outline-none"
                        />
                      </div>

                      {profilePan && (
                        <button
                          type="button"
                          onClick={() => handleAutofillPan(item)}
                          className="bg-amber-100 hover:bg-amber-200 text-amber-950 border-2 border-black px-2.5 py-1.5 text-xs font-black uppercase flex items-center gap-1 shadow-[2px_2px_0px_0px_#000] cursor-pointer"
                          title={`Autofill PAN (${profilePan})`}
                        >
                          <KeyRound className="w-3.5 h-3.5" />
                          <span>Try PAN ({profilePan.slice(0, 5)}...)</span>
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => handleUnlockAndRetry(item)}
                        className="bg-[#10B981] hover:bg-emerald-400 text-black border-2 border-black px-4 py-1.5 text-xs font-black uppercase shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
                      >
                        Unlock &amp; Parse
                      </button>
                    </div>
                  </div>
                )}

                {/* Error message card */}
                {item.status === 'error' && item.errorMessage && (
                  <div className="mt-2 text-xs font-mono font-bold text-red-700 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                    <span>{item.errorMessage}</span>
                  </div>
                )}

                {/* Extracted Compensation / Statement Verification Preview */}
                {item.status === 'success' && (
                  <div className="mt-3 pt-3 border-t-2 border-dashed border-gray-300 font-mono">
                    {item.salaryResult && (
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="bg-[#3730A3] text-white px-2 py-0.5 text-[11px] font-black border border-black">
                          📅 {new Date(item.salaryResult.year, item.salaryResult.month - 1).toLocaleString('default', { month: 'short' })} {item.salaryResult.year} (FY {item.salaryResult.financial_year || `${item.salaryResult.year}-${item.salaryResult.year + 1}`})
                        </span>
                        <span className="bg-white text-black px-2 py-0.5 text-[11px] font-bold border border-black">
                          Net Pay: ₹{(item.salaryResult.net_pay || 0).toLocaleString('en-IN')}
                        </span>
                        <span className="bg-white text-gray-700 px-2 py-0.5 text-[11px] font-bold border border-black">
                          Basic: ₹{((item.salaryResult.basic || item.salaryResult.basic_pay) || 0).toLocaleString('en-IN')}
                        </span>
                        <span className="bg-white text-gray-700 px-2 py-0.5 text-[11px] font-bold border border-black">
                          HRA: ₹{(item.salaryResult.hra || 0).toLocaleString('en-IN')}
                        </span>
                        <span className="bg-white text-gray-700 px-2 py-0.5 text-[11px] font-bold border border-black">
                          PF: ₹{((item.salaryResult.employee_pf || item.salaryResult.provident_fund) || 0).toLocaleString('en-IN')}
                        </span>
                        {item.salaryResult.tds ? (
                          <span className="bg-amber-100 text-amber-950 px-2 py-0.5 text-[11px] font-black border border-black">
                            TDS: ₹{(item.salaryResult.tds || 0).toLocaleString('en-IN')}
                          </span>
                        ) : null}
                        <span className="bg-emerald-100 text-emerald-950 px-2 py-0.5 text-[10px] font-black border border-black flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-700" />
                          CONF: {((item.salaryResult.extraction_confidence || item.salaryResult.parse_confidence || 0.95) * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}

                    {item.statementResult && (
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="bg-[#18153B] text-white px-2 py-0.5 text-[11px] font-black border border-black">
                          UPLOAD #{item.statementResult.upload_id}
                        </span>
                        <span className="bg-white text-black px-2 py-0.5 text-[11px] font-bold border border-black">
                          Txns: {item.statementResult.transactions_count || item.statementResult.transactions_parsed || 0}
                        </span>
                        {item.statementResult.balance_reconciled ? (
                          <span className="bg-emerald-200 text-emerald-950 px-2 py-0.5 text-[11px] font-black border border-black flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
                            BALANCE RECONCILED (Δ ≤ ₹1.00)
                          </span>
                        ) : (
                          <span className="bg-amber-200 text-amber-950 px-2 py-0.5 text-[11px] font-black border border-black flex items-center gap-1">
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                            BALANCE DISCREPANCY DETECTED
                          </span>
                        )}
                        <span className="bg-white text-gray-700 px-2 py-0.5 text-[11px] font-bold border border-black">
                          Conf: {((item.statementResult.parse_confidence || 0.95) * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Direct Launchpad to Bank Deduction Harvester */}
      {totalSuccess.length > 0 && (
        <div className="bg-[#FACC15] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000] relative overflow-hidden">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-1.5 bg-black text-[#FACC15] px-2.5 py-0.5 text-[11px] font-mono font-black uppercase mb-2">
                <Sparkles className="w-3.5 h-3.5" />
                <span>CLEAN DATA FUEL READY</span>
              </div>
              <h3 className="font-['Space_Grotesk'] font-black text-2xl md:text-3xl uppercase text-[#18153B] leading-none mb-2">
                INGESTION COMPLETE // LAUNCH DEDUCTION HARVESTER
              </h3>
              <p className="font-mono text-xs md:text-sm font-bold text-gray-900 max-w-2xl">
                {totalSuccess.length} document{totalSuccess.length > 1 ? 's' : ''} ingested ({totalTxns} bank transactions, {parsedSalaries.length} salary slip{parsedSalaries.length > 1 ? 's' : ''}). We are ready to scan for Section 80C, 80D, 80E, 80G, and 80TTA deductions.
              </p>
            </div>

            <button
              onClick={() => {
                if (onNavigateTab) {
                  onNavigateTab('catalog');
                }
              }}
              className="bg-[#18153B] hover:bg-black text-[#FACC15] border-3 border-black px-6 py-3.5 font-black text-sm uppercase tracking-wider shadow-[4px_4px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 flex items-center gap-3 cursor-pointer whitespace-nowrap"
            >
              <span>MINE DEDUCTIONS NOW</span>
              <ArrowRight className="w-5 h-5 stroke-[3]" />
            </button>
          </div>
        </div>
      )}

      {/* Advanced Bank CSV Column Mapper (Accordion Drawer) */}
      <div className="bg-[#FFFDF9] border-4 border-black shadow-[6px_6px_0px_0px_#000000]">
        <button
          onClick={() => setShowAdvancedMapper((v) => !v)}
          className="w-full p-4 flex items-center justify-between font-['Space_Grotesk'] font-black text-sm uppercase tracking-wider text-left cursor-pointer hover:bg-[#FAF7F2]"
        >
          <div className="flex items-center gap-2">
            <span>⚙️ ADVANCED BANK CSV COLUMN MAPPER &amp; FORMAT ADAPTER</span>
            <span className="bg-gray-200 text-black text-[10px] font-mono font-bold px-2 py-0.5 border border-black">
              {bankFormat === 'auto' ? 'AUTO-DETECT' : bankFormat.toUpperCase()}
            </span>
          </div>
          {showAdvancedMapper ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>

        {showAdvancedMapper && (
          <div className="p-6 border-t-2 border-black bg-[#FAF7F2] font-mono text-xs space-y-4">
            <div>
              <label className="block text-xs font-black uppercase tracking-wider text-gray-700 mb-1">
                Bank Adapter / Format:
              </label>
              <select
                value={bankFormat}
                onChange={(e) => setBankFormat(e.target.value)}
                className="w-full bg-white border-2 border-black p-2 font-bold text-xs shadow-[2px_2px_0px_0px_#000] outline-none"
              >
                <option value="auto">Auto-Detect Format (Recommended)</option>
                <option value="hdfc">HDFC Bank</option>
                <option value="icici">ICICI Bank</option>
                <option value="sbi">State Bank of India (SBI)</option>
                <option value="axis">Axis Bank</option>
                <option value="custom">Custom Bank CSV (Manual Column Mapper)</option>
              </select>
            </div>

            {bankFormat === 'custom' && (
              <div className="p-4 bg-white border-2 border-black space-y-3 shadow-[2px_2px_0px_0px_#000]">
                <span className="font-black uppercase text-[#3730A3] block">
                  CUSTOM CSV COLUMN SPECIFICATION:
                </span>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-black uppercase text-gray-700">Date Column Name:</label>
                    <input
                      type="text"
                      value={customDateCol}
                      onChange={(e) => setCustomDateCol(e.target.value)}
                      className="w-full bg-[#FAF7F2] border border-black p-1.5 font-bold outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-black uppercase text-gray-700">Narration Column Name:</label>
                    <input
                      type="text"
                      value={customNarrationCol}
                      onChange={(e) => setCustomNarrationCol(e.target.value)}
                      className="w-full bg-[#FAF7F2] border border-black p-1.5 font-bold outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-black uppercase text-gray-700 mb-1">
                    Sign Convention:
                  </label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        name="signMode"
                        checked={customSignMode === 'separate'}
                        onChange={() => setCustomSignMode('separate')}
                      />
                      <span className="font-bold text-[11px]">Separate Debit / Credit</span>
                    </label>
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input
                        type="radio"
                        name="signMode"
                        checked={customSignMode === 'single'}
                        onChange={() => setCustomSignMode('single')}
                      />
                      <span className="font-bold text-[11px]">Single Amount (Balance Delta)</span>
                    </label>
                  </div>
                </div>

                {customSignMode === 'separate' ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[10px] font-black uppercase text-gray-700">Debit Column Name:</label>
                      <input
                        type="text"
                        value={customDebitCol}
                        onChange={(e) => setCustomDebitCol(e.target.value)}
                        className="w-full bg-[#FAF7F2] border border-black p-1.5 font-bold outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-black uppercase text-gray-700">Credit Column Name:</label>
                      <input
                        type="text"
                        value={customCreditCol}
                        onChange={(e) => setCustomCreditCol(e.target.value)}
                        className="w-full bg-[#FAF7F2] border border-black p-1.5 font-bold outline-none"
                      />
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="block text-[10px] font-black uppercase text-gray-700">Amount Column Name:</label>
                    <input
                      type="text"
                      value={customAmountCol}
                      onChange={(e) => setCustomAmountCol(e.target.value)}
                      className="w-full bg-[#FAF7F2] border border-black p-1.5 font-bold outline-none"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-[10px] font-black uppercase text-gray-700">Balance Column Name (optional):</label>
                  <input
                    type="text"
                    value={customBalanceCol}
                    onChange={(e) => setCustomBalanceCol(e.target.value)}
                    className="w-full bg-[#FAF7F2] border border-black p-1.5 font-bold outline-none"
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Uploaded Documents Vault (File Manager & Deletion) */}
      <div data-tour="vault-manager">
        <UploadedFilesVault
          onFileDeleted={() => {
            setRefreshVaultCounter((c) => c + 1);
            onUploadSuccess();
          }}
          refreshTrigger={refreshVaultCounter}
        />
      </div>
    </div>
  );
};
