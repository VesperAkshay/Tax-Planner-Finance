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
import { DeductionCatalogView } from './components/DeductionCatalogView';
import { LifecycleModal } from './components/LifecycleModal';
import { BYOKModal } from './components/BYOKModal';
import { OnboardingTourModal } from './components/OnboardingTourModal';
import { TaxpayerProfileModal } from './components/TaxpayerProfileModal';
import { HouseholdSummaryModal } from './components/HouseholdSummaryModal';
import { CommandPaletteModal } from './components/CommandPaletteModal';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AnimatedFeatureRibbon } from './components/AnimatedFeatureRibbon';
import { api } from './api/client';
import type { User, TaxpayerProfile, ProfileReadinessResponse } from './types';
import { Users } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('upload');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [lifecycleModalOpen, setLifecycleModalOpen] = useState(false);
  const [byokModalOpen, setByokModalOpen] = useState(false);
  const [tourModalOpen, setTourModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [flagCount, setFlagCount] = useState<number>(0);
  const [initializing, setInitializing] = useState(true);

  // Multi-Taxpayer Profiles & Command Hub State
  const [profiles, setProfiles] = useState<TaxpayerProfile[]>([]);
  const [activeProfile, setActiveProfile] = useState<TaxpayerProfile | null>(null);
  const [readiness, setReadiness] = useState<ProfileReadinessResponse | null>(null);
  const [addProfileModalOpen, setAddProfileModalOpen] = useState(false);
  const [editProfileModalData, setEditProfileModalData] = useState<TaxpayerProfile | null>(null);
  const [householdModalOpen, setHouseholdModalOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  // Keyboard shortcut: Ctrl + K (or Cmd + K) opens Global Command Palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const loadProfiles = async () => {
    try {
      const data = await api.getProfiles();
      setProfiles(data);
      const savedId = api.getActiveProfileId();
      const current = data.find((p) => p.id === savedId) || data.find((p) => p.is_default) || data[0] || null;
      setActiveProfile(current);
      if (current) {
        api.setActiveProfileId(current.id);
      }
    } catch {
      setProfiles([]);
      setActiveProfile(null);
    }
  };

  const loadReadiness = async () => {
    try {
      const data = await api.getProfileReadiness();
      setReadiness(data);
    } catch {
      setReadiness(null);
    }
  };

  const handleSwitchProfile = async (profileId: number) => {
    api.setActiveProfileId(profileId);
    const target = profiles.find((p) => p.id === profileId) || null;
    setActiveProfile(target);
    await Promise.all([loadFlags(), loadReadiness()]);
  };

  const handleSaveProfile = async (profileData: Partial<TaxpayerProfile>) => {
    if (editProfileModalData) {
      await api.updateProfile(editProfileModalData.id, profileData);
    } else {
      const newProfile = await api.createProfile(profileData);
      api.setActiveProfileId(newProfile.id);
    }
    await loadProfiles();
    await loadReadiness();
    await loadFlags();
  };

  const checkAuth = async () => {
    setInitializing(true);
    try {
      const user = await api.getCurrentUser();
      setCurrentUser(user);
      if (user) {
        await Promise.all([loadFlags(), loadProfiles(), loadReadiness()]);
        if (!localStorage.getItem('taxplanner_onboarding_tour_seen')) {
          setTourModalOpen(true);
        }
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
    api.setActiveProfileId(null);
    setCurrentUser(null);
    setActiveProfile(null);
    setProfiles([]);
    setReadiness(null);
    setActiveTab('upload');
  };

  const handleOpenAuth = (mode: 'login' | 'register') => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  const handleAuthSuccess = async (user: User) => {
    setCurrentUser(user);
    await Promise.all([loadFlags(), loadProfiles(), loadReadiness()]);
    setActiveTab('upload');
    if (!localStorage.getItem('taxplanner_onboarding_tour_seen')) {
      setTourModalOpen(true);
    }
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
        onOpenLifecycleModal={() => setLifecycleModalOpen(true)}
        onOpenBYOKModal={() => setByokModalOpen(true)}
        onOpenTour={() => setTourModalOpen(true)}
        profiles={profiles}
        activeProfile={activeProfile}
        readiness={readiness}
        onSelectProfile={handleSwitchProfile}
        onOpenAddProfile={() => setAddProfileModalOpen(true)}
        onOpenEditProfile={(p) => setEditProfileModalData(p)}
        onOpenHousehold={() => setHouseholdModalOpen(true)}
        onOpenCommandPalette={() => setCommandPaletteOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-3 sm:px-4 md:px-6 py-4 sm:py-6 md:py-8 space-y-6 sm:space-y-8 md:space-y-12">
        {/* If user is NOT logged in: Show Gen Alpha packaging Landing Page */}
        {!currentUser ? (
          <LandingView onOpenAuth={handleOpenAuth} />
        ) : (
          /* If user IS logged in: Show real Dashboard with 6 Views */
          <div className="space-y-6 sm:space-y-8">
            {/* User Vault Header Strip */}
            <div className="bg-[#FAF7F2] border-3 border-black p-3 sm:p-4 shadow-[4px_4px_0px_0px_#000] flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 font-mono text-xs">
              <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse flex-shrink-0" />
                <span className="font-bold">
                  ACTIVE: <span className="text-[#3730A3] font-black">{activeProfile?.name || currentUser.full_name || currentUser.email}</span>
                </span>
                <span className="bg-[#3730A3] text-white border border-black px-1.5 py-0.5 font-bold uppercase text-[10px]">
                  {activeProfile?.persona?.toUpperCase() || 'SALARIED'}
                </span>
                {(activeProfile?.pan || currentUser.pan) && (
                  <span className="bg-gray-200 border border-black px-1.5 py-0.5 font-bold text-[10px] sm:text-xs">
                    PAN: {activeProfile?.pan || currentUser.pan}
                  </span>
                )}
                {readiness && (
                  <span className="bg-emerald-100 text-emerald-950 border border-black px-1.5 py-0.5 font-black text-[10px]">
                    READINESS: {readiness.overall_score}%
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-2.5 w-full sm:w-auto">
                <button
                  onClick={() => setHouseholdModalOpen(true)}
                  className="bg-[#FACC15] hover:bg-yellow-400 text-black px-3 py-1.5 sm:py-1 border-2 border-black font-black uppercase text-[10px] shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 flex items-center justify-center gap-1.5 cursor-pointer w-full sm:w-auto"
                  title="Open Joint Family Tax Optimizer & Arbitrage"
                >
                  <Users className="w-3.5 h-3.5" />
                  <span>HOUSEHOLD TAX HUB</span>
                </button>
                <div className="text-gray-600 font-bold hidden md:block">
                  SECURE VAULT
                </div>
              </div>
            </div>

            {/* Dynamic View Switched by Tabs with ErrorBoundary protection */}
            <ErrorBoundary key={activeTab}>
              {activeTab === 'upload' && (
                <UploadView
                  onUploadSuccess={() => {
                    loadFlags();
                  }}
                  onNavigateTab={(tab) => setActiveTab(tab as any)}
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

              {activeTab === 'catalog' && (
                <DeductionCatalogView
                  onCatalogUpdated={() => {
                    loadFlags();
                  }}
                  onNavigateToReport={() => setActiveTab('report')}
                />
              )}

              {activeTab === 'chat' && (
                <AgentChatView
                  onDeductionsUpdated={() => {
                    loadFlags();
                  }}
                  onNavigateToCatalog={() => setActiveTab('catalog')}
                />
              )}

              {activeTab === 'report' && (
                <TaxReportView
                  onNavigateToCatalog={() => setActiveTab('catalog')}
                />
              )}
            </ErrorBoundary>

            {/* Smooth Hardware-Accelerated Feature & Guarantees Ribbon (Render Style) */}
            <AnimatedFeatureRibbon />
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

      {/* Data Lifecycle & Privacy Vault Modal (Phase 15) */}
      <LifecycleModal
        isOpen={lifecycleModalOpen}
        onClose={() => setLifecycleModalOpen(false)}
        onAccountDeleted={handleLogout}
        onDataReset={() => {
          loadFlags();
          setActiveTab('upload');
        }}
      />

      {/* BYOK AI Settings Modal (v1.2) */}
      <BYOKModal
        isOpen={byokModalOpen}
        onClose={() => setByokModalOpen(false)}
      />

      {/* Interactive Onboarding Tour Modal */}
      <OnboardingTourModal
        isOpen={tourModalOpen}
        onClose={() => setTourModalOpen(false)}
        onSelectTab={setActiveTab}
      />

      {/* Add / Edit Taxpayer Profile Modal */}
      <TaxpayerProfileModal
        isOpen={addProfileModalOpen || !!editProfileModalData}
        onClose={() => {
          setAddProfileModalOpen(false);
          setEditProfileModalData(null);
        }}
        onSave={handleSaveProfile}
        editingProfile={editProfileModalData}
      />

      {/* Joint Household Tax Optimizer Modal */}
      <HouseholdSummaryModal
        isOpen={householdModalOpen}
        onClose={() => setHouseholdModalOpen(false)}
        onSelectProfile={handleSwitchProfile}
      />

      {/* Global Command Palette (Ctrl+K) */}
      <CommandPaletteModal
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onSelectTab={setActiveTab}
        profiles={profiles}
        activeProfile={activeProfile}
        onSelectProfile={handleSwitchProfile}
        onOpenAddProfile={() => setAddProfileModalOpen(true)}
        onOpenHousehold={() => setHouseholdModalOpen(true)}
        onOpenBYOK={() => setByokModalOpen(true)}
        onOpenLifecycle={() => setLifecycleModalOpen(true)}
        onOpenTour={() => setTourModalOpen(true)}
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
