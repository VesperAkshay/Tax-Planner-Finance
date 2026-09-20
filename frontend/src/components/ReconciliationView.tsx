import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  RefreshCw,
  Sparkles,
  ShieldAlert,
  HelpCircle,
} from 'lucide-react';
import { api } from '../api/client';
import type { ReconciliationFlag } from '../types';

interface ReconciliationViewProps {
  onFlagUpdate?: () => void;
}

interface FlagTypeInfo {
  title: string;
  badgeColor: string;
  hint: string;
}

const FLAG_TYPE_CONFIG: Record<string, FlagTypeInfo> = {
  missing_salary_slip: {
    title: 'Missing Salary Slip',
    badgeColor: 'bg-amber-300 text-amber-950',
    hint: 'A salary credit was found in your bank statement, but the corresponding monthly payslip has not been uploaded yet.',
  },
  missing_bank_credit: {
    title: 'Missing Bank Salary Deposit',
    badgeColor: 'bg-rose-200 text-rose-950',
    hint: 'A payslip was uploaded for this month, but no matching credit transaction was detected in your uploaded bank statement.',
  },
  mismatched_amount: {
    title: 'Net Salary Amount Discrepancy',
    badgeColor: 'bg-orange-200 text-orange-950',
    hint: 'Bank credit amount differs from payslip net pay beyond the permissible tolerance limit.',
  },
  bonus_variable_pay: {
    title: 'Bonus / Variable Pay Detected',
    badgeColor: 'bg-blue-200 text-blue-950',
    hint: 'Deposit significantly exceeded base salary, indicating quarterly performance bonus or incentive payout.',
  },
  unexplained_credit: {
    title: 'Additional Unexplained Salary Credit',
    badgeColor: 'bg-purple-200 text-purple-950',
    hint: 'Multiple salary credits detected within the same month alongside regular salary.',
  },
};

