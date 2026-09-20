import React, { useEffect, useState } from 'react';
import {
  X,
  Users,
  ShieldCheck,
  Lightbulb,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { api } from '../api/client';
import type { HouseholdSummaryResponse } from '../types';

interface HouseholdSummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectProfile?: (profileId: number) => void;
}

export const HouseholdSummaryModal: React.FC<HouseholdSummaryModalProps> = ({
  isOpen,
  onClose,
  onSelectProfile,
}) => {
  const [summary, setSummary] = useState<HouseholdSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadHouseholdSummary();
    }
  }, [isOpen]);

  const loadHouseholdSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHouseholdSummary();
      setSummary(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load household summary.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/65 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto font-mono">
      <div className="bg-[#FFFDF9] border-4 border-black w-full max-w-3xl shadow-[10px_10px_0px_0px_#000000] flex flex-col animate-in fade-in zoom-in-95 duration-150 my-6">
        {/* Header */}
        <div className="bg-[#18153B] text-white p-4 border-b-3 border-black flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#FACC15] text-black border border-black shadow-[2px_2px_0px_0px_#000]">
              <Users className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="bg-[#FACC15] text-black text-[10px] font-black px-1.5 py-0.2 border border-black uppercase font-mono">
                  HOUSEHOLD TAX HUB
                </span>
                <span className="text-gray-300 text-xs font-bold">FY 2025–26</span>
              </div>
              <h3 className="font-black text-lg uppercase font-['Space_Grotesk'] text-[#FACC15] leading-tight">
                JOINT FAMILY TAX OPTIMIZER &amp; ARBITRAGE
              </h3>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadHouseholdSummary}
              disabled={loading}
              className="text-white hover:text-[#FACC15] p-1.5 border border-white/20 hover:border-[#FACC15] cursor-pointer"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="text-white hover:text-[#FACC15] p-1.5 border border-white/20 hover:border-[#FACC15] cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-6 text-xs">
          {loading ? (
            <div className="p-12 text-center space-y-3">
              <div className="w-8 h-8 border-4 border-black border-t-[#FACC15] rounded-full animate-spin mx-auto" />
              <p className="font-black uppercase tracking-wider">
                COMPUTING JOINT HOUSEHOLD SLABS &amp; ARBITRAGE...
              </p>
            </div>
          ) : error || !summary ? (
            <div className="p-6 bg-red-100 border-2 border-black text-red-900 font-bold text-center">
              {error || 'Unable to compute household summary.'}
            </div>
          ) : (
            <>
              {/* Executive Summary Metrics Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-[#FAF7F2] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000]">
                  <span className="text-[10px] uppercase font-bold text-gray-600 block">
                    TOTAL HOUSEHOLD GROSS
                  </span>
                  <span className="text-2xl font-black text-[#18153B] font-['Space_Grotesk'] mt-1 block">
                    ₹{summary.total_household_income.toLocaleString('en-IN')}
                  </span>
                  <span className="text-[10px] text-gray-500 font-semibold mt-0.5 block">
                    Across {summary.members_count} family profile(s)
                  </span>
                </div>

                <div className="bg-[#FAF7F2] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000]">
                  <span className="text-[10px] uppercase font-bold text-gray-600 block">
                    TOTAL FAMILY TAX OUTFLOW
                  </span>
                  <span className="text-2xl font-black text-[#3730A3] font-['Space_Grotesk'] mt-1 block">
                    ₹{summary.total_household_tax.toLocaleString('en-IN')}
                  </span>
                  <span className="text-[10px] text-emerald-700 font-black mt-0.5 block flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" />
                    <span>Calculated with zero arithmetic drift</span>
                  </span>
                </div>

                <div className="bg-[#FAF7F2] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000]">
                  <span className="text-[10px] uppercase font-bold text-gray-600 block">
                    TOTAL JOINT TAX SAVINGS
                  </span>
                  <span className="text-2xl font-black text-emerald-600 font-['Space_Grotesk'] mt-1 block">
                    ₹{summary.total_household_savings.toLocaleString('en-IN')}
                  </span>
                  <span className="text-[10px] text-gray-600 font-semibold mt-0.5 block">
                    Via optimal regime selection
                  </span>
                </div>
              </div>

              {/* Family Members Breakdown Table */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-black text-xs uppercase tracking-wider text-[#18153B] flex items-center gap-1.5">
                    <Users className="w-4 h-4 text-[#3730A3]" />
                    <span>TAXPAYER BREAKDOWN PER FAMILY MEMBER:</span>
                  </h4>
                  <span className="text-[11px] text-gray-500 font-bold">
                    Click member to switch active workspace
                  </span>
                </div>

                <div className="border-3 border-black bg-white overflow-x-auto shadow-[4px_4px_0px_0px_#000]">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-[#18153B] text-white border-b-2 border-black font-black uppercase text-[10px]">
                        <th className="p-3 border-r border-black/30">Taxpayer</th>
                        <th className="p-3 border-r border-black/30">Persona</th>
                        <th className="p-3 border-r border-black/30">Gross Income</th>
                        <th className="p-3 border-r border-black/30">Deductions</th>
                        <th className="p-3 border-r border-black/30">Recommended</th>
                        <th className="p-3 border-r border-black/30">Optimal Tax</th>
                        <th className="p-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y-2 divide-black/10 font-bold">
                      {summary.members.map((m) => (
                        <tr key={m.profile_id} className="hover:bg-[#FAF7F2] transition-colors">
                          <td className="p-3 border-r border-black/20">
                            <span className="font-black text-[#18153B] block">{m.name}</span>
                            <span className="text-[10px] text-gray-500 uppercase">
                              {m.relationship} {m.pan ? `• ${m.pan}` : ''}
                            </span>
                          </td>
                          <td className="p-3 border-r border-black/20 font-mono text-[11px]">
                            <span className="bg-gray-100 border border-black px-1.5 py-0.5 text-[10px]">
                              {m.persona.toUpperCase()}
                            </span>
                          </td>
                          <td className="p-3 border-r border-black/20 font-mono">
                            ₹{m.gross_income.toLocaleString('en-IN')}
                          </td>
                          <td className="p-3 border-r border-black/20 font-mono text-emerald-700">
                            ₹{m.total_deductions.toLocaleString('en-IN')}
                          </td>
                          <td className="p-3 border-r border-black/20">
                            <span className="bg-[#FACC15] text-black border border-black px-1.5 py-0.5 text-[10px] font-black">
                              {m.recommended_regime}
                            </span>
                          </td>
                          <td className="p-3 border-r border-black/20 font-mono font-black text-[#3730A3]">
                            ₹{m.optimal_tax.toLocaleString('en-IN')}
                          </td>
                          <td className="p-3 text-right">
                            {onSelectProfile && (
                              <button
                                onClick={() => {
                                  onSelectProfile(m.profile_id);
                                  onClose();
                                }}
                                className="bg-[#FAF7F2] hover:bg-[#FACC15] text-black border border-black px-2.5 py-1 text-[10px] font-black uppercase shadow-[1px_1px_0px_0px_#000] cursor-pointer"
                              >
                                SWITCH
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Joint Household Deduction Arbitrage Advice */}
              <div className="bg-[#FFFDF9] border-3 border-black p-4 space-y-3 shadow-[4px_4px_0px_0px_#000]">
                <div className="flex items-center gap-2 border-b-2 border-black pb-2">
                  <div className="p-1 bg-[#FACC15] border border-black">
                    <Lightbulb className="w-4 h-4 text-black" />
                  </div>
                  <div>
                    <h4 className="font-black text-xs uppercase tracking-wider text-[#18153B]">
                      💡 HOUSEHOLD DEDUCTION ARBITRAGE OPPORTUNITIES
                    </h4>
                    <p className="text-[11px] text-gray-600 font-semibold font-['Plus_Jakarta_Sans']">
                      Strategically routing investments across family PANs maximizes joint tax relief.
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  {summary.arbitrage_opportunities.map((item, idx) => (
                    <div
                      key={idx}
                      className="bg-amber-50 border-2 border-black p-3 space-y-1.5 shadow-[2px_2px_0px_0px_#000]"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-black text-xs text-[#3730A3] uppercase">
                          {item.title}
                        </span>
                        <span className="bg-emerald-200 text-emerald-950 font-mono font-black text-[10px] px-2 py-0.5 border border-black">
                          SAVE UP TO ₹{item.impact_amount.toLocaleString('en-IN')}
                        </span>
                      </div>
                      <p className="text-xs text-gray-800 font-medium font-['Plus_Jakarta_Sans'] leading-relaxed">
                        {item.description}
                      </p>
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-gray-700 bg-white p-1.5 border border-black mt-1">
                        <ArrowRight className="w-3.5 h-3.5 text-black flex-shrink-0" />
                        <span>Action: {item.actionable_tip}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-[#FAF7F2] border-t-3 border-black flex items-center justify-between">
          <span className="text-[11px] text-gray-600 font-bold">
            100% Exact Math Guarantee • Section 115BAC &amp; Chapter VI-A
          </span>
          <button
            onClick={onClose}
            className="bg-[#18153B] text-white hover:bg-black px-6 py-2 border-2 border-black font-black uppercase text-xs shadow-[2px_2px_0px_0px_#000] cursor-pointer"
          >
            CLOSE HUB
          </button>
        </div>
      </div>
    </div>
  );
};
