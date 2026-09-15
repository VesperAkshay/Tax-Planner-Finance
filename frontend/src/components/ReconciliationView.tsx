import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  RefreshCw,
  Sparkles,
  ShieldAlert,
} from 'lucide-react';
import { api } from '../api/client';
import type { ReconciliationFlag } from '../types';

interface ReconciliationViewProps {
  onFlagUpdate?: () => void;
}

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
    <div className="space-y-8">
      {/* Banner */}
      <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-2">
          <div className="inline-flex items-center gap-2 bg-[#F59E0B] px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase text-black">
            <Sparkles className="w-4 h-4" />
            <span>PHASE 9.3 // SALARY RECONCILIATION FLAGS</span>
          </div>

          <button
            onClick={loadFlags}
            className="flex items-center gap-2 bg-[#FAF7F2] hover:bg-gray-100 text-black px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs font-mono"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            RE-RUN ENGINE CHECK
          </button>
        </div>

        <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none">
          RECONCILIATION FLAGS
        </h2>
        <p className="text-sm md:text-base font-medium text-gray-800 max-w-xl font-['Plus_Jakarta_Sans'] mt-2">
          Compares bank salary credits against salary slip net pay. Flags discrepancies outside the
          tolerance boundary ($\max(₹500, 1\%)$).
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
                ? `${pendingCount} ITEMS REQUIRE TAXPAYER REVIEW`
                : 'ALL TRANSACTIONS FULLY RECONCILED'}
            </h3>
            <p className="text-xs font-mono text-gray-700">
              Tolerance applied: max(₹500, 1% of net pay). Unresolved flags do not alter tax engine basis.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="bg-[#FAF7F2] border-2 border-black px-3 py-1 font-mono font-black text-xs shadow-[2px_2px_0px_0px_#000]">
            TOTAL FLAGS: {flags.length}
          </span>
          <span className="bg-[#FACC15] border-2 border-black px-3 py-1 font-mono font-black text-xs shadow-[2px_2px_0px_0px_#000]">
            PENDING: {pendingCount}
          </span>
        </div>
      </div>

      {/* Flags List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-[#FFFDF9] border-3 border-black p-8 text-center font-mono font-bold">
            LOADING FLAGS...
          </div>
        ) : flags.length === 0 ? (
          <div className="bg-[#FFFDF9] border-3 border-black p-8 text-center font-mono font-bold text-emerald-800">
            ✓ No reconciliation flags detected. All salary credits match within threshold!
          </div>
        ) : (
          flags.map((flag) => {
            const isPending = flag.status === 'pending';
            const isResolved = flag.status === 'resolved';

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
                      className={`text-xs font-mono font-black px-2.5 py-1 border border-black uppercase ${
                        isPending
                          ? 'bg-[#FACC15] text-black'
                          : isResolved
                          ? 'bg-emerald-400 text-black'
                          : 'bg-gray-300 text-gray-700'
                      }`}
                    >
                      {flag.status.toUpperCase()}
                    </span>
                    <span className="font-mono text-xs font-bold text-gray-700">
                      FLAG #{flag.id} • {flag.flag_type}
                    </span>
                  </div>

                  {flag.discrepancy_amount > 0 && (
                    <div className="font-mono font-black text-sm bg-red-100 border border-black px-2 py-0.5 text-red-900">
                      Δ ₹{flag.discrepancy_amount.toLocaleString('en-IN')}
                    </div>
                  )}
                </div>

                <p className="text-sm font-semibold text-gray-900 mb-4 font-['Space_Grotesk'] leading-relaxed">
                  {flag.reason}
                </p>

                <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t-2 border-gray-200">
                  <span className="text-[11px] font-mono text-gray-600">
                    Logged: {new Date(flag.created_at).toLocaleDateString('en-IN')}
                  </span>

                  {isPending && (
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleResolve(flag.id, 'resolve')}
                        disabled={resolvingId === flag.id}
                        className="bg-[#10B981] text-black text-xs font-black uppercase px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] hover:bg-emerald-400 active:translate-x-0.5 active:translate-y-0.5 active:shadow-none flex items-center gap-1.5 transition-all"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>MARK VERIFIED / RESOLVED</span>
                      </button>

                      <button
                        onClick={() => handleResolve(flag.id, 'ignore')}
                        disabled={resolvingId === flag.id}
                        className="bg-[#FAF7F2] text-gray-800 text-xs font-black uppercase px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] hover:bg-gray-200 active:translate-x-0.5 active:translate-y-0.5 active:shadow-none flex items-center gap-1.5 transition-all"
                      >
                        <XCircle className="w-3.5 h-3.5 text-gray-600" />
                        <span>IGNORE / SPLIT</span>
                      </button>
                    </div>
                  )}

                  {!isPending && (
                    <span className="text-xs font-mono font-bold text-emerald-800">
                      ✓ Resolved at {new Date(flag.resolved_at || '').toLocaleTimeString()}
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
