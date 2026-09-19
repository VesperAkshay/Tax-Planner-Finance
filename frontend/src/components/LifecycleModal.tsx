import React, { useState } from 'react';
import {
  X,
  Download,
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  HardDriveDownload,
  CalendarX,
  UserX,
} from 'lucide-react';
import { api } from '../api/client';
import { UploadedFilesVault } from './UploadedFilesVault';

interface LifecycleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAccountDeleted: () => void;
  onDataReset: () => void;
}

export const LifecycleModal: React.FC<LifecycleModalProps> = ({
  isOpen,
  onClose,
  onAccountDeleted,
  onDataReset,
}) => {
  const [financialYear, setFinancialYear] = useState('2025-2026');
  const [isExporting, setIsExporting] = useState(false);
  const [isResettingFy, setIsResettingFy] = useState(false);
  const [isErasingAccount, setIsErasingAccount] = useState(false);

  // Confirmation flags
  const [showFyConfirm, setShowFyConfirm] = useState(false);
  const [showAccountConfirm, setShowAccountConfirm] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  if (!isOpen) return null;

  const handleExportZip = async () => {
    setIsExporting(true);
    setStatusMessage(null);
    try {
      await api.exportDataArchive(financialYear);
      setStatusMessage({
        type: 'success',
        text: `Full data archive for FY ${financialYear} downloaded successfully (transactions.csv, declared_deductions.json, export_summary.json, and PDF memo).`,
      });
    } catch (e: unknown) {
      setStatusMessage({
        type: 'error',
        text: e instanceof Error ? e.message : 'Export failed.',
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleResetFinancialYear = async () => {
    setIsResettingFy(true);
    setStatusMessage(null);
    try {
      const res = await api.deleteFinancialYear(financialYear);
      setStatusMessage({ type: 'success', text: res.message });
      setShowFyConfirm(false);
      onDataReset();
    } catch (e: unknown) {
      setStatusMessage({
        type: 'error',
        text: e instanceof Error ? e.message : 'Failed to reset financial year data.',
      });
    } finally {
      setIsResettingFy(false);
    }
  };

  const handleEraseAccount = async () => {
    setIsErasingAccount(true);
    setStatusMessage(null);
    try {
      await api.deleteAccount();
      onAccountDeleted();
      onClose();
    } catch (e: unknown) {
      setStatusMessage({
        type: 'error',
        text: e instanceof Error ? e.message : 'Failed to erase account.',
      });
      setIsErasingAccount(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto font-mono">
      <div className="bg-[#FFFDF9] border-4 border-black w-full max-w-2xl shadow-[8px_8px_0px_0px_#000] relative max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-[#18153B] text-white p-4 border-b-3 border-black flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 bg-[#FACC15] text-black border border-black font-black text-xs">
              TP//SEC
            </div>
            <div>
              <h3 className="font-black text-base uppercase font-['Space_Grotesk'] text-[#FACC15]">
                DATA &amp; PRIVACY VAULT MANAGEMENT
              </h3>
              <p className="text-[11px] text-gray-300 font-mono">
                Statutory Data Lifecycle, Export &amp; Right-to-Erasure Controls
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-[#FACC15] p-1 border border-white/20 hover:border-[#FACC15] cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 overflow-y-auto text-xs">
          {statusMessage && (
            <div
              className={`p-3 border-2 border-black flex items-center gap-2 shadow-[2px_2px_0px_0px_#000] ${
                statusMessage.type === 'success'
                  ? 'bg-emerald-100 text-emerald-900'
                  : 'bg-red-100 text-red-900'
              }`}
            >
              {statusMessage.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              )}
              <span className="font-bold">{statusMessage.text}</span>
            </div>
          )}

          {/* Section 1: Data Export Bundle */}
          <div className="bg-[#FAF7F2] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000]">
            <div className="flex items-center gap-2 border-b-2 border-black pb-2 mb-3">
              <HardDriveDownload className="w-4 h-4 text-[#3730A3]" />
              <h4 className="font-black text-sm uppercase font-['Space_Grotesk'] text-[#18153B]">
                1. EXPORT COMPLETE DATA ARCHIVE (ZIP)
              </h4>
            </div>
            <p className="text-gray-700 font-semibold mb-3 leading-relaxed">
              Download all your parsed banking transactions (CSV), declared tax deductions (JSON), audit summary metadata,
              and your vector-grade Neo-Brutalist tax invoice PDF into a single encrypted ZIP archive.
            </p>

            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="font-bold text-gray-700">FY:</span>
                <select
                  value={financialYear}
                  onChange={(e) => setFinancialYear(e.target.value)}
                  className="bg-white border-2 border-black px-2 py-1 font-bold outline-none"
                >
                  <option value="2025-2026">2025-2026 (AY 2026-27)</option>
                  <option value="2024-2025">2024-2025 (AY 2025-26)</option>
                </select>
              </div>

              <button
                onClick={handleExportZip}
                disabled={isExporting}
                className="flex items-center gap-2 bg-[#FACC15] hover:bg-yellow-400 text-black px-4 py-2 border-2 border-black font-black uppercase shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer disabled:opacity-50"
              >
                <Download className={`w-4 h-4 ${isExporting ? 'animate-bounce' : ''}`} />
                <span>{isExporting ? 'PACKAGING ARCHIVE...' : 'DOWNLOAD ZIP BUNDLE'}</span>
              </button>
            </div>
          </div>

          {/* Section 2: Manage & Delete Specific Documents (Interactive Vault) */}
          <UploadedFilesVault onFileDeleted={onDataReset} compact={true} />

          {/* Section 3: Reset Financial Year */}
          <div className="bg-[#FAF7F2] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000]">
            <div className="flex items-center gap-2 border-b-2 border-black pb-2 mb-3">
              <CalendarX className="w-4 h-4 text-amber-700" />
              <h4 className="font-black text-sm uppercase font-['Space_Grotesk'] text-[#18153B]">
                3. RESET FINANCIAL YEAR DATA
              </h4>
            </div>
            <p className="text-gray-700 font-semibold mb-3 leading-relaxed">
              Permanently delete all salary slips, declared deductions, and computations for financial year{' '}
              <span className="font-black text-black underline">{financialYear}</span>.
            </p>

            {showFyConfirm ? (
              <div className="bg-amber-100 border-2 border-amber-800 p-3 space-y-2">
                <span className="font-black text-amber-950 block">
                  ⚠️ ARE YOU SURE? All data for FY {financialYear} will be deleted.
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleResetFinancialYear}
                    disabled={isResettingFy}
                    className="bg-red-600 text-white border-2 border-black px-3 py-1 font-black uppercase cursor-pointer"
                  >
                    {isResettingFy ? 'RESETTING...' : 'YES, PERMANENTLY RESET FY'}
                  </button>
                  <button
                    onClick={() => setShowFyConfirm(false)}
                    className="bg-white text-black border-2 border-black px-3 py-1 font-bold uppercase cursor-pointer"
                  >
                    CANCEL
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowFyConfirm(true)}
                className="bg-amber-200 hover:bg-amber-300 text-amber-950 border-2 border-black px-4 py-1.5 font-black uppercase shadow-[2px_2px_0px_0px_#000] cursor-pointer"
              >
                RESET FY {financialYear}
              </button>
            )}
          </div>

          {/* Section 4: Right-to-Erasure (Account Wipe) */}
          <div className="bg-red-50 border-3 border-red-800 p-4 shadow-[4px_4px_0px_0px_#000]">
            <div className="flex items-center gap-2 border-b-2 border-red-800 pb-2 mb-3 text-red-900">
              <ShieldAlert className="w-4 h-4" />
              <h4 className="font-black text-sm uppercase font-['Space_Grotesk']">
                4. RIGHT-TO-ERASURE (PERMANENT ACCOUNT PURGE)
              </h4>
            </div>
            <p className="text-red-900 font-semibold mb-3 leading-relaxed">
              In compliance with data protection laws, this completely purges your user identity, accounts, bank transactions,
              salary slips, deduction declarations, and computation history with zero orphaned database rows.
            </p>

            {showAccountConfirm ? (
              <div className="bg-red-200 border-2 border-red-900 p-3 space-y-2">
                <span className="font-black text-red-950 block uppercase">
                  🚨 IRREVERSIBLE ACTION: THIS WILL PERMANENTLY ERASE YOUR ACCOUNT!
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleEraseAccount}
                    disabled={isErasingAccount}
                    className="bg-black text-white hover:bg-gray-800 border-2 border-black px-4 py-1.5 font-black uppercase cursor-pointer"
                  >
                    {isErasingAccount ? 'PURGING...' : 'I CONFIRM: WIPE EVERYTHING'}
                  </button>
                  <button
                    onClick={() => setShowAccountConfirm(false)}
                    className="bg-white text-black border-2 border-black px-3 py-1 font-bold uppercase cursor-pointer"
                  >
                    ABORT
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowAccountConfirm(true)}
                className="bg-red-700 hover:bg-red-800 text-white border-2 border-black px-4 py-1.5 font-black uppercase shadow-[2px_2px_0px_0px_#000] cursor-pointer flex items-center gap-2"
              >
                <UserX className="w-4 h-4" />
                <span>PURGE ACCOUNT &amp; ALL DATA</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
