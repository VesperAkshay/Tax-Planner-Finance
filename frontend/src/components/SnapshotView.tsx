import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  PiggyBank,
  Percent,
  Calendar,
  AlertCircle,
  Sparkles,
  PieChart,
} from 'lucide-react';
import { api } from '../api/client';
import type { FinancialSnapshot } from '../types';

export const SnapshotView: React.FC = () => {
  const [snapshot, setSnapshot] = useState<FinancialSnapshot | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSnapshot();
  }, []);

  const loadSnapshot = async () => {
    setLoading(true);
    try {
      const data = await api.getFinancialSnapshot();
      setSnapshot(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !snapshot) {
    return (
      <div className="bg-[#FFFDF9] border-4 border-black p-12 text-center shadow-[6px_6px_0px_0px_#000]">
        <span className="font-black text-lg tracking-wider animate-pulse font-mono">
          CALCULATING REAL FINANCIAL SNAPSHOT...
        </span>
      </div>
    );
  }

  if (snapshot.total_transactions_analyzed === 0) {
    return (
      <div className="space-y-8">
        <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
          <div className="inline-flex items-center gap-2 bg-[#3730A3] text-white px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase mb-2">
            <Sparkles className="w-4 h-4 text-[#FACC15]" />
            <span>PHASE 9.2 // CASHFLOW &amp; SPENDING ANALYTICS</span>
          </div>
          <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none">
            FINANCIAL SNAPSHOT
          </h2>
          <p className="text-sm font-medium text-gray-800 max-w-xl font-['Plus_Jakarta_Sans'] mt-2">
            Derived directly from your verified statement uploads with zero fake metrics.
          </p>
        </div>

        <div className="bg-[#FFFDF9] border-4 border-black p-10 shadow-[6px_6px_0px_0px_#000] text-center">
          <div className="p-4 bg-[#FACC15] border-2 border-black inline-block mb-4">
            <PieChart className="w-8 h-8 text-black" />
          </div>
          <h3 className="text-2xl font-black uppercase font-['Space_Grotesk'] mb-2">
            NO TRANSACTIONS INGESTED YET
          </h3>
          <p className="text-xs font-mono text-gray-700 max-w-md mx-auto mb-4 font-bold">
            Your user vault is completely isolated. Go to Tab 1 (Ingest Docs) to upload your bank statement CSV/PDF and generate your real cashflow metrics!
          </p>
          <div className="font-mono text-xs bg-[#FAF7F2] border-2 border-black p-3 max-w-md mx-auto">
            TOTAL INCOME: ₹0.00 • TOTAL EXPENSES: ₹0.00 • SAVINGS: 0%
          </div>
        </div>
      </div>
    );
  }

  const categoryColors = [
    'bg-[#FACC15]', // Yellow
    'bg-[#F59E0B]', // Marigold
    'bg-[#3730A3] text-white', // Indigo
    'bg-[#10B981] text-black', // Emerald
    'bg-[#FB7185] text-black', // Rose
    'bg-[#60A5FA] text-black', // Blue
    'bg-[#C084FC] text-black', // Purple
    'bg-[#A3E635] text-black', // Lime
  ];

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-2">
          <div className="inline-flex items-center gap-2 bg-[#3730A3] text-white px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase">
            <Sparkles className="w-4 h-4 text-[#FACC15]" />
            <span>PHASE 9.2 // CASHFLOW &amp; SPENDING ANALYTICS</span>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs font-bold bg-[#FFFDF9] px-3 py-1 border-2 border-black">
            <Calendar className="w-3.5 h-3.5 text-gray-700" />
            <span>FY 2025–26 (01 APR 2025 – 31 MAR 2026)</span>
          </div>
        </div>

        <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none">
          FINANCIAL SNAPSHOT
        </h2>
        <p className="text-sm md:text-base font-medium text-gray-800 max-w-xl font-['Plus_Jakarta_Sans'] mt-2">
          Aggregated cashflow derived from verified statement uploads. Automatically isolates self-transfers
          and groups expenses through calibrated ML categorization.
        </p>
      </div>

      {/* KPI Cards (4 Column Grid) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Income */}
        <div className="bg-[#FFFDF9] border-4 border-black p-5 shadow-[6px_6px_0px_0px_#000]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-black uppercase text-gray-700 font-['Space_Grotesk']">
              TOTAL INCOME
            </span>
            <div className="p-2 bg-[#FACC15] border-2 border-black">
              <TrendingUp className="w-5 h-5 text-black stroke-[2.5]" />
            </div>
          </div>
          <div className="font-mono text-3xl font-black text-black">
            ₹{snapshot.total_income.toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] font-mono text-emerald-800 font-bold mt-2">
            ✓ Verified Salary + Credits
          </p>
        </div>

        {/* Total Expenses */}
        <div className="bg-[#FFFDF9] border-4 border-black p-5 shadow-[6px_6px_0px_0px_#000]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-black uppercase text-gray-700 font-['Space_Grotesk']">
              TOTAL EXPENSES
            </span>
            <div className="p-2 bg-[#FB7185] border-2 border-black">
              <TrendingDown className="w-5 h-5 text-black stroke-[2.5]" />
            </div>
          </div>
          <div className="font-mono text-3xl font-black text-black">
            ₹{snapshot.total_expenses.toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] font-mono text-gray-600 font-bold mt-2">
            Excludes self-transfers
          </p>
        </div>

        {/* Net Savings */}
        <div className="bg-[#FFFDF9] border-4 border-black p-5 shadow-[6px_6px_0px_0px_#000]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-black uppercase text-gray-700 font-['Space_Grotesk']">
              NET SAVINGS
            </span>
            <div className="p-2 bg-[#F59E0B] border-2 border-black">
              <PiggyBank className="w-5 h-5 text-black stroke-[2.5]" />
            </div>
          </div>
          <div className="font-mono text-3xl font-black text-[#3730A3]">
            ₹{snapshot.net_savings.toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] font-mono text-gray-600 font-bold mt-2">
            Income minus outlays
          </p>
        </div>

        {/* Savings Rate */}
        <div className="bg-[#FFFDF9] border-4 border-black p-5 shadow-[6px_6px_0px_0px_#000]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-black uppercase text-gray-700 font-['Space_Grotesk']">
              SAVINGS RATE
            </span>
            <div className="p-2 bg-[#3730A3] border-2 border-black">
              <Percent className="w-5 h-5 text-white stroke-[2.5]" />
            </div>
          </div>
          <div className="font-mono text-3xl font-black text-black">
            {snapshot.savings_rate.toFixed(1)}%
          </div>
          <p className="text-[11px] font-mono text-emerald-800 font-bold mt-2">
            ★ Healthy financial buffer
          </p>
        </div>
      </div>

      {/* Category Spending Breakdown (Bento Grid) */}
      <div className="bg-[#FFFDF9] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b-3 border-black pb-4 mb-6">
          <div>
            <h3 className="text-2xl font-black uppercase font-['Space_Grotesk'] tracking-tight">
              CATEGORY SPENDING BREAKDOWN
            </h3>
            <p className="text-xs font-mono text-gray-700 mt-1">
              Classified via 384-d MiniLM embeddings + Logistic Regression classifier.
            </p>
          </div>
          <span className="bg-[#FACC15] text-black text-xs font-mono font-black px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
            {snapshot.category_spending.length} ACTIVE CATEGORIES
          </span>
        </div>

        {/* Stacked Neo-Brutalist Visual Progress Bar */}
        <div className="w-full h-8 border-3 border-black flex overflow-hidden shadow-[4px_4px_0px_0px_#000] mb-8 bg-gray-200">
          {snapshot.category_spending.map((cat, idx) => (
            <div
              key={cat.category_name}
              style={{ width: `${cat.percentage_of_total}%` }}
              title={`${cat.category_name}: ${cat.percentage_of_total}%`}
              className={`${categoryColors[idx % categoryColors.length]} border-r-2 border-black relative group transition-all duration-200 hover:opacity-90`}
            />
          ))}
        </div>

        {/* Category Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {snapshot.category_spending.map((cat, idx) => (
            <div
              key={cat.category_name}
              className="bg-[#FAF7F2] border-2 border-black p-4 shadow-[4px_4px_0px_0px_#000] flex flex-col justify-between"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-black text-sm uppercase tracking-wide">
                  {cat.category_name}
                </span>
                <span
                  className={`text-[11px] font-black px-2 py-0.5 border border-black font-mono ${
                    categoryColors[idx % categoryColors.length]
                  }`}
                >
                  {cat.percentage_of_total.toFixed(1)}%
                </span>
              </div>
              <div className="font-mono text-xl font-black text-black">
                ₹{cat.amount.toLocaleString('en-IN')}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Informational Brutalist Strip */}
      <div className="bg-[#FAF7F2] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000] flex items-center gap-3">
        <AlertCircle className="w-5 h-5 text-[#3730A3] flex-shrink-0" />
        <p className="text-xs font-bold text-gray-800 font-mono">
          Self-transfers between user accounts have been isolated by Phase 2 reconciler to prevent
          double-counting in expenditure calculations.
        </p>
      </div>
    </div>
  );
};