export const ReconciliationView: React.FC<ReconciliationViewProps> = ({ onFlagUpdate }) => {
  const [flags, setFlags] = useState<ReconciliationFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  useEffect(() => {
    loadFlags();
  }, []);

  const loadFlags = async () => {
    setLoading(true);
    try {
      const data = await api.getReconciliationFlags();
      setFlags(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    try {
      await api.runReconciliation();
      const data = await api.getReconciliationFlags();
      setFlags(data);
      if (onFlagUpdate) onFlagUpdate();
    } catch (e) {
      console.error('Reconciliation run error', e);
      await loadFlags();
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (flagId: number, resolution: 'resolve' | 'ignore') => {
    setResolvingId(flagId);
    try {
      await api.resolveFlag(flagId, resolution, 'Taxpayer confirmed in frontend UI');
      setFlags((prev) =>
        prev.map((f) =>
          f.id === flagId
            ? {
                ...f,
                status: resolution === 'ignore' ? 'ignored' : 'resolved',
                resolved_at: new Date().toISOString(),
              }
            : f
        )
      );
      if (onFlagUpdate) onFlagUpdate();
    } catch (e) {
      console.error('Resolve failed', e);
    } finally {
      setResolvingId(null);
    }
  };

  const pendingCount = flags.filter((f) => f.status === 'pending').length;

  return (
    <div data-tour="reconciliation-view" className="space-y-8">
      {/* Banner */}
      <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-2">
          <div className="inline-flex items-center gap-2 bg-[#F59E0B] px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase text-black">
            <Sparkles className="w-4 h-4" />
            <span>PAYROLL AUDIT // SALARY CROSS-VERIFICATION</span>
          </div>

          <button
            onClick={handleRerun}
            disabled={loading}
            className="flex items-center gap-2 bg-[#FAF7F2] hover:bg-gray-100 text-black px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs font-mono disabled:opacity-50 cursor-pointer active:translate-x-0.5 active:translate-y-0.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            RE-RUN ENGINE AUDIT
          </button>
        </div>

        <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none">
          SALARY RECONCILIATION
        </h2>
        <p className="text-sm md:text-base font-medium text-gray-800 max-w-2xl font-['Plus_Jakarta_Sans'] mt-2">
          Cross-checks credited bank deposits against verified salary slip net pay. Flags any discrepancies outside the statutory tolerance threshold (greater of ₹500 or 1% of net salary).
        </p>
      </div>

      {/* Summary Alert */}
      <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000] flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-3 border-2 border-black ${
              pendingCount > 0 ? 'bg-amber-300' : 'bg-emerald-300'
            }`}
          >
            {pendingCount > 0 ? (
              <ShieldAlert className="w-6 h-6 text-black stroke-[2.5]" />
            ) : (
              <CheckCircle2 className="w-6 h-6 text-black stroke-[2.5]" />
            )}
          </div>
          <div>
            <h3 className="font-black text-lg uppercase font-['Space_Grotesk']">
              {pendingCount > 0
                ? `${pendingCount} SALARY ITEM${pendingCount > 1 ? 'S' : ''} REQUIRE REVIEW`
                : 'ALL SALARY CREDITS FULLY RECONCILED'}
            </h3>
            <p className="text-xs font-mono text-gray-700">
              Audit Rule: Tolerance limit is greater of ₹500 or 1% of net salary. Unresolved items do not alter your tax computation basis.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="bg-[#FAF7F2] border-2 border-black px-3 py-1 font-mono font-black text-xs shadow-[2px_2px_0px_0px_#000]">
            TOTAL ITEMS: {flags.length}
          </span>
          <span className="bg-[#FACC15] border-2 border-black px-3 py-1 font-mono font-black text-xs shadow-[2px_2px_0px_0px_#000]">
            PENDING: {pendingCount}
          </span>
        </div>
      </div>

      {/* Explanatory Guide Strip */}
      <div className="bg-[#FAF7F2] border-2 border-black p-4 shadow-[3px_3px_0px_0px_#000] text-xs font-mono text-gray-800 flex items-start gap-2.5">
        <HelpCircle className="w-4 h-4 text-[#3730A3] flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-black text-black uppercase block mb-0.5">Why am I seeing these items?</span>
          <span>
            These flags appear when there is an uneven coverage between uploaded bank statements and salary slips (for instance, uploading a payslip for a month whose bank statement is not yet uploaded, or vice-versa). You can resolve them directly below or upload the remaining month's document in Tab 1.
          </span>
        </div>
      </div>

      {/* Flags List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-[#FFFDF9] border-3 border-black p-8 text-center font-mono font-bold">
            CROSS-CHECKING SALARY &amp; BANK STATEMENTS...
          </div>
        ) : flags.length === 0 ? (
          <div className="bg-[#FFFDF9] border-3 border-black p-8 text-center font-mono font-bold text-emerald-800">
            ✓ No reconciliation discrepancies detected. All salary deposits match uploaded payslips within threshold!
          </div>
        ) : (
          flags.map((flag) => {
            const isPending = flag.status === 'pending';
            const isResolved = flag.status === 'resolved';
            const meta = FLAG_TYPE_CONFIG[flag.flag_type] || {
              title: flag.flag_type.replace(/_/g, ' ').toUpperCase(),
              badgeColor: 'bg-gray-200 text-gray-800',
              hint: 'Verify the document records for this month.',
            };

            return (
              <div
                key={flag.id}
                className={`border-3 border-black p-5 shadow-[5px_5px_0px_0px_#000] transition-all ${
                  isPending
                    ? 'bg-[#FFFDF9]'
                    : isResolved
                    ? 'bg-emerald-50 opacity-80'
                    : 'bg-gray-100 opacity-70'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-4 mb-3">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-mono font-black px-2.5 py-0.5 border border-black uppercase ${
                        isPending
                          ? 'bg-[#FACC15] text-black'
                          : isResolved
                          ? 'bg-emerald-400 text-black'
                          : 'bg-gray-300 text-gray-700'
                      }`}
                    >
                      {flag.status.toUpperCase()}
                    </span>
                    <span className={`text-xs font-mono font-black px-2.5 py-0.5 border border-black uppercase ${meta.badgeColor}`}>
                      {meta.title}
                    </span>
                  </div>

                  {flag.discrepancy_amount > 0 && (
                    <div className="font-mono font-black text-sm bg-red-100 border border-black px-2 py-0.5 text-red-900">
                      Discrepancy: ₹{flag.discrepancy_amount.toLocaleString('en-IN')}
                    </div>
                  )}
                </div>

                <div className="mb-3">
                  <p className="text-sm font-bold text-gray-900 font-['Space_Grotesk'] leading-relaxed">
                    {flag.reason}
                  </p>
                  <p className="text-xs font-mono text-gray-600 mt-1">
                    💡 <span className="font-semibold">{meta.hint}</span>
                  </p>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t-2 border-gray-200">
                  <span className="text-[11px] font-mono text-gray-500">
                    Logged: {new Date(flag.created_at).toLocaleDateString('en-IN')}
                  </span>

                  {isPending && (
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleResolve(flag.id, 'resolve')}
                        disabled={resolvingId === flag.id}
                        className="bg-[#10B981] hover:bg-emerald-400 text-black text-xs font-black uppercase px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none flex items-center gap-1.5 transition-all cursor-pointer"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>MARK VERIFIED / RESOLVED</span>
                      </button>

                      <button
                        onClick={() => handleResolve(flag.id, 'ignore')}
                        disabled={resolvingId === flag.id}
                        className="bg-[#FAF7F2] hover:bg-gray-200 text-gray-800 text-xs font-black uppercase px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none flex items-center gap-1.5 transition-all cursor-pointer"
                      >
                        <XCircle className="w-3.5 h-3.5 text-gray-600" />
                        <span>IGNORE / SPLIT</span>
                      </button>
                    </div>
                  )}

                  {!isPending && (
                    <span className="text-xs font-mono font-bold text-emerald-800 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
                      <span>Resolved on {new Date(flag.resolved_at || '').toLocaleDateString('en-IN')}</span>
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
