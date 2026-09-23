import React from 'react';
import {
  UploadCloud,
  GitCompare,
  PieChart,
  BookOpen,
  Briefcase,
  MessageSquareCode,
  FileCheck2,
  Users,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
} from 'lucide-react';

export type FlowStageId = 1 | 2 | 3;

export interface FlowPipelineNavProps {
  currentStage: FlowStageId;
  activeSubView: string;
  onSelectStage: (stage: FlowStageId) => void;
  onSelectSubView: (view: string) => void;
  flagCount: number;
  hasDocuments: boolean;
  isFilingReady: boolean;
}

export const FlowPipelineNav: React.FC<FlowPipelineNavProps> = ({
  currentStage,
  activeSubView,
  onSelectStage,
  onSelectSubView,
  flagCount,
  hasDocuments,
  isFilingReady,
}) => {
  // Define the sub-views for each stage
  const stageSubViews: Record<
    FlowStageId,
    Array<{
      id: string;
      label: string;
      icon: React.ReactNode;
      badge?: number;
      badgeType?: 'danger' | 'success';
    }>
  > = {
    1: [
      {
        id: 'upload',
        label: '1. Ingest Vault',
        icon: <UploadCloud className="w-3.5 h-3.5" />,
      },
      {
        id: 'reconciliation',
        label: '2. Salary Reconciliation',
        icon: <GitCompare className="w-3.5 h-3.5" />,
        badge: flagCount > 0 ? flagCount : undefined,
        badgeType: 'danger',
      },
      {
        id: 'snapshot',
        label: '3. Spending Snapshot',
        icon: <PieChart className="w-3.5 h-3.5" />,
      },
    ],
    2: [
      {
        id: 'catalog',
        label: '4. Chapter VI-A Deductions',
        icon: <BookOpen className="w-3.5 h-3.5" />,
      },
      {
        id: 'career',
        label: '5. Career Switch & Form 12B',
        icon: <Briefcase className="w-3.5 h-3.5" />,
      },
      {
        id: 'chat',
        label: '6. Mr. Planner AI Strategist',
        icon: <MessageSquareCode className="w-3.5 h-3.5" />,
      },
    ],
    3: [
      {
        id: 'report',
        label: '7. Dual-Regime Tax Report',
        icon: <FileCheck2 className="w-3.5 h-3.5" />,
      },
      {
        id: 'household',
        label: '8. Joint Family Hub',
        icon: <Users className="w-3.5 h-3.5" />,
      },
    ],
  };

  const stages = [
    {
      id: 1 as FlowStageId,
      stepNumber: '01',
      title: 'Inflow & Audit',
      description: 'Ingest & reconcile cashflows',
      isComplete: hasDocuments && flagCount === 0,
      hasAlert: flagCount > 0,
    },
    {
      id: 2 as FlowStageId,
      stepNumber: '02',
      title: 'Strategy & Optimize',
      description: 'Deductions, switches & traps',
      isComplete: isFilingReady,
      hasAlert: false,
    },
    {
      id: 3 as FlowStageId,
      stepNumber: '03',
      title: 'Compliance & Filing',
      description: 'Dual-regime audit & CA PDF',
      isComplete: isFilingReady,
      hasAlert: false,
    },
  ];

  return (
    <div className="space-y-3 font-['Space_Grotesk'] select-none">
      {/* ========================================================================= */}
      {/* 1. THREE-STAGE PROGRESSIVE STEPPER                                        */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2 sm:gap-3">
        {stages.map((stage) => {
          const isActive = currentStage === stage.id;
          return (
            <button
              key={stage.id}
              onClick={() => {
                onSelectStage(stage.id);
                // Auto-switch to the first sub-view of the chosen stage if not already in it
                const firstSub = stageSubViews[stage.id][0].id;
                const isCurrentInStage = stageSubViews[stage.id].some((sv) => sv.id === activeSubView);
                if (!isCurrentInStage) {
                  onSelectSubView(firstSub);
                }
              }}
              className={`border-3 border-black p-3 sm:p-4 text-left transition-all cursor-pointer relative ${
                isActive
                  ? 'bg-[#18153B] text-white shadow-[4px_4px_0px_0px_#000] -translate-y-0.5'
                  : 'bg-white hover:bg-[#FAF7F2] text-black shadow-[2px_2px_0px_0px_#000]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span
                  className={`font-mono text-xs font-black px-2 py-0.5 border border-black ${
                    isActive ? 'bg-[#FACC15] text-black' : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  STAGE {stage.stepNumber}
                </span>

                {stage.hasAlert ? (
                  <span className="flex items-center gap-1 font-mono text-[10px] font-bold bg-rose-500 text-white px-2 py-0.5 border border-black animate-pulse">
                    <AlertTriangle className="w-3 h-3" />
                    AUDIT NEEDED
                  </span>
                ) : stage.isComplete ? (
                  <span className="flex items-center gap-1 font-mono text-[10px] font-bold bg-emerald-400 text-emerald-950 px-2 py-0.5 border border-black">
                    <CheckCircle2 className="w-3 h-3" />
                    VERIFIED
                  </span>
                ) : null}
              </div>

              <div className="mt-2">
                <h3 className="font-black text-base sm:text-lg leading-tight">
                  {stage.title}
                </h3>
                <p
                  className={`font-mono text-[11px] sm:text-xs mt-0.5 ${
                    isActive ? 'text-gray-300' : 'text-gray-600'
                  }`}
                >
                  {stage.description}
                </p>
              </div>

              {isActive && (
                <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-[#18153B] border-r-2 border-b-2 border-black rotate-45 hidden md:block" />
              )}
            </button>
          );
        })}
      </div>

      {/* ========================================================================= */}
      {/* 2. SUB-VIEW PILL DOCK FOR ACTIVE STAGE                                    */}
      {/* ========================================================================= */}
      <div className="bg-[#FAF7F2] border-3 border-black p-2.5 shadow-[4px_4px_0px_0px_#000] flex flex-wrap items-center justify-between gap-2 font-mono text-xs">
        <div className="flex items-center gap-2 overflow-x-auto py-0.5 w-full sm:w-auto">
          <span className="font-black text-gray-500 uppercase text-[11px] shrink-0 mr-1 hidden sm:inline">
            STAGE {currentStage} TOOLS:
          </span>

          {stageSubViews[currentStage].map((subView) => {
            const isSubActive = activeSubView === subView.id;
            return (
              <button
                key={subView.id}
                onClick={() => onSelectSubView(subView.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 font-bold uppercase border-2 border-black text-xs transition-all shrink-0 cursor-pointer ${
                  isSubActive
                    ? 'bg-[#FACC15] text-black shadow-[2px_2px_0px_0px_#000] -translate-y-0.5 font-black'
                    : 'bg-white hover:bg-amber-50 text-gray-800'
                }`}
              >
                {subView.icon}
                <span>{subView.label}</span>
                {subView.badge !== undefined && (
                  <span
                    className={`font-mono text-[10px] px-1.5 py-0.2 rounded-full border border-black font-black ${
                      subView.badgeType === 'danger'
                        ? 'bg-rose-500 text-white animate-pulse'
                        : 'bg-emerald-400 text-emerald-950'
                    }`}
                  >
                    {subView.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Quick Help / Breadcrumb Indicator */}
        <div className="text-[11px] text-gray-600 font-bold hidden lg:flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>Finance Act 2025–26 Compliant</span>
        </div>
      </div>
    </div>
  );
};
