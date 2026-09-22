import React, { useState } from 'react';
import {
  Briefcase,
  AlertTriangle,
  TrendingUp,
  FileText,
  Copy,
  Check,
  ShieldAlert,
  ArrowRight,
  Download,
  Info,
  DollarSign,
  Building2,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
import type {
  DecodeOfferResponse,
  SimulateSwitchResponse,
  CompareOffersResponse,
  Form12BResponse,
} from '../types';

type ActiveSubTab = 'decoder' | 'switch_simulator' | 'offer_compare';

export const CareerSwitchView: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<ActiveSubTab>('decoder');

  // ============================================================================
  // Tab 1: Offer Letter Decoder State
  // ============================================================================
  const [ctc, setCtc] = useState<number>(1800000);
  const [basic, setBasic] = useState<number | undefined>(undefined);
  const [hra, setHra] = useState<number | undefined>(undefined);
  const [specialAllowance, setSpecialAllowance] = useState<number | undefined>(undefined);
  const [variablePay, setVariablePay] = useState<number>(200000);
  const [joiningBonus, setJoiningBonus] = useState<number>(100000);
  const [clawbackMonths, setClawbackMonths] = useState<number>(12);
  const [esopAnnual, setEsopAnnual] = useState<number>(0);
  const [gratuityIncluded, setGratuityIncluded] = useState<boolean>(true);
  const [employerPfIncluded, setEmployerPfIncluded] = useState<boolean>(true);
  const [medicalInsurance, setMedicalInsurance] = useState<number>(15000);

  const [decoderLoading, setDecoderLoading] = useState<boolean>(false);
  const [decoderError, setDecoderError] = useState<string | null>(null);
  const [decodedData, setDecodedData] = useState<DecodeOfferResponse | null>(null);
  const [copiedEmail, setCopiedEmail] = useState<boolean>(false);

  // ============================================================================
  // Tab 2: Mid-Year Job Switch Simulator State
  // ============================================================================
  const [companyAMonths, setCompanyAMonths] = useState<number>(6);
  const [companyAGross, setCompanyAGross] = useState<number>(800000);
  const [companyATds, setCompanyATds] = useState<number>(0);
  const [companyAEpf, setCompanyAEpf] = useState<number>(38400);
  const [companyBMonthlyGross, setCompanyBMonthlyGross] = useState<number>(150000);

  const [switchLoading, setSwitchLoading] = useState<boolean>(false);
  const [switchError, setSwitchError] = useState<string | null>(null);
  const [switchData, setSwitchData] = useState<SimulateSwitchResponse | null>(null);

  // Form 12B Generator Modal / Drawer State
  const [showForm12BModal, setShowForm12BModal] = useState<boolean>(false);
  const [companyAName, setCompanyAName] = useState<string>('Acme Technologies Pvt Ltd');
  const [companyATan, setCompanyATan] = useState<string>('BLRA12345C');
  const [periodStart, setPeriodStart] = useState<string>('01-Apr-2024');
  const [periodEnd, setPeriodEnd] = useState<string>('30-Sep-2024');
  const [form12bLoading, setForm12bLoading] = useState<boolean>(false);
  const [form12bData, setForm12bData] = useState<Form12BResponse | null>(null);
  const [copiedFormText, setCopiedFormText] = useState<boolean>(false);

  // ============================================================================
  // Tab 3: Offer Comparison State
  // ============================================================================
  const [currentCtc, setCurrentCtc] = useState<number>(1200000);
  const [offerACtc, setOfferACtc] = useState<number>(1800000);
  const [offerBCtc, setOfferBCtc] = useState<number>(2200000);
  const [compareLoading, setCompareLoading] = useState<boolean>(false);
  const [compareError, setCompareError] = useState<string | null>(null);
  const [compareData, setCompareData] = useState<CompareOffersResponse | null>(null);

  // ============================================================================
  // Handlers
  // ============================================================================

  const handleDecodeOffer = async () => {
    setDecoderLoading(true);
    setDecoderError(null);
    try {
      const res = await api.decodeOffer({
        ctc,
        basic: basic || undefined,
        hra: hra || undefined,
        special_allowance: specialAllowance || undefined,
        variable_pay: variablePay,
        joining_bonus: joiningBonus,
        bonus_clawback_months: clawbackMonths,
        esop_annual: esopAnnual,
        gratuity_included: gratuityIncluded,
        employer_pf_included: employerPfIncluded,
        medical_insurance_annual: medicalInsurance,
      });
      setDecodedData(res);
    } catch (e: unknown) {
      setDecoderError(e instanceof Error ? e.message : 'Failed to decode offer');
    } finally {
      setDecoderLoading(false);
    }
  };

  const handleSimulateSwitch = async () => {
    setSwitchLoading(true);
    setSwitchError(null);
    try {
      const res = await api.simulateSwitch({
        company_a_months: companyAMonths,
        company_a_gross: companyAGross,
        company_a_tds: companyATds,
        company_a_epf: companyAEpf,
        company_b_months: 12 - companyAMonths,
        company_b_monthly_gross: companyBMonthlyGross,
      });
      setSwitchData(res);
    } catch (e: unknown) {
      setSwitchError(e instanceof Error ? e.message : 'Failed to simulate job switch');
    } finally {
      setSwitchLoading(false);
    }
  };

  const handleCompareOffers = async () => {
    setCompareLoading(true);
    setCompareError(null);
    try {
      const res = await api.compareOffers({
        current_ctc: currentCtc,
        offer_a_ctc: offerACtc,
        offer_b_ctc: offerBCtc || undefined,
      });
      setCompareData(res);
    } catch (e: unknown) {
      setCompareError(e instanceof Error ? e.message : 'Failed to compare offers');
    } finally {
      setCompareLoading(false);
    }
  };

  const handleGenerateForm12B = async () => {
    setForm12bLoading(true);
    try {
      const res = await api.generateForm12B({
        company_a_name: companyAName,
        company_a_tan: companyATan || undefined,
        company_a_gross: companyAGross,
        company_a_tds: companyATds,
        company_a_epf: companyAEpf,
        period_start: periodStart,
        period_end: periodEnd,
      });
      setForm12bData(res);
      setShowForm12BModal(true);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to generate Form 12B');
    } finally {
      setForm12bLoading(false);
    }
  };

  const copyToClipboard = (text: string, setCopied: (v: boolean) => void) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      {/* Neo-Brutalist Hero Header */}
      <div className="border-4 border-black p-6 bg-[#FAF7F2] shadow-[8px_8px_0px_0px_#000] relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 bg-[#18153B] text-[#FACC15] font-mono text-xs px-3 py-1 border-2 border-black font-black uppercase mb-3">
              <Briefcase className="w-3.5 h-3.5" />
              Career Switch & Offer Letter Decoder
            </div>
            <h1 className="text-3xl md:text-4xl font-black font-['Space_Grotesk'] text-[#18153B] tracking-tight">
              Don't Get Trapped By Paper CTC & Dual-Employer Tax Bombs
            </h1>
            <p className="text-gray-700 font-medium text-sm md:text-base mt-2 max-w-3xl">
              Decode inflated CTCs into real monthly bank cash, uncover hidden gratuity and clawback traps,
              and prevent the lethal mid-year <strong>Double Standard Deduction &amp; Section 234B interest trap</strong> before July ITR filing.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="bg-emerald-300 text-emerald-950 border-2 border-black px-3 py-1.5 font-mono text-xs font-black shadow-[2px_2px_0px_0px_#000]">
              FY 2025-26 ACT RULES
            </span>
            <span className="bg-[#FACC15] text-black border-2 border-black px-3 py-1.5 font-mono text-xs font-black shadow-[2px_2px_0px_0px_#000]">
              FORM 12B COMPLIANT
            </span>
          </div>
        </div>

        {/* Sub-Navigation Tabs */}
        <div className="flex flex-wrap gap-3 mt-6 pt-4 border-t-2 border-black font-mono">
          <button
            onClick={() => setActiveSubTab('decoder')}
            className={`px-4 py-2 border-2 border-black font-black uppercase text-xs md:text-sm flex items-center gap-2 transition-all ${
              activeSubTab === 'decoder'
                ? 'bg-[#18153B] text-white shadow-[4px_4px_0px_0px_#000] -translate-y-0.5'
                : 'bg-white text-black hover:bg-gray-100'
            }`}
          >
            <Sparkles className="w-4 h-4 text-[#FACC15]" />
            1. Offer Letter & CTC Decoder
          </button>

          <button
            onClick={() => setActiveSubTab('switch_simulator')}
            className={`px-4 py-2 border-2 border-black font-black uppercase text-xs md:text-sm flex items-center gap-2 transition-all ${
              activeSubTab === 'switch_simulator'
                ? 'bg-[#18153B] text-white shadow-[4px_4px_0px_0px_#000] -translate-y-0.5'
                : 'bg-white text-black hover:bg-gray-100'
            }`}
          >
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            2. Mid-Year Switch Tax Simulator
          </button>

          <button
            onClick={() => setActiveSubTab('offer_compare')}
            className={`px-4 py-2 border-2 border-black font-black uppercase text-xs md:text-sm flex items-center gap-2 transition-all ${
              activeSubTab === 'offer_compare'
                ? 'bg-[#18153B] text-white shadow-[4px_4px_0px_0px_#000] -translate-y-0.5'
                : 'bg-white text-black hover:bg-gray-100'
            }`}
          >
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            3. Compare 2 Job Offers
          </button>
        </div>
      </div>

      {/* ==================================================================== */}
      {/* SUB-TAB 1: OFFER LETTER DECODER */}
      {/* ==================================================================== */}
      {activeSubTab === 'decoder' && (
        <div className="space-y-8">
          {/* Preset Buttons */}
          <div className="flex flex-wrap items-center gap-2 bg-[#FFFDF9] border-2 border-black p-3 shadow-[4px_4px_0px_0px_#000]">
            <span className="font-mono text-xs font-black text-gray-600 mr-2">QUICK PRESETS:</span>
            <button
              onClick={() => {
                setCtc(1800000);
                setBasic(720000);
                setHra(288000);
                setSpecialAllowance(500000);
                setVariablePay(200000);
                setJoiningBonus(100000);
                setClawbackMonths(12);
                setGratuityIncluded(true);
                setEmployerPfIncluded(true);
              }}
              className="bg-white hover:bg-amber-50 text-black border border-black px-2.5 py-1 text-xs font-bold"
            >
              ₹18L SDE-2 (High Variable + Bonus)
            </button>
            <button
              onClick={() => {
                setCtc(3000000);
                setBasic(1200000);
                setHra(480000);
                setSpecialAllowance(800000);
                setVariablePay(500000);
                setJoiningBonus(0);
                setEsopAnnual(200000);
                setGratuityIncluded(true);
                setEmployerPfIncluded(true);
              }}
              className="bg-white hover:bg-amber-50 text-black border border-black px-2.5 py-1 text-xs font-bold"
            >
              ₹30L Tech Lead (ESOP + 17% Var)
            </button>
            <button
              onClick={() => {
                setCtc(1100000);
                setBasic(440000);
                setHra(176000);
                setSpecialAllowance(400000);
                setVariablePay(50000);
                setJoiningBonus(0);
                setGratuityIncluded(true);
                setEmployerPfIncluded(true);
              }}
              className="bg-white hover:bg-amber-50 text-black border border-black px-2.5 py-1 text-xs font-bold"
            >
              ₹11L (Under §87A 12L Threshold)
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Input Form Column */}
            <div className="lg:col-span-5 border-4 border-black p-6 bg-[#FAF7F2] shadow-[6px_6px_0px_0px_#000] space-y-4">
              <div className="border-b-2 border-black pb-3">
                <h3 className="text-xl font-black font-['Space_Grotesk'] text-[#18153B] flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-[#FACC15]" />
                  Enter Offer Annexure Figures
                </h3>
                <p className="text-xs text-gray-600 mt-1">
                  Feed in the numbers from your HR compensation letter. Leave optional items blank to use statutory defaults.
                </p>
              </div>

              {/* Annual CTC */}
              <div>
                <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                  Annual Cost-to-Company (CTC) *
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 font-bold text-gray-500">₹</span>
                  <input
                    type="number"
                    value={ctc}
                    onChange={(e) => setCtc(Number(e.target.value))}
                    className="w-full pl-8 pr-3 py-2 border-2 border-black font-mono font-bold text-base focus:bg-amber-50 focus:outline-none"
                    placeholder="e.g. 1800000"
                  />
                </div>
              </div>

              {/* Basic Pay & HRA */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                    Annual Basic Pay
                  </label>
                  <input
                    type="number"
                    value={basic ?? ''}
                    onChange={(e) => setBasic(e.target.value ? Number(e.target.value) : undefined)}
                    placeholder="Auto 40% of CTC"
                    className="w-full px-3 py-2 border-2 border-black font-mono text-sm focus:bg-amber-50 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                    Annual HRA
                  </label>
                  <input
                    type="number"
                    value={hra ?? ''}
                    onChange={(e) => setHra(e.target.value ? Number(e.target.value) : undefined)}
                    placeholder="Auto 40% Basic"
                    className="w-full px-3 py-2 border-2 border-black font-mono text-sm focus:bg-amber-50 focus:outline-none"
                  />
                </div>
              </div>

              {/* Special Allowance */}
              <div>
                <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                  Special Allowance (Tax Sinkhole)
                </label>
                <input
                  type="number"
                  value={specialAllowance ?? ''}
                  onChange={(e) => setSpecialAllowance(e.target.value ? Number(e.target.value) : undefined)}
                  placeholder="Auto remaining fixed"
                  className="w-full px-3 py-2 border-2 border-black font-mono text-sm focus:bg-amber-50 focus:outline-none"
                />
              </div>

              {/* Variable Pay & Joining Bonus */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                    Variable / At-Risk Pay
                  </label>
                  <input
                    type="number"
                    value={variablePay}
                    onChange={(e) => setVariablePay(Number(e.target.value))}
                    className="w-full px-3 py-2 border-2 border-black font-mono text-sm focus:bg-amber-50 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                    Joining Bonus
                  </label>
                  <input
                    type="number"
                    value={joiningBonus}
                    onChange={(e) => setJoiningBonus(Number(e.target.value))}
                    className="w-full px-3 py-2 border-2 border-black font-mono text-sm focus:bg-amber-50 focus:outline-none"
                  />
                </div>
              </div>

              {/* Bonus Clawback & ESOP */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                    Bonus Lock-in (Months)
                  </label>
                  <input
                    type="number"
                    value={clawbackMonths}
                    onChange={(e) => setClawbackMonths(Number(e.target.value))}
                    className="w-full px-3 py-2 border-2 border-black font-mono text-sm focus:bg-amber-50 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                    Annual ESOP / RSU
                  </label>
                  <input
                    type="number"
                    value={esopAnnual}
                    onChange={(e) => setEsopAnnual(Number(e.target.value))}
                    className="w-full px-3 py-2 border-2 border-black font-mono text-sm focus:bg-amber-50 focus:outline-none"
                  />
                </div>
              </div>

              {/* Medical Insurance in CTC */}
              <div>
                <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                  Group Medical Insurance Premium (in CTC)
                </label>
                <input
                  type="number"
                  value={medicalInsurance}
                  onChange={(e) => setMedicalInsurance(Number(e.target.value))}
                  className="w-full px-3 py-2 border-2 border-black font-mono text-sm focus:bg-amber-50 focus:outline-none"
                  placeholder="15000"
                />
              </div>

              {/* Checkboxes for Retirals in CTC */}
              <div className="space-y-2 pt-2 border-t border-gray-300">
                <label className="flex items-center gap-2 cursor-pointer font-mono text-xs font-bold">
                  <input
                    type="checkbox"
                    checked={gratuityIncluded}
                    onChange={(e) => setGratuityIncluded(e.target.checked)}
                    className="w-4 h-4 border-2 border-black accent-[#18153B]"
                  />
                  Gratuity (4.81% of Basic) included inside CTC
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-mono text-xs font-bold">
                  <input
                    type="checkbox"
                    checked={employerPfIncluded}
                    onChange={(e) => setEmployerPfIncluded(e.target.checked)}
                    className="w-4 h-4 border-2 border-black accent-[#18153B]"
                  />
                  Employer PF (12% of Basic) included inside CTC
                </label>
              </div>

              {/* Decode Button */}
              <button
                onClick={handleDecodeOffer}
                disabled={decoderLoading}
                className="w-full mt-4 bg-[#FACC15] hover:bg-yellow-400 text-black border-2 border-black font-mono font-black py-3 px-4 uppercase text-sm shadow-[4px_4px_0px_0px_#000] active:translate-x-1 active:translate-y-1 transition-all flex items-center justify-center gap-2"
              >
                {decoderLoading ? 'Decoding Compensation...' : 'Decode Real Monthly In-Hand Cash'}
                <ArrowRight className="w-4 h-4" />
              </button>

              {decoderError && (
                <div className="p-3 bg-rose-100 border-2 border-rose-500 text-rose-900 text-xs font-bold">
                  {decoderError}
                </div>
              )}
            </div>

            {/* Results Column */}
            <div className="lg:col-span-7 space-y-6">
              {!decodedData ? (
                <div className="border-4 border-dashed border-gray-400 p-12 text-center bg-white/50 flex flex-col items-center justify-center min-h-[400px]">
                  <Briefcase className="w-12 h-12 text-gray-400 mb-3" />
                  <h4 className="font-['Space_Grotesk'] font-bold text-lg text-gray-700">
                    Ready to Decode Your Compensation Letter
                  </h4>
                  <p className="text-xs text-gray-500 max-w-sm mt-1">
                    Click "Decode Real Monthly In-Hand Cash" or select a preset to uncover your statutory take-home pay and hidden contract traps.
                  </p>
                </div>
              ) : (
                <>
                  {/* Big In-Hand Take Home Banner */}
                  <div className="border-4 border-black p-6 bg-[#18153B] text-white shadow-[6px_6px_0px_0px_#000]">
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-700 pb-4">
                      <div>
                        <span className="text-xs font-mono font-bold uppercase text-[#FACC15]">
                          GUARANTEED REAL TAKE-HOME PAY
                        </span>
                        <div className="text-4xl font-black font-mono text-white mt-1">
                          ₹{decodedData.monthly_breakdown.guaranteed_in_hand.toLocaleString('en-IN')}
                          <span className="text-sm font-normal text-gray-300"> / month</span>
                        </div>
                      </div>

                      <div className="text-left sm:text-right">
                        <span className="text-xs font-mono text-gray-400">PAPER CTC MONTHLY</span>
                        <div className="text-lg font-mono font-bold line-through text-gray-400">
                          ₹{Math.round(decodedData.annual_ctc / 12).toLocaleString('en-IN')}
                        </div>
                        <span className="text-[11px] font-mono text-rose-300 font-bold">
                          {Math.round(
                            ((decodedData.annual_ctc / 12 - decodedData.monthly_breakdown.guaranteed_in_hand) /
                              (decodedData.annual_ctc / 12)) *
                              100
                          )}
                          % deducted (Tax + PF + Retirals)
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 text-center font-mono">
                      <div className="bg-black/40 p-2.5 border border-gray-700">
                        <div className="text-[10px] text-gray-400">ANNUAL TAKE-HOME</div>
                        <div className="font-bold text-sm text-[#FACC15]">
                          ₹{decodedData.annual_totals.annual_in_hand.toLocaleString('en-IN')}
                        </div>
                      </div>
                      <div className="bg-black/40 p-2.5 border border-gray-700">
                        <div className="text-[10px] text-gray-400">ANNUAL TAX (NEW REGIME)</div>
                        <div className="font-bold text-sm text-rose-300">
                          ₹{decodedData.annual_totals.annual_tax.toLocaleString('en-IN')}
                        </div>
                      </div>
                      <div className="bg-black/40 p-2.5 border border-gray-700">
                        <div className="text-[10px] text-gray-400">MONTHLY TDS DEDUCTED</div>
                        <div className="font-bold text-sm text-white">
                          ₹{decodedData.monthly_breakdown.monthly_tds_tax.toLocaleString('en-IN')}
                        </div>
                      </div>
                      <div className="bg-black/40 p-2.5 border border-gray-700">
                        <div className="text-[10px] text-gray-400">MONTHLY EMPLOYEE PF</div>
                        <div className="font-bold text-sm text-white">
                          ₹{decodedData.monthly_breakdown.employee_pf_deduction.toLocaleString('en-IN')}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Monthly Cashflow Breakdown Breakdown Table */}
                  <div className="border-4 border-black p-5 bg-white shadow-[6px_6px_0px_0px_#000]">
                    <h4 className="font-black font-['Space_Grotesk'] text-base text-[#18153B] mb-3 border-b-2 border-black pb-2 flex items-center justify-between">
                      <span>Monthly Salary Slip Breakdown</span>
                      <span className="font-mono text-xs text-gray-600 font-normal">Fixed Gross: ₹{decodedData.monthly_breakdown.fixed_gross.toLocaleString('en-IN')}</span>
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 font-mono text-xs">
                      <div className="p-2 bg-gray-50 border border-gray-300">
                        <span className="text-gray-500">Basic Pay:</span>
                        <div className="font-bold text-gray-900">₹{decodedData.monthly_breakdown.basic.toLocaleString('en-IN')}</div>
                      </div>
                      <div className="p-2 bg-gray-50 border border-gray-300">
                        <span className="text-gray-500">HRA:</span>
                        <div className="font-bold text-gray-900">₹{decodedData.monthly_breakdown.hra.toLocaleString('en-IN')}</div>
                      </div>
                      <div className="p-2 bg-amber-50 border border-amber-300">
                        <span className="text-amber-800">Special Allowance:</span>
                        <div className="font-bold text-amber-950">₹{decodedData.monthly_breakdown.special_allowance.toLocaleString('en-IN')}</div>
                      </div>
                      <div className="p-2 bg-gray-50 border border-gray-300">
                        <span className="text-gray-500">PF Deduction (12%):</span>
                        <div className="font-bold text-gray-900">-₹{decodedData.monthly_breakdown.employee_pf_deduction.toLocaleString('en-IN')}</div>
                      </div>
                      <div className="p-2 bg-gray-50 border border-gray-300">
                        <span className="text-gray-500">Professional Tax:</span>
                        <div className="font-bold text-gray-900">-₹{decodedData.monthly_breakdown.professional_tax.toLocaleString('en-IN')}</div>
                      </div>
                      <div className="p-2 bg-rose-50 border border-rose-300">
                        <span className="text-rose-800">Income Tax (TDS):</span>
                        <div className="font-bold text-rose-950">-₹{decodedData.monthly_breakdown.monthly_tds_tax.toLocaleString('en-IN')}</div>
                      </div>
                    </div>
                  </div>

                  {/* Red-Flag Traps Cards */}
                  <div className="space-y-3">
                    <h4 className="font-black font-['Space_Grotesk'] text-base text-[#18153B] flex items-center gap-2">
                      <ShieldAlert className="w-5 h-5 text-rose-600" />
                      Hidden Traps Uncovered in This Offer ({decodedData.traps_detected.length})
                    </h4>
                    {decodedData.traps_detected.length === 0 ? (
                      <div className="p-4 bg-emerald-50 border-2 border-emerald-500 text-emerald-900 font-medium text-xs">
                        Clean Offer! No predatory traps detected in this structure.
                      </div>
                    ) : (
                      decodedData.traps_detected.map((trap, idx) => (
                        <div
                          key={idx}
                          className={`border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000] ${
                            trap.severity === 'high' ? 'bg-rose-50 border-rose-600' : 'bg-amber-50 border-amber-600'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <h5 className="font-black font-mono text-sm text-[#18153B] flex items-center gap-1.5">
                              <AlertTriangle className={`w-4 h-4 ${trap.severity === 'high' ? 'text-rose-600' : 'text-amber-600'}`} />
                              {trap.title}
                            </h5>
                            <span className="font-mono text-xs font-bold bg-white px-2 py-0.5 border border-black">
                              ₹{trap.amount.toLocaleString('en-IN')}
                            </span>
                          </div>
                          <p className="text-xs text-gray-800 leading-relaxed font-sans">{trap.description}</p>
                        </div>
                      ))
                    )}
                  </div>

                  {/* AI Restructuring & Negotiation Counter-Proposal */}
                  <div className="border-4 border-black p-5 bg-[#FAF7F2] shadow-[6px_6px_0px_0px_#000] space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-[#FACC15]" />
                        <h4 className="font-black font-['Space_Grotesk'] text-base text-[#18153B]">
                          Tax-Saving Salary Restructure Playbook
                        </h4>
                      </div>
                      <span className="bg-emerald-300 text-emerald-950 font-mono text-xs font-black px-2 py-1 border border-black">
                        Saves ₹{decodedData.negotiation_playbook.annual_tax_saved.toLocaleString('en-IN')}/yr in Tax
                      </span>
                    </div>

                    <p className="text-xs text-gray-700">
                      Convert taxable Special Allowance into statutory tax-free components at <strong>zero extra cost</strong> to the company:
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
                      <div className="bg-white p-3 border-2 border-black">
                        <div className="font-bold text-gray-900 mb-1">1. Employer NPS (Sec 80CCD(2))</div>
                        <div className="text-emerald-700 font-black">
                          ₹{decodedData.negotiation_playbook.suggested_80ccd2_monthly.toLocaleString('en-IN')}/mo
                        </div>
                        <div className="text-[10px] text-gray-500">100% Tax-Exempt up to 14% of Basic under New Regime</div>
                      </div>
                      <div className="bg-white p-3 border-2 border-black">
                        <div className="font-bold text-gray-900 mb-1">2. Broadband Reimbursement</div>
                        <div className="text-emerald-700 font-black">
                          ₹{decodedData.negotiation_playbook.suggested_broadband_monthly.toLocaleString('en-IN')}/mo
                        </div>
                        <div className="text-[10px] text-gray-500">Tax-free official communication allowance</div>
                      </div>
                    </div>

                    {/* Copy Email Button */}
                    <button
                      onClick={() =>
                        copyToClipboard(
                          decodedData.negotiation_playbook.counter_proposal_email,
                          setCopiedEmail
                        )
                      }
                      className="w-full mt-2 bg-[#18153B] hover:bg-[#252055] text-white border-2 border-black font-mono text-xs font-bold py-2.5 px-3 flex items-center justify-center gap-2 shadow-[2px_2px_0px_0px_#000]"
                    >
                      {copiedEmail ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4 text-[#FACC15]" />}
                      {copiedEmail ? 'Counter-Proposal Email Copied!' : 'Copy HR Negotiation Counter-Proposal Email'}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* SUB-TAB 2: MID-YEAR JOB SWITCH SIMULATOR */}
      {/* ==================================================================== */}
      {activeSubTab === 'switch_simulator' && (
        <div className="space-y-8">
          {/* Statutory Explainer Card */}
          <div className="border-4 border-black p-4 bg-amber-50 shadow-[4px_4px_0px_0px_#000] flex items-start gap-3">
            <Info className="w-6 h-6 text-amber-700 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-950 space-y-1">
              <span className="font-black uppercase tracking-wider block font-mono">
                The Statutory Trap: Dual Employers &amp; Double Standard Deduction
              </span>
              <p>
                When you switch jobs midway through a financial year (e.g. from Company A to Company B),
                both companies independently assume they are your only employer. Both deduct the ₹75,000 standard deduction
                and place your income in the lowest 0% / 5% tax slabs.
              </p>
              <p className="font-bold text-rose-800">
                In July, the Income Tax Department combines both incomes with only ONE standard deduction, triggering a surprise ₹50,000 to ₹1,50,000 demand plus 4% to 6% Section 234B/C interest penalties!
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Input Controls */}
            <div className="lg:col-span-5 space-y-6">
              {/* Company A Card */}
              <div className="border-4 border-black p-5 bg-[#FAF7F2] shadow-[6px_6px_0px_0px_#000] space-y-4">
                <div className="border-b-2 border-black pb-2 flex items-center justify-between">
                  <h4 className="font-black font-['Space_Grotesk'] text-base text-[#18153B] flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-[#FACC15]" />
                    Company A (Previous Employer)
                  </h4>
                  <span className="font-mono text-xs font-bold bg-white px-2 py-0.5 border border-black">
                    {companyAMonths} Months (Apr - {['May','Jun','Jul','Aug','Sep','Oct','Nov','Dec','Jan','Feb','Mar'][companyAMonths - 1]})
                  </span>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-mono font-bold mb-1">
                    <span>Tenure at Company A:</span>
                    <span>{companyAMonths} Months</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="11"
                    value={companyAMonths}
                    onChange={(e) => setCompanyAMonths(Number(e.target.value))}
                    className="w-full accent-[#18153B] cursor-pointer"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                    Total Gross Salary Paid by Company A
                  </label>
                  <input
                    type="number"
                    value={companyAGross}
                    onChange={(e) => setCompanyAGross(Number(e.target.value))}
                    className="w-full px-3 py-2 border-2 border-black font-mono font-bold focus:bg-amber-50 focus:outline-none"
                    placeholder="e.g. 800000"
                  />
                  <span className="text-[11px] text-gray-500 font-mono mt-0.5 block">
                    (Found in Box 1 of Form 16 Part B from Company A)
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                      Total TDS Deducted
                    </label>
                    <input
                      type="number"
                      value={companyATds}
                      onChange={(e) => setCompanyATds(Number(e.target.value))}
                      className="w-full px-3 py-2 border-2 border-black font-mono text-sm focus:bg-amber-50 focus:outline-none"
                      placeholder="0"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                      Employee PF Deducted
                    </label>
                    <input
                      type="number"
                      value={companyAEpf}
                      onChange={(e) => setCompanyAEpf(Number(e.target.value))}
                      className="w-full px-3 py-2 border-2 border-black font-mono text-sm focus:bg-amber-50 focus:outline-none"
                      placeholder="38400"
                    />
                  </div>
                </div>
              </div>

              {/* Company B Card */}
              <div className="border-4 border-black p-5 bg-[#FAF7F2] shadow-[6px_6px_0px_0px_#000] space-y-4">
                <div className="border-b-2 border-black pb-2 flex items-center justify-between">
                  <h4 className="font-black font-['Space_Grotesk'] text-base text-[#18153B] flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-emerald-600" />
                    Company B (New Employer)
                  </h4>
                  <span className="font-mono text-xs font-bold bg-white px-2 py-0.5 border border-black">
                    {12 - companyAMonths} Months Remaining
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                    Offered Monthly Gross Salary at Company B
                  </label>
                  <input
                    type="number"
                    value={companyBMonthlyGross}
                    onChange={(e) => setCompanyBMonthlyGross(Number(e.target.value))}
                    className="w-full px-3 py-2 border-2 border-black font-mono font-bold text-base focus:bg-amber-50 focus:outline-none"
                    placeholder="e.g. 150000"
                  />
                  <span className="text-[11px] text-gray-500 font-mono mt-0.5 block">
                    Expected Gross: ₹{Math.round(companyBMonthlyGross * (12 - companyAMonths)).toLocaleString('en-IN')} over remaining {12 - companyAMonths} months
                  </span>
                </div>
              </div>

              {/* Simulate Button */}
              <button
                onClick={handleSimulateSwitch}
                disabled={switchLoading}
                className="w-full bg-[#18153B] hover:bg-[#252055] text-white border-2 border-black font-mono font-black py-3 px-4 uppercase text-sm shadow-[4px_4px_0px_0px_#000] active:translate-x-1 active:translate-y-1 transition-all flex items-center justify-center gap-2"
              >
                {switchLoading ? 'Calculating Combined Liabilities...' : 'Simulate Dual-Employer Tax Shock'}
                <ArrowRight className="w-4 h-4 text-[#FACC15]" />
              </button>

              {switchError && (
                <div className="p-3 bg-rose-100 border-2 border-rose-500 text-rose-900 text-xs font-bold">
                  {switchError}
                </div>
              )}
            </div>

            {/* Results Column */}
            <div className="lg:col-span-7 space-y-6">
              {!switchData ? (
                <div className="border-4 border-dashed border-gray-400 p-12 text-center bg-white/50 flex flex-col items-center justify-center min-h-[400px]">
                  <AlertTriangle className="w-12 h-12 text-amber-500 mb-3" />
                  <h4 className="font-['Space_Grotesk'] font-bold text-lg text-gray-700">
                    Dual-Employer Liability Calculator
                  </h4>
                  <p className="text-xs text-gray-500 max-w-sm mt-1">
                    Hit "Simulate Dual-Employer Tax Shock" to test the surprise tax demand and see how much Form 12B saves you.
                  </p>
                </div>
              ) : (
                <>
                  {/* The Tax Shock Alert Box */}
                  <div
                    className={`border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000] ${
                      switchData.the_tax_shock.has_critical_shortfall
                        ? 'bg-rose-500 text-white'
                        : 'bg-emerald-500 text-black'
                    }`}
                  >
                    <div className="flex items-center gap-2 font-mono text-xs font-black uppercase mb-1">
                      <ShieldAlert className="w-4 h-4" />
                      {switchData.the_tax_shock.has_critical_shortfall
                        ? 'CRITICAL TAX SHOCK DETECTED (WITHOUT FORM 12B)'
                        : 'MILD / NO TDS SHORTFALL'}
                    </div>

                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mt-2">
                      <div>
                        <div className="text-3xl sm:text-4xl font-black font-mono">
                          ₹{switchData.the_tax_shock.total_july_demand.toLocaleString('en-IN')}
                        </div>
                        <div className="text-xs font-mono font-bold mt-1 opacity-90">
                          Surprise Tax &amp; Interest Due When Filing ITR in July
                        </div>
                      </div>

                      <div className="bg-black/20 p-3 border border-white/40 text-xs font-mono space-y-1">
                        <div>TDS Shortfall: ₹{switchData.the_tax_shock.tds_shortfall.toLocaleString('en-IN')}</div>
                        <div>Sec 234B Interest (4%): ₹{switchData.the_tax_shock.section_234b_interest.toLocaleString('en-IN')}</div>
                        <div>Sec 234C Deferment: ₹{switchData.the_tax_shock.section_234c_interest.toLocaleString('en-IN')}</div>
                      </div>
                    </div>
                  </div>

                  {/* Side-by-Side Comparison: Without 12B vs With 12B */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Without Form 12B */}
                    <div className="border-4 border-black p-4 bg-white shadow-[4px_4px_0px_0px_#000] space-y-3">
                      <div className="border-b-2 border-black pb-2">
                        <span className="text-xs font-mono font-black text-rose-600 uppercase">SCENARIO A</span>
                        <h5 className="font-black font-['Space_Grotesk'] text-base text-[#18153B]">
                          Without Form 12B
                        </h5>
                      </div>

                      <div className="font-mono text-xs space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Company A TDS:</span>
                          <span className="font-bold">₹{switchData.without_form_12b.company_a_tds.toLocaleString('en-IN')}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Company B Naive TDS:</span>
                          <span className="font-bold">₹{switchData.without_form_12b.company_b_projected_tds.toLocaleString('en-IN')}</span>
                        </div>
                        <div className="flex justify-between border-t pt-1 border-gray-300">
                          <span className="text-gray-600">Total Deducted:</span>
                          <span className="font-bold">₹{switchData.without_form_12b.total_tds_collected.toLocaleString('en-IN')}</span>
                        </div>
                        <div className="flex justify-between text-rose-700 font-bold border-t pt-1 border-gray-300">
                          <span>July Self-Assessment Tax:</span>
                          <span>₹{switchData.the_tax_shock.total_july_demand.toLocaleString('en-IN')}</span>
                        </div>
                      </div>
                    </div>

                    {/* With Form 12B */}
                    <div className="border-4 border-black p-4 bg-emerald-50 border-emerald-600 shadow-[4px_4px_0px_0px_#000] space-y-3">
                      <div className="border-b-2 border-emerald-600 pb-2">
                        <span className="text-xs font-mono font-black text-emerald-700 uppercase">SCENARIO B (RECOMMENDED)</span>
                        <h5 className="font-black font-['Space_Grotesk'] text-base text-[#18153B]">
                          With Form 12B Submitted
                        </h5>
                      </div>

                      <div className="font-mono text-xs space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Total Annual Liability:</span>
                          <span className="font-bold">₹{switchData.true_statutory_liability.total_tax_due.toLocaleString('en-IN')}</span>
                        </div>
                        <div className="flex justify-between text-emerald-800 font-bold">
                          <span>Company B Monthly TDS:</span>
                          <span>₹{switchData.with_form_12b.adjusted_monthly_tds.toLocaleString('en-IN')}/mo</span>
                        </div>
                        <div className="flex justify-between border-t pt-1 border-emerald-200">
                          <span className="text-gray-600">July Tax Surprise:</span>
                          <span className="font-bold text-emerald-700">₹0.00</span>
                        </div>
                        <div className="flex justify-between text-emerald-900 font-bold border-t pt-1 border-emerald-200">
                          <span>Interest Penalties Saved:</span>
                          <span>₹{switchData.with_form_12b.interest_saved.toLocaleString('en-IN')}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Remediation & 1-Click Form 12B Generator */}
                  <div className="border-4 border-black p-6 bg-[#FAF7F2] shadow-[6px_6px_0px_0px_#000] space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-black font-['Space_Grotesk'] text-lg text-[#18153B]">
                          Statutory Remedy: Form 12B
                        </h4>
                        <p className="text-xs text-gray-600 mt-0.5">
                          Under Rule 26A / Section 192(2) of the Income Tax Act, submit this verified declaration to Company B's HR.
                        </p>
                      </div>
                      <span className="bg-[#18153B] text-[#FACC15] font-mono text-xs font-black px-2.5 py-1 border border-black">
                        SEC 192(2)
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-mono font-bold text-gray-700 mb-1">
                          Previous Employer Name
                        </label>
                        <input
                          type="text"
                          value={companyAName}
                          onChange={(e) => setCompanyAName(e.target.value)}
                          className="w-full px-3 py-1.5 border-2 border-black font-mono text-xs focus:bg-amber-50 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-mono font-bold text-gray-700 mb-1">
                          Company A TAN (Optional)
                        </label>
                        <input
                          type="text"
                          value={companyATan}
                          onChange={(e) => setCompanyATan(e.target.value)}
                          className="w-full px-3 py-1.5 border-2 border-black font-mono text-xs uppercase focus:bg-amber-50 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-mono font-bold text-gray-700 mb-1">
                          Period Start Date
                        </label>
                        <input
                          type="text"
                          value={periodStart}
                          onChange={(e) => setPeriodStart(e.target.value)}
                          className="w-full px-3 py-1.5 border-2 border-black font-mono text-xs focus:bg-amber-50 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-mono font-bold text-gray-700 mb-1">
                          Period End Date
                        </label>
                        <input
                          type="text"
                          value={periodEnd}
                          onChange={(e) => setPeriodEnd(e.target.value)}
                          className="w-full px-3 py-1.5 border-2 border-black font-mono text-xs focus:bg-amber-50 focus:outline-none"
                        />
                      </div>
                    </div>

                    <button
                      onClick={handleGenerateForm12B}
                      disabled={form12bLoading}
                      className="w-full bg-[#FACC15] hover:bg-yellow-400 text-black border-2 border-black font-mono font-black py-2.5 px-4 uppercase text-xs shadow-[3px_3px_0px_0px_#000] flex items-center justify-center gap-2"
                    >
                      <FileText className="w-4 h-4" />
                      {form12bLoading ? 'Generating Form 12B...' : 'Generate & Download Statutory Form 12B'}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* SUB-TAB 3: OFFER COMPARISON */}
      {/* ==================================================================== */}
      {activeSubTab === 'offer_compare' && (
        <div className="space-y-8">
          <div className="border-4 border-black p-5 bg-[#FAF7F2] shadow-[6px_6px_0px_0px_#000] space-y-4">
            <h3 className="text-xl font-black font-['Space_Grotesk'] text-[#18153B] border-b-2 border-black pb-2">
              Compare Real In-Hand Take-Home Between Multiple Offers
            </h3>
            <p className="text-xs text-gray-600 max-w-2xl">
              Employers often advertise a massive 40% paper CTC hike, but after accounting for higher tax slabs,
              locked gratuity, and variable pay, your actual bank account credit might increase by only 15%.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div>
                <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                  Current CTC
                </label>
                <input
                  type="number"
                  value={currentCtc}
                  onChange={(e) => setCurrentCtc(Number(e.target.value))}
                  className="w-full px-3 py-2 border-2 border-black font-mono font-bold text-sm focus:bg-amber-50 focus:outline-none"
                  placeholder="e.g. 1200000"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                  Offer A Annual CTC
                </label>
                <input
                  type="number"
                  value={offerACtc}
                  onChange={(e) => setOfferACtc(Number(e.target.value))}
                  className="w-full px-3 py-2 border-2 border-black font-mono font-bold text-sm focus:bg-amber-50 focus:outline-none"
                  placeholder="e.g. 1800000"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold uppercase text-gray-800 mb-1">
                  Offer B Annual CTC (Optional)
                </label>
                <input
                  type="number"
                  value={offerBCtc}
                  onChange={(e) => setOfferBCtc(Number(e.target.value))}
                  className="w-full px-3 py-2 border-2 border-black font-mono font-bold text-sm focus:bg-amber-50 focus:outline-none"
                  placeholder="e.g. 2200000"
                />
              </div>
            </div>

            <button
              onClick={handleCompareOffers}
              disabled={compareLoading}
              className="bg-[#18153B] hover:bg-[#252055] text-white border-2 border-black font-mono font-black py-2.5 px-6 uppercase text-xs shadow-[3px_3px_0px_0px_#000] flex items-center gap-2"
            >
              {compareLoading ? 'Comparing Offers...' : 'Run Comparative In-Hand Analysis'}
              <ArrowRight className="w-4 h-4 text-[#FACC15]" />
            </button>

            {compareError && (
              <div className="p-3 bg-rose-100 border-2 border-rose-500 text-rose-900 text-xs font-bold">
                {compareError}
              </div>
            )}
          </div>

          {compareData && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Current Job */}
              <div className="border-4 border-black p-5 bg-white shadow-[6px_6px_0px_0px_#000] space-y-4">
                <div className="border-b-2 border-black pb-2">
                  <span className="font-mono text-xs font-bold text-gray-500 uppercase">BENCHMARK</span>
                  <h4 className="font-black font-['Space_Grotesk'] text-lg text-[#18153B]">Current Salary</h4>
                </div>

                <div className="font-mono space-y-2 text-sm">
                  <div>
                    <span className="text-gray-500 text-xs">Annual CTC:</span>
                    <div className="font-bold">₹{compareData.current.ctc.toLocaleString('en-IN')}</div>
                  </div>
                  <div>
                    <span className="text-gray-500 text-xs">Monthly In-Hand:</span>
                    <div className="text-xl font-black text-gray-900">
                      ₹{compareData.current.monthly_in_hand.toLocaleString('en-IN')}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500 text-xs">Annual Tax (New Regime):</span>
                    <div className="font-bold text-rose-700">₹{compareData.current.annual_tax.toLocaleString('en-IN')}</div>
                  </div>
                </div>
              </div>

              {/* Offer A */}
              <div className="border-4 border-black p-5 bg-amber-50 border-amber-600 shadow-[6px_6px_0px_0px_#000] space-y-4">
                <div className="border-b-2 border-amber-600 pb-2 flex justify-between items-center">
                  <div>
                    <span className="font-mono text-xs font-black text-amber-800 uppercase">OPTION 1</span>
                    <h4 className="font-black font-['Space_Grotesk'] text-lg text-[#18153B]">Offer A</h4>
                  </div>
                  <span className="bg-[#18153B] text-[#FACC15] font-mono text-xs font-black px-2 py-0.5 border border-black">
                    +{compareData.offer_a.paper_ctc_hike_pct}% CTC
                  </span>
                </div>

                <div className="font-mono space-y-2 text-sm">
                  <div>
                    <span className="text-gray-500 text-xs">Annual CTC:</span>
                    <div className="font-bold">₹{compareData.offer_a.ctc.toLocaleString('en-IN')}</div>
                  </div>
                  <div>
                    <span className="text-gray-500 text-xs">Monthly In-Hand:</span>
                    <div className="text-xl font-black text-emerald-800">
                      ₹{compareData.offer_a.monthly_in_hand.toLocaleString('en-IN')}
                    </div>
                  </div>
                  <div className="p-2 bg-emerald-100 border border-emerald-600 text-xs font-bold text-emerald-950">
                    Real In-Hand Hike: +{compareData.offer_a.real_in_hand_hike_pct}% (+₹{compareData.offer_a.monthly_cash_gain?.toLocaleString('en-IN')}/mo)
                  </div>
                </div>
              </div>

              {/* Offer B */}
              {compareData.offer_b && (
                <div className="border-4 border-black p-5 bg-emerald-50 border-emerald-600 shadow-[6px_6px_0px_0px_#000] space-y-4">
                  <div className="border-b-2 border-emerald-600 pb-2 flex justify-between items-center">
                    <div>
                      <span className="font-mono text-xs font-black text-emerald-800 uppercase">OPTION 2</span>
                      <h4 className="font-black font-['Space_Grotesk'] text-lg text-[#18153B]">Offer B</h4>
                    </div>
                    <span className="bg-[#18153B] text-[#FACC15] font-mono text-xs font-black px-2 py-0.5 border border-black">
                      +{compareData.offer_b.paper_ctc_hike_pct}% CTC
                    </span>
                  </div>

                  <div className="font-mono space-y-2 text-sm">
                    <div>
                      <span className="text-gray-500 text-xs">Annual CTC:</span>
                      <div className="font-bold">₹{compareData.offer_b.ctc.toLocaleString('en-IN')}</div>
                    </div>
                    <div>
                      <span className="text-gray-500 text-xs">Monthly In-Hand:</span>
                      <div className="text-xl font-black text-emerald-800">
                        ₹{compareData.offer_b.monthly_in_hand.toLocaleString('en-IN')}
                      </div>
                    </div>
                    <div className="p-2 bg-emerald-100 border border-emerald-600 text-xs font-bold text-emerald-950">
                      Real In-Hand Hike: +{compareData.offer_b.real_in_hand_hike_pct}% (+₹{compareData.offer_b.monthly_cash_gain?.toLocaleString('en-IN')}/mo)
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* FORM 12B MODAL */}
      {/* ==================================================================== */}
      {showForm12BModal && form12bData && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-[#FAF7F2] border-4 border-black max-w-2xl w-full p-6 shadow-[8px_8px_0px_0px_#000] space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b-2 border-black pb-3">
              <div>
                <span className="text-xs font-mono font-black text-[#18153B] uppercase">STATUTORY DECLARATION</span>
                <h3 className="text-xl font-black font-['Space_Grotesk'] text-[#18153B]">
                  Form No. 12B (Section 192(2))
                </h3>
              </div>
              <button
                onClick={() => setShowForm12BModal(false)}
                className="bg-white hover:bg-gray-100 border-2 border-black font-mono font-bold px-3 py-1 text-sm"
              >
                ✕ Close
              </button>
            </div>

            <p className="text-xs text-gray-700">
              Hand this statement to your new employer's finance or payroll team so they deduct the correct TDS each month, preventing surprise interest penalties.
            </p>

            <pre className="bg-[#18153B] text-emerald-400 p-4 font-mono text-xs whitespace-pre-wrap border-2 border-black overflow-x-auto leading-relaxed select-all">
              {form12bData.raw_form_text}
            </pre>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => copyToClipboard(form12bData.raw_form_text, setCopiedFormText)}
                className="bg-[#FACC15] hover:bg-yellow-400 text-black border-2 border-black font-mono font-bold text-xs py-2 px-4 shadow-[2px_2px_0px_0px_#000] flex items-center gap-1.5"
              >
                {copiedFormText ? <Check className="w-4 h-4 text-emerald-700" /> : <Copy className="w-4 h-4" />}
                {copiedFormText ? 'Copied Form 12B!' : 'Copy Form 12B Text'}
              </button>
              <button
                onClick={() => {
                  const blob = new Blob([form12bData.raw_form_text], { type: 'text/plain;charset=utf-8' });
                  const url = URL.createObjectURL(blob);
                  const link = document.createElement('a');
                  link.href = url;
                  link.download = `Form_12B_${form12bData.employee_name.replace(/\s+/g, '_')}.txt`;
                  link.click();
                  URL.revokeObjectURL(url);
                }}
                className="bg-[#18153B] hover:bg-[#252055] text-white border-2 border-black font-mono font-bold text-xs py-2 px-4 shadow-[2px_2px_0px_0px_#000] flex items-center gap-1.5"
              >
                <Download className="w-4 h-4 text-[#FACC15]" />
                Download .txt File
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
