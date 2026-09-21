import React from 'react';
import {
  Zap,
  Calculator,
  Lock,
  GitCompare,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';

interface FeatureCard {
  id: string;
  icon: React.ReactNode;
  iconBg: string;
  badge: string;
  badgeBg: string;
  title: string;
  description: string;
  metric: string;
}

const FEATURE_CARDS: FeatureCard[] = [
  {
    id: 'math',
    icon: <Zap className="w-4 h-4 text-black stroke-[2.5]" />,
    iconBg: 'bg-[#FACC15]',
    badge: 'ZERO GUESSWORK',
    badgeBg: 'bg-yellow-100 text-yellow-950 border-yellow-500',
    title: 'EXACT STATUTORY MATH',
    description:
      'All tax liability figures are computed using pure mathematical logic adhering directly to Finance Act statutory slabs with zero guesswork.',
    metric: '₹0.00 Arithmetic Drift',
  },
  {
    id: 'compliant',
    icon: <Calculator className="w-4 h-4 text-black stroke-[2.5]" />,
    iconBg: 'bg-[#F59E0B]',
    badge: 'FINANCE ACT 2025',
    badgeBg: 'bg-amber-100 text-amber-950 border-amber-500',
    title: 'FY 2025–26 COMPLIANT',
    description:
      'Revised Section 115BAC slabs, ₹75,000 standard deduction, and ₹12,00,000 rebate with statutory marginal relief guarantees.',
    metric: 'AY 2026–27 Certified',
  },
  {
    id: 'vault',
    icon: <Lock className="w-4 h-4 text-white stroke-[2.5]" />,
    iconBg: 'bg-[#3730A3]',
    badge: 'AES-256 ENCRYPTED',
    badgeBg: 'bg-indigo-100 text-indigo-950 border-indigo-500',
    title: 'PRIVATE DATA VAULT',
    description:
      'Bank-grade security and complete data isolation. Your uploads, records, and deductions are strictly accessible only by your account.',
    metric: 'Right-to-Erasure Active',
  },
  {
    id: 'reconcile',
    icon: <GitCompare className="w-4 h-4 text-black stroke-[2.5]" />,
    iconBg: 'bg-[#A7F3D0]',
    badge: 'Δ ≤ ₹1.00 TOLERANCE',
    badgeBg: 'bg-emerald-100 text-emerald-950 border-emerald-500',
    title: 'PAYROLL RECONCILIATION',
    description:
      'Automated payroll audit cross-checks bank deposits against salary slips, highlighting net pay and tax deductions variance instantly.',
    metric: 'Automated Audit Trail',
  },
  {
    id: 'planner',
    icon: <Sparkles className="w-4 h-4 text-black stroke-[2.5]" />,
    iconBg: 'bg-[#FED7AA]',
    badge: 'LEGAL RAG RETRIEVAL',
    badgeBg: 'bg-orange-100 text-orange-950 border-orange-500',
    title: 'MR. PLANNER AI INTEL',
    description:
      'Conversational strategist backed by ChromaDB vector search across IT Act 1961 with 100% Top-1 statutory clause accuracy.',
    metric: 'Deterministic AI Advisory',
  },
  {
    id: 'audit',
    icon: <ShieldCheck className="w-4 h-4 text-black stroke-[2.5]" />,
    iconBg: 'bg-[#E9D5FF]',
    badge: 'OFFICIAL TAX REPORT',
    badgeBg: 'bg-purple-100 text-purple-950 border-purple-500',
    title: 'DUAL-REGIME MEMORANDUM',
    description:
      'Detailed side-by-side audit comparing Old vs New regime with 1-click official vector PDF tax invoice generation.',
    metric: 'Instant PDF Export',
  },
];

export const AnimatedFeatureRibbon: React.FC = () => {
  // Duplicate list to create a seamless, non-stop loop
  const duplicatedCards = [...FEATURE_CARDS, ...FEATURE_CARDS];

  return (
    <div className="w-full pt-6 pb-2 font-mono">
      {/* Section Header Label */}
      <div className="flex items-center justify-between px-1 mb-3">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
          <span className="text-[11px] font-black uppercase tracking-wider text-gray-700">
            PLATFORM GUARANTEES &amp; STATUTORY INTELLIGENCE
          </span>
        </div>
        <span className="text-[10px] text-gray-500 font-bold hidden sm:inline">
          HOVER TO PAUSE • SEAMLESS HARDWARE ACCELERATED
        </span>
      </div>

      {/* Infinite Smooth Ribbon Container with Gradient Edge Masks */}
      <div className="relative w-full overflow-hidden group">
        {/* Left Fade Mask (Render.com / Stripe Style) */}
        <div className="pointer-events-none absolute inset-y-0 left-0 w-8 sm:w-16 bg-gradient-to-r from-[#FAF7F2] to-transparent z-10" />

        {/* Right Fade Mask (Render.com / Stripe Style) */}
        <div className="pointer-events-none absolute inset-y-0 right-0 w-8 sm:w-16 bg-gradient-to-l from-[#FAF7F2] to-transparent z-10" />

        {/* Marquee Track */}
        <div className="animate-ribbon flex items-center gap-4 py-2">
          {duplicatedCards.map((card, index) => (
            <div
              key={`${card.id}-${index}`}
              className="w-72 sm:w-80 flex-shrink-0 bg-[#FFFDF9] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000] hover:shadow-[6px_6px_0px_0px_#000] hover:-translate-y-1 transition-all duration-200 cursor-default flex flex-col justify-between"
            >
              <div>
                {/* Header: Icon + Badge */}
                <div className="flex items-center justify-between mb-2.5">
                  <div className={`p-1.5 ${card.iconBg} border-2 border-black shadow-[1px_1px_0px_0px_#000]`}>
                    {card.icon}
                  </div>
                  <span
                    className={`text-[9px] font-black uppercase px-2 py-0.5 border ${card.badgeBg}`}
                  >
                    {card.badge}
                  </span>
                </div>

                {/* Card Title */}
                <h4 className="text-sm font-black uppercase font-['Space_Grotesk'] text-[#18153B] tracking-tight mb-1.5">
                  {card.title}
                </h4>

                {/* Card Description */}
                <p className="text-[11px] font-medium text-gray-700 leading-snug font-['Plus_Jakarta_Sans']">
                  {card.description}
                </p>
              </div>

              {/* Card Footer Pill */}
              <div className="mt-3 pt-2 border-t border-black/15 flex items-center justify-between text-[10px]">
                <span className="font-bold text-gray-500 uppercase">STATUS:</span>
                <span className="font-black text-emerald-800 bg-emerald-50 border border-emerald-600 px-1.5 py-0.2">
                  ✓ {card.metric}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
