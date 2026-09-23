import React, { useState } from 'react';
import {
  TrendingUp,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  ChevronDown,
  CheckCircle2,
  Users,
  CircleAlert,
  ChevronUp,
} from 'lucide-react';
import type {
  TaxpayerProfile,
  ProfileReadinessResponse,
  TaxComparisonReport,
} from '../types';

interface TaxFlightDeckProps {
  readiness: ProfileReadinessResponse | null;
  report: TaxComparisonReport | null;
  flagCount: number;
  activeProfile: TaxpayerProfile | null;
  profiles: TaxpayerProfile[];
  onSelectProfile: (id: number) => void;
  onNavigateToSubView: (view: string) => void;
  onOpenHousehold: () => void;
}

export const TaxFlightDeck: React.FC<TaxFlightDeckProps> = ({
  readiness,
  report,
  flagCount,
  activeProfile,
  profiles,
  onSelectProfile,
  onNavigateToSubView,
  onOpenHousehold,
}) => {
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const [readinessPopoverOpen, setReadinessPopoverOpen] = useState(false);

  // Compute live financial metrics
  const grossIncome = report?.gross_income ?? 0;
  const newRegimeTax = report?.new_regime?.total_tax ?? report?.new_regime?.total_tax_liability ?? 0;
  const oldRegimeTax = report?.old_regime?.total_tax ?? report?.old_regime?.total_tax_liability ?? 0;
  const recommendedRegime = report?.recommended_regime ?? (newRegimeTax <= oldRegimeTax ? 'new' : 'old');
  const optimalTax = recommendedRegime === 'new' ? newRegimeTax : oldRegimeTax;
  const taxSavings = report?.tax_savings ?? Math.abs(oldRegimeTax - newRegimeTax);
  const readinessScore = readiness?.overall_score ?? 0;

  // Determine Dynamic Smart Directive
  const getSmartDirective = () => {
    if (flagCount > 0) {
      return {
        type: 'warning' as const,
        icon: <AlertTriangle className="w-4 h-4 text-rose-600 animate-pulse" />,
        text: `Audit Alert: ${flagCount} Net Pay Discrepanc${flagCount > 1 ? 'ies' : 'y'} detected between salary slips and bank credits.`,
        actionLabel: 'Audit Flags ➔',
        targetView: 'reconciliation',
      };
    }
    if (!report || grossIncome === 0) {
      return {
        type: 'action' as const,
        icon: <Sparkles className="w-4 h-4 text-[#FACC15]" />,
        text: 'Vault Empty: Drop your Form 16, Salary Slips, or Bank Statements to begin your audit.',
        actionLabel: 'Drop Files ➔',
        targetView: 'upload',
      };
    }
    if (readiness && !readiness.is_filing_ready) {
      return {
        type: 'action' as const,
        icon: <TrendingUp className="w-4 h-4 text-amber-500" />,
        text: readiness.next_step || 'Review Chapter VI-A deductions to maximize Old vs New regime arbitrage.',
        actionLabel: 'Optimize ➔',
        targetView: 'catalog',
      };
    }
    return {
      type: 'success' as const,
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-500" />,
      text: 'All Checks Passed! Your return is audit-ready under Finance Act 2025–26 rules.',
      actionLabel: 'View Final Report ➔',
      targetView: 'report',
    };
  };

  const directive = getSmartDirective();

  return (
    <div className="space-y-2 select-none">
      {/* ========================================================================= */}
      {/* 1. MAIN COCKPIT / HUD STRIP                                               */}
      {/* ========================================================================= */}
      <div className="bg-[#FAF7F2] border-4 border-black p-3 sm:p-4 shadow-[6px_6px_0px_0px_#000] relative">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 items-center">
          {/* Tile 1: Gross Income Detected */}
          <div className="bg-white border-2 border-black p-2.5 sm:p-3 shadow-[2px_2px_0px_0px_#000]">
            <span className="font-mono text-[10px] sm:text-xs font-black text-gray-500 uppercase block tracking-wider">
              GROSS INCOME (PARSED)
            </span>
            <div className="text-lg sm:text-2xl font-black font-mono text-[#18153B] mt-0.5 truncate">
              {grossIncome > 0 ? `₹${grossIncome.toLocaleString('en-IN')}` : '₹0.00'}
            </div>
            <span className="text-[10px] font-mono text-gray-500 flex items-center gap-1 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              {report?.gross_income_extrapolated ? 'Annualized Estimate' : 'Document Verified'}
            </span>
          </div>

          {/* Tile 2: Optimal Regime Live Tracker */}
          <div className="bg-white border-2 border-black p-2.5 sm:p-3 shadow-[2px_2px_0px_0px_#000] relative overflow-hidden">
            <span className="font-mono text-[10px] sm:text-xs font-black text-gray-500 uppercase block tracking-wider">
              OPTIMAL TAX REGIME
            </span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span
                className={`font-black font-mono text-xs sm:text-sm px-2 py-0.5 border border-black uppercase ${
                  recommendedRegime === 'new'
                    ? 'bg-[#18153B] text-[#FACC15]'
                    : 'bg-emerald-300 text-emerald-950'
                }`}
              >
                {recommendedRegime.toUpperCase()} REGIME
              </span>
            </div>
            <div className="text-[10px] sm:text-[11px] font-mono font-bold text-emerald-700 mt-1 truncate">
              {taxSavings > 0
                ? `⚡ Saves ₹${Math.round(taxSavings).toLocaleString('en-IN')} vs ${recommendedRegime === 'new' ? 'Old' : 'New'}`
                : optimalTax === 0
                ? 'Zero Tax (§87A Rebate)'
                : 'Equal Tax Liability'}
            </div>
          </div>

          {/* Tile 3: Live Tax Due */}
          <div className="bg-white border-2 border-black p-2.5 sm:p-3 shadow-[2px_2px_0px_0px_#000]">
            <span className="font-mono text-[10px] sm:text-xs font-black text-gray-500 uppercase block tracking-wider">
              STATUTORY TAX DUE
            </span>
            <div className="text-lg sm:text-2xl font-black font-mono text-rose-600 mt-0.5 truncate">
              ₹{Math.round(optimalTax).toLocaleString('en-IN')}
            </div>
            <span className="text-[10px] font-mono text-gray-500 block mt-0.5">
              Incl. 4% Cess &amp; §87A
            </span>
          </div>

          {/* Tile 4: Interactive Readiness Radial & Profile Context */}
          <div className="bg-white border-2 border-black p-2.5 sm:p-3 shadow-[2px_2px_0px_0px_#000] flex flex-col justify-between relative">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] sm:text-xs font-black text-gray-500 uppercase tracking-wider">
                FILING READINESS
              </span>
              <button
                onClick={() => setReadinessPopoverOpen(!readinessPopoverOpen)}
                className="font-mono text-[10px] font-bold text-[#18153B] hover:underline flex items-center gap-0.5"
                title="View milestone audit checklist"
              >
                {readinessScore}%
                {readinessPopoverOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            </div>

            {/* Visual Progress Bar */}
            <div className="w-full bg-gray-200 h-2.5 border border-black my-1.5 overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  readinessScore >= 90
                    ? 'bg-emerald-500'
                    : readinessScore >= 60
                    ? 'bg-[#FACC15]'
                    : 'bg-rose-500'
                }`}
                style={{ width: `${readinessScore}%` }}
              />
            </div>

            {/* Profile Dropdown Trigger */}
            <div className="flex items-center justify-between pt-0.5">
              <div className="relative">
                <button
                  onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                  className="font-mono text-[10px] font-bold bg-gray-100 hover:bg-gray-200 border border-black px-1.5 py-0.5 flex items-center gap-1 cursor-pointer"
                  title="Switch Taxpayer Profile"
                >
                  <span className="truncate max-w-[90px]">
                    {activeProfile?.name || 'PRIMARY'}
                  </span>
                  <ChevronDown className="w-2.5 h-2.5 text-gray-600" />
                </button>

                {/* Profile Switcher Menu */}
                {profileDropdownOpen && (
                  <div className="absolute left-0 bottom-full mb-1 z-50 bg-white border-2 border-black p-2 shadow-[4px_4px_0px_0px_#000] min-w-[180px] font-mono text-xs space-y-1">
                    <span className="text-[10px] font-bold text-gray-500 uppercase block border-b pb-1">
                      SWITCH PROFILE
                    </span>
                    {profiles.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => {
                          onSelectProfile(p.id);
                          setProfileDropdownOpen(false);
                        }}
                        className={`w-full text-left px-2 py-1 flex items-center justify-between text-[11px] ${
                          p.id === activeProfile?.id
                            ? 'bg-[#18153B] text-white font-bold'
                            : 'hover:bg-gray-100 text-black'
                        }`}
                      >
                        <span className="truncate">{p.name}</span>
                        <span className="text-[9px] uppercase opacity-75">{p.relationship}</span>
                      </button>
                    ))}
                    <button
                      onClick={() => {
                        setProfileDropdownOpen(false);
                        onOpenHousehold();
                      }}
                      className="w-full text-left px-2 py-1 text-[10px] font-bold text-[#18153B] bg-amber-100 hover:bg-amber-200 border-t mt-1 flex items-center gap-1"
                    >
                      <Users className="w-3 h-3" />
                      Joint Family Hub
                    </button>
                  </div>
                )}
              </div>

              <span className="font-mono text-[10px] font-black text-gray-600">
                AY 2026–27
              </span>
            </div>
          </div>
        </div>

        {/* Milestone Popover Drawer */}
        {readinessPopoverOpen && readiness?.milestones && (
          <div className="mt-3 pt-3 border-t-2 border-black font-mono text-xs bg-[#FFFDF9] p-3 border-2 border-black shadow-[3px_3px_0px_0px_#000] animate-fade-in">
            <div className="flex items-center justify-between mb-2">
              <span className="font-black text-xs uppercase text-[#18153B] flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                Filing Readiness Audit Milestones
              </span>
              <button
                onClick={() => setReadinessPopoverOpen(false)}
                className="text-[10px] font-bold text-gray-500 hover:text-black"
              >
                ✕ Close
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
              {readiness.milestones.map((m, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    if (m.action_tab) onNavigateToSubView(m.action_tab);
                    setReadinessPopoverOpen(false);
                  }}
                  className={`p-2 border border-black cursor-pointer transition-all ${
                    m.is_complete
                      ? 'bg-emerald-50 border-emerald-500'
                      : 'bg-white hover:bg-amber-50'
                  }`}
                >
                  <div className="flex items-center justify-between text-[11px] font-bold">
                    <span>{m.name}</span>
                    {m.is_complete ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <CircleAlert className="w-3.5 h-3.5 text-amber-500" />
                    )}
                  </div>
                  <p className="text-[10px] text-gray-600 mt-1 line-clamp-1">{m.details}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 2. DYNAMIC SMART DIRECTIVE BAR ("Next Best Action")                       */}
      {/* ========================================================================= */}
      <div
        className={`border-3 border-black p-2.5 sm:p-3 shadow-[4px_4px_0px_0px_#000] flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono ${
          directive.type === 'warning'
            ? 'bg-rose-100 border-rose-600 text-rose-950'
            : directive.type === 'action'
            ? 'bg-[#FFFDF9] text-[#18153B]'
            : 'bg-emerald-100 text-emerald-950'
        }`}
      >
        <div className="flex items-center gap-2">
          {directive.icon}
          <span className="font-bold">{directive.text}</span>
        </div>

        <button
          onClick={() => onNavigateToSubView(directive.targetView)}
          className="bg-[#18153B] hover:bg-[#252055] text-white border-2 border-black px-3 py-1 font-black text-xs uppercase flex items-center justify-center gap-1.5 shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer self-end sm:self-auto shrink-0"
        >
          <span>{directive.actionLabel}</span>
        </button>
      </div>
    </div>
  );
};
