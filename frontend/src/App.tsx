import React, { useState, useEffect } from 'react';
import { Ticker } from './components/Ticker';
import type { TabKey } from './components/Navbar';
import { Navbar } from './components/Navbar';
import { TestimonialCard } from './components/TestimonialCard';
import { UploadView } from './components/UploadView';
import { SnapshotView } from './components/SnapshotView';
import { ReconciliationView } from './components/ReconciliationView';
import { AgentChatView } from './components/AgentChatView';
import { TaxReportView } from './components/TaxReportView';
import { api } from './api/client';
import type { User } from './types';
import {
  Calculator,
  Lock,
  Zap,
} from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('upload');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [flagCount, setFlagCount] = useState<number>(2);

  useEffect(() => {
    initUser();
  }, []);

  const initUser = async () => {
    const user = await api.getCurrentUser();
    setCurrentUser(user);
    try {
      const flags = await api.getReconciliationFlags();
      setFlagCount(flags.filter((f) => f.status === 'pending').length);
    } catch {
      setFlagCount(1);
    }
  };

  const handleSwitchUser = async (email: string) => {
    const res = await api.login(email, 'testpassword123');
    setCurrentUser(res.user);
    const flags = await api.getReconciliationFlags();
    setFlagCount(flags.filter((f) => f.status === 'pending').length);
  };

  return (
    <div className="min-h-screen bg-[#FAF7F2] text-[#0F0E17] flex flex-col font-['Plus_Jakarta_Sans'] selection:bg-[#FACC15] selection:text-black">
      {/* Top Ticker Marquee */}
      <Ticker />

      {/* Main Header & Navigation */}
      <Navbar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        currentUser={currentUser}
        onSwitchUser={handleSwitchUser}
        flagCount={flagCount}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 space-y-12">
        {/* Dynamic View Switched by Tabs */}
        {activeTab === 'upload' && (
          <UploadView
            onUploadSuccess={() => {
              // Automatically guide user to next logical step
            }}
          />
        )}

        {activeTab === 'snapshot' && <SnapshotView />}

        {activeTab === 'reconciliation' && (
          <ReconciliationView
            onFlagUpdate={async () => {
              const flags = await api.getReconciliationFlags();
              setFlagCount(flags.filter((f) => f.status === 'pending').length);
            }}
          />
        )}

        {activeTab === 'chat' && <AgentChatView />}

        {activeTab === 'report' && <TaxReportView />}

        {/* Neo-Brutalist Trust & Testimonial Section */}
        <div className="pt-8">
          <TestimonialCard />
        </div>

        {/* Feature Highlights Grid with Brutalist Stickers */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
          <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000000]">
            <div className="p-3 bg-[#FACC15] border-2 border-black inline-block mb-3">
              <Zap className="w-6 h-6 text-black stroke-[2.5]" />
            </div>
            <h4 className="text-xl font-black uppercase font-['Space_Grotesk'] mb-2">
              ZERO LLM ARITHMETIC
            </h4>
            <p className="text-xs font-semibold text-gray-700 leading-relaxed font-['Plus_Jakarta_Sans']">
              Unlike generic chatbot calculators that hallucinate numbers, all tax figures are computed
              by AST-verified pure Python functions with 100% statement test coverage.
            </p>
          </div>

          <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000000]">
            <div className="p-3 bg-[#F59E0B] border-2 border-black inline-block mb-3">
              <Calculator className="w-6 h-6 text-black stroke-[2.5]" />
            </div>
            <h4 className="text-xl font-black uppercase font-['Space_Grotesk'] mb-2">
              FY 2025–26 COMPLIANT
            </h4>
            <p className="text-xs font-semibold text-gray-700 leading-relaxed font-['Plus_Jakarta_Sans']">
              Complete implementation of revised Section 115BAC slabs, ₹75,000 standard deduction, and
              enhanced ₹12,00,000 rebate with marginal relief.
            </p>
          </div>

          <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000000]">
            <div className="p-3 bg-[#3730A3] border-2 border-black inline-block mb-3">
              <Lock className="w-6 h-6 text-white stroke-[2.5]" />
            </div>
            <h4 className="text-xl font-black uppercase font-['Space_Grotesk'] mb-2">
              MULTI-TENANT ISOLATED
            </h4>
            <p className="text-xs font-semibold text-gray-700 leading-relaxed font-['Plus_Jakarta_Sans']">
              Neon PostgreSQL schema with strict row-level authorization scopes. User B cannot read or
              alter User A's uploads, accounts, or deductions.
            </p>
          </div>
        </div>
      </main>

      {/* Neo-Brutalist Footer */}
      <footer className="bg-[#18153B] text-white border-t-4 border-black py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3">
              <span className="bg-[#FACC15] text-black font-black text-xs px-2 py-0.5 border border-black font-mono">
                TP//2025-26
              </span>
              <h5 className="font-black text-lg font-['Space_Grotesk'] text-[#FACC15]">
                TAX PLANNER &amp; FINANCE ENGINE
              </h5>
            </div>
            <p className="text-xs text-gray-400 font-mono mt-1">
              Personal Finance + Tax Regime Planner for FY 2025–26 / AY 2026–27.
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono text-gray-300">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              FastAPI + Neon DB
            </span>
            <span>•</span>
            <span>Docling Parsers</span>
            <span>•</span>
            <span>LangGraph Agent</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
