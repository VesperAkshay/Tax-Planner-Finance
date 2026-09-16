import React from 'react';

export const Ticker: React.FC = () => {
  const items = [
    '⚡ 100% EXACT STATUTORY MATH GUARANTEE',
    '★ FY 2025–26 & AY 2026–27 COMPLIANT',
    '🏛️ REVISED SECTION 115BAC NEW REGIME SLABS',
    '💰 ₹12,00,000 ZERO TAX REBATE & MARGINAL RELIEF',
    '🔒 PRIVATE ENCRYPTED USER VAULT',
    '📊 AUTOMATIC BALANCE CONTINUITY TO ₹1.00',
    '🎯 INTELLIGENT SPENDING CATEGORIZATION',
  ];

  return (
    <div className="bg-[#FACC15] border-b-4 border-black overflow-hidden select-none py-2 font-black text-xs md:text-sm tracking-widest text-black">
      <div className="animate-marquee whitespace-nowrap flex items-center gap-8">
        {items.concat(items).map((item, index) => (
          <span key={index} className="inline-flex items-center gap-2">
            <span className="text-black font-extrabold">{item}</span>
            <span className="text-black font-bold">///</span>
          </span>
        ))}
      </div>
    </div>
  );
};
