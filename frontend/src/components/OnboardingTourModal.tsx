import React, { useState, useEffect, useCallback } from 'react';
import {
  X,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Minimize2,
  Maximize2,
  Target,
  Check,
  ChevronRight,
  Eye,
} from 'lucide-react';
import type { TabKey } from './Navbar';

interface OnboardingTourModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTab: (tab: TabKey) => void;
}

interface TourStep {
  stepNumber: number;
  title: string;
  tabKey: TabKey;
  targetSelector: string;
  targetName: string;
  badgeText: string;
  tag: string;
  whatItDoes: string;
  whatToDo: string[];
}

export const OnboardingTourModal: React.FC<OnboardingTourModalProps> = ({
  isOpen,
  onClose,
  onSelectTab,
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isMinimized, setIsMinimized] = useState(false);
  const [dontShowAgain, setDontShowAgain] = useState(true);
  const [targetRect, setTargetRect] = useState<{
    top: number;
    left: number;
    width: number;
    height: number;
  } | null>(null);

  const steps: TourStep[] = [
    {
      stepNumber: 1,
      title: '6-Step Financial Workflow Navigation',
      tabKey: 'upload',
      targetSelector: '[data-tour="nav-tabs"]',
      targetName: 'Top Navigation Bar (Tabs 1 to 6)',
      badgeText: '👇 LOOK HERE: 6-STEP FINANCIAL WORKFLOW',
      tag: 'PIPELINE & OVERVIEW',
      whatItDoes:
        'Tax Planner is structured into 6 sequential phases for FY 2025–26. Each tab guides you from raw document intake, through automated ML transaction analysis and salary cross-reconciliation, to deduction optimization and final tax liability computation.',
      whatToDo: [
        'Notice the 6 tabs: 1. Ingest Docs → 2. Snapshot → 3. Reconciliation → 4. Catalog → 5. Mr. Planner → 6. Final Report.',
        'You can jump between tabs anytime. All tax liability math is computed mathematically with ₹0.00 drift.',
      ],
    },
    {
      stepNumber: 2,
      title: 'Multi-Bank Statement & Salary Slip Upload',
      tabKey: 'upload',
      targetSelector: '[data-tour="upload-cards"]',
      targetName: 'Bank Statement & Salary Slip Dropzones',
      badgeText: '👇 LOOK HERE: STATEMENT & SALARY DROPZONES',
      tag: 'TAB 1: DOCUMENT INGESTION',
      whatItDoes:
        'The intake parser reads multi-bank statements (HDFC, ICICI, SBI, Axis, or custom CSV) and salary slips. It extracts transactions, parses earnings and deductions, and mathematically verifies balance continuity (Opening + Credits - Debits = Closing) within ₹1.00 tolerance.',
      whatToDo: [
        'Select your bank format (or leave as Auto-Detect).',
        'Drop your CSV or PDF statement into the left card and click "Upload Bank Statement".',
        'Upload your salary slip in the right card to extract basic pay, HRA, and TDS deductions.',
      ],
    },
    {
      stepNumber: 3,
      title: 'Secure Document Vault & Verification Badges',
      tabKey: 'upload',
      targetSelector: '[data-tour="vault-manager"]',
      targetName: 'Uploaded Documents Vault',
      badgeText: '👇 LOOK HERE: VERIFIED STATEMENT RECORDS',
      tag: 'TAB 1: ENCRYPTED VAULT',
      whatItDoes:
        'Every uploaded statement is archived securely in your private vault. The system displays verified upload IDs, continuity status, and gives you instant 1-click deletion if you ever want to replace a document.',
      whatToDo: [
        'Check for the "VERIFIED (Δ ≤ ₹1.00)" green badge to confirm mathematical accuracy.',
        'Use the red "Delete" button on any statement to immediately purge it and recalculate your cashflow.',
      ],
    },
    {
      stepNumber: 4,
      title: 'Financial Snapshot & ML Intelligence',
      tabKey: 'snapshot',
      targetSelector: '[data-tour="snapshot-view"]',
      targetName: 'Cashflow Metrics & 50/30/20 Diagnostics',
      badgeText: '👇 LOOK HERE: REAL CASHFLOW & ML CATEGORIZATION',
      tag: 'TAB 2: FINANCIAL INTELLIGENCE',
      whatItDoes:
        'Our in-house 384-dimensional MiniLM semantic embedding model classifies every transaction with 91.67% accuracy into statutory buckets (Salary, Groceries, Dining, Investments, Rent, Medical). Zero synthetic data is used.',
      whatToDo: [
        'Review your Total Inflow vs Outflow and Net Savings Rate.',
        'Inspect your 50/30/20 budget diagnostic (Needs vs Wants vs Savings).',
        'Use the search filter to examine classified merchant transactions and confidence scores.',
      ],
    },
    {
      stepNumber: 5,
      title: 'Salary Slip vs Bank Cross-Reconciliation',
      tabKey: 'reconciliation',
      targetSelector: '[data-tour="reconciliation-view"]',
      targetName: 'Payroll Audit & Discrepancy Flags',
      badgeText: '👇 LOOK HERE: SALARY CROSS-MATCHING ENGINE',
      tag: 'TAB 3: PAYROLL AUDIT',
      whatItDoes:
        'The reconciliation engine cross-checks the net pay printed on your salary slip against the actual salary deposit in your bank statement. If the amounts diverge by more than max(₹500, 1%), an audit flag is raised.',
      whatToDo: [
        'Click "Run Cross-Reconciliation" to audit your salary credits.',
        'If any discrepancy flags appear, inspect the variance and resolve or ignore them with full audit trail history.',
      ],
    },
    {
      stepNumber: 6,
      title: '18 Statutory Deductions & HRA Optimizer',
      tabKey: 'catalog',
      targetSelector: '[data-tour="deduction-catalog"]',
      targetName: 'Chapter VI-A Statutory Repository',
      badgeText: '👇 LOOK HERE: CHAPTER VI-A DEDUCTIONS',
      tag: 'TAB 4: DEDUCTION REPOSITORY',
      whatItDoes:
        'Complete interactive catalog of all 18 statutory deductions under the Old Tax Regime, including Section 80C (up to ₹1.5L), 80D (Health Insurance up to ₹1L), 80CCD(1B) (NPS ₹50K), 80E, 80G, and Section 10(13A) HRA exemption.',
      whatToDo: [
        'Click on any deduction section to declare investments or enter rent paid.',
        'The system automatically enforces statutory legal caps and recalculates tax savings in real time.',
      ],
    },
    {
      stepNumber: 7,
      title: 'Mr. Planner: AI Tax Strategist with RAG',
      tabKey: 'chat',
      targetSelector: '[data-tour="agent-chat"]',
      targetName: 'Mr. Planner Conversational Agent',
      badgeText: '👇 LOOK HERE: AI TAX ADVISORY CHAT',
      tag: 'TAB 5: AI TAX STRATEGIST',
      whatItDoes:
        'Mr. Planner is an intelligent agent built on LangGraph and ChromaDB vector retrieval across the Indian Income Tax Act 1961. It retrieves legal tax clauses with 100% Top-1 accuracy while delegating currency math to the deterministic engine.',
      whatToDo: [
        'Ask questions in natural language: "Should I switch to the New Tax Regime?", "How much HRA can I claim for ₹30,000 rent?".',
        'Click any suggested prompt pill to run instant scenario audits.',
      ],
    },
    {
      stepNumber: 8,
      title: 'Section 115BAC Dual-Regime Report & PDF',
      tabKey: 'report',
      targetSelector: '[data-tour="tax-report"]',
      targetName: 'Dual-Regime Audit & Vector PDF Export',
      badgeText: '👇 LOOK HERE: EXACT TAX LIABILITY & PDF EXPORT',
      tag: 'TAB 6: DUAL-REGIME TAX AUDIT',
      whatItDoes:
        'Computes side-by-side tax liability for FY 2025–26 under Section 115BAC (New Regime) and Old Regime, applying ₹75,000 standard deduction, revised slabs, and marginal relief rebate up to ₹12 Lakhs income.',
      whatToDo: [
        'See which regime saves you more tax with the recommended regime banner.',
        'Inspect the slab-by-slab breakdown and effective tax rate.',
        'Click "DOWNLOAD TAX INVOICE (PDF)" to generate an official report.',
      ],
    },
    {
      stepNumber: 9,
      title: 'Data Sovereignty & Bring-Your-Own-Key (BYOK)',
      tabKey: 'report',
      targetSelector: '[data-tour="vault-actions"]',
      targetName: 'VAULT DATA & AI KEYS (BYOK) Buttons',
      badgeText: '👆 LOOK HERE: PRIVACY VAULT & BYOK SETTINGS',
      tag: 'SECURITY & SETTINGS',
      whatItDoes:
        'You have complete data sovereignty. "VAULT DATA" allows 1-click ZIP export and right-to-erasure account purging. "AI KEYS (BYOK)" allows you to plug in your personal OpenRouter, OpenAI, Groq, or Gemini keys.',
      whatToDo: [
        'Click "AI KEYS (BYOK)" in the top header if you wish to use your own free OpenRouter key.',
        'Click "VAULT DATA" anytime you want to export your records or delete your account.',
        'Click "FINISH TOUR" below to start planning your taxes!',
      ],
    },
  ];

  const currentStep = steps[currentStepIndex];

  // Reposition target spotlight overlay
  const updateTargetRect = useCallback(() => {
    if (!isOpen || !currentStep?.targetSelector) {
      setTargetRect(null);
      return;
    }

    const el = document.querySelector(currentStep.targetSelector) as HTMLElement | null;
    if (el) {
      const rect = el.getBoundingClientRect();
      setTargetRect({
        top: rect.top + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width,
        height: rect.height,
      });

      // Smooth scroll target into view if it is not fully visible
      const isVisible =
        rect.top >= 50 &&
        rect.bottom <= window.innerHeight - 80;

      if (!isVisible) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    } else {
      setTargetRect(null);
    }
  }, [isOpen, currentStep]);

  // Sync background tab and re-anchor spotlight
  useEffect(() => {
    if (!isOpen) return;

    if (currentStep.tabKey) {
      onSelectTab(currentStep.tabKey);
    }

    // Small timeouts to allow React DOM re-rendering after tab change
    const timer1 = setTimeout(updateTargetRect, 80);
    const timer2 = setTimeout(updateTargetRect, 260);

    window.addEventListener('resize', updateTargetRect);
    window.addEventListener('scroll', updateTargetRect, { passive: true });

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      window.removeEventListener('resize', updateTargetRect);
      window.removeEventListener('scroll', updateTargetRect);
    };
  }, [isOpen, currentStepIndex, currentStep, onSelectTab, updateTargetRect]);

  if (!isOpen) return null;

  const handleNext = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const handleComplete = () => {
    if (dontShowAgain) {
      localStorage.setItem('taxplanner_onboarding_tour_seen', 'true');
    }
    onClose();
  };

  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === steps.length - 1;
  const progressPercent = Math.round(((currentStepIndex + 1) / steps.length) * 100);

  return (
    <>
      {/* 1. VISUAL SPOTLIGHT OVERLAY & TARGET BEACON (NON-BLOCKING) */}
      {targetRect && (
        <div
          className="fixed pointer-events-none z-[9990] transition-all duration-300 ease-out"
          style={{
            top: targetRect.top - window.scrollY - 6,
            left: targetRect.left - window.scrollX - 6,
            width: targetRect.width + 12,
            height: targetRect.height + 12,
            outline: '4px solid #000',
            boxShadow: '0 0 0 4px #FACC15, 0 0 35px rgba(250, 204, 21, 0.9), inset 0 0 15px rgba(250, 204, 21, 0.3)',
          }}
        >
          {/* Animated Target Beacon Badge */}
          <div className="absolute -top-10 left-2 bg-[#18153B] text-[#FACC15] px-3 py-1 border-2 border-black shadow-[3px_3px_0px_0px_#000] flex items-center gap-2 font-mono font-black text-xs uppercase tracking-wider animate-bounce whitespace-nowrap">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FACC15] animate-ping" />
            <span>{currentStep.badgeText}</span>
          </div>
        </div>
      )}

      {/* 2. FLOATING SMART GUIDE DOCK (BOTTOM-RIGHT, NON-OBTRUSIVE) */}
      <div className="fixed bottom-5 right-5 z-[9999] w-[94vw] max-w-lg font-mono">
        {isMinimized ? (
          /* Minimized Compact Guide Pill */
          <div className="bg-[#FFFDF9] border-4 border-black p-3 shadow-[6px_6px_0px_0px_#000000] flex items-center justify-between gap-3 animate-in fade-in slide-in-from-bottom-3 duration-200">
            <div className="flex items-center gap-2">
              <div className="p-1 bg-[#FACC15] border border-black">
                <Sparkles className="w-4 h-4 text-black" />
              </div>
              <div>
                <span className="text-[10px] font-black uppercase text-[#3730A3] block">
                  STEP {currentStep.stepNumber} OF {steps.length} • {currentStep.tag}
                </span>
                <span className="text-xs font-black text-black truncate block max-w-[240px] sm:max-w-xs">
                  {currentStep.title}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsMinimized(false)}
                className="bg-[#FACC15] hover:bg-yellow-400 text-black px-2.5 py-1.5 border-2 border-black font-black text-xs shadow-[2px_2px_0px_0px_#000] flex items-center gap-1 cursor-pointer active:translate-x-0.5 active:translate-y-0.5"
                title="Expand Tour Guide"
              >
                <Maximize2 className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">EXPAND</span>
              </button>
              <button
                onClick={handleComplete}
                className="bg-gray-200 hover:bg-gray-300 text-black p-1.5 border border-black cursor-pointer"
                title="Exit Tour"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ) : (
          /* Expanded Full Tour Card */
          <div className="bg-[#FFFDF9] border-4 border-black shadow-[8px_8px_0px_0px_#000000] flex flex-col animate-in fade-in zoom-in-95 duration-200">
            {/* Header */}
            <div className="bg-[#18153B] text-white p-3 border-b-3 border-black flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="p-1 bg-[#FACC15] text-black border border-black font-black text-[10px] tracking-wider">
                  STEP {currentStep.stepNumber}/{steps.length}
                </span>
                <span className="text-xs font-black text-[#FACC15] uppercase tracking-wide">
                  {currentStep.tag}
                </span>
              </div>

              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setIsMinimized(true)}
                  className="text-white hover:text-[#FACC15] p-1 border border-white/20 hover:border-[#FACC15] cursor-pointer transition-colors"
                  title="Minimize to Corner"
                >
                  <Minimize2 className="w-4 h-4" />
                </button>
                <button
                  onClick={handleComplete}
                  className="text-white hover:text-red-400 p-1 border border-white/20 hover:border-red-400 cursor-pointer transition-colors"
                  title="Exit Tour"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Visual Progress Bar */}
            <div className="w-full bg-gray-200 h-2 border-b-2 border-black">
              <div
                className="bg-[#FACC15] h-full transition-all duration-300 border-r-2 border-black"
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            {/* Content Body */}
            <div className="p-4 sm:p-5 space-y-3.5 text-xs">
              {/* Highlight Target Indicator Strip */}
              <div className="bg-[#FAF7F2] border-2 border-black p-2 flex items-center gap-2 shadow-[2px_2px_0px_0px_#000]">
                <Target className="w-4 h-4 text-[#3730A3] flex-shrink-0" />
                <div className="truncate">
                  <span className="text-[10px] text-gray-500 font-bold uppercase block">
                    CURRENTLY HIGHLIGHTED ON SCREEN:
                  </span>
                  <span className="font-black text-[#18153B] uppercase text-[11px] truncate block">
                    {currentStep.targetName}
                  </span>
                </div>
              </div>

              {/* Step Title */}
              <div>
                <h4 className="text-base font-black uppercase text-[#18153B] font-['Space_Grotesk'] leading-tight">
                  {currentStep.title}
                </h4>
                <p className="text-xs text-gray-700 font-medium font-['Plus_Jakarta_Sans'] mt-1 leading-relaxed">
                  {currentStep.whatItDoes}
                </p>
              </div>

              {/* Actionable Guidance (What You Should Do) */}
              <div className="bg-amber-50 border-2 border-black p-3 space-y-1.5 shadow-[2px_2px_0px_0px_#000]">
                <span className="font-black text-[10px] uppercase text-[#3730A3] flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5 text-[#3730A3]" />
                  <span>WHAT TO DO HERE:</span>
                </span>
                <ul className="space-y-1 text-[11px] text-gray-800 font-semibold font-['Plus_Jakarta_Sans']">
                  {currentStep.whatToDo.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <ChevronRight className="w-3.5 h-3.5 text-black flex-shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Step Dots (Click to Jump Directly) */}
              <div className="flex items-center justify-between pt-1 border-t border-gray-300">
                <span className="text-[10px] font-bold text-gray-500">JUMP TO:</span>
                <div className="flex items-center gap-1.5">
                  {steps.map((s, idx) => (
                    <button
                      key={s.stepNumber}
                      onClick={() => setCurrentStepIndex(idx)}
                      className={`w-6 h-6 flex items-center justify-center text-[10px] font-black border border-black cursor-pointer transition-all ${
                        idx === currentStepIndex
                          ? 'bg-[#FACC15] text-black shadow-[2px_2px_0px_0px_#000] -translate-y-0.5'
                          : idx < currentStepIndex
                          ? 'bg-[#3730A3] text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-100'
                      }`}
                      title={`Step ${s.stepNumber}: ${s.title}`}
                    >
                      {idx < currentStepIndex ? <Check className="w-3 h-3" /> : idx + 1}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer Controls */}
            <div className="p-3 bg-[#FAF7F2] border-t-3 border-black flex flex-wrap items-center justify-between gap-2">
              <label className="flex items-center gap-1.5 cursor-pointer select-none text-[11px] font-bold text-gray-700">
                <input
                  type="checkbox"
                  checked={dontShowAgain}
                  onChange={(e) => setDontShowAgain(e.target.checked)}
                  className="w-3.5 h-3.5 accent-[#3730A3] border border-black cursor-pointer"
                />
                <span>Don't auto-show again</span>
              </label>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleComplete}
                  className="bg-white hover:bg-gray-100 text-black px-2.5 py-1.5 border-2 border-black font-black uppercase text-[11px] shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
                >
                  SKIP
                </button>

                {!isFirstStep && (
                  <button
                    onClick={handlePrev}
                    className="flex items-center gap-1 bg-white hover:bg-gray-100 text-black px-2.5 py-1.5 border-2 border-black font-black uppercase text-[11px] shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>PREV</span>
                  </button>
                )}

                <button
                  onClick={handleNext}
                  className={`flex items-center gap-1.5 px-4 py-1.5 border-2 border-black font-black uppercase text-[11px] shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer ${
                    isLastStep
                      ? 'bg-emerald-400 hover:bg-emerald-300 text-black animate-pulse'
                      : 'bg-[#FACC15] hover:bg-yellow-400 text-black'
                  }`}
                >
                  <span>{isLastStep ? 'FINISH TOUR 🚀' : 'NEXT STEP'}</span>
                  {!isLastStep && <ArrowRight className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};
