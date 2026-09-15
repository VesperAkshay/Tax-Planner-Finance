import React from 'react';
import {
  UploadCloud,
  PieChart,
  GitCompare,
  MessageSquareCode,
  FileCheck2,
  ShieldCheck,
  User as UserIcon,
} from 'lucide-react';
import type { User } from '../types';

export type TabKey = 'upload' | 'snapshot' | 'reconciliation' | 'chat' | 'report';

interface NavbarProps {
  activeTab: TabKey;
  onSelectTab: (tab: TabKey) => void;
  currentUser: User | null;
  onSwitchUser: (email: string) => void;
  flagCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onSelectTab,
  currentUser,
  onSwitchUser,
  flagCount,
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
    { key: 'chat', label: '4. Tax Agent Chat', icon: <MessageSquareCode className="w-4 h-4" /> },
    { key: 'report', label: '5. Final Tax Report', icon: <FileCheck2 className="w-4 h-4" /> },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#FAF7F2] border-b-4 border-black">
      {/* Top Bar */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
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
              Zero LLM Tax Arithmetic • Sec 115BAC Engine
            </p>
          </div>
        </div>

        {/* Right Info & User Switcher */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-1.5 bg-[#FFFDF9] px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] text-xs font-bold">
            <ShieldCheck className="w-4 h-4 text-emerald-600 stroke-[2.5]" />
            <span>NEON DB CONNECTED</span>
          </div>

          <div className="flex items-center bg-[#FFFDF9] border-2 border-black shadow-[3px_3px_0px_0px_#000] px-2 py-1 gap-2 text-xs font-bold">
            <UserIcon className="w-4 h-4 text-[#3730A3]" />
            <select
              value={currentUser?.email || 'alice@taxplanner.test'}
              onChange={(e) => onSwitchUser(e.target.value)}
              className="bg-transparent font-mono font-bold text-xs outline-none cursor-pointer"
            >
              <option value="alice@taxplanner.test">User A (Alice)</option>
              <option value="bob@taxplanner.test">User B (Bob)</option>
              <option value="demo@taxplanner.local">Demo Taxpayer</option>
            </select>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-[#FFFDF9] border-t-2 border-black overflow-x-auto">
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
    </header>
  );
};
