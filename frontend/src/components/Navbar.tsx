import React from 'react';
import {
  UploadCloud,
  PieChart,
  GitCompare,
  MessageSquareCode,
  FileCheck2,
  ShieldCheck,
  User as UserIcon,
  LogOut,
  LogIn,
  UserPlus,
  BookOpen,
  Database,
  Key,
  Sparkles,
} from 'lucide-react';
import type { User } from '../types';

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
}) => {
  const navItems: { key: TabKey; label: string; icon: React.ReactNode; badge?: number }[] = [
    { key: 'upload', label: '1. Ingest Docs', icon: <UploadCloud className="w-4 h-4" /> },
    { key: 'snapshot', label: '2. Financial Snapshot', icon: <PieChart className="w-4 h-4" /> },
    {
      key: 'reconciliation',
      label: '3. Reconciliation',
      icon: <GitCompare className="w-4 h-4" />,
      badge: flagCount > 0 ? flagCount : undefined,
    },
    { key: 'catalog', label: '4. Deduction Catalog', icon: <BookOpen className="w-4 h-4" /> },
    { key: 'chat', label: '5. Mr. Planner (AI)', icon: <MessageSquareCode className="w-4 h-4" /> },
    { key: 'report', label: '6. Final Tax Report', icon: <FileCheck2 className="w-4 h-4" /> },
  ];

  return (
    <header className="sticky top-0 z-40 bg-[#FAF7F2] border-b-4 border-black">
      {/* Top Bar */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Brand Logo & Tag */}
        <div className="flex items-center gap-3">
          <div className="bg-[#3730A3] text-white p-2.5 border-3 border-black shadow-[3px_3px_0px_0px_#000] rotate-[-1deg]">
            <span className="font-black text-xl tracking-tighter font-['Space_Grotesk']">TP//26</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl md:text-2xl font-black tracking-tight text-black font-['Space_Grotesk']">
                TAX PLANNER
              </h1>
              <span className="bg-[#F59E0B] text-black text-[11px] font-black px-2 py-0.5 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
                FY 2025–26
              </span>
            </div>
            <p className="text-xs font-mono text-gray-700 font-semibold hidden sm:block">
              100% Exact Math Guarantee • Private &amp; Encrypted Vault
            </p>
          </div>
        </div>

        {/* Right Section: Auth Actions or User Profile */}
        <div className="flex items-center gap-3">
          {currentUser ? (
            <>
              <div className="hidden md:flex items-center gap-1.5 bg-[#FFFDF9] px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] text-xs font-bold">
                <ShieldCheck className="w-4 h-4 text-emerald-600 stroke-[2.5]" />
                <span>ACTIVE VAULT</span>
              </div>

              {/* Actions container for BYOK, Vault Data and Guide */}
              <div data-tour="vault-actions" className="flex items-center gap-2 flex-wrap">
                {/* Interactive Product Tour Button */}
                {onOpenTour && (
                  <button
                    onClick={onOpenTour}
                    className="flex items-center gap-1.5 bg-[#A7F3D0] hover:bg-[#6EE7B7] text-black px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs font-mono uppercase cursor-pointer transition-colors"
                    title="Take the Interactive Platform Tour"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-emerald-800" />
                    <span className="hidden sm:inline">GUIDE / TOUR</span>
                  </button>
                )}

                {/* Data Lifecycle / Privacy Vault Button */}
                {onOpenLifecycleModal && (
                  <button
                    onClick={onOpenLifecycleModal}
                    className="flex items-center gap-1.5 bg-[#FACC15] hover:bg-yellow-400 text-black px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs font-mono uppercase cursor-pointer"
                    title="Data Export, Reset & Right-to-Erasure"
                  >
                    <Database className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">VAULT DATA</span>
                  </button>
                )}

                {/* BYOK / AI Settings Button */}
                {onOpenBYOKModal && (
                  <button
                    onClick={onOpenBYOKModal}
                    className="flex items-center gap-1.5 bg-[#FFFDF9] hover:bg-[#FACC15] text-black px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs font-mono uppercase cursor-pointer transition-colors"
                    title="Configure personal AI keys (OpenRouter, OpenAI, Groq, Gemini, Claude)"
                  >
                    <Key className="w-3.5 h-3.5 text-[#3730A3]" />
                    <span className="hidden sm:inline">AI KEYS (BYOK)</span>
                  </button>
                )}
              </div>

              {/* Logged in User Badge */}
              <div className="flex items-center bg-[#FFFDF9] border-2 border-black shadow-[3px_3px_0px_0px_#000] px-3 py-1.5 gap-2 text-xs font-bold">
                <UserIcon className="w-4 h-4 text-[#3730A3]" />
                <span className="font-mono text-xs font-bold truncate max-w-[140px] sm:max-w-[200px]">
                  {currentUser.full_name || currentUser.email}
                </span>
              </div>

              {/* Logout Button */}
              <button
                onClick={onLogout}
                className="flex items-center gap-1.5 bg-[#FB7185] hover:bg-rose-400 text-black px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all font-black text-xs font-mono uppercase cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">LOCK VAULT</span>
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => onOpenAuth('login')}
                className="flex items-center gap-1.5 bg-[#FAF7F2] hover:bg-white text-black px-4 py-2 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all font-black text-xs uppercase"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>SIGN IN</span>
              </button>

              <button
                onClick={() => onOpenAuth('register')}
                className="flex items-center gap-1.5 bg-[#FACC15] hover:bg-yellow-400 text-black px-4 py-2 border-2 border-black shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all font-black text-xs uppercase"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>REGISTER</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Navigation Tabs (Only visible when user is logged into dashboard) */}
      {currentUser && (
        <div data-tour="nav-tabs" className="bg-[#FFFDF9] border-t-2 border-black overflow-x-auto">
          <div className="max-w-7xl mx-auto px-4 flex items-center gap-2 py-2 min-w-max">
            {navItems.map((item) => {
              const isActive = activeTab === item.key;
              return (
                <button
                  key={item.key}
                  onClick={() => onSelectTab(item.key)}
                  className={`flex items-center gap-2 px-4 py-2 text-xs md:text-sm font-black tracking-wide border-2 border-black transition-all ${
                    isActive
                      ? 'bg-[#FACC15] text-black shadow-[3px_3px_0px_0px_#000] -translate-y-0.5'
                      : 'bg-[#FAF7F2] text-black hover:bg-[#F59E0B]/20 hover:shadow-[2px_2px_0px_0px_#000]'
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                  {item.badge !== undefined && (
                    <span className="bg-red-500 text-white font-mono text-[10px] px-1.5 py-0.2 rounded-full border border-black animate-pulse">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
};
