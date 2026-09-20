import React, { useState } from 'react';
import {
  X,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  UploadCloud,
  PieChart,
  GitCompare,
  BookOpen,
  MessageSquareCode,
  FileCheck2,
  ShieldCheck,
  Lightbulb,
  Check,
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
  tabKey?: TabKey;
  icon: React.ReactNode;
  tag: string;
  headline: string;
  description: string;
  highlights: string[];
  proTip: string;
}

export const OnboardingTourModal: React.FC<OnboardingTourModalProps> = ({
  isOpen,
  onClose,
  onSelectTab,
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [dontShowAgain, setDontShowAgain] = useState(true);

  if (!isOpen) return null;

  const steps: TourStep[] = [
    {
      stepNumber: 1,
      title: 'Welcome to Tax Planner FY 2025–26',
      tabKey: 'upload',
      icon: <Sparkles className="w-8 h-8 text-black" />,
      tag: 'OVERVIEW & ARCHITECTURE',
      headline: 'Autonomous Personal Finance & Dual-Regime Tax Planner',
      description:
        'Tax Planner is an enterprise-grade financial intelligence engine. It combines in-house machine learning for transaction categorization, deterministic statutory tax rules, and an AI conversational agent.',
      highlights: [
        '100% Exact Math Guarantee: All tax liabilities are computed via deterministic Python formulas with ₹0.00 variance.',
        'Zero LLM Arithmetic: The AI strictly advises and gathers inputs; it never computes currency math.',
        'Private & Isolated: All data is cross-tenant isolated with complete DPDP/GDPR right-to-erasure controls.',
      ],
      proTip:
        'This 2-minute tour will walk you through each tab. The background will automatically navigate as you progress!',
    },
    {
      stepNumber: 2,
      title: 'Tab 1: Document Intake & Ingestion',
      tabKey: 'upload',
      icon: <UploadCloud className="w-8 h-8 text-white" />,
      tag: 'TAB 1 // INGESTION VAULT',
      headline: 'Ingest Bank Statements & Salary Slips Seamlessly',
      description:
        'Upload your multi-bank account statements (HDFC, ICICI, SBI, Axis, Kotak) in PDF or CSV format, plus monthly corporate salary slips.',
      highlights: [
        'Running Balance Continuity Check: Validates debit/credit continuity with strict Δ ≤ ₹1.00 tolerance check.',
        'Intelligent PDF & OCR Parser: Handles text PDFs, scanned statements via RapidOCR, and custom CSV column mappings.',
        'Interactive Document Vault: View parsed files, date ranges, and 1-click delete individual uploads without manual IDs.',
      ],
      proTip:
        'You can drop password-free PDFs or CSVs directly into the upload cards above to parse hundreds of transactions in seconds.',
    },
    {
      stepNumber: 3,
      title: 'Tab 2: Financial Snapshot & ML Intelligence',
      tabKey: 'snapshot',
      icon: <PieChart className="w-8 h-8 text-black" />,
      tag: 'TAB 2 // SPENDING INTELLIGENCE',
      headline: 'Dense NLP Semantic Categorization & 50/30/20 Budgeting',
      description:
        'Our in-house ML model encodes transactions into 384-dimensional dense semantic vectors using sentence-transformers to categorize your spendings.',
      highlights: [
        '91.67% Classification Accuracy: Outperforms XGBoost baselines across 12 canonical financial categories.',
        'Active Learning Drift Correction: Low-confidence transactions (<0.60) can be reviewed to continuously improve accuracy.',
        'Budget Diagnostics: Automated 50/30/20 Needs vs Wants vs Savings breakdown and recurring subscription detection.',
      ],
      proTip:
        'Check your Top Merchants and Recurring Subscriptions list to identify hidden expenses and tax-deductible outflows.',
    },
    {
      stepNumber: 4,
      title: 'Tab 3: Bank & Salary Reconciliation',
      tabKey: 'reconciliation',
      icon: <GitCompare className="w-8 h-8 text-white" />,
      tag: 'TAB 3 // CONTINUITY AUDIT',
      headline: 'Cross-Match Salary Credits with Bank Transactions',
      description:
        'Reconciles your employer salary slips against your actual bank account credits, highlighting discrepancies and missing months.',
      highlights: [
        'Deterministic Reconciliation Gate: Flags discrepancies exceeding max(₹500, 1%) between net pay and bank credits.',
        'Actionable Flag Resolver: Resolve flags with 1-click actions (reimbursement adjustment, timing delay, or manual override).',
        'Continuous Sync: Any file deletion automatically re-triggers the reconciliation pipeline across your account.',
      ],
      proTip:
        'Look at the red badge in the Navbar navigation—it displays the number of pending discrepancies requiring your attention.',
    },
    {
      stepNumber: 5,
      title: 'Tab 4: Statutory Deductions Catalog',
      tabKey: 'catalog',
      icon: <BookOpen className="w-8 h-8 text-black" />,
      tag: 'TAB 4 // STATUTORY DEDUCTIONS',
      headline: 'Claim Deductions under Chapter VI-A with Official Ceilings',
      description:
        'Explore and declare deductions across all 18 personal tax provisions under the Indian Income Tax Act with statutory limits.',
      highlights: [
        'Comprehensive Sections: Section 80C (₹1.5L cap), 80D (Health Insurance), 80CCD(1B) NPS (₹50k), HRA, 80G, 80TTA, and Section 24(b).',
        'Auto-Detected Claims: Transactions matching eligible tax-deductible merchants are automatically flagged for claim.',
        'Interactive Eligibility Gate: Fill in declarations with real-time feedback before computing your tax liability.',
      ],
      proTip:
        'You can also add custom deductions using the "Self-Add Deduction" button if you made direct investments offline.',
    },
    {
      stepNumber: 6,
      title: 'Tab 5: Mr. Planner — AI Conversational Tax Agent',
      tabKey: 'chat',
      icon: <MessageSquareCode className="w-8 h-8 text-white" />,
      tag: 'TAB 5 // AI TAX ADVISOR',
      headline: 'LangGraph State Machine with ChromaDB RAG Retrieval',
      description:
        'Chat with our specialized conversational tax agent to get statutory guidance grounded directly in the Finance Act FY 2025–26.',
      highlights: [
        '100% Top-1 RAG Accuracy: Queries are matched against verified tax circulars indexed in a ChromaDB vector database.',
        'Statutory Citations: Every answer provides direct hyperlinks to official Income Tax Department rules.',
        'Bring Your Own Key (BYOK): Supports OpenRouter, OpenAI, Anthropic, Gemini, or local models with client-side key encryption.',
      ],
      proTip:
        'Ask questions like "How is HRA calculated for Mumbai?" or "What is the 80D limit for senior citizen parents?" for instant statutory answers.',
    },
    {
      stepNumber: 7,
      title: 'Tab 6: Final Tax Report & Old vs New Comparison',
      tabKey: 'report',
      icon: <FileCheck2 className="w-8 h-8 text-black" />,
      tag: 'TAB 6 // STATUTORY COMPARISON',
      headline: 'Exact Side-by-Side Tax Computation & PDF Memo Export',
      description:
        'The culmination of your data: a rupee-exact comparison of your liability under the Old Regime vs revised Section 115BAC New Regime.',
      highlights: [
        'Finance Act 2024/2025 Compliant: Includes revised slabs, ₹75,000 standard deduction, and Section 87A ₹12L rebate with marginal relief.',
        'Recommended Regime Highlight: Instantly see exactly how many rupees you save by opting for Old vs New regime.',
        'Vector PDF Tax Invoice: Download an executive, publication-grade tax memo with your AIS checklist and deductions breakdown.',
      ],
      proTip:
        'Use the "Download Vector PDF Report" button to save or share your tax calculation memo with your CA or accountant!',
    },
    {
      stepNumber: 8,
      title: 'Privacy Vault & Complete Data Control',
      tabKey: 'upload',
      icon: <ShieldCheck className="w-8 h-8 text-white" />,
      tag: 'PRIVACY // RIGHT-TO-ERASURE',
      headline: 'Your Data, Your Keys, Complete GDPR/DPDP Compliance',
      description:
        'We believe in absolute data sovereignty. You have total control over your financial data and AI integration credentials.',
      highlights: [
        'Vault Data Management: Access "VAULT DATA" in the top bar to export a complete ZIP bundle (CSV, JSON, and PDF) or purge individual FY data.',
        'Permanent Right-to-Erasure: 1-click complete account wipe with zero orphaned rows in the database.',
        'BYOK Encryption: Your AI API keys are stored in encrypted browser memory or AES-vault storage, never shared with third parties.',
      ],
      proTip:
        'You can replay this interactive tutorial at any time by clicking the "GUIDE / TOUR" button in the top navigation bar!',
    },
  ];

  const currentStep = steps[currentStepIndex];
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === steps.length - 1;
  const progressPercent = Math.round(((currentStepIndex + 1) / steps.length) * 100);

  const handleNext = () => {
    if (isLastStep) {
      handleFinish();
    } else {
      const nextIndex = currentStepIndex + 1;
      setCurrentStepIndex(nextIndex);
      if (steps[nextIndex].tabKey) {
        onSelectTab(steps[nextIndex].tabKey!);
      }
    }
  };

  const handlePrev = () => {
    if (!isFirstStep) {
      const prevIndex = currentStepIndex - 1;
      setCurrentStepIndex(prevIndex);
      if (steps[prevIndex].tabKey) {
        onSelectTab(steps[prevIndex].tabKey!);
      }
    }
  };

  const handleFinish = () => {
    if (dontShowAgain) {
      localStorage.setItem('taxplanner_onboarding_tour_seen', 'true');
    }
    onClose();
  };

  const handleSkip = () => {
    if (dontShowAgain) {
      localStorage.setItem('taxplanner_onboarding_tour_seen', 'true');
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto font-mono">
      <div className="bg-[#FFFDF9] border-4 border-black w-full max-w-2xl shadow-[10px_10px_0px_0px_#000000] relative flex flex-col animate-in fade-in zoom-in-95 duration-200">
        {/* Top Header */}
        <div className="bg-[#18153B] text-white p-4 border-b-3 border-black flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-1.5 bg-[#FACC15] text-black border border-black font-black text-xs">
              TOUR // {currentStep.stepNumber} OF {steps.length}
            </div>
            <div>
              <span className="text-[11px] font-mono text-[#FACC15] font-black uppercase tracking-wider block">
                {currentStep.tag}
              </span>
              <h3 className="font-black text-base uppercase font-['Space_Grotesk'] text-white truncate max-w-sm sm:max-w-md">
                {currentStep.title}
              </h3>
            </div>
          </div>
          <button
            onClick={handleSkip}
            className="text-white hover:text-[#FACC15] p-1.5 border border-white/20 hover:border-[#FACC15] cursor-pointer transition-colors"
            title="Close Tour"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Visual Progress Bar */}
        <div className="w-full bg-gray-200 h-2.5 border-b-2 border-black">
          <div
            className="bg-[#FACC15] h-full transition-all duration-300 border-r-2 border-black"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Modal Content Body */}
        <div className="p-6 space-y-5 text-xs">
          {/* Main Visual Banner */}
          <div className="flex items-start gap-4 bg-[#FAF7F2] p-4 border-3 border-black shadow-[4px_4px_0px_0px_#000]">
            <div className="p-3 bg-[#3730A3] text-white border-2 border-black shadow-[2px_2px_0px_0px_#000] flex-shrink-0">
              {currentStep.icon}
            </div>
            <div className="space-y-1">
              <h4 className="font-black text-base text-[#18153B] font-['Space_Grotesk'] uppercase leading-snug">
                {currentStep.headline}
              </h4>
              <p className="text-gray-800 font-medium font-['Plus_Jakarta_Sans'] leading-relaxed text-xs">
                {currentStep.description}
              </p>
            </div>
          </div>

          {/* Key Highlights Bullet List */}
          <div className="space-y-2.5">
            <span className="text-[11px] font-black uppercase text-gray-700 tracking-wider block">
              Core Capabilities in this Section:
            </span>
            <div className="space-y-2 font-mono">
              {currentStep.highlights.map((point, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2.5 bg-white p-2.5 border-2 border-black shadow-[2px_2px_0px_0px_#000]"
                >
                  <div className="p-0.5 bg-[#FACC15] border border-black flex-shrink-0 mt-0.5">
                    <Check className="w-3.5 h-3.5 text-black stroke-[3]" />
                  </div>
                  <span className="text-gray-900 font-bold leading-relaxed">{point}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Pro-Tip Box */}
          <div className="bg-amber-50 border-2 border-amber-900 p-3 flex items-center gap-2.5 shadow-[2px_2px_0px_0px_#000]">
            <Lightbulb className="w-5 h-5 text-amber-700 flex-shrink-0" />
            <span className="text-amber-950 font-bold text-xs font-mono">
              {currentStep.proTip}
            </span>
          </div>

          {/* Step Indicators (Dots) */}
          <div className="flex items-center justify-center gap-2 pt-1">
            {steps.map((_, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setCurrentStepIndex(idx);
                  if (steps[idx].tabKey) onSelectTab(steps[idx].tabKey!);
                }}
                className={`w-3 h-3 border-2 border-black transition-all cursor-pointer ${
                  idx === currentStepIndex
                    ? 'bg-[#FACC15] scale-125 shadow-[1px_1px_0px_0px_#000]'
                    : idx < currentStepIndex
                    ? 'bg-[#3730A3]'
                    : 'bg-white'
                }`}
                title={`Jump to step ${idx + 1}`}
              />
            ))}
          </div>
        </div>

        {/* Footer Controls */}
        <div className="p-4 bg-[#FAF7F2] border-t-3 border-black flex flex-wrap items-center justify-between gap-3 font-mono">
          <label className="flex items-center gap-2 cursor-pointer select-none text-xs font-bold text-gray-700">
            <input
              type="checkbox"
              checked={dontShowAgain}
              onChange={(e) => setDontShowAgain(e.target.checked)}
              className="w-4 h-4 accent-[#3730A3] border-2 border-black cursor-pointer"
            />
            <span>Don't show automatically on next login</span>
          </label>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSkip}
              className="bg-white hover:bg-gray-100 text-black px-3 py-2 border-2 border-black font-black uppercase text-xs shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
            >
              SKIP TOUR
            </button>

            {!isFirstStep && (
              <button
                onClick={handlePrev}
                className="flex items-center gap-1.5 bg-white hover:bg-gray-100 text-black px-3 py-2 border-2 border-black font-black uppercase text-xs shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>PREV</span>
              </button>
            )}

            <button
              onClick={handleNext}
              className={`flex items-center gap-2 px-5 py-2 border-2 border-black font-black uppercase text-xs shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer ${
                isLastStep
                  ? 'bg-emerald-400 hover:bg-emerald-300 text-black'
                  : 'bg-[#FACC15] hover:bg-yellow-400 text-black'
              }`}
            >
              <span>{isLastStep ? 'START PLANNING 🚀' : 'NEXT STEP'}</span>
              {!isLastStep && <ArrowRight className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
