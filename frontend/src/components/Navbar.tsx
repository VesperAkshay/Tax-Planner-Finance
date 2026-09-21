import React from 'react';
import {
  UploadCloud,
  PieChart,
  GitCompare,
  MessageSquareCode,
  FileCheck2,
  LogIn,
  UserPlus,
  BookOpen,
  Database,
  Key,
  Sparkles,
  Search,
} from 'lucide-react';
import type { User, TaxpayerProfile, ProfileReadinessResponse } from '../types';
import { ProfileCommandHub } from './ProfileCommandHub';

export type TabKey = 'upload' | 'snapshot' | 'reconciliation' | 'catalog' | 'chat' | 'report';

interface NavbarProps {
  activeTab: TabKey;
  onSelectTab: (tab: TabKey) => void;
  currentUser: User | null;
  onLogout: () => void;
  onOpenAuth: (mode: 'login' | 'register') => void;
  flagCount: number;
  onOpenLifecycleModal?: () => void;
  onOpenBYOKModal?: () => void;
  onOpenTour?: () => void;
  profiles?: TaxpayerProfile[];
  activeProfile?: TaxpayerProfile | null;
  readiness?: ProfileReadinessResponse | null;
  onSelectProfile?: (profileId: number) => void;
  onOpenAddProfile?: () => void;
  onOpenEditProfile?: (profile: TaxpayerProfile) => void;
  onOpenHousehold?: () => void;
  onOpenCommandPalette?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onSelectTab,
  currentUser,
  onLogout,
  onOpenAuth,
  flagCount,
  onOpenLifecycleModal,
  onOpenBYOKModal,
  onOpenTour,
  profiles,
  activeProfile,
  readiness,
  onSelectProfile,
  onOpenAddProfile,
  onOpenEditProfile,
  onOpenHousehold,
  onOpenCommandPalette,
}) => {
  const navItems: {
    key: TabKey;
    shortLabel: string;
    fullLabel: string;
    icon: React.ReactNode;
    badge?: number;
  }[] = [
    {
      key: 'upload',
      shortLabel: '1. Ingest',
      fullLabel: '1. Ingest Docs',
      icon: <UploadCloud className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
    },
    {
      key: 'snapshot',
      shortLabel: '2. Snapshot',
      fullLabel: '2. Snapshot',
      icon: <PieChart className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
    },
    {
      key: 'reconciliation',
      shortLabel: '3. Reconcile',
      fullLabel: '3. Reconciliation',
      icon: <GitCompare className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
      badge: flagCount > 0 ? flagCount : undefined,
    },
    {
      key: 'catalog',
      shortLabel: '4. Deductions',
      fullLabel: '4. Deductions',
      icon: <BookOpen className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
    },
    {
      key: 'chat',
      shortLabel: '5. AI Planner',
      fullLabel: '5. Mr. Planner (AI)',
      icon: <MessageSquareCode className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
    },
    {
      key: 'report',
      shortLabel: '6. Report',
      fullLabel: '6. Tax Report',
      icon: <FileCheck2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
    },
  ];

  return (
    <header className="sticky top-0 z-40 bg-[#FAF7F2] border-b-4 border-black">
      {/* Option 2: Integrated Single-Bar Header */}
      <div className="max-w-[1700px] mx-auto px-3 sm:px-4 py-2 flex items-center justify-between gap-2 lg:gap-4">
        {/* Left Section: Brand Logo & FY Badge */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="bg-[#3730A3] text-white px-2 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] rotate-[-1deg] select-none">
            <span className="font-black text-base md:text-lg tracking-tight font-['Space_Grotesk']">TP//26</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-sm md:text-base font-black tracking-tight text-black font-['Space_Grotesk'] whitespace-nowrap hidden sm:inline-block">
              TAX PLANNER
            </span>
            <span className="bg-[#F59E0B] text-black text-[10px] font-black px-1.5 py-0.5 border border-black shadow-[1px_1px_0px_0px_#000] whitespace-nowrap">
              FY 25–26
            </span>
          </div>
        </div>

        {/* Center Section: 6 Streamlined Workflow Tabs (Integrated into Single Bar) */}
        {currentUser && (
          <nav
            data-tour="nav-tabs"
            className="flex items-center gap-1 sm:gap-1.5 overflow-x-auto no-scrollbar py-0.5 mx-1 flex-shrink min-w-0"
          >
            {navItems.map((item) => {
              const isActive = activeTab === item.key;
              return (
                <button
                  key={item.key}
                  onClick={() => onSelectTab(item.key)}
                  className={`flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-1 sm:py-1.5 text-xs font-black tracking-tight border-2 border-black transition-all flex-shrink-0 cursor-pointer ${
                    isActive
                      ? 'bg-[#FACC15] text-black shadow-[2px_2px_0px_0px_#000] -translate-y-0.5'
                      : 'bg-[#FFFDF9] text-black hover:bg-[#FACC15]/20 hover:shadow-[1px_1px_0px_0px_#000]'
                  }`}
                  title={item.fullLabel}
                >
                  {item.icon}
                  <span className="hidden xl:inline">{item.fullLabel}</span>
                  <span className="xl:hidden">{item.shortLabel}</span>
                  {item.badge !== undefined && (
                    <span className="bg-red-500 text-white font-mono text-[9px] px-1 py-0.2 rounded-full border border-black animate-pulse">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        )}

        {/* Right Section: Compact Power Cluster (Idea B) & Profile Hub */}
        <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
          {currentUser ? (
            <>
              {/* Idea B: Compact Icon Pills */}
              <div data-tour="vault-actions" className="flex items-center gap-1 sm:gap-1.5">
                {/* Search / Command Palette Pill */}
                {onOpenCommandPalette && (
                  <button
                    onClick={onOpenCommandPalette}
                    className="flex items-center gap-1 bg-[#FFFDF9] hover:bg-white text-black px-2 sm:px-2.5 py-1 sm:py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs font-mono cursor-pointer transition-colors"
                    title="Search & Command Palette (Ctrl+K)"
                  >
                    <Search className="w-3.5 h-3.5 text-gray-700" />
                    <span className="hidden md:inline text-[11px]">Ctrl+K</span>
                  </button>
                )}

                {/* Tour Button */}
                {onOpenTour && (
                  <button
                    onClick={onOpenTour}
                    className="flex items-center gap-1 bg-[#A7F3D0] hover:bg-[#6EE7B7] text-black px-2 sm:px-2.5 py-1 sm:py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs font-mono uppercase cursor-pointer transition-colors"
                    title="Take the Interactive Platform Tour"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-emerald-800" />
                    <span className="hidden lg:inline text-[11px]">TOUR</span>
                  </button>
                )}

                {/* AI Keys Pill (Idea B) */}
                {onOpenBYOKModal && (
                  <button
                    onClick={onOpenBYOKModal}
                    className="flex items-center gap-1 bg-[#FFFDF9] hover:bg-[#FACC15] text-black px-2 sm:px-2.5 py-1 sm:py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs font-mono uppercase cursor-pointer transition-colors"
                    title="Configure personal AI keys (OpenRouter, OpenAI, Groq, Gemini)"
                  >
                    <Key className="w-3.5 h-3.5 text-[#3730A3]" />
                    <span className="hidden xl:inline text-[11px]">KEYS</span>
                  </button>
                )}

                {/* Vault Data Pill (Idea B) */}
                {onOpenLifecycleModal && (
                  <button
                    onClick={onOpenLifecycleModal}
                    className="flex items-center gap-1 bg-[#FFFDF9] hover:bg-[#FACC15] text-black px-2 sm:px-2.5 py-1 sm:py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs font-mono uppercase cursor-pointer transition-colors"
                    title="Data Export, Reset & Right-to-Erasure"
                  >
                    <Database className="w-3.5 h-3.5 text-amber-600" />
                    <span className="hidden xl:inline text-[11px]">VAULT</span>
                  </button>
                )}
              </div>

              {/* Interactive Taxpayer Profile Command Hub */}
              <ProfileCommandHub
                currentUser={currentUser}
                profiles={profiles || []}
                activeProfile={activeProfile || null}
                readiness={readiness || null}
                onSelectProfile={onSelectProfile || (() => {})}
                onOpenAddProfile={onOpenAddProfile || (() => {})}
                onOpenEditProfile={onOpenEditProfile || (() => {})}
                onOpenHousehold={onOpenHousehold || (() => {})}
                onOpenCommandPalette={onOpenCommandPalette || (() => {})}
                onOpenLifecycleModal={onOpenLifecycleModal}
                onOpenBYOKModal={onOpenBYOKModal}
                onLogout={onLogout}
              />
            </>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => onOpenAuth('login')}
                className="flex items-center gap-1.5 bg-[#FAF7F2] hover:bg-white text-black px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs uppercase cursor-pointer"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>SIGN IN</span>
              </button>

              <button
                onClick={() => onOpenAuth('register')}
                className="flex items-center gap-1.5 bg-[#FACC15] hover:bg-yellow-400 text-black px-3.5 py-1.5 border-2 border-black shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs uppercase cursor-pointer"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>REGISTER</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
