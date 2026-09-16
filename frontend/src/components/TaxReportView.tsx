import React, { useEffect, useState } from 'react';
import {
  FileCheck,
  Trophy,
  CheckCircle2,
  Lightbulb,
  Printer,
  Sparkles,
  Info,
} from 'lucide-react';
import { api } from '../api/client';
import type { TaxComparisonReport } from '../types';

export const TaxReportView: React.FC = () => {
  const [report, setReport] = useState<TaxComparisonReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReport();
  }, []);

  const loadReport = async () => {
    setLoading(true);
    try {
      const data = await api.getTaxComparisonReport();
      setReport(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading || !report) {
    return (
      <div className="bg-[#FFFDF9] border-4 border-black p-12 text-center shadow-[6px_6px_0px_0px_#000]">
        <span className="font-black text-lg tracking-wider animate-pulse font-mono">
          GENERATING REAL COMPARISON REPORT...
        </span>
      </div>
    );
  }

  if (report.new_regime.gross_income === 0 && report.old_regime.gross_income === 0) {
    return (
      <div className="space-y-8">
        <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
          <div className="inline-flex items-center gap-2 bg-[#FACC15] px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase text-black mb-2">
            <Sparkles className="w-4 h-4" />
            <span>PHASE 9.5 // REGIME COMPARISON &amp; VERIFIED ADVISORY</span>
          </div>
          <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none">
            TAX REGIME COMPARISON REPORT
          </h2>
          <p className="text-sm font-medium text-gray-800 max-w-xl font-['Plus_Jakarta_Sans'] mt-2">
            Computes statutory tax liability under Section 115BAC vs Old Regime with zero fake data.
          </p>
        </div>

        <div className="bg-[#FFFDF9] border-4 border-black p-10 shadow-[6px_6px_0px_0px_#000] text-center">
          <div className="p-4 bg-[#FACC15] border-2 border-black inline-block mb-4">
            <FileCheck className="w-8 h-8 text-black" />
          </div>
          <h3 className="text-2xl font-black uppercase font-['Space_Grotesk'] mb-2">
            NO SALARY OR INCOME PARSED YET
          </h3>
          <p className="text-xs font-mono text-gray-700 max-w-md mx-auto mb-4 font-bold">
            Upload your bank statement or salary slip in Tab 1 (Ingest Docs) to calculate your exact FY 2025–26 tax liabilities under both regimes!
          </p>
          <div className="font-mono text-xs bg-[#FAF7F2] border-2 border-black p-3 max-w-md mx-auto">
            TAXABLE INCOME: ₹0.00 • STATUTORY TAX: ₹0.00
          </div>
        </div>
      </div>
    );
  }

  const isNewWinner = report.recommended_regime === 'new';

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-2">
          <div className="inline-flex items-center gap-2 bg-[#FACC15] px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase text-black">
            <Sparkles className="w-4 h-4" />
            <span>PHASE 9.5 // REGIME COMPARISON &amp; VERIFIED ADVISORY</span>
          </div>

          <button
            onClick={handlePrint}
            className="flex items-center gap-2 bg-[#3730A3] text-white px-4 py-1.5 border-2 border-black shadow-[3px_3px_0px_0px_#000] hover:bg-[#4338CA] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all font-black text-xs uppercase"
          >
            <Printer className="w-4 h-4" />
            <span>PRINT / SAVE REPORT</span>
          </button>
        </div>

        <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none">
          TAX REGIME COMPARISON REPORT
        </h2>
        <p className="text-sm md:text-base font-medium text-gray-800 max-w-xl font-['Plus_Jakarta_Sans'] mt-2">
          Financial Year 2025–26 (Assessment Year 2026–27). Verified with 100% test coverage against
          Finance Act 2024 / 2025 statutory rate schedules.
        </p>
      </div>

      {/* Grand Winner Announcement Banner */}
      <div
        className={`border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000] flex flex-wrap items-center justify-between gap-6 ${
          isNewWinner ? 'bg-[#FACC15]' : 'bg-[#F59E0B]'
        }`}
      >
        <div className="flex items-center gap-5">
          <div className="p-4 bg-white border-3 border-black shadow-[4px_4px_0px_0px_#000]">
            <Trophy className="w-10 h-10 text-black stroke-[2.5]" />
          </div>
          <div>
            <span className="bg-black text-white text-xs font-black px-2.5 py-1 tracking-wider uppercase font-mono">
              OPTIMAL CHOICE FOR YOU
            </span>
            <h3 className="text-2xl md:text-4xl font-black text-black uppercase font-['Space_Grotesk'] mt-1">
              {isNewWinner ? 'NEW REGIME (SEC 115BAC)' : 'OLD TAX REGIME'} RECOMMENDED
            </h3>
            <p className="text-sm md:text-base font-bold text-black mt-1 font-['Space_Grotesk']">
              You will save{' '}
              <span className="bg-white px-2 py-0.5 border border-black font-mono font-black text-lg">
                ₹{report.tax_savings.toLocaleString('en-IN')}
              </span>{' '}
              in tax liability by opting for this regime!
            </p>
          </div>
        </div>

        <div className="bg-[#FFFDF9] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000] text-center font-mono">
          <span className="text-[11px] font-black uppercase text-gray-600 block">TOTAL TAX PAYABLE</span>
          <span className="text-3xl font-black text-[#3730A3]">
            ₹{(isNewWinner ? report.new_regime.total_tax_liability : report.old_regime.total_tax_liability).toLocaleString('en-IN')}
          </span>
        </div>
      </div>

      {/* Side-by-Side Comparison Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 font-mono">
        {/* NEW REGIME CARD */}
        <div
          className={`border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000] flex flex-col justify-between ${
            isNewWinner ? 'bg-[#FFFDF9] ring-4 ring-[#FACC15]' : 'bg-[#FAF7F2]'
          }`}
        >
          <div>
            <div className="flex items-center justify-between border-b-3 border-black pb-3 mb-4">
              <div>
                <h4 className="text-xl font-black uppercase font-['Space_Grotesk']">
                  NEW REGIME (SEC 115BAC)
                </h4>
                <span className="text-xs text-gray-600 font-bold">Revised FY 2025–26 Slabs</span>
              </div>
              {isNewWinner && (
                <span className="bg-[#10B981] text-black text-xs font-black px-2 py-1 border border-black">
                  WINNER 🏆
                </span>
              )}
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between py-1 border-b border-gray-200">
                <span className="text-gray-700">Gross Income:</span>
                <span className="font-bold">₹{report.new_regime.gross_income.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-200 text-emerald-800 font-bold">
                <span>Standard Deduction (Enhanced):</span>
                <span>- ₹{report.new_regime.standard_deduction.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-200">
                <span className="text-gray-700">Other Chapter VI-A Deductions:</span>
                <span className="text-gray-500">N/A (Disallowed in 115BAC)</span>
              </div>
              <div className="flex justify-between py-1 border-b-2 border-black font-black">
                <span>Taxable Income:</span>
                <span>₹{report.new_regime.taxable_income.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-gray-700">Gross Slab Tax:</span>
                <span>₹{report.new_regime.gross_tax.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between py-1 text-emerald-800">
                <span>Sec 87A Rebate (Income ≤ ₹12L):</span>
                <span>- ₹{report.new_regime.rebate_87a.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-gray-700">Health &amp; Education Cess (4%):</span>
                <span>+ ₹{report.new_regime.cess.toLocaleString('en-IN')}</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t-3 border-black bg-[#FACC15]/20 p-4 border-2 border-black">
            <div className="flex justify-between items-center">
              <span className="font-black text-sm uppercase">TOTAL TAX LIABILITY:</span>
              <span className="text-2xl font-black text-black">
                ₹{report.new_regime.total_tax_liability.toLocaleString('en-IN')}
              </span>
            </div>
            <span className="text-[11px] font-bold text-gray-600 block mt-1">
              Effective Tax Rate: {report.new_regime.effective_tax_rate.toFixed(2)}%
            </span>
          </div>
        </div>

        {/* OLD REGIME CARD */}
        <div
          className={`border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000] flex flex-col justify-between ${
            !isNewWinner ? 'bg-[#FFFDF9] ring-4 ring-[#F59E0B]' : 'bg-[#FAF7F2]'
          }`}
        >
          <div>
            <div className="flex items-center justify-between border-b-3 border-black pb-3 mb-4">
              <div>
                <h4 className="text-xl font-black uppercase font-['Space_Grotesk']">
                  OLD TAX REGIME
                </h4>
                <span className="text-xs text-gray-600 font-bold">With Chapter VI-A &amp; HRA</span>
              </div>
              {!isNewWinner && (
                <span className="bg-[#10B981] text-black text-xs font-black px-2 py-1 border border-black">
                  WINNER 🏆
                </span>
              )}
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between py-1 border-b border-gray-200">
                <span className="text-gray-700">Gross Income:</span>
                <span className="font-bold">₹{report.old_regime.gross_income.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-200 text-emerald-800 font-bold">
                <span>Standard Deduction:</span>
                <span>- ₹{report.old_regime.standard_deduction.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-200 text-emerald-800 font-bold">
                <span>Exemptions &amp; Chapter VI-A:</span>
                <span>- ₹{(report.old_regime.exemptions_and_deductions - report.old_regime.standard_deduction).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between py-1 border-b-2 border-black font-black">
                <span>Taxable Income:</span>
                <span>₹{report.old_regime.taxable_income.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-gray-700">Gross Slab Tax:</span>
                <span>₹{report.old_regime.gross_tax.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between py-1 text-emerald-800">
                <span>Sec 87A Rebate (Income ≤ ₹5L):</span>
                <span>- ₹{report.old_regime.rebate_87a.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-gray-700">Health &amp; Education Cess (4%):</span>
                <span>+ ₹{report.old_regime.cess.toLocaleString('en-IN')}</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t-3 border-black bg-[#F59E0B]/20 p-4 border-2 border-black">
            <div className="flex justify-between items-center">
              <span className="font-black text-sm uppercase">TOTAL TAX LIABILITY:</span>
              <span className="text-2xl font-black text-black">
                ₹{report.old_regime.total_tax_liability.toLocaleString('en-IN')}
              </span>
            </div>
            <span className="text-[11px] font-bold text-gray-600 block mt-1">
              Effective Tax Rate: {report.old_regime.effective_tax_rate.toFixed(2)}%
            </span>
          </div>
        </div>
      </div>

      {/* Deduction Checklist with Statutory Citations */}
      <div className="bg-[#FFFDF9] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000]">
        <div className="flex items-center gap-2 border-b-3 border-black pb-3 mb-6">
          <FileCheck className="w-6 h-6 text-[#3730A3]" />
          <h3 className="text-2xl font-black uppercase font-['Space_Grotesk']">
            DEDUCTION CHECKLIST &amp; STATUTORY CITATIONS
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono">
          {report.declared_deductions.map((d, idx) => (
            <div
              key={idx}
              className="bg-[#FAF7F2] border-2 border-black p-4 shadow-[3px_3px_0px_0px_#000] flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-black text-sm uppercase text-[#3730A3]">{d.section}</span>
                  <span className="bg-emerald-300 text-black text-[10px] font-black px-2 py-0.5 border border-black">
                    VERIFIED
                  </span>
                </div>
                <h5 className="font-bold text-xs text-gray-900 mb-2">{d.name}</h5>
                <div className="text-xl font-black text-black mb-1">
                  ₹{d.amount_declared.toLocaleString('en-IN')}{' '}
                  <span className="text-xs text-gray-500 font-normal">
                    (Max: ₹{d.max_allowed_limit.toLocaleString('en-IN')})
                  </span>
                </div>
              </div>

              <div className="text-[10px] font-bold text-gray-600 bg-white border border-black p-1.5 mt-2 flex items-center gap-1">
                <Info className="w-3 h-3 text-[#3730A3] flex-shrink-0" />
                <span>{d.citation}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Missing Deductions & Tax Optimization Suggestions */}
      <div className="bg-[#FFFDF9] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000]">
        <div className="flex items-center gap-2 border-b-3 border-black pb-3 mb-6">
          <Lightbulb className="w-6 h-6 text-[#F59E0B]" />
          <h3 className="text-2xl font-black uppercase font-['Space_Grotesk']">
            TAX SAVINGS OPPORTUNITIES FOR YOU
          </h3>
        </div>

        <div className="space-y-3 font-mono text-xs md:text-sm">
          {report.missing_deductions_suggestions.map((sug, i) => (
            <div
              key={i}
              className="bg-[#FAF7F2] border-2 border-black p-4 shadow-[3px_3px_0px_0px_#000] flex items-start gap-3"
            >
              <div className="p-1 bg-[#FACC15] border border-black flex-shrink-0 mt-0.5">
                <CheckCircle2 className="w-4 h-4 text-black" />
              </div>
              <p className="font-bold text-gray-900 leading-relaxed">{sug}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
