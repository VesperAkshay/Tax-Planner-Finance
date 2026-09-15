import React, { useState } from 'react';
import { Star, Quote, ChevronLeft, ChevronRight } from 'lucide-react';

interface Testimonial {
  name: string;
  role: string;
  company: string;
  quote: string;
  savedAmount: string;
  tag: string;
}

const TESTIMONIALS: Testimonial[] = [
  {
    name: 'Pooja Venkatesh',
    role: 'Staff Software Engineer',
    company: 'Fintech Corp, Bengaluru',
    quote:
      'The deterministic calculation is a game changer. Unlike generic AI bots that hallucinate tax numbers, TaxPlanner matched my hand calculations to the exact rupee and saved me ₹46,800 under the New Regime.',
    savedAmount: '₹46,800',
    tag: 'NEW REGIME BENEFICIARY',
  },
  {
    name: 'Arunav Sengupta',
    role: 'Senior Product Lead',
    company: 'HealthTech, Gurugram',
    quote:
      'The salary slip and bank statement reconciliation flagged a ₹4,500 reimbursement mismatch that my HR had split across months. Fixed it in one click!',
    savedAmount: '₹31,200',
    tag: 'RECONCILIATION CHAMPION',
  },
  {
    name: 'Meera Nambiar',
    role: 'VP Marketing',
    company: 'SaaS Platform, Mumbai',
    quote:
      'The Old vs New Regime side-by-side breakdown with Section 80C, 80D, and 80CCD(1B) NPS citations made my declaration effortless before the March 31 deadline.',
    savedAmount: '₹58,400',
    tag: 'OLD REGIME OPTIMIZER',
  },
];

export const TestimonialCard: React.FC = () => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const prev = () => {
    setCurrentIndex((i) => (i === 0 ? TESTIMONIALS.length - 1 : i - 1));
  };

  const next = () => {
    setCurrentIndex((i) => (i === TESTIMONIALS.length - 1 ? 0 : i + 1));
  };

  const t = TESTIMONIALS[currentIndex];

  return (
    <div className="bg-[#18153B] text-white border-4 border-black shadow-[6px_6px_0px_0px_#000000] p-6 md:p-8 relative overflow-hidden">
      {/* Neo-brutalist decorative header sticker */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b-2 border-white/20 pb-4 mb-6">
        <div className="flex items-center gap-2">
          <Quote className="w-8 h-8 text-[#F59E0B]" />
          <span className="font-extrabold text-sm tracking-wider uppercase bg-[#F59E0B] text-black px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
            TAXPAYER TESTIMONIAL
          </span>
        </div>
        <div className="flex items-center gap-1 bg-[#FACC15] text-black font-black text-xs px-3 py-1 border-2 border-black">
          {[...Array(5)].map((_, i) => (
            <Star key={i} className="w-3.5 h-3.5 fill-black" />
          ))}
          <span className="ml-1.5 font-bold">5.0 / 5.0 VERIFIED</span>
        </div>
      </div>

      <p className="text-lg md:text-xl font-medium leading-relaxed mb-6 font-['Space_Grotesk'] text-[#FFFDF9]">
        &ldquo;{t.quote}&rdquo;
      </p>

      <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t-2 border-white/15">
        <div>
          <h4 className="text-lg font-black text-[#FACC15] uppercase tracking-wide">{t.name}</h4>
          <p className="text-xs text-white/80 font-mono">
            {t.role} • <span className="text-[#F59E0B]">{t.company}</span>
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="bg-[#FAF7F2] text-black px-3 py-1.5 border-2 border-black shadow-[3px_3px_0px_0px_#000] font-black text-xs">
            SAVED <span className="text-[#3730A3] font-mono text-sm">{t.savedAmount}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={prev}
              aria-label="Previous testimonial"
              className="bg-[#F59E0B] text-black p-2 border-2 border-black shadow-[2px_2px_0px_0px_#000] hover:bg-[#FBBF24] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all"
            >
              <ChevronLeft className="w-4 h-4 stroke-[3]" />
            </button>
            <button
              onClick={next}
              aria-label="Next testimonial"
              className="bg-[#FACC15] text-black p-2 border-2 border-black shadow-[2px_2px_0px_0px_#000] hover:bg-[#FFE600] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all"
            >
              <ChevronRight className="w-4 h-4 stroke-[3]" />
            </button>
          </div>
        </div>
      </div>

      {/* Pagination dots respecting user memory: White dot = active, Blue dot = inactive */}
      <div className="flex items-center justify-center gap-3 mt-6 pt-2">
        {TESTIMONIALS.map((_, idx) => {
          const isActive = idx === currentIndex;
          return (
            <button
              key={idx}
              onClick={() => setCurrentIndex(idx)}
              aria-label={`Go to testimonial ${idx + 1}`}
              className={`w-3.5 h-3.5 rounded-full border-2 border-black transition-all ${
                isActive
                  ? 'bg-white scale-125 shadow-[1px_1px_0px_0px_#000]'
                  : 'bg-blue-600 hover:bg-blue-500'
              }`}
            />
          );
        })}
      </div>
    </div>
  );
};
