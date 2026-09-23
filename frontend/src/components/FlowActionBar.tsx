import React from 'react';
import { ArrowLeft, ArrowRight, CheckCircle2, Download } from 'lucide-react';

interface FlowActionBarProps {
  activeSubView: string;
  onNavigateToSubView: (view: string) => void;
  onDownloadPdf?: () => void;
}

export const FlowActionBar: React.FC<FlowActionBarProps> = ({
  activeSubView,
  onNavigateToSubView,
  onDownloadPdf,
}) => {
  // Ordered linear progression of subviews
  const sequence = [
    { id: 'upload', label: '1. Ingest Documents', stage: 1 },
    { id: 'reconciliation', label: '2. Salary Reconciliation', stage: 1 },
    { id: 'snapshot', label: '3. Spending Snapshot', stage: 1 },
    { id: 'catalog', label: '4. Chapter VI-A Deductions', stage: 2 },
    { id: 'career', label: '5. Career Switch & Form 12B', stage: 2 },
    { id: 'chat', label: '6. Mr. Planner AI Strategist', stage: 2 },
    { id: 'report', label: '7. Dual-Regime Tax Report', stage: 3 },
    { id: 'household', label: '8. Joint Family Hub', stage: 3 },
  ];

  const currentIndex = sequence.findIndex((s) => s.id === activeSubView);
  const currentItem = sequence[currentIndex] || sequence[0];
  const prevItem = currentIndex > 0 ? sequence[currentIndex - 1] : null;
  const nextItem = currentIndex < sequence.length - 1 ? sequence[currentIndex + 1] : null;

  return (
    <div className="bg-[#FAF7F2] border-3 border-black p-3 sm:p-4 shadow-[4px_4px_0px_0px_#000] flex flex-col sm:flex-row items-center justify-between gap-3 font-mono text-xs select-none">
      {/* Previous Step Button */}
      <button
        onClick={() => prevItem && onNavigateToSubView(prevItem.id)}
        disabled={!prevItem}
        className={`w-full sm:w-auto px-4 py-2 border-2 border-black font-bold uppercase flex items-center justify-center gap-2 transition-all ${
          prevItem
            ? 'bg-white hover:bg-gray-100 text-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer'
            : 'bg-gray-200 text-gray-400 border-gray-400 cursor-not-allowed'
        }`}
      >
        <ArrowLeft className="w-4 h-4" />
        <span>{prevItem ? `Back: ${prevItem.label.split('.')[1]}` : 'First Step'}</span>
      </button>

      {/* Middle Progress Summary */}
      <div className="text-center font-bold text-gray-700">
        <span className="text-[#18153B] font-black uppercase">
          STAGE {currentItem.stage}: {currentItem.label}
        </span>
        <span className="text-gray-400 mx-2">|</span>
        <span className="text-gray-500">
          Step {currentIndex + 1} of {sequence.length}
        </span>
      </div>

      {/* Next Step / Action Button */}
      {nextItem ? (
        <button
          onClick={() => onNavigateToSubView(nextItem.id)}
          className="w-full sm:w-auto bg-[#FACC15] hover:bg-yellow-400 text-black px-5 py-2 border-2 border-black font-black uppercase flex items-center justify-center gap-2 shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer transition-all"
        >
          <span>Continue: {nextItem.label.split('.')[1]}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      ) : onDownloadPdf ? (
        <button
          onClick={onDownloadPdf}
          className="w-full sm:w-auto bg-emerald-400 hover:bg-emerald-300 text-black px-5 py-2 border-2 border-black font-black uppercase flex items-center justify-center gap-2 shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer transition-all"
        >
          <Download className="w-4 h-4" />
          <span>Download CA Memorandum PDF</span>
        </button>
      ) : (
        <div className="flex items-center gap-1.5 text-emerald-700 font-bold">
          <CheckCircle2 className="w-4 h-4" />
          <span>All Stages Complete</span>
        </div>
      )}
    </div>
  );
};
