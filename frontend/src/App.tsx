import React, { useState, useEffect } from 'react';
import { Ticker } from './components/Ticker';
import type { TabKey } from './components/Navbar';
import { Navbar } from './components/Navbar';
import { LandingView } from './components/LandingView';
import { AuthModal } from './components/AuthModal';
import { UploadView } from './components/UploadView';
import { SnapshotView } from './components/SnapshotView';
import { ReconciliationView } from './components/ReconciliationView';
import { AgentChatView } from './components/AgentChatView';
import { TaxReportView } from './components/TaxReportView';
import { ErrorBoundary } from './components/ErrorBoundary';
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
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [flagCount, setFlagCount] = useState<number>(0);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    setInitializing(true);
    try {
      const user = await api.getCurrentUser();
      setCurrentUser(user);
      if (user) {
        loadFlags();
      }
    } catch {
      setCurrentUser(null);
    } finally {
      setInitializing(false);
    }
  };

  const loadFlags = async () => {
    try {
      const flags = await api.getReconciliationFlags();
      setFlagCount(flags.filter((f) => f.status === 'pending').length);
    } catch {
      setFlagCount(0);
    }
  };

  const handleLogout = () => {
    api.clearToken();
    setCurrentUser(null);
    setActiveTab('upload');
  };

  const handleOpenAuth = (mode: 'login' | 'register') => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  const handleAuthSuccess = (user: User) => {
    setCurrentUser(user);
    loadFlags();
    setActiveTab('upload');
  };

  if (initializing) {
    return (
      <div className="min-h-screen bg-[#FAF7F2] flex items-center justify-center font-mono">
        <div className="bg-white border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000] text-center">
          <span className="font-black text-sm uppercase tracking-widest animate-pulse">
            LOADING SECURE TAX VAULT...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF7F2] text-[#0F0E17] flex flex-col font-['Plus_Jakarta_Sans'] selection:bg-[#FACC15] selection:text-black">
      {/* Top Ticker Marquee */}
      <Ticker />

      {/* Main Header & Navigation */}
      <Navbar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        currentUser={currentUser}
        onLogout={handleLogout}
        onOpenAuth={handleOpenAuth}
        flagCount={flagCount}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 space-y-12">
        {/* If user is NOT logged in: Show Gen Alpha packaging Landing Page */}
        {!currentUser ? (
          <LandingView onOpenAuth={handleOpenAuth} />
        ) : (
          /* If user IS logged in: Show real Dashboard with 5 Views */
          <div className="space-y-8">
            {/* User Vault Header Strip */}
            <div className="bg-[#FAF7F2] border-3 border-black p-4 shadow-[4px_4px_0px_0px_#000] flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="font-bold">
                  AUTHENTICATED AS: <span className="text-[#3730A3] font-black">{currentUser.email}</span>
                </span>
                {currentUser.pan && (
                  <span className="bg-gray-200 border border-black px-1.5 py-0.5 font-bold">
                    PAN: {currentUser.pan}
                  </span>
                )}
              </div>
              <div className="text-gray-600 font-bold">
                SECURE ENCRYPTED VAULT
              </div>
            </div>

            {/* Dynamic View Switched by Tabs with ErrorBoundary protection */}
            <ErrorBoundary key={activeTab}>
              {activeTab === 'upload' && (
                <UploadView
                  onUploadSuccess={() => {
                    loadFlags();
                  }}
                />
              )}

              {activeTab === 'snapshot' && <SnapshotView onNavigateToTab={setActiveTab} />}

              {activeTab === 'reconciliation' && (
                <ReconciliationView
                  onFlagUpdate={() => {
                    loadFlags();
                  }}
                />
              )}

              {activeTab === 'chat' && <AgentChatView />}

              {activeTab === 'report' && <TaxReportView />}
            </ErrorBoundary>

            {/* Feature Highlights Grid with Brutalist Stickers */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
              <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000000]">
                <div className="p-3 bg-[#FACC15] border-2 border-black inline-block mb-3">
                  <Zap className="w-6 h-6 text-black stroke-[2.5]" />
                </div>
                <h4 className="text-xl font-black uppercase font-['Space_Grotesk'] mb-2">
                  EXACT STATUTORY MATH
                </h4>
                <p className="text-xs font-semibold text-gray-700 leading-relaxed font-['Plus_Jakarta_Sans']">
                  All tax liability figures are computed using pure mathematical logic adhering directly
                  to Finance Act statutory slabs with zero guesswork.
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
                  Revised Section 115BAC slabs, ₹75,000 standard deduction, and ₹12,00,000 rebate
                  with marginal relief.
                </p>
              </div>

              <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000000]">
                <div className="p-3 bg-[#3730A3] border-2 border-black inline-block mb-3">
                  <Lock className="w-6 h-6 text-white stroke-[2.5]" />
                </div>
                <h4 className="text-xl font-black uppercase font-['Space_Grotesk'] mb-2">
                  PRIVATE DATA VAULT
                </h4>
                <p className="text-xs font-semibold text-gray-700 leading-relaxed font-['Plus_Jakarta_Sans']">
                  Bank-grade security and complete data isolation. Your uploads, records, and deductions
                  are strictly accessible only by your account.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Auth Modal for Real Login & Registration */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={handleAuthSuccess}
        initialMode={authMode}
      />

      {/* Neo-Brutalist Packaging Footer */}
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
              Bank-Grade Encryption
            </span>
            <span>•</span>
            <span>Document OCR</span>
            <span>•</span>
            <span>Interactive Tax Advisory</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
