import React from 'react';
import {
  Sparkles,
  ArrowRight,
  FileSpreadsheet,
  FileCheck2,
  Bot,
  Scissors,
} from 'lucide-react';

interface LandingViewProps {
  onOpenAuth: (mode: 'login' | 'register') => void;
}

export const LandingView: React.FC<LandingViewProps> = ({ onOpenAuth }) => {
  return (
    <div className="space-y-16 py-6">
      {/* Gen Alpha Packaging Hero Section */}
      <div className="relative bg-[#FAF7F2] border-4 border-black p-6 md:p-12 shadow-[10px_10px_0px_0px_#000000] overflow-hidden">
        {/* Decorative Tape Strip at the Top */}
        <div className="absolute top-0 left-0 right-0 bg-[#FACC15] border-b-3 border-black py-1 px-4 flex items-center justify-between text-[11px] font-black tracking-widest uppercase font-mono overflow-hidden">
          <div className="flex items-center gap-4 animate-marquee whitespace-nowrap">
            <span>⚠️ DO NOT ACCEPT IF RECONCILIATION SEAL IS BROKEN</span>
            <span>★</span>
            <span>BATCH NO: FY2025-26-AY26</span>
            <span>★</span>
            <span>OFFICIAL STATUTORY RATE ENGINE</span>
            <span>★</span>
            <span>100% EXACT STATUTORY MATH GUARANTEE</span>
            <span>★</span>
          </div>
        </div>

        {/* Top Stickers */}
        <div className="flex flex-wrap items-center justify-between gap-4 mt-6 mb-6">
          <div className="flex items-center gap-2">
            <span className="bg-[#3730A3] text-white font-black text-xs px-3 py-1.5 border-2 border-black shadow-[3px_3px_0px_0px_#000] rotate-[-2deg] font-mono">
              TAX PLANNER // COLLECTOR EDITION
            </span>
            <span className="bg-[#F59E0B] text-black font-black text-xs px-3 py-1.5 border-2 border-black shadow-[3px_3px_0px_0px_#000] rotate-[1deg] font-mono">
              LIMITED FY 25–26 DROP
            </span>
          </div>

          <div className="font-mono text-xs font-black bg-white border-2 border-black px-3 py-1 shadow-[2px_2px_0px_0px_#000]">
            EDITION: SALARIED-FY26
          </div>
        </div>

        {/* Hero Packaging Headline */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-7 space-y-6">
            <h1 className="text-4xl sm:text-6xl md:text-7xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-[0.95]">
              STOP GUESSING TAXES.
              <br />
              <span className="bg-[#FACC15] px-2 py-0.5 border-3 border-black shadow-[4px_4px_0px_0px_#000] inline-block mt-2">
                MAXIMIZE REBATE.
              </span>
            </h1>

            <p className="text-base sm:text-lg font-medium text-gray-800 leading-relaxed font-['Plus_Jakarta_Sans'] max-w-xl">
              The first salaried tax intelligence platform engineered for FY 2025–26. Ingest real bank
              statements, reconcile salary slips within ₹1.00 tolerance, and compare New vs Old Tax
              Regime with zero arithmetic hallucinations.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                onClick={() => onOpenAuth('register')}
                className="bg-[#3730A3] hover:bg-[#4338CA] text-white px-8 py-4 border-3 border-black shadow-[6px_6px_0px_0px_#000000] font-black text-sm md:text-base tracking-wider uppercase flex items-center gap-3 active:translate-x-1 active:translate-y-1 active:shadow-none transition-all"
              >
                <span>OPEN YOUR TAX VAULT</span>
                <ArrowRight className="w-5 h-5 stroke-[3]" />
              </button>

              <button
                onClick={() => onOpenAuth('login')}
                className="bg-[#FAF7F2] hover:bg-white text-black px-6 py-4 border-3 border-black shadow-[4px_4px_0px_0px_#000000] font-black text-sm md:text-base tracking-wider uppercase active:translate-x-1 active:translate-y-1 active:shadow-none transition-all"
              >
                <span>SIGN IN TO VAULT</span>
              </button>
            </div>

            {/* Barcode Strip */}
            <div className="pt-4 flex items-center gap-3 text-gray-700 font-mono text-xs">
              <span className="tracking-widest font-black text-sm">|||| | ||||| || | |||| ||||| | ||</span>
              <span className="font-bold">100% DETERMINISTIC CALCULATION</span>
            </div>
          </div>

          {/* Right Packaging "TAX FACTS" Nutrition Label (Gen Alpha / Streetwear Packaging Vibe) */}
          <div className="lg:col-span-5 bg-white border-4 border-black p-5 shadow-[8px_8px_0px_0px_#000000] font-mono">
            <div className="border-b-8 border-black pb-1 mb-2">
              <h3 className="text-3xl font-black uppercase tracking-tighter leading-none font-['Space_Grotesk']">
                TAX FACTS
              </h3>
              <p className="text-xs font-bold text-gray-700">
                Serving Size: 1 Indian Salaried Return (FY 2025–26)
              </p>
            </div>

            <div className="border-b-4 border-black py-1 flex justify-between font-black text-xs">
              <span>Amount Per Filing</span>
              <span>% Statutory Value*</span>
            </div>

            <div className="space-y-1.5 py-2 text-xs border-b border-black">
              <div className="flex justify-between font-bold">
                <span>Arithmetic Hallucinations</span>
                <span className="font-black bg-red-200 px-1 border border-black">0g (0%)</span>
              </div>
              <div className="flex justify-between font-bold">
                <span>Deterministic Slips Engine</span>
                <span className="font-black bg-emerald-200 px-1 border border-black">100% DV</span>
              </div>
              <div className="flex justify-between font-bold">
                <span>Section 115BAC Rebate S.87A</span>
                <span className="font-black">Up to ₹12,00,000</span>
              </div>
              <div className="flex justify-between font-bold">
                <span>New Standard Deduction</span>
                <span className="font-black">₹75,000 (Enhanced)</span>
              </div>
              <div className="flex justify-between font-bold">
                <span>Old Regime Chapter VI-A Cap</span>
                <span className="font-black">₹1,50,000 (80C)</span>
              </div>
              <div className="flex justify-between font-bold">
                <span>NPS Tier-I Exclusive S.80CCD(1B)</span>
                <span className="font-black">₹50,000</span>
              </div>
              <div className="flex justify-between font-bold">
                <span>Tolerance Discrepancy Gate</span>
                <span className="font-black">max(₹500, 1%)</span>
              </div>
            </div>

            <div className="pt-2 text-[10px] leading-tight text-gray-600">
              * Percentage Daily Values are based on the Finance Act 2024 / 2025 statutory schedules.
              Calculations follow exact statutory provisions with 100% mathematical accuracy.
            </div>
          </div>
        </div>

        {/* Tear Strip at Bottom of Hero */}
        <div className="mt-10 pt-6 border-t-2 border-dashed border-black flex items-center justify-between text-xs font-mono font-black text-gray-700">
          <div className="flex items-center gap-2">
            <Scissors className="w-4 h-4" />
            <span>TEAR HERE TO UNBOX YOUR REAL DATA</span>
          </div>
          <span className="hidden sm:inline">AUTHENTICATED USER SCOPE // ISOLATION CERTIFIED</span>
        </div>
      </div>

      {/* 4 Packaging Steps (How It Works) */}
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <span className="bg-[#FACC15] text-black text-xs font-black font-mono px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
            UNBOXING SPECIFICATION
          </span>
          <h2 className="text-2xl md:text-3xl font-black uppercase font-['Space_Grotesk'] text-[#18153B]">
            HOW THE ENGINE PROCESSES YOUR TAXES
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Step 1 */}
          <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-2xl font-black bg-[#FACC15] text-black w-10 h-10 border-2 border-black flex items-center justify-center">
                  01
                </span>
                <FileSpreadsheet className="w-6 h-6 text-[#3730A3]" />
              </div>
              <h4 className="text-lg font-black uppercase font-['Space_Grotesk'] mb-2">
                INGESTION &amp; OCR
              </h4>
              <p className="text-xs font-semibold text-gray-700 leading-relaxed font-['Plus_Jakarta_Sans']">
                Smart document intake parses multi-bank statements (HDFC, ICICI, SBI, Axis) and
                salary slips, extracting exact earnings, PF, and tax debits.
              </p>
            </div>
            <span className="mt-4 pt-3 border-t-2 border-gray-200 text-[11px] font-mono font-bold text-emerald-800">
              ✓ Auto Balance Continuity
            </span>
          </div>

          {/* Step 2 */}
          <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-2xl font-black bg-[#F59E0B] text-black w-10 h-10 border-2 border-black flex items-center justify-center">
                  02
                </span>
                <Sparkles className="w-6 h-6 text-[#F59E0B]" />
              </div>
              <h4 className="text-lg font-black uppercase font-['Space_Grotesk'] mb-2">
                EXPENSE CATEGORIZATION
              </h4>
              <p className="text-xs font-semibold text-gray-700 leading-relaxed font-['Plus_Jakarta_Sans']">
                Automated intelligence categorizes transactions into 12 spending categories, flagging
                low-confidence items for your review.
              </p>
            </div>
            <span className="mt-4 pt-3 border-t-2 border-gray-200 text-[11px] font-mono font-bold text-emerald-800">
              ✓ Self-Transfers Isolated
            </span>
          </div>

          {/* Step 3 */}
          <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-2xl font-black bg-[#3730A3] text-white w-10 h-10 border-2 border-black flex items-center justify-center">
                  03
                </span>
                <Bot className="w-6 h-6 text-[#3730A3]" />
              </div>
              <h4 className="text-lg font-black uppercase font-['Space_Grotesk'] mb-2">
                MR. PLANNER (AI)
              </h4>
              <p className="text-xs font-semibold text-gray-700 leading-relaxed font-['Plus_Jakarta_Sans']">
                Meet Mr. Planner, your AI Tax Strategist who guides you through Section 80C, 80D, 80CCD(1B), and HRA
                exemptions with verified deduction discovery.
              </p>
            </div>
            <span className="mt-4 pt-3 border-t-2 border-gray-200 text-[11px] font-mono font-bold text-emerald-800">
              ✓ Exact Math Guarantee
            </span>
          </div>

          {/* Step 4 */}
          <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-2xl font-black bg-[#10B981] text-black w-10 h-10 border-2 border-black flex items-center justify-center">
                  04
                </span>
                <FileCheck2 className="w-6 h-6 text-[#10B981]" />
              </div>
              <h4 className="text-lg font-black uppercase font-['Space_Grotesk'] mb-2">
                FINAL TAX REPORT
              </h4>
              <p className="text-xs font-semibold text-gray-700 leading-relaxed font-['Plus_Jakarta_Sans']">
                Side-by-side comparison of Section 115BAC New Regime vs Old Regime with statutory
                citations, rebate calculations, and optimization suggestions.
              </p>
            </div>
            <span className="mt-4 pt-3 border-t-2 border-gray-200 text-[11px] font-mono font-bold text-emerald-800">
              ✓ ₹12L Zero Tax Rebate
            </span>
          </div>
        </div>
      </div>

      {/* Big Packaging CTA Bar at Bottom */}
      <div className="bg-[#FACC15] border-4 border-black p-8 shadow-[8px_8px_0px_0px_#000] flex flex-wrap items-center justify-between gap-6">
        <div>
          <span className="bg-black text-white text-xs font-black font-mono px-2.5 py-1 uppercase">
            INSTANT PRIVATE VAULT ACCESS
          </span>
          <h3 className="text-3xl md:text-4xl font-black uppercase font-['Space_Grotesk'] text-black mt-2">
            READY TO UNBOX YOUR FY 2025–26 SAVINGS?
          </h3>
          <p className="text-sm font-bold text-black max-w-xl mt-1">
            Create your private account in seconds. Your financial records remain completely private and
            encrypted.
          </p>
        </div>

        <button
          onClick={() => onOpenAuth('register')}
          className="bg-[#3730A3] hover:bg-[#4338CA] text-white px-8 py-4 border-3 border-black shadow-[4px_4px_0px_0px_#000] font-black text-base uppercase tracking-wider flex items-center gap-3 active:translate-x-1 active:translate-y-1 active:shadow-none transition-all"
        >
          <span>CREATE ACCOUNT NOW</span>
          <ArrowRight className="w-5 h-5 stroke-[3]" />
        </button>
      </div>
    </div>
  );
};
