import React, { useState, useEffect, useCallback } from 'react';
import {
  FileSpreadsheet,
  FileText,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Calendar,
  Layers,
  Clock,
  ShieldCheck,
} from 'lucide-react';
import { api } from '../api/client';
import type { UploadedFileItem } from '../types';

interface UploadedFilesVaultProps {
  onFileDeleted?: () => void;
  refreshTrigger?: number;
  compact?: boolean;
}

export const UploadedFilesVault: React.FC<UploadedFilesVaultProps> = ({
  onFileDeleted,
  refreshTrigger,
  compact = false,
}) => {
  const [files, setFiles] = useState<UploadedFileItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // ID being confirmed for deletion: string key like "statement-12" or "salary_slip-5"
  const [deletingKey, setDeletingKey] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchFiles = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.getUserUploadedFiles();
      setFiles(res.files || []);
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : 'Failed to load uploaded files.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles, refreshTrigger]);

  const handleDelete = async (file: UploadedFileItem) => {
    setIsDeleting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    // 1. Optimistic UI update: remove card immediately from view
    setFiles((prev) => prev.filter((f) => !(f.type === file.type && f.id === file.id)));

    try {
      if (file.type === 'salary_slip') {
        const res = await api.deleteSalarySlip(file.id);
        setSuccessMsg(res.message || `Salary slip '${file.file_name}' removed.`);
      } else {
        const res = await api.deleteUpload(file.id);
        setSuccessMsg(res.message || `Statement '${file.file_name}' and parsed transactions removed.`);
      }
      setDeletingKey(null);
      onFileDeleted?.();
      await fetchFiles();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to delete file.';
      // If already deleted on server (404 / not found), treat as successfully removed
      if (msg.toLowerCase().includes('not found') || msg.toLowerCase().includes('already')) {
        setSuccessMsg(`Document '${file.file_name}' removed from your vault.`);
        setDeletingKey(null);
        onFileDeleted?.();
        await fetchFiles();
      } else {
        setErrorMsg(msg);
        // Rollback optimistic removal by fetching actual state
        await fetchFiles();
      }
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'Unknown date';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className={`bg-[#FFFDF9] border-4 border-black ${compact ? 'p-4' : 'p-6'} shadow-[6px_6px_0px_0px_#000000]`}>
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b-3 border-black pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-[#3730A3] text-[#FACC15] border-2 border-black font-black">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-black text-lg uppercase font-['Space_Grotesk'] tracking-tight text-[#18153B]">
                DOCUMENT VAULT &amp; ATTACHMENTS
              </h3>
              <span className="bg-[#FACC15] text-black border border-black font-mono font-black text-xs px-2 py-0.5 shadow-[1px_1px_0px_0px_#000]">
                {files.length} {files.length === 1 ? 'FILE' : 'FILES'}
              </span>
            </div>
            <p className="text-xs text-gray-700 font-mono">
              Interactive document manager — view parsed records and 1-click delete files without manual IDs.
            </p>
          </div>
        </div>

        <button
          onClick={fetchFiles}
          disabled={isLoading}
          className="flex items-center gap-1.5 bg-white hover:bg-gray-100 text-black border-2 border-black px-3 py-1 text-xs font-mono font-black uppercase shadow-[2px_2px_0px_0px_#000] cursor-pointer active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-50"
          title="Refresh files"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>REFRESH</span>
        </button>
      </div>

      {/* Alert Notices */}
      {errorMsg && (
        <div className="mb-4 bg-red-100 border-2 border-black p-3 text-red-900 font-mono text-xs font-bold flex items-center gap-2 shadow-[2px_2px_0px_0px_#000]">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="mb-4 bg-emerald-100 border-2 border-black p-3 text-emerald-950 font-mono text-xs font-bold flex items-center gap-2 shadow-[2px_2px_0px_0px_#000]">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-700" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Loading State */}
      {isLoading && files.length === 0 ? (
        <div className="py-10 text-center font-mono">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#3730A3] mb-2" />
          <p className="font-bold text-gray-700 uppercase text-xs tracking-wider">
            Loading document vault...
          </p>
        </div>
      ) : files.length === 0 ? (
        /* Empty State */
        <div className="border-3 border-dashed border-gray-400 p-8 text-center bg-[#FAF7F2] font-mono">
          <Layers className="w-10 h-10 mx-auto text-gray-400 mb-2" />
          <h4 className="font-black text-sm uppercase text-gray-800 font-['Space_Grotesk'] mb-1">
            No Documents Ingested Yet
          </h4>
          <p className="text-xs text-gray-600 max-w-md mx-auto">
            Upload your multi-bank statements (PDF or CSV) or monthly salary slips above. They will be indexed here with complete parse history and 1-click deletion controls.
          </p>
        </div>
      ) : (
        /* Files Grid / List (ChatGPT-Style) */
        <div className="space-y-3 font-mono">
          {files.map((file) => {
            const key = `${file.type}-${file.id}`;
            const isConfirmingThis = deletingKey === key;
            const isStatement = file.type === 'statement';

            return (
              <div
                key={key}
                className="bg-[#FAF7F2] border-2 border-black p-3.5 shadow-[3px_3px_0px_0px_#000] hover:shadow-[4px_4px_0px_0px_#000] transition-all flex flex-col md:flex-row md:items-center justify-between gap-3"
              >
                {/* File Info */}
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div
                    className={`p-2.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] flex-shrink-0 ${
                      isStatement ? 'bg-indigo-100 text-[#3730A3]' : 'bg-amber-100 text-[#B45309]'
                    }`}
                  >
                    {isStatement ? (
                      <FileSpreadsheet className="w-5 h-5" />
                    ) : (
                      <FileText className="w-5 h-5" />
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="font-black text-sm text-[#18153B] truncate max-w-xs md:max-w-md" title={file.file_name}>
                        {file.file_name}
                      </span>

                      {/* Type Badge */}
                      <span
                        className={`text-[10px] font-black uppercase px-2 py-0.5 border border-black shadow-[1px_1px_0px_0px_#000] ${
                          isStatement
                            ? 'bg-[#3730A3] text-white'
                            : 'bg-[#F59E0B] text-black'
                        }`}
                      >
                        {isStatement ? `STATEMENT (${file.file_type.toUpperCase()})` : 'SALARY SLIP (PDF)'}
                      </span>

                      {/* Reconciliation / Review Badge */}
                      {file.details?.balance_reconciled === true && (
                        <span className="inline-flex items-center gap-1 bg-emerald-100 text-emerald-900 border border-black text-[10px] font-black px-1.5 py-0.5">
                          <ShieldCheck className="w-3 h-3 text-emerald-700" />
                          <span>RECONCILED</span>
                        </span>
                      )}

                      {file.details?.needs_review && (
                        <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-900 border border-black text-[10px] font-black px-1.5 py-0.5">
                          <AlertTriangle className="w-3 h-3 text-amber-700" />
                          <span>NEEDS REVIEW</span>
                        </span>
                      )}
                    </div>

                    {/* Metadata Subtitle Row */}
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-700">
                      {/* Date Range / Period */}
                      {file.date_range && (
                        <span className="inline-flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5 text-gray-500" />
                          <span className="font-bold">{file.date_range}</span>
                        </span>
                      )}

                      {/* Transaction / Slip Count */}
                      <span className="inline-flex items-center gap-1 font-bold text-gray-900">
                        <span className="bg-white px-1.5 py-0.2 border border-black text-[11px]">
                          {isStatement
                            ? `${file.transaction_count ?? 0} txns`
                            : `Net: ₹${(file.details?.net_pay || 0).toLocaleString('en-IN')}`}
                        </span>
                      </span>

                      {/* Upload Time */}
                      <span className="inline-flex items-center gap-1 text-[11px] text-gray-600">
                        <Clock className="w-3 h-3 text-gray-400" />
                        <span>{formatDate(file.created_at)}</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Action Section: 1-Click Delete with Inline Confirmation */}
                <div className="flex-shrink-0 flex items-center justify-end">
                  {isConfirmingThis ? (
                    <div className="bg-red-50 border-2 border-red-800 p-2 flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-black text-red-950 uppercase">
                        Confirm delete?
                      </span>
                      <button
                        onClick={() => handleDelete(file)}
                        disabled={isDeleting}
                        className="bg-red-600 hover:bg-red-700 text-white border border-black px-2.5 py-1 text-xs font-black uppercase cursor-pointer disabled:opacity-50"
                      >
                        {isDeleting ? 'DELETING...' : 'YES, DELETE'}
                      </button>
                      <button
                        onClick={() => setDeletingKey(null)}
                        disabled={isDeleting}
                        className="bg-white hover:bg-gray-100 text-black border border-black px-2 py-1 text-xs font-bold uppercase cursor-pointer disabled:opacity-50"
                      >
                        CANCEL
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setDeletingKey(key)}
                      className="inline-flex items-center gap-1.5 bg-red-100 hover:bg-red-200 text-red-900 border-2 border-black px-3 py-1.5 text-xs font-black uppercase shadow-[2px_2px_0px_0px_#000] cursor-pointer active:translate-x-0.5 active:translate-y-0.5 transition-all"
                      title={`Delete ${file.file_name}`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>DELETE</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
