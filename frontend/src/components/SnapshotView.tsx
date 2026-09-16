import React, { useEffect, useState, useMemo } from 'react';
import {
  TrendingUp,
  TrendingDown,
  PiggyBank,
  Percent,
  Calendar,
  AlertCircle,
  Sparkles,
  PieChart,
  Flame,
  ShieldCheck,
  RefreshCw,
  Search,
  CheckCircle2,
  Receipt,
  Tag,
  ArrowUpRight,
  ArrowDownLeft,
} from 'lucide-react';
import { api } from '../api/client';
import type { FinancialSnapshot } from '../types';

interface SnapshotViewProps {
  onNavigateToTab?: (tab: any) => void;
}

export const SnapshotView: React.FC<SnapshotViewProps> = ({ onNavigateToTab }) => {
  const [snapshot, setSnapshot] = useState<FinancialSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recategorizing, setRecategorizing] = useState(false);
  const [recategorizeMessage, setRecategorizeMessage] = useState<string | null>(null);

  // Search & Filter state for Transactions Explorer
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedType, setSelectedType] = useState<string>('ALL');

  useEffect(() => {
    loadSnapshot();
  }, []);

  const loadSnapshot = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getFinancialSnapshot();
      setSnapshot(data);
    } catch (e: unknown) {
      console.error(e);
      setError(e instanceof Error ? e.message : 'Failed to retrieve financial snapshot');
    } finally {
      setLoading(false);
    }
  };

  const handleReCategorize = async () => {
    setRecategorizing(true);
    setRecategorizeMessage(null);
    try {
      const res = await api.reCategorizeTransactions();
      setRecategorizeMessage(res.message);
      await loadSnapshot();
    } catch (e: unknown) {
      setRecategorizeMessage(e instanceof Error ? e.message : 'Re-categorization failed');
    } finally {
      setRecategorizing(false);
    }
  };

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

  // Filtered transactions
  const filteredTransactions = useMemo(() => {
    if (!snapshot?.recent_transactions) return [];
    return snapshot.recent_transactions.filter((txn) => {
      const matchesSearch =
        txn.merchant.toLowerCase().includes(searchQuery.toLowerCase()) ||
        txn.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory =
        selectedCategory === 'ALL' || txn.category.toLowerCase() === selectedCategory.toLowerCase();
      const matchesType =
        selectedType === 'ALL' || txn.transaction_type.toLowerCase() === selectedType.toLowerCase();
      return matchesSearch && matchesCategory && matchesType;
    });
  }, [snapshot?.recent_transactions, searchQuery, selectedCategory, selectedType]);

  if (loading) {
    return (
      <div className="bg-[#FFFDF9] border-4 border-black p-12 text-center shadow-[6px_6px_0px_0px_#000]">
        <div className="animate-spin inline-block w-8 h-8 border-4 border-black border-t-[#FACC15] rounded-full mb-3" />
        <p className="font-black text-lg tracking-wider font-mono">
          AGGREGATING REAL CASHFLOW &amp; INTELLIGENT ANALYTICS...
        </p>
      </div>
    );
  }

  if (error || !snapshot) {
    return (
      <div className="bg-[#FFFDF9] border-4 border-black p-10 shadow-[6px_6px_0px_0px_#000] text-center space-y-4">
        <div className="inline-block p-3 bg-red-200 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
          <AlertCircle className="w-8 h-8 text-red-900" />
        </div>
        <h3 className="text-2xl font-black uppercase font-['Space_Grotesk']">
          UNABLE TO LOAD SNAPSHOT
        </h3>
        <p className="font-mono text-xs text-gray-700 max-w-md mx-auto font-bold">
          {error || 'No snapshot data available. Upload a bank statement in Tab 1 to populate.'}
        </p>
        <button
          onClick={loadSnapshot}
          className="bg-[#FACC15] hover:bg-yellow-400 text-black px-4 py-2 border-2 border-black font-black font-mono text-xs shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5"
        >
          RETRY LOADING
        </button>
      </div>
    );
  }

  if (snapshot.total_transactions_analyzed === 0) {
    return (
      <div className="space-y-8">
        <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
          <div className="inline-flex items-center gap-2 bg-[#3730A3] text-white px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase mb-2">
            <Sparkles className="w-4 h-4 text-[#FACC15]" />
            <span>FINANCIAL INTELLIGENCE // CASHFLOW &amp; BUDGET ANALYTICS</span>
          </div>
          <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none">
            FINANCIAL SNAPSHOT
          </h2>
          <p className="text-sm font-medium text-gray-800 max-w-xl font-['Plus_Jakarta_Sans'] mt-2">
            Derived directly from your verified statement uploads with zero synthetic metrics.
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
            Upload your bank statement in Tab 1 (Ingest Docs) to activate real-time merchant categorization, 50/30/20 budget diagnostic, and tax deduction discovery.
          </p>
        </div>
      </div>
    );
  }

  const budgetDiag = snapshot.budget_rule_diagnostic;

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-2">
          <div className="inline-flex items-center gap-2 bg-[#3730A3] text-white px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase">
            <Sparkles className="w-4 h-4 text-[#FACC15]" />
            <span>FINANCIAL INTELLIGENCE // AI CATEGORIZATION ENGINE</span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 font-mono text-xs font-bold bg-[#FFFDF9] px-3 py-1 border-2 border-black">
              <Calendar className="w-3.5 h-3.5 text-gray-700" />
              <span>FY 2025–26 (01 APR 2025 – 31 MAR 2026)</span>
            </div>

            <button
              onClick={handleReCategorize}
              disabled={recategorizing}
              className="bg-[#FACC15] hover:bg-yellow-400 text-black px-3 py-1 border-2 border-black font-black font-mono text-xs shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${recategorizing ? 'animate-spin' : ''}`} />
              <span>{recategorizing ? 'RE-CATEGORIZING...' : 'UPGRADE CATEGORIES'}</span>
            </button>
          </div>
        </div>

        <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none">
          FINANCIAL SNAPSHOT
        </h2>
        <p className="text-sm md:text-base font-medium text-gray-800 max-w-2xl font-['Plus_Jakarta_Sans'] mt-2">
          Aggregated cashflow &amp; spending analytics powered by our hybrid Indian Merchant Pattern Matcher + XGBoost + OpenRouter LLM pipeline.
        </p>

        {recategorizeMessage && (
          <div className="mt-4 p-3 bg-emerald-100 border-2 border-black font-mono text-xs font-bold text-emerald-900 flex items-center gap-2 shadow-[2px_2px_0px_0px_#000]">
            <CheckCircle2 className="w-4 h-4 text-emerald-700 flex-shrink-0" />
            <span>{recategorizeMessage}</span>
          </div>
        )}
      </div>

      {/* KPI Metric Cards (5 Columns) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Income */}
        <div className="bg-[#FFFDF9] border-4 border-black p-5 shadow-[6px_6px_0px_0px_#000]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-black uppercase text-gray-700 font-['Space_Grotesk']">
              TOTAL INFLOWS
            </span>
            <div className="p-2 bg-[#FACC15] border-2 border-black">
              <TrendingUp className="w-5 h-5 text-black stroke-[2.5]" />
            </div>
          </div>
          <div className="font-mono text-2xl md:text-3xl font-black text-black">
            ₹{snapshot.total_income.toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] font-mono text-emerald-800 font-bold mt-2">
            ✓ Verified Salary &amp; Credits
          </p>
        </div>

        {/* Total Expenses */}
        <div className="bg-[#FFFDF9] border-4 border-black p-5 shadow-[6px_6px_0px_0px_#000]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-black uppercase text-gray-700 font-['Space_Grotesk']">
              TOTAL OUTFLOWS
            </span>
            <div className="p-2 bg-[#FB7185] border-2 border-black">
              <TrendingDown className="w-5 h-5 text-black stroke-[2.5]" />
            </div>
          </div>
          <div className="font-mono text-2xl md:text-3xl font-black text-black">
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
          <div className="font-mono text-2xl md:text-3xl font-black text-[#3730A3]">
            ₹{snapshot.net_savings.toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] font-mono text-gray-600 font-bold mt-2">
            Net Monthly Surplus
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
          <div className="font-mono text-2xl md:text-3xl font-black text-black">
            {snapshot.savings_rate.toFixed(1)}%
          </div>
          <p className="text-[11px] font-mono text-emerald-800 font-bold mt-2">
            ★ Benchmark: &gt;20%
          </p>
        </div>

        {/* Daily Burn Rate */}
        <div className="bg-[#FFFDF9] border-4 border-black p-5 shadow-[6px_6px_0px_0px_#000]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-black uppercase text-gray-700 font-['Space_Grotesk']">
              DAILY BURN
            </span>
            <div className="p-2 bg-orange-400 border-2 border-black">
              <Flame className="w-5 h-5 text-black stroke-[2.5]" />
            </div>
          </div>
          <div className="font-mono text-2xl md:text-3xl font-black text-black">
            ₹{(snapshot.daily_burn_rate ?? 0).toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] font-mono text-gray-600 font-bold mt-2">
            Average Spend / Day
          </p>
        </div>
      </div>

      {/* 50/30/20 Budget Rule Diagnostic Card */}
      {budgetDiag && budgetDiag.status !== 'No Data' && (
        <div className="bg-[#FFFDF9] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000]">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b-3 border-black pb-4 mb-6">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <ShieldCheck className="w-5 h-5 text-[#3730A3]" />
                <h3 className="text-2xl font-black uppercase font-['Space_Grotesk'] tracking-tight">
                  50 / 30 / 20 BUDGET DIAGNOSTIC
                </h3>
              </div>
              <p className="text-xs font-mono text-gray-700">
                Measures essential Needs (50%), discretionary Wants (30%), and Savings (20%).
              </p>
            </div>
            <span className="bg-[#3730A3] text-white text-xs font-mono font-black px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] uppercase">
              STATUS: {budgetDiag.status}
            </span>
          </div>

          {/* 3-Bar Comparison Progress */}
          <div className="space-y-4 mb-6">
            {/* Needs */}
            <div>
              <div className="flex justify-between font-mono text-xs font-bold mb-1">
                <span>ESSENTIAL NEEDS (Rent, Groceries, Utilities, Medical)</span>
                <span>₹{budgetDiag.needs_amount.toLocaleString('en-IN')} ({budgetDiag.needs_pct}% / Target: 50%)</span>
              </div>
              <div className="w-full h-4 bg-gray-200 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
                <div
                  className={`h-full border-r-2 border-black ${
                    budgetDiag.needs_pct > 55 ? 'bg-rose-500' : 'bg-emerald-400'
                  }`}
                  style={{ width: `${Math.min(100, budgetDiag.needs_pct)}%` }}
                />
              </div>
            </div>

            {/* Wants */}
            <div>
              <div className="flex justify-between font-mono text-xs font-bold mb-1">
                <span>DISCRETIONARY WANTS (Dining, Shopping, Subscriptions, Entertainment)</span>
                <span>₹{budgetDiag.wants_amount.toLocaleString('en-IN')} ({budgetDiag.wants_pct}% / Target: 30%)</span>
              </div>
              <div className="w-full h-4 bg-gray-200 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
                <div
                  className={`h-full border-r-2 border-black ${
                    budgetDiag.wants_pct > 35 ? 'bg-amber-400' : 'bg-[#60A5FA]'
                  }`}
                  style={{ width: `${Math.min(100, budgetDiag.wants_pct)}%` }}
                />
              </div>
            </div>

            {/* Savings */}
            <div>
              <div className="flex justify-between font-mono text-xs font-bold mb-1">
                <span>SAVINGS &amp; INVESTMENTS (Net Surplus &amp; Investments)</span>
                <span>₹{budgetDiag.savings_amount.toLocaleString('en-IN')} ({budgetDiag.savings_pct}% / Target: 20%)</span>
              </div>
              <div className="w-full h-4 bg-gray-200 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
                <div
                  className="h-full bg-[#FACC15] border-r-2 border-black"
                  style={{ width: `${Math.min(100, budgetDiag.savings_pct)}%` }}
                />
              </div>
            </div>
          </div>

          <div className="p-3 bg-[#FAF7F2] border-2 border-black font-mono text-xs font-semibold text-gray-800 flex items-start gap-2 shadow-[2px_2px_0px_0px_#000]">
            <span className="font-black text-[#3730A3] uppercase">Actionable Insight:</span>
            <span>{budgetDiag.advice}</span>
          </div>
        </div>
      )}

      {/* Tax-Deductible Spends Auto-Radar */}
      {snapshot.tax_deductible_spends && snapshot.tax_deductible_spends.length > 0 && (
        <div className="bg-[#FEF3C7] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000]">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b-2 border-black pb-3 mb-4">
            <div className="flex items-center gap-2">
              <Receipt className="w-6 h-6 text-amber-900" />
              <div>
                <h3 className="text-xl md:text-2xl font-black uppercase font-['Space_Grotesk'] text-amber-950">
                  TAX-DEDUCTIBLE SPENDS RADAR
                </h3>
                <p className="text-xs font-mono text-amber-900 font-bold">
                  Identified potential tax-exempt or Chapter VI-A deductible transactions in your statements.
                </p>
              </div>
            </div>
            {onNavigateToTab && (
              <button
                onClick={() => onNavigateToTab('chat')}
                className="bg-[#18153B] text-[#FACC15] px-4 py-2 border-2 border-black font-black font-mono text-xs shadow-[2px_2px_0px_0px_#000] hover:bg-black active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
              >
                ASK MR. PLANNER →
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {snapshot.tax_deductible_spends.map((item, idx) => (
              <div
                key={idx}
                className="bg-[#FFFDF9] border-2 border-black p-4 shadow-[3px_3px_0px_0px_#000] flex flex-col justify-between"
              >
                <div>
                  <span className="inline-block bg-[#FACC15] border border-black px-2 py-0.5 font-black text-[10px] uppercase font-mono mb-2">
                    {item.section}
                  </span>
                  <h4 className="font-black text-sm uppercase text-gray-900 mb-1">
                    {item.title}
                  </h4>
                  <p className="text-[11px] font-mono text-gray-600 mb-3">
                    {item.description}
                  </p>
                </div>
                <div className="border-t border-black pt-2 flex items-center justify-between">
                  <span className="font-mono text-xs text-gray-500 font-bold">{item.transaction_count} txn(s)</span>
                  <span className="font-mono text-base font-black text-[#3730A3]">
                    ₹{item.amount.toLocaleString('en-IN')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Two Column Grid: Top Merchants & Subscriptions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Top 5 Merchants */}
        <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000]">
          <div className="flex items-center justify-between border-b-2 border-black pb-3 mb-4">
            <h3 className="text-xl font-black uppercase font-['Space_Grotesk']">
              TOP 5 MERCHANTS
            </h3>
            <span className="text-[11px] font-mono font-bold text-gray-600">BY SPEND VOLUME</span>
          </div>

          {snapshot.top_merchants && snapshot.top_merchants.length > 0 ? (
            <div className="space-y-3">
              {snapshot.top_merchants.map((m, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-[#FAF7F2] border-2 border-black shadow-[2px_2px_0px_0px_#000]"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 bg-[#FACC15] border border-black font-mono font-black text-xs flex items-center justify-center">
                      #{idx + 1}
                    </span>
                    <div>
                      <div className="font-black text-sm uppercase font-['Space_Grotesk'] text-gray-900">
                        {m.merchant}
                      </div>
                      <span className="text-[10px] font-mono text-gray-600">
                        {m.category} • {m.transaction_count} order(s)
                      </span>
                    </div>
                  </div>
                  <div className="font-mono text-base font-black text-black">
                    ₹{m.total_spent.toLocaleString('en-IN')}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="font-mono text-xs text-gray-500">No merchant volume detected.</p>
          )}
        </div>

        {/* Subscriptions & Fixed Overheads */}
        <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000]">
          <div className="flex items-center justify-between border-b-2 border-black pb-3 mb-4">
            <h3 className="text-xl font-black uppercase font-['Space_Grotesk']">
              RECURRING OVERHEADS
            </h3>
            <span className="text-[11px] font-mono font-bold text-gray-600">MONTHLY RADAR</span>
          </div>

          {snapshot.recurring_subscriptions && snapshot.recurring_subscriptions.length > 0 ? (
            <div className="space-y-3">
              {snapshot.recurring_subscriptions.map((sub, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-[#FAF7F2] border-2 border-black shadow-[2px_2px_0px_0px_#000]"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-[#3730A3] text-white border border-black">
                      <Receipt className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-black text-sm uppercase font-['Space_Grotesk'] text-gray-900">
                        {sub.name}
                      </div>
                      <span className="text-[10px] font-mono text-gray-600">
                        {sub.category} • {sub.frequency}
                      </span>
                    </div>
                  </div>
                  <div className="font-mono text-base font-black text-[#3730A3]">
                    ₹{sub.amount.toLocaleString('en-IN')}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="font-mono text-xs text-gray-500">No recurring subscriptions detected.</p>
          )}
        </div>
      </div>

      {/* Category Spending Breakdown */}
      <div className="bg-[#FFFDF9] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b-3 border-black pb-4 mb-6">
          <div>
            <h3 className="text-2xl font-black uppercase font-['Space_Grotesk'] tracking-tight">
              CATEGORY SPENDING BREAKDOWN
            </h3>
            <p className="text-xs font-mono text-gray-700 mt-1">
              Classified automatically across 12 standard financial categories.
            </p>
          </div>
          <span className="bg-[#FACC15] text-black text-xs font-mono font-black px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
            {snapshot.category_spending.length} ACTIVE CATEGORIES
          </span>
        </div>

        {/* Stacked Neo-Brutalist Visual Progress Bar */}
        <div className="w-full h-8 border-3 border-black flex overflow-hidden shadow-[4px_4px_0px_0px_#000] mb-8 bg-gray-200">
          {snapshot.category_spending.map((cat, idx) => {
            const pct = cat.percentage ?? cat.percentage_of_total ?? 0;
            return (
              <div
                key={cat.category_name}
                style={{ width: `${pct}%` }}
                title={`${cat.category_name}: ${pct.toFixed(1)}%`}
                className={`${categoryColors[idx % categoryColors.length]} border-r-2 border-black relative group transition-all duration-200 hover:opacity-90`}
              />
            );
          })}
        </div>

        {/* Category Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {snapshot.category_spending.map((cat, idx) => {
            const pct = cat.percentage ?? cat.percentage_of_total ?? 0;
            const amt = cat.total_amount ?? cat.amount ?? 0;
            return (
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
                    {pct.toFixed(1)}%
                  </span>
                </div>
                <div className="font-mono text-xl font-black text-black">
                  ₹{amt.toLocaleString('en-IN')}
                </div>
                <span className="text-[10px] font-mono text-gray-500 mt-2 block">
                  {cat.transaction_count ?? 1} transaction(s)
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Interactive Transactions Explorer */}
      {snapshot.recent_transactions && snapshot.recent_transactions.length > 0 && (
        <div className="bg-[#FFFDF9] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000]">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b-3 border-black pb-4 mb-6">
            <div>
              <h3 className="text-2xl font-black uppercase font-['Space_Grotesk'] tracking-tight">
                TRANSACTIONS EXPLORER
              </h3>
              <p className="text-xs font-mono text-gray-700 mt-1">
                Filter and audit real transactions ingested from your bank statements.
              </p>
            </div>

            {/* Search & Filters */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="relative">
                <Search className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search merchant or UPI..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-[#FAF7F2] border-2 border-black pl-9 pr-3 py-1.5 font-mono text-xs font-bold outline-none shadow-[2px_2px_0px_0px_#000] w-48 md:w-64"
                />
              </div>

              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-[#FAF7F2] border-2 border-black px-3 py-1.5 font-mono text-xs font-bold outline-none shadow-[2px_2px_0px_0px_#000] cursor-pointer"
              >
                <option value="ALL">ALL CATEGORIES</option>
                {snapshot.category_spending.map((c) => (
                  <option key={c.category_name} value={c.category_name}>
                    {c.category_name.toUpperCase()}
                  </option>
                ))}
              </select>

              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="bg-[#FAF7F2] border-2 border-black px-3 py-1.5 font-mono text-xs font-bold outline-none shadow-[2px_2px_0px_0px_#000] cursor-pointer"
              >
                <option value="ALL">ALL TYPES</option>
                <option value="debit">DEBITS (SPENDS)</option>
                <option value="credit">CREDITS (INCOME)</option>
              </select>
            </div>
          </div>

          {/* Transactions Table */}
          <div className="overflow-x-auto border-2 border-black">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-[#18153B] text-white uppercase text-[11px] font-black border-b-2 border-black">
                <tr>
                  <th className="p-3">Date</th>
                  <th className="p-3">Merchant / Entity</th>
                  <th className="p-3">Raw Narration</th>
                  <th className="p-3">Category</th>
                  <th className="p-3 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/20 bg-[#FAF7F2]">
                {filteredTransactions.slice(0, 30).map((txn) => {
                  const isCredit = txn.transaction_type.toLowerCase() === 'credit';
                  return (
                    <tr key={txn.id} className="hover:bg-white transition-colors">
                      <td className="p-3 font-bold whitespace-nowrap text-gray-700">
                        {txn.date}
                      </td>
                      <td className="p-3 font-black text-black uppercase font-['Space_Grotesk'] text-sm">
                        {txn.merchant}
                      </td>
                      <td className="p-3 text-gray-600 max-w-xs truncate" title={txn.description}>
                        {txn.description}
                      </td>
                      <td className="p-3">
                        <span className="inline-block px-2 py-0.5 border border-black text-[10px] font-black uppercase bg-[#FFFDF9] shadow-[1px_1px_0px_0px_#000]">
                          <Tag className="w-3 h-3 inline-block mr-1" />
                          {txn.category}
                        </span>
                      </td>
                      <td className={`p-3 text-right font-black whitespace-nowrap text-sm ${isCredit ? 'text-emerald-700' : 'text-black'}`}>
                        <span className="inline-flex items-center gap-1">
                          {isCredit ? (
                            <ArrowDownLeft className="w-3.5 h-3.5 text-emerald-700" />
                          ) : (
                            <ArrowUpRight className="w-3.5 h-3.5 text-gray-500" />
                          )}
                          ₹{txn.amount.toLocaleString('en-IN')}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="mt-3 text-[11px] font-mono text-gray-500 font-bold text-right">
            Showing {Math.min(30, filteredTransactions.length)} of {filteredTransactions.length} matching transactions
          </div>
        </div>
      )}
    </div>
  );
};
