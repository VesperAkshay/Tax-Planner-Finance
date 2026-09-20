import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Search,
  RefreshCw,
  Edit3,
  ShieldCheck,
  CheckSquare,
  Square,
  ArrowRight,
} from 'lucide-react';
import { api } from '../api/client';
import type { CatalogListResponse, DeductionCatalogItem } from '../types';

interface DeductionCatalogViewProps {
  onCatalogUpdated?: () => void;
  onNavigateToReport?: () => void;
}

export const DeductionCatalogView: React.FC<DeductionCatalogViewProps> = ({
  onCatalogUpdated,
  onNavigateToReport,
}) => {
  const [catalog, setCatalog] = useState<CatalogListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [regimeFilter, setRegimeFilter] = useState<'all' | 'old_only' | 'both'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'declared' | 'unclaimed'>('all');

  // Inline editing state: section_code -> amount
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [editAmount, setEditAmount] = useState<string>('');
  const [eligibilityChecked, setEligibilityChecked] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    loadCatalog();
  }, []);

  const loadCatalog = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCatalog('2025-2026', true);
      setCatalog(data);
    } catch (e: unknown) {
      console.error(e);
      setError(e instanceof Error ? e.message : 'Failed to load deduction catalog');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkViewed = async () => {
    try {
      await api.markCatalogViewed('2025-2026');
      await loadCatalog();
      if (onCatalogUpdated) onCatalogUpdated();
      setSaveMessage('Catalog checkpoint verified! Final tax calculation report is now unlocked.');
      setTimeout(() => setSaveMessage(null), 4000);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to mark catalog as reviewed');
    }
  };

  const startEdit = (item: DeductionCatalogItem) => {
    setEditingSection(item.section_code);
    setEditAmount(item.declared_amount ? String(item.declared_amount) : '');
    setEligibilityChecked(item.declared_amount !== null && item.declared_amount > 0);
  };

  const cancelEdit = () => {
    setEditingSection(null);
    setEditAmount('');
    setEligibilityChecked(false);
  };

  const handleSaveDeduction = async (item: DeductionCatalogItem, overrideAmount?: number) => {
    const rawVal = overrideAmount !== undefined ? overrideAmount : parseFloat(editAmount);
    const amountToSave = isNaN(rawVal) || rawVal < 0 ? 0 : rawVal;

    if (item.requires_eligibility_check && !eligibilityChecked && amountToSave > 0) {
      alert(`Please confirm that you satisfy the statutory eligibility requirements for Section ${item.section_code}.`);
      return;
    }

    setIsSaving(true);
    try {
      await api.declareDeduction(
        item.section_code,
        amountToSave,
        item.requires_eligibility_check ? eligibilityChecked : true,
        '2025-2026'
      );
      setSaveMessage(`Section ${item.section_code} updated to ₹${amountToSave.toLocaleString('en-IN')}!`);
      setTimeout(() => setSaveMessage(null), 3500);
      cancelEdit();
      await loadCatalog();
      if (onCatalogUpdated) onCatalogUpdated();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to save deduction');
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-[#FFFDF9] border-4 border-black p-12 text-center shadow-[6px_6px_0px_0px_#000]">
        <div className="inline-block p-4 bg-[#FACC15] border-2 border-black mb-4 animate-spin">
          <RefreshCw className="w-8 h-8 text-black" />
        </div>
        <span className="font-black text-lg tracking-wider block font-mono">
          LOADING 18-SECTION STATUTORY DEDUCTION CATALOG...
        </span>
        <span className="text-xs font-mono text-gray-600 mt-2 block">
          Synchronizing statutory limits, Chapter VI-A caps, and live declarations.
        </span>
      </div>
    );
  }

  if (error || !catalog) {
    return (
      <div className="bg-[#FFFDF9] border-4 border-black p-10 shadow-[6px_6px_0px_0px_#000] text-center space-y-4">
        <div className="inline-block p-3 bg-red-200 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
          <AlertCircle className="w-8 h-8 text-red-900" />
        </div>
        <h3 className="text-2xl font-black uppercase font-['Space_Grotesk']">
          FAILED TO LOAD DEDUCTION CATALOG
        </h3>
        <p className="text-sm font-mono text-gray-700 max-w-md mx-auto">{error}</p>
        <button
          onClick={loadCatalog}
          className="bg-[#FACC15] hover:bg-yellow-400 text-black px-6 py-2 border-2 border-black font-black font-mono text-xs uppercase shadow-[2px_2px_0px_0px_#000]"
        >
          RETRY CATALOG LOAD
        </button>
      </div>
    );
  }

  // Filter sections
  const filteredSections = catalog.sections.filter((item) => {
    // Search
    const matchesSearch =
      searchQuery === '' ||
      item.section_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase());

    // Regime
    const matchesRegime =
      regimeFilter === 'all' ||
      (regimeFilter === 'old_only' && item.applicable_regimes === 'old_only') ||
      (regimeFilter === 'both' && (item.applicable_regimes === 'both' || item.applicable_regimes === 'new_and_old'));

    // Status
    const isDeclared = item.declared_amount !== null && item.declared_amount > 0;
    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'declared' && isDeclared) ||
      (statusFilter === 'unclaimed' && !isDeclared);

    return matchesSearch && matchesRegime && matchesStatus;
  });

  return (
    <div data-tour="deduction-catalog" className="space-y-8">
      {/* Top Banner */}
      <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-2">
          <div className="inline-flex items-center gap-2 bg-[#FACC15] px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase text-black">
            <Sparkles className="w-4 h-4" />
            <span>STATUTORY REPOSITORY // 18 STATUTORY TAX SECTIONS (FY 2025–26)</span>
          </div>

          <div className="flex items-center gap-3">
            {catalog.catalog_viewed ? (
              <div className="flex items-center gap-1.5 bg-emerald-100 text-emerald-950 px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs font-mono">
                <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                <span>CHECKPOINT SATISFIED • FINAL REPORT UNLOCKED</span>
              </div>
            ) : (
              <button
                onClick={handleMarkViewed}
                className="flex items-center gap-1.5 bg-[#FACC15] hover:bg-yellow-400 text-black px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs font-mono uppercase cursor-pointer"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>CONFIRM CATALOG REVIEWED</span>
              </button>
            )}
          </div>
        </div>

        <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none">
          STATUTORY DEDUCTION CATALOG
        </h2>
        <p className="text-sm md:text-base font-medium text-gray-800 max-w-2xl font-['Plus_Jakarta_Sans'] mt-2">
          Browse all 18 personal statutory deductions under Chapter VI-A and Section 10 of the Income Tax Act.
          Directly declare or edit your deductions with live cap headroom tracking and statutory eligibility verification.
        </p>

        {saveMessage && (
          <div className="mt-4 p-3 bg-emerald-200 border-2 border-black font-mono text-xs font-bold text-emerald-900 flex items-center gap-2 shadow-[3px_3px_0px_0px_#000]">
            <CheckCircle2 className="w-4 h-4" />
            <span>{saveMessage}</span>
          </div>
        )}
      </div>

      {/* KPI Overview Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        <div className="bg-[#FFFDF9] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000]">
          <span className="text-[11px] font-bold text-gray-600 uppercase block">TOTAL SECTIONS AVAILABLE</span>
          <span className="text-3xl font-black text-[#18153B]">{catalog.total_sections}</span>
          <span className="text-[10px] text-gray-500 block mt-1">18 Official Statutory Clauses</span>
        </div>

        <div className="bg-[#FFFDF9] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000]">
          <span className="text-[11px] font-bold text-gray-600 uppercase block">SECTIONS CLAIMED</span>
          <span className="text-3xl font-black text-[#3730A3]">
            {catalog.declared_count} / {catalog.total_sections}
          </span>
          <span className="text-[10px] text-gray-500 block mt-1">
            {catalog.total_sections - catalog.declared_count} potential deductions untouched
          </span>
        </div>

        <div className="bg-[#FFFDF9] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000]">
          <span className="text-[11px] font-bold text-gray-600 uppercase block">TOTAL DECLARED DEDUCTIONS</span>
          <span className="text-3xl font-black text-emerald-700">
            ₹{catalog.total_declared_deductions.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
          <span className="text-[10px] text-gray-500 block mt-1">Directly reduces Old Regime tax</span>
        </div>

        <div className="bg-[#FFFDF9] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000] flex flex-col justify-between">
          <div>
            <span className="text-[11px] font-bold text-gray-600 uppercase block">REPORT GOVERNANCE</span>
            <span className={`text-xl font-black ${catalog.catalog_viewed ? 'text-emerald-700' : 'text-amber-700'}`}>
              {catalog.catalog_viewed ? 'FINAL AUDIT READY' : 'DRAFT MODE'}
            </span>
          </div>
          {onNavigateToReport && (
            <button
              onClick={onNavigateToReport}
              className="mt-2 text-xs font-black text-[#3730A3] hover:underline flex items-center gap-1"
            >
              <span>View Tax Comparison</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Filter and Search Controls */}
      <div className="bg-[#FFFDF9] border-4 border-black p-4 shadow-[6px_6px_0px_0px_#000] flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
        {/* Search */}
        <div className="flex items-center gap-2 bg-[#FAF7F2] border-2 border-black px-3 py-2 flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-gray-600" />
          <input
            type="text"
            placeholder="Search section (e.g. 80C, 80D, NPS, rent, tuition, disability)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent border-none outline-none w-full font-mono text-xs text-black placeholder-gray-500 font-bold"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className="text-gray-500 hover:text-black font-bold">
              ✕
            </button>
          )}
        </div>

        {/* Regime Filter */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="font-bold text-gray-600 mr-1">REGIME:</span>
          {(['all', 'old_only', 'both'] as const).map((r) => (
            <button
              key={r}
              onClick={() => setRegimeFilter(r)}
              className={`px-3 py-1.5 border-2 border-black font-bold uppercase transition-all ${
                regimeFilter === r
                  ? 'bg-[#18153B] text-white shadow-[2px_2px_0px_0px_#000]'
                  : 'bg-white text-black hover:bg-gray-100'
              }`}
            >
              {r === 'all' ? 'All Regimes' : r === 'old_only' ? 'Old Regime Only' : 'Both (New & Old)'}
            </button>
          ))}
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="font-bold text-gray-600 mr-1">STATUS:</span>
          {(['all', 'declared', 'unclaimed'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 border-2 border-black font-bold uppercase transition-all ${
                statusFilter === s
                  ? 'bg-[#FACC15] text-black shadow-[2px_2px_0px_0px_#000]'
                  : 'bg-white text-black hover:bg-gray-100'
              }`}
            >
              {s === 'all' ? 'All' : s === 'declared' ? 'Claimed' : 'Unclaimed'}
            </button>
          ))}
        </div>
      </div>

      {/* Catalog Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSections.map((item) => {
          const isDeclared = item.declared_amount !== null && item.declared_amount > 0;
          const isEditing = editingSection === item.section_code;
          const isBothRegimes = item.applicable_regimes === 'both' || item.applicable_regimes === 'new_and_old';

          return (
            <div
              key={item.id}
              className={`border-4 border-black p-5 shadow-[6px_6px_0px_0px_#000] flex flex-col justify-between transition-all ${
                isDeclared ? 'bg-[#FFFDF9] ring-2 ring-emerald-500' : 'bg-[#FAF7F2]'
              }`}
            >
              <div>
                {/* Header Tag Line */}
                <div className="flex items-center justify-between gap-2 border-b-2 border-black pb-2 mb-3 font-mono">
                  <div className="flex items-center gap-2">
                    <span className="bg-[#18153B] text-[#FACC15] font-black text-xs px-2.5 py-0.5 border border-black">
                      SEC {item.section_code}
                    </span>
                    {isBothRegimes ? (
                      <span className="bg-emerald-300 text-emerald-950 font-black text-[10px] px-2 py-0.5 border border-black">
                        NEW &amp; OLD
                      </span>
                    ) : (
                      <span className="bg-amber-200 text-amber-950 font-black text-[10px] px-2 py-0.5 border border-black">
                        OLD REGIME ONLY
                      </span>
                    )}
                  </div>

                  {isDeclared && (
                    <span className="bg-emerald-100 text-emerald-800 font-bold text-[10px] px-1.5 py-0.5 border border-emerald-500">
                      CLAIMED
                    </span>
                  )}
                </div>

                {/* Section Title */}
                <h4 className="font-black text-base font-['Space_Grotesk'] text-[#18153B] mb-2 leading-tight">
                  {item.display_name}
                </h4>

                {/* Plain-English Description */}
                <p className="text-xs font-semibold text-gray-700 leading-relaxed mb-4 font-['Plus_Jakarta_Sans']">
                  {item.description}
                </p>

                {/* Cap & Formula Pill */}
                <div className="bg-white border-2 border-black p-2.5 mb-4 font-mono text-xs">
                  <div className="flex justify-between items-center text-[11px] mb-1">
                    <span className="font-bold text-gray-600">STATUTORY LIMIT:</span>
                    <span className="font-black text-[#18153B]">
                      {item.cap_amount
                        ? `₹${item.cap_amount.toLocaleString('en-IN')}`
                        : item.cap_formula
                        ? item.cap_formula
                        : 'Actual Expense / Formula'}
                    </span>
                  </div>

                  {/* Cap Utilization Bar */}
                  {item.cap_amount && item.cap_amount > 0 && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 h-2 border border-black overflow-hidden">
                        <div
                          className="bg-emerald-500 h-full transition-all duration-300"
                          style={{ width: `${item.used_percentage || 0}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-[10px] text-gray-600 mt-1 font-bold">
                        <span>Used: ₹{(item.declared_amount || 0).toLocaleString('en-IN')}</span>
                        <span>
                          {item.remaining_cap !== null
                            ? `Remaining: ₹${item.remaining_cap.toLocaleString('en-IN')}`
                            : ''}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Action / Declaration Area */}
              <div className="pt-2 border-t-2 border-black">
                {isEditing ? (
                  /* Inline Edit Form */
                  <div className="space-y-3 bg-[#FAF7F2] p-3 border-2 border-black font-mono text-xs">
                    <div>
                      <label className="block text-[11px] font-black uppercase text-gray-700 mb-1">
                        Deduction Amount (₹ INR):
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="1000"
                        placeholder="e.g. 50000"
                        value={editAmount}
                        onChange={(e) => setEditAmount(e.target.value)}
                        className="w-full bg-white border-2 border-black px-2.5 py-1.5 font-mono font-bold text-sm outline-none focus:ring-2 focus:ring-[#FACC15]"
                        autoFocus
                      />
                      {Boolean(item.cap_amount && item.cap_amount > 0 && parseFloat(editAmount || '0') > item.cap_amount) && (
                        <p className="text-[10px] text-amber-900 font-bold mt-1 bg-amber-100 p-1.5 border border-amber-600">
                          ⚠️ Amount exceeds statutory ceiling of ₹{item.cap_amount!.toLocaleString('en-IN')}. Tax engine will cap eligible deduction to ₹{item.cap_amount!.toLocaleString('en-IN')}.
                        </p>
                      )}
                    </div>

                    {item.requires_eligibility_check && (
                      <div
                        onClick={() => setEligibilityChecked(!eligibilityChecked)}
                        className="flex items-start gap-2 cursor-pointer bg-white p-2 border border-black"
                      >
                        {eligibilityChecked ? (
                          <CheckSquare className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                        ) : (
                          <Square className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                        )}
                        <span className="text-[10px] font-semibold text-gray-800 leading-tight">
                          I confirm that I meet the statutory conditions required under Section {item.section_code}.
                        </span>
                      </div>
                    )}

                    <div className="flex items-center gap-2 pt-1">
                      <button
                        onClick={() => handleSaveDeduction(item)}
                        disabled={isSaving}
                        className="flex-1 bg-[#10B981] hover:bg-emerald-400 text-black font-black py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] cursor-pointer text-center uppercase"
                      >
                        {isSaving ? 'SAVING...' : 'SAVE'}
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="bg-white hover:bg-gray-100 text-black font-bold px-3 py-1.5 border-2 border-black cursor-pointer uppercase"
                      >
                        CANCEL
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Standard Card Action Strip */
                  <div className="space-y-2">
                    <div className="flex items-center justify-between font-mono text-xs">
                      <span className="font-bold text-gray-600">CLAIMED AMOUNT:</span>
                      <span className="font-black text-sm text-[#18153B]">
                        ₹{(item.declared_amount || 0).toLocaleString('en-IN')}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 pt-1">
                      <button
                        onClick={() => startEdit(item)}
                        className="flex-1 flex items-center justify-center gap-1.5 bg-[#FACC15] hover:bg-yellow-400 text-black py-1.5 border-2 border-black font-mono font-black text-xs uppercase shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>{isDeclared ? 'EDIT CLAIM' : 'DECLARE'}</span>
                      </button>

                      {item.cap_amount && item.cap_amount > 0 && !isDeclared && (
                        <button
                          onClick={() => {
                            if (item.requires_eligibility_check) {
                              startEdit(item);
                              setEditAmount(String(item.cap_amount));
                            } else {
                              handleSaveDeduction(item, item.cap_amount!);
                            }
                          }}
                          className="bg-white hover:bg-gray-100 text-black px-2.5 py-1.5 border-2 border-black font-mono font-bold text-[11px] uppercase shadow-[2px_2px_0px_0px_#000] cursor-pointer"
                          title="Quickly declare the full statutory cap"
                        >
                          MAX CAP
                        </button>
                      )}

                      {isDeclared && (
                        <button
                          onClick={() => handleSaveDeduction(item, 0)}
                          className="bg-red-100 hover:bg-red-200 text-red-900 px-2 py-1.5 border-2 border-black font-mono font-bold text-[11px] uppercase cursor-pointer"
                          title="Clear this deduction"
                        >
                          RESET
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {filteredSections.length === 0 && (
        <div className="bg-[#FFFDF9] border-4 border-black p-8 text-center shadow-[6px_6px_0px_0px_#000]">
          <span className="font-mono font-bold text-sm text-gray-700">
            No statutory deduction sections match your search or filter criteria.
          </span>
          <button
            onClick={() => {
              setSearchQuery('');
              setRegimeFilter('all');
              setStatusFilter('all');
            }}
            className="mt-3 block mx-auto bg-[#FACC15] px-4 py-1.5 border-2 border-black font-mono font-black text-xs uppercase shadow-[2px_2px_0px_0px_#000]"
          >
            RESET FILTERS
          </button>
        </div>
      )}
    </div>
  );
};
