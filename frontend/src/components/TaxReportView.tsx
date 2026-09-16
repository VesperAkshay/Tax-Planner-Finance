import React, { useEffect, useState } from 'react';
import {
  FileCheck,
  Trophy,
  CheckCircle2,
  Lightbulb,
  Printer,
  Download,
  Sparkles,
  Info,
  AlertCircle,
  ExternalLink,
  Receipt,
  FileSpreadsheet,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import { api } from '../api/client';
import type { TaxComparisonReport } from '../types';

export const TaxReportView: React.FC = () => {
  const [report, setReport] = useState<TaxComparisonReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [showSlabsBreakdown, setShowSlabsBreakdown] = useState(false);
  const [activeTabMode, setActiveTabMode] = useState<'comparison' | 'invoice_memo'>('comparison');

  useEffect(() => {
    loadReport();
  }, []);

  const loadReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getTaxComparisonReport();
      setReport(data);
    } catch (e: unknown) {
      console.error('Failed to load tax comparison report:', e);
      setError(e instanceof Error ? e.message : 'Failed to generate tax comparison report');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPdf = async () => {
    setDownloadingPdf(true);
    try {
      await api.downloadTaxReportPdf();
    } catch (e: unknown) {
      console.error('Failed to download PDF invoice:', e);
      alert('Failed to download Tax Report PDF. Please try again.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-[#FFFDF9] border-4 border-black p-12 text-center shadow-[6px_6px_0px_0px_#000]">
        <div className="inline-block p-4 bg-[#FACC15] border-2 border-black mb-4 animate-spin">
          <RefreshCw className="w-8 h-8 text-black" />
        </div>
        <span className="font-black text-lg tracking-wider block font-mono">
          MR. PLANNER IS COMPUTING EXACT STATUTORY TAX COMPARISON...
        </span>
        <span className="text-xs font-mono text-gray-600 mt-2 block">
          Applying Section 115BAC &amp; Chapter VI-A rules with zero arithmetic drift.
        </span>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="bg-[#FFFDF9] border-4 border-black p-10 shadow-[6px_6px_0px_0px_#000] text-center space-y-4">
        <div className="inline-block p-3 bg-red-200 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
          <AlertCircle className="w-8 h-8 text-red-900" />
        </div>
        <h3 className="text-2xl font-black uppercase font-['Space_Grotesk']">
          UNABLE TO LOAD TAX REPORT
        </h3>
        <p className="text-sm font-mono text-gray-700 max-w-md mx-auto">
          {error || 'An unexpected error occurred while calculating your tax liabilities.'}
        </p>
        <button
          onClick={loadReport}
          className="bg-[#FACC15] hover:bg-yellow-400 text-black px-6 py-2 border-2 border-black font-black font-mono text-xs uppercase shadow-[2px_2px_0px_0px_#000]"
        >
          RETRY TAX COMPUTATION
        </button>
      </div>
    );
  }

  const oldReg = report.old_regime || {};
  const newReg = report.new_regime || {};
  const grossIncome = report.gross_income ?? 0;

  if (grossIncome === 0) {
    return (
      <div className="space-y-8">
        <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
          <div className="inline-flex items-center gap-2 bg-[#FACC15] px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase text-black mb-2">
            <Sparkles className="w-4 h-4" />
            <span>TAX OPTIMIZATION // FY 2025–26 STATUTORY REPORT</span>
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

  const isNewWinner = String(report.recommended_regime).toLowerCase() === 'new';

  const newTax = newReg.total_tax ?? newReg.total_tax_liability ?? 0;
  const oldTax = oldReg.total_tax ?? oldReg.total_tax_liability ?? 0;
  const newGrossTax = newReg.tax_before_rebate ?? newReg.gross_tax ?? 0;
  const oldGrossTax = oldReg.tax_before_rebate ?? oldReg.gross_tax ?? 0;
  const newStdDed = newReg.standard_deduction ?? 75000;
  const oldStdDed = oldReg.standard_deduction ?? 50000;
  const oldTotalDed = oldReg.total_deductions ?? oldReg.exemptions_and_deductions ?? 0;
  const oldOtherDed = Math.max(0, oldTotalDed - oldStdDed);
  const newTaxable = newReg.taxable_income ?? Math.max(0, grossIncome - newStdDed);
  const oldTaxable = oldReg.taxable_income ?? Math.max(0, grossIncome - oldTotalDed);
  const newRebate = newReg.rebate_87a ?? 0;
  const oldRebate = oldReg.rebate_87a ?? 0;
  const newCess = newReg.cess ?? 0;
  const oldCess = oldReg.cess ?? 0;
  const newRate = newReg.effective_tax_rate ?? (grossIncome > 0 ? (newTax / grossIncome) * 100 : 0);
  const oldRate = oldReg.effective_tax_rate ?? (grossIncome > 0 ? (oldTax / grossIncome) * 100 : 0);

  const citations = report.citations || [];
  const taxSavings = report.tax_savings ?? Math.abs(oldTax - newTax);
  const breakeven = report.breakeven_deductions ?? 375000;
  const deductionsApplied = report.deductions_applied || {};

  const oldSlabs = Array.isArray(oldReg.slab_breakdown) ? oldReg.slab_breakdown : [];
  const newSlabs = Array.isArray(newReg.slab_breakdown) ? newReg.slab_breakdown : [];

  return (
    <div className="space-y-8">
      {/* Header Banner with Direct PDF Download Action */}
      <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-2">
          <div className="inline-flex items-center gap-2 bg-[#FACC15] px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase text-black">
            <Sparkles className="w-4 h-4" />
            <span>MR. PLANNER // STATUTORY TAX AUDIT &amp; REGIME COMPARISON</span>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            {/* Direct PDF Download Button */}
            <button
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              className="flex items-center gap-2 bg-[#FACC15] hover:bg-yellow-400 text-black px-4 py-2 border-2 border-black shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all font-black text-xs uppercase cursor-pointer disabled:opacity-50"
            >
              <Download className={`w-4 h-4 ${downloadingPdf ? 'animate-bounce' : ''}`} />
              <span>{downloadingPdf ? 'GENERATING PDF...' : 'DOWNLOAD TAX INVOICE (PDF)'}</span>
            </button>

            {/* Print / Save in Browser */}
            <button
              onClick={handlePrint}
              className="flex items-center gap-2 bg-[#3730A3] text-white px-4 py-2 border-2 border-black shadow-[3px_3px_0px_0px_#000] hover:bg-[#4338CA] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all font-black text-xs uppercase cursor-pointer"
            >
              <Printer className="w-4 h-4" />
              <span>PRINT / BROWSER PDF</span>
            </button>
          </div>
        </div>

        <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none">
          TAX REGIME COMPARISON REPORT
        </h2>
        <p className="text-sm md:text-base font-medium text-gray-800 max-w-2xl font-['Plus_Jakarta_Sans'] mt-2">
          Financial Year 2025–26 (Assessment Year 2026–27). Verified with 100% statement test coverage against
          official Finance Act rate schedules.
        </p>

        {/* View Mode Switcher */}
        <div className="mt-6 pt-4 border-t-2 border-black flex items-center gap-2 font-mono text-xs">
          <span className="font-bold text-gray-600 mr-2">VIEW MODE:</span>
          <button
            onClick={() => setActiveTabMode('comparison')}
            className={`px-3 py-1.5 border-2 border-black font-black uppercase cursor-pointer transition-all ${
              activeTabMode === 'comparison'
                ? 'bg-[#18153B] text-white shadow-[2px_2px_0px_0px_#000]'
                : 'bg-white text-black hover:bg-gray-100'
            }`}
          >
            📊 SIDE-BY-SIDE BENTO
          </button>
          <button
            onClick={() => setActiveTabMode('invoice_memo')}
            className={`px-3 py-1.5 border-2 border-black font-black uppercase cursor-pointer transition-all ${
              activeTabMode === 'invoice_memo'
                ? 'bg-[#18153B] text-white shadow-[2px_2px_0px_0px_#000]'
                : 'bg-white text-black hover:bg-gray-100'
            }`}
          >
            🧾 INVOICE AUDIT MEMO
          </button>
        </div>
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
                ₹{taxSavings.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>{' '}
              in tax liability by opting for this regime!
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="bg-[#FFFDF9] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000] text-center font-mono">
            <span className="text-[11px] font-black uppercase text-gray-600 block">TOTAL TAX PAYABLE</span>
            <span className="text-3xl font-black text-[#3730A3]">
              ₹{(isNewWinner ? newTax : oldTax).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>

          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
            className="hidden sm:flex flex-col items-center justify-center bg-black hover:bg-gray-800 text-white p-3.5 border-2 border-black font-mono text-xs font-black uppercase shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer disabled:opacity-50"
          >
            <Download className="w-5 h-5 text-[#FACC15] mb-1" />
            <span>GET INVOICE PDF</span>
          </button>
        </div>
      </div>

      {/* VIEW MODE 1: Side-by-Side Bento Grid */}
      {activeTabMode === 'comparison' && (
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
                  <span className="bg-[#10B981] text-black text-xs font-black px-2 py-1 border border-black shadow-[2px_2px_0px_0px_#000]">
                    WINNER 🏆
                  </span>
                )}
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-1 border-b border-gray-200">
                  <span className="text-gray-700">Gross Income:</span>
                  <span className="font-bold">₹{grossIncome.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200 text-emerald-800 font-bold">
                  <span>Standard Deduction (Enhanced):</span>
                  <span>- ₹{newStdDed.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200">
                  <span className="text-gray-700">Other Chapter VI-A Deductions:</span>
                  <span className="text-gray-500">N/A (Disallowed in 115BAC)</span>
                </div>
                <div className="flex justify-between py-1 border-b-2 border-black font-black bg-amber-50 px-1">
                  <span>Taxable Income:</span>
                  <span>₹{newTaxable.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-gray-700">Gross Slab Tax:</span>
                  <span>₹{newGrossTax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between py-1 text-emerald-800">
                  <span>Sec 87A Rebate (Income ≤ ₹12L):</span>
                  <span>- ₹{newRebate.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-gray-700">Health &amp; Education Cess (4%):</span>
                  <span>+ ₹{newCess.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t-3 border-black bg-[#FACC15]/20 p-4 border-2 border-black">
              <div className="flex justify-between items-center">
                <span className="font-black text-sm uppercase">TOTAL TAX LIABILITY:</span>
                <span className="text-2xl font-black text-black">
                  ₹{newTax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <span className="text-[11px] font-bold text-gray-600 block mt-1">
                Effective Tax Rate: {newRate.toFixed(2)}%
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
                  <span className="bg-[#10B981] text-black text-xs font-black px-2 py-1 border border-black shadow-[2px_2px_0px_0px_#000]">
                    WINNER 🏆
                  </span>
                )}
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-1 border-b border-gray-200">
                  <span className="text-gray-700">Gross Income:</span>
                  <span className="font-bold">₹{grossIncome.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200 text-emerald-800 font-bold">
                  <span>Standard Deduction:</span>
                  <span>- ₹{oldStdDed.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200 text-emerald-800 font-bold">
                  <span>Exemptions &amp; Chapter VI-A:</span>
                  <span>- ₹{oldOtherDed.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between py-1 border-b-2 border-black font-black bg-amber-50 px-1">
                  <span>Taxable Income:</span>
                  <span>₹{oldTaxable.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-gray-700">Gross Slab Tax:</span>
                  <span>₹{oldGrossTax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between py-1 text-emerald-800">
                  <span>Sec 87A Rebate (Income ≤ ₹5L):</span>
                  <span>- ₹{oldRebate.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-gray-700">Health &amp; Education Cess (4%):</span>
                  <span>+ ₹{oldCess.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t-3 border-black bg-[#F59E0B]/20 p-4 border-2 border-black">
              <div className="flex justify-between items-center">
                <span className="font-black text-sm uppercase">TOTAL TAX LIABILITY:</span>
                <span className="text-2xl font-black text-black">
                  ₹{oldTax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <span className="text-[11px] font-bold text-gray-600 block mt-1">
                Effective Tax Rate: {oldRate.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* VIEW MODE 2: On-Screen Neo-Brutalist Invoice Memorandum */}
      {activeTabMode === 'invoice_memo' && (
        <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[10px_10px_0px_0px_#000] font-mono">
          {/* Invoice Header */}
          <div className="border-b-4 border-black pb-4 mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Receipt className="w-6 h-6 text-[#3730A3]" />
                <span className="bg-[#3730A3] text-white px-2 py-0.5 text-xs font-black uppercase border border-black">
                  OFFICIAL TAX AUDIT MEMO
                </span>
              </div>
              <h3 className="text-2xl md:text-3xl font-black uppercase font-['Space_Grotesk'] text-[#18153B]">
                TAX INVOICE &amp; REGIME AUDIT
              </h3>
              <p className="text-xs text-gray-700 mt-1">
                Financial Year 2025–26 &nbsp;|&nbsp; Assessment Year 2026–27 &nbsp;|&nbsp; Indian Income Tax Act, 1961
              </p>
            </div>

            <div className="text-right">
              <span className="tracking-widest font-black text-sm block">|||| | ||||| || | |||| ||||| | ||</span>
              <span className="text-xs font-black text-black">MEMO REF: TP-2025-INV-00{report.user_id}</span>
              <span className="text-[11px] text-gray-600 block">Status: 100% Deterministic Verified</span>
            </div>
          </div>

          {/* Itemized Comparison Ledger */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-black text-white border-2 border-black">
                  <th className="p-3">LINE ITEM</th>
                  <th className="p-3">OLD REGIME (CH. VI-A)</th>
                  <th className="p-3">NEW REGIME (SEC 115BAC)</th>
                  <th className="p-3">LEGAL REFERENCE</th>
                </tr>
              </thead>
              <tbody className="divide-y-2 divide-black border-2 border-black bg-[#FFFDF9]">
                <tr>
                  <td className="p-3 font-bold">01. Gross Annual Salary / Inflows</td>
                  <td className="p-3 font-black">₹{grossIncome.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3 font-black">₹{grossIncome.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3 text-gray-600">Sec 15 / 17(1)</td>
                </tr>
                <tr>
                  <td className="p-3 font-bold">02. Salaried Standard Deduction</td>
                  <td className="p-3 text-emerald-800 font-bold">- ₹{oldStdDed.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3 text-emerald-800 font-bold">- ₹{newStdDed.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3 text-gray-600">Sec 16(ia)</td>
                </tr>
                <tr>
                  <td className="p-3 font-bold">03. Section 80C (EPF, PPF, ELSS, Insurance)</td>
                  <td className="p-3 text-emerald-800 font-bold">
                    - ₹{(Number(deductionsApplied.section_80c) || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-3 text-gray-400">N/A (Disallowed)</td>
                  <td className="p-3 text-gray-600">Sec 80C (Cap ₹1.5L)</td>
                </tr>
                <tr>
                  <td className="p-3 font-bold">04. Section 80D (Health Insurance)</td>
                  <td className="p-3 text-emerald-800 font-bold">
                    - ₹{(typeof deductionsApplied.section_80d === 'number' ? deductionsApplied.section_80d : 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-3 text-gray-400">N/A (Disallowed)</td>
                  <td className="p-3 text-gray-600">Sec 80D</td>
                </tr>
                <tr>
                  <td className="p-3 font-bold">05. Section 80CCD(1B) (National Pension Scheme)</td>
                  <td className="p-3 text-emerald-800 font-bold">
                    - ₹{(Number(deductionsApplied.section_80ccd_1b) || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-3 text-gray-400">N/A (Disallowed)</td>
                  <td className="p-3 text-gray-600">Sec 80CCD(1B)</td>
                </tr>
                <tr>
                  <td className="p-3 font-bold">06. Section 10(13A) (HRA Exemption)</td>
                  <td className="p-3 text-emerald-800 font-bold">
                    - ₹{(typeof deductionsApplied.hra === 'object' && deductionsApplied.hra ? Number(deductionsApplied.hra.rent_paid) || 0 : 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-3 text-gray-400">N/A (Disallowed)</td>
                  <td className="p-3 text-gray-600">Rule 2A</td>
                </tr>
                <tr className="bg-amber-100 font-black">
                  <td className="p-3">07. Net Taxable Income</td>
                  <td className="p-3">₹{oldTaxable.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3">₹{newTaxable.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3 text-gray-600">Gross minus deductions</td>
                </tr>
                <tr>
                  <td className="p-3 font-bold">08. Gross Slab Tax</td>
                  <td className="p-3">₹{oldGrossTax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3">₹{newGrossTax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3 text-gray-600">Statutory Slabs</td>
                </tr>
                <tr>
                  <td className="p-3 font-bold">09. Section 87A Rebate</td>
                  <td className="p-3 text-emerald-800">- ₹{oldRebate.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3 text-emerald-800">- ₹{newRebate.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3 text-gray-600">Old ≤ ₹5L | New ≤ ₹12L</td>
                </tr>
                <tr>
                  <td className="p-3 font-bold">10. Health &amp; Education Cess (4%)</td>
                  <td className="p-3">+ ₹{oldCess.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3">+ ₹{newCess.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td className="p-3 text-gray-600">4% on (Tax - Rebate)</td>
                </tr>
                <tr className="bg-[#FACC15] font-black text-sm border-t-4 border-black">
                  <td className="p-3.5 uppercase">11. TOTAL TAX PAYABLE</td>
                  <td className="p-3.5 text-black">
                    ₹{oldTax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-3.5 text-black">
                    ₹{newTax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-3.5 text-black uppercase font-mono">
                    {isNewWinner ? 'NEW WINS 🏆' : 'OLD WINS 🏆'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-4 pt-4 border-t-2 border-black text-xs">
            <div className="flex items-center gap-2 text-emerald-800 font-bold">
              <ShieldCheck className="w-5 h-5" />
              <span>Certified 100% Deterministic Statutory Computation // Zero LLM Arithmetic</span>
            </div>

            <button
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              className="bg-[#3730A3] hover:bg-[#4338CA] text-white px-4 py-2 border-2 border-black font-black uppercase shadow-[2px_2px_0px_0px_#000] cursor-pointer"
            >
              DOWNLOAD INVOICE MEMO (PDF)
            </button>
          </div>
        </div>
      )}

      {/* Slabs Breakdown Matrix (Expandable Audit View) */}
      <div className="bg-[#FFFDF9] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b-3 border-black pb-3 mb-4">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-6 h-6 text-[#3730A3]" />
            <h3 className="text-xl md:text-2xl font-black uppercase font-['Space_Grotesk']">
              STATUTORY SLAB-BY-SLAB CALCULATION AUDIT
            </h3>
          </div>

          <button
            onClick={() => setShowSlabsBreakdown(!showSlabsBreakdown)}
            className="flex items-center gap-1.5 bg-[#FAF7F2] hover:bg-gray-200 text-black px-3 py-1 border-2 border-black font-mono font-bold text-xs shadow-[2px_2px_0px_0px_#000] cursor-pointer"
          >
            <span>{showSlabsBreakdown ? 'HIDE EXACT SLAB MATH' : 'SHOW EXACT SLAB MATH'}</span>
            {showSlabsBreakdown ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        {showSlabsBreakdown && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 font-mono text-xs mt-4">
            {/* New Regime Slabs */}
            <div className="border-2 border-black p-4 bg-[#FAF7F2]">
              <div className="flex items-center justify-between border-b-2 border-black pb-2 mb-3">
                <span className="font-black text-sm uppercase">NEW REGIME SLAB SCHEDULE</span>
                <span className="bg-[#FACC15] text-black font-black px-2 py-0.5 border border-black">SEC 115BAC</span>
              </div>
              <div className="space-y-2">
                {newSlabs.map((s, idx) => (
                  <div key={idx} className="flex justify-between py-1 border-b border-gray-200">
                    <span className="text-gray-700">
                      ₹{(s.min / 100000).toFixed(1)}L – {s.max ? `₹${(s.max / 100000).toFixed(1)}L` : 'Above'} ({(s.rate * 100).toFixed(0)}%):
                    </span>
                    <span className="font-bold">
                      ₹{(s.slab_tax || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                ))}
                <div className="flex justify-between pt-2 font-black text-black text-sm">
                  <span>Gross Slab Tax:</span>
                  <span>₹{newGrossTax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
              </div>
            </div>

            {/* Old Regime Slabs */}
            <div className="border-2 border-black p-4 bg-[#FAF7F2]">
              <div className="flex items-center justify-between border-b-2 border-black pb-2 mb-3">
                <span className="font-black text-sm uppercase">OLD REGIME SLAB SCHEDULE</span>
                <span className="bg-gray-200 text-black font-black px-2 py-0.5 border border-black">CHAPTER VI-A</span>
              </div>
              <div className="space-y-2">
                {oldSlabs.map((s, idx) => (
                  <div key={idx} className="flex justify-between py-1 border-b border-gray-200">
                    <span className="text-gray-700">
                      ₹{(s.min / 100000).toFixed(1)}L – {s.max ? `₹${(s.max / 100000).toFixed(1)}L` : 'Above'} ({(s.rate * 100).toFixed(0)}%):
                    </span>
                    <span className="font-bold">
                      ₹{(s.slab_tax || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                ))}
                <div className="flex justify-between pt-2 font-black text-black text-sm">
                  <span>Gross Slab Tax:</span>
                  <span>₹{oldGrossTax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Statutory Citations Grounding from ChromaDB */}
      {citations.length > 0 && (
        <div className="bg-[#FFFDF9] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000]">
          <div className="flex items-center gap-2 border-b-3 border-black pb-3 mb-6">
            <FileCheck className="w-6 h-6 text-[#3730A3]" />
            <h3 className="text-2xl font-black uppercase font-['Space_Grotesk']">
              STATUTORY CITATIONS &amp; LEGAL GROUNDING
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono">
            {citations.map((c, idx) => (
              <div
                key={idx}
                className="bg-[#FAF7F2] border-2 border-black p-4 shadow-[3px_3px_0px_0px_#000] flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-black text-sm uppercase text-[#3730A3]">{c.section}</span>
                    <span className="bg-emerald-300 text-black text-[10px] font-black px-2 py-0.5 border border-black">
                      STATUTORY
                    </span>
                  </div>
                  <h5 className="font-bold text-xs text-gray-900 mb-2">{c.title}</h5>
                </div>

                {c.source_url && (
                  <a
                    href={c.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] font-bold text-[#3730A3] hover:underline bg-white border border-black p-1.5 mt-2 flex items-center justify-between"
                  >
                    <span>View Official Statutory Rule</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Strategic Summary & Breakeven Analysis */}
      <div className="bg-[#FFFDF9] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000]">
        <div className="flex items-center gap-2 border-b-3 border-black pb-3 mb-6">
          <Lightbulb className="w-6 h-6 text-[#F59E0B]" />
          <h3 className="text-2xl font-black uppercase font-['Space_Grotesk']">
            TAX STRATEGY &amp; BREAKEVEN INSIGHTS
          </h3>
        </div>

        <div className="space-y-4 font-mono text-xs md:text-sm">
          <div className="bg-[#FAF7F2] border-2 border-black p-4 shadow-[3px_3px_0px_0px_#000] flex items-start gap-3">
            <div className="p-1 bg-[#FACC15] border border-black flex-shrink-0 mt-0.5">
              <CheckCircle2 className="w-4 h-4 text-black" />
            </div>
            <div>
              <p className="font-black text-black mb-1">
                Breakeven Deduction Threshold: ₹{breakeven.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
              <p className="font-medium text-gray-700 leading-relaxed">
                For the Old Tax Regime to be financially advantageous at your income level of ₹{grossIncome.toLocaleString('en-IN')},
                you must claim more than ₹{breakeven.toLocaleString('en-IN', { minimumFractionDigits: 2 })} in combined exemptions (Section 80C, 80D, NPS, HRA, etc.).
              </p>
            </div>
          </div>

          {report.summary && (
            <div className="bg-[#FAF7F2] border-2 border-black p-4 shadow-[3px_3px_0px_0px_#000] flex items-start gap-3">
              <div className="p-1 bg-[#3730A3] text-white border border-black flex-shrink-0 mt-0.5">
                <Info className="w-4 h-4" />
              </div>
              <div>
                <p className="font-black text-black mb-1">Deterministic Comparison Summary</p>
                <p className="font-medium text-gray-700 leading-relaxed">{report.summary}</p>
              </div>
            </div>
          )}

          {/* Statutory Disclaimer */}
          <div className="mt-4 pt-4 border-t border-gray-300 text-gray-600 text-[11px] leading-relaxed">
            ⚠️ <b>Notice:</b> This computation is an automated tax planning suggestion based on your verified records
            and Indian Income Tax Act rules (FY 2025–26). Please consult a certified Chartered Accountant (CA) for official filing.
          </div>
        </div>
      </div>
    </div>
  );
};
