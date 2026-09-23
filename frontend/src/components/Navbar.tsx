import React, { useState } from 'react';
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
  Menu,
  X,
  Users,
  LogOut,
  Briefcase,
} from 'lucide-react';
import type { User, TaxpayerProfile, ProfileReadinessResponse } from '../types';
import { ProfileCommandHub } from './ProfileCommandHub';

export type TabKey = 'upload' | 'snapshot' | 'reconciliation' | 'catalog' | 'career' | 'chat' | 'report';

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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems: {
    key: TabKey;
    stepNumber: number;
    microLabel: string;
    shortLabel: string;
    fullLabel: string;
    icon: React.ReactNode;
    badge?: number;
  }[] = [
    {
      key: 'upload',
      stepNumber: 1,
      microLabel: 'Ingest',
      shortLabel: '1. Ingest',
      fullLabel: '1. Ingest Docs',
      icon: <UploadCloud className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
    },
    {
      key: 'snapshot',
      stepNumber: 2,
      microLabel: 'Snapshot',
      shortLabel: '2. Snapshot',
      fullLabel: '2. Snapshot',
      icon: <PieChart className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
    },
    {
      key: 'reconciliation',
      stepNumber: 3,
      microLabel: 'Audit',
      shortLabel: '3. Reconcile',
      fullLabel: '3. Reconciliation',
      icon: <GitCompare className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
      badge: flagCount > 0 ? flagCount : undefined,
    },
    {
      key: 'catalog',
      stepNumber: 4,
      microLabel: 'Deduct',
      shortLabel: '4. Deductions',
      fullLabel: '4. Deductions',
      icon: <BookOpen className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
    },
    {
      key: 'career',
      stepNumber: 5,
      microLabel: 'Career',
      shortLabel: '5. Career Switch',
      fullLabel: '5. Career Switch',
      icon: <Briefcase className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
    },
    {
      key: 'chat',
      stepNumber: 6,
      microLabel: 'Planner',
      shortLabel: '6. AI Planner',
      fullLabel: '6. Mr. Planner (AI)',
      icon: <MessageSquareCode className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
    },
    {
      key: 'report',
      stepNumber: 7,
      microLabel: 'Report',
      shortLabel: '7. Report',
      fullLabel: '7. Tax Report',
      icon: <FileCheck2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />,
    },
  ];

  const handleTabClick = (key: TabKey) => {
    onSelectTab(key);
    setMobileMenuOpen(false);
  };

  const displayName =
    activeProfile?.name ||
    currentUser?.full_name ||
    currentUser?.email.split('@')[0] ||
    'Taxpayer';

  return (
    <header className="sticky top-0 z-40 bg-[#FAF7F2] border-b-4 border-black font-['Plus_Jakarta_Sans'] select-none">
      {/* ========================================================================= */}
      {/* 1. TOP BAR: BRAND + DESKTOP TABS + ACTIONS OR MOBILE CONTROLS             */}
      {/* ========================================================================= */}
      <div className="max-w-[1700px] mx-auto px-3 sm:px-4 py-2 sm:py-2.5 flex items-center justify-between gap-2 lg:gap-4">
        {/* Left Section: Brand Logo & FY Badge */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="bg-[#3730A3] text-white px-2 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] rotate-[-1deg] select-none">
            <span className="font-black text-base md:text-lg tracking-tight font-['Space_Grotesk']">TP//26</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-sm md:text-base font-black tracking-tight text-black font-['Space_Grotesk'] whitespace-nowrap">
              TAX PLANNER
            </span>
            <span className="bg-[#F59E0B] text-black text-[9px] sm:text-[10px] font-black px-1.5 py-0.5 border border-black shadow-[1px_1px_0px_0px_#000] whitespace-nowrap">
              FY 25–26
            </span>
          </div>
        </div>

        {/* Center Section: Desktop-Only 3-Stage Guided Flow Breadcrumb */}
        {currentUser && (
          <div data-tour="nav-tabs" className="hidden lg:flex items-center gap-1.5 font-mono text-xs">
            <button
              onClick={() => handleTabClick('upload')}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 border-2 border-black transition-all cursor-pointer ${
                activeTab === 'upload' || activeTab === 'reconciliation' || activeTab === 'snapshot'
                  ? 'bg-[#18153B] text-white shadow-[2px_2px_0px_0px_#000] font-black'
                  : 'bg-[#FFFDF9] text-gray-700 hover:bg-gray-100 font-bold'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  activeTab === 'upload' || activeTab === 'reconciliation' || activeTab === 'snapshot'
                    ? 'bg-[#FACC15] animate-pulse'
                    : 'bg-emerald-500'
                }`}
              />
              <span>1. INFLOW &amp; AUDIT</span>
              {flagCount > 0 && (
                <span className="bg-rose-500 text-white font-mono text-[9px] px-1 py-0.2 rounded-full border border-black animate-pulse">
                  {flagCount}
                </span>
              )}
            </button>

            <span className="text-gray-400 font-bold">➔</span>

            <button
              onClick={() => handleTabClick('catalog')}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 border-2 border-black transition-all cursor-pointer ${
                activeTab === 'catalog' || activeTab === 'career' || activeTab === 'chat'
                  ? 'bg-[#18153B] text-white shadow-[2px_2px_0px_0px_#000] font-black'
                  : 'bg-[#FFFDF9] text-gray-700 hover:bg-gray-100 font-bold'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  activeTab === 'catalog' || activeTab === 'career' || activeTab === 'chat'
                    ? 'bg-[#FACC15] animate-pulse'
                    : 'bg-gray-400'
                }`}
              />
              <span>2. STRATEGY &amp; OPTIMIZE</span>
            </button>

            <span className="text-gray-400 font-bold">➔</span>

            <button
              onClick={() => handleTabClick('report')}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 border-2 border-black transition-all cursor-pointer ${
                activeTab === 'report'
                  ? 'bg-[#18153B] text-white shadow-[2px_2px_0px_0px_#000] font-black'
                  : 'bg-[#FFFDF9] text-gray-700 hover:bg-gray-100 font-bold'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  activeTab === 'report' ? 'bg-emerald-400 animate-pulse' : 'bg-gray-400'
                }`}
              />
              <span>3. COMPLIANCE &amp; FILE</span>
            </button>
          </div>
        )}

        {/* Right Section: Authenticated Actions or Auth Buttons */}
        <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
          {currentUser ? (
            <>
              {/* Desktop-Only Action Pills (Hidden on Mobile < 1024px) */}
              <div data-tour="vault-actions" className="hidden lg:flex items-center gap-1.5">
                {/* Search / Command Palette Pill */}
                {onOpenCommandPalette && (
                  <button
                    onClick={onOpenCommandPalette}
                    className="flex items-center gap-1 bg-[#FFFDF9] hover:bg-white text-black px-2.5 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs font-mono cursor-pointer transition-colors"
                    title="Search & Command Palette (Ctrl+K)"
                  >
                    <Search className="w-3.5 h-3.5 text-gray-700" />
                    <span className="text-[11px]">Ctrl+K</span>
                  </button>
                )}

                {/* Tour Button */}
                {onOpenTour && (
                  <button
                    onClick={onOpenTour}
                    className="flex items-center gap-1 bg-[#A7F3D0] hover:bg-[#6EE7B7] text-black px-2.5 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs font-mono uppercase cursor-pointer transition-colors"
                    title="Take the Interactive Platform Tour"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-emerald-800" />
                    <span className="text-[11px]">TOUR</span>
                  </button>
                )}

                {/* AI Keys Pill (Idea B) */}
                {onOpenBYOKModal && (
                  <button
                    onClick={onOpenBYOKModal}
                    className="flex items-center gap-1 bg-[#FFFDF9] hover:bg-[#FACC15] text-black px-2.5 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs font-mono uppercase cursor-pointer transition-colors"
                    title="Configure personal AI keys (OpenRouter, OpenAI, Groq, Gemini)"
                  >
                    <Key className="w-3.5 h-3.5 text-[#3730A3]" />
                    <span className="text-[11px]">KEYS</span>
                  </button>
                )}

                {/* Vault Data Pill (Idea B) */}
                {onOpenLifecycleModal && (
                  <button
                    onClick={onOpenLifecycleModal}
                    className="flex items-center gap-1 bg-[#FFFDF9] hover:bg-[#FACC15] text-black px-2.5 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs font-mono uppercase cursor-pointer transition-colors"
                    title="Data Export, Reset & Right-to-Erasure"
                  >
                    <Database className="w-3.5 h-3.5 text-amber-600" />
                    <span className="text-[11px]">VAULT</span>
                  </button>
                )}
              </div>

              {/* Mobile Quick Action Buttons (< 1024px) */}
              <div className="flex lg:hidden items-center gap-1">
                {onOpenCommandPalette && (
                  <button
                    onClick={onOpenCommandPalette}
                    className="p-1.5 bg-[#FFFDF9] hover:bg-white text-black border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
                    title="Search (Ctrl+K)"
                  >
                    <Search className="w-4 h-4 text-gray-700" />
                  </button>
                )}

                {onOpenTour && (
                  <button
                    onClick={onOpenTour}
                    className="p-1.5 bg-[#A7F3D0] hover:bg-[#6EE7B7] text-black border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
                    title="Platform Tour"
                  >
                    <Sparkles className="w-4 h-4 text-emerald-800" />
                  </button>
                )}
              </div>

              {/* Taxpayer Profile Command Hub Trigger (Always Visible) */}
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

              {/* Mobile Menu Hamburger Button (< 1024px) */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-1.5 sm:p-2 bg-[#FAF7F2] hover:bg-[#FACC15] text-black border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer transition-colors"
                title="Toggle Navigation Menu"
                aria-label="Toggle Navigation Menu"
              >
                {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
              </button>
            </>
          ) : (
            <div className="flex items-center gap-1.5 sm:gap-2">
              <button
                onClick={() => onOpenAuth('login')}
                className="flex items-center gap-1 bg-[#FAF7F2] hover:bg-white text-black px-2.5 sm:px-3 py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs uppercase cursor-pointer"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>SIGN IN</span>
              </button>

              <button
                onClick={() => onOpenAuth('register')}
                className="flex items-center gap-1 bg-[#FACC15] hover:bg-yellow-400 text-black px-2.5 sm:px-3.5 py-1.5 border-2 border-black shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 font-black text-xs uppercase cursor-pointer"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>REGISTER</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. MOBILE 3-STAGE GUIDED FLOW BAR (< 1024px)                              */}
      {/* PERFECT 3-STAGE FIT WITH ZERO HORIZONTAL OVERFLOW                         */}
      {/* ========================================================================= */}
      {currentUser && (
        <nav
          data-tour="nav-tabs"
          className="lg:hidden bg-[#FFFDF9] border-t-2 border-black p-1.5 grid grid-cols-3 gap-1.5 w-full shadow-[inset_0px_2px_4px_rgba(0,0,0,0.05)] font-mono text-[10px] sm:text-xs"
        >
          <button
            onClick={() => handleTabClick('upload')}
            className={`py-1.5 px-1 text-center border-2 border-black font-black uppercase transition-all cursor-pointer truncate ${
              activeTab === 'upload' || activeTab === 'reconciliation' || activeTab === 'snapshot'
                ? 'bg-[#18153B] text-[#FACC15] shadow-[2px_2px_0px_0px_#000] -translate-y-0.5'
                : 'bg-[#FAF7F2] text-black hover:bg-gray-100'
            }`}
          >
            1. INFLOW {flagCount > 0 && <span className="text-rose-400">({flagCount})</span>}
          </button>

          <button
            onClick={() => handleTabClick('catalog')}
            className={`py-1.5 px-1 text-center border-2 border-black font-black uppercase transition-all cursor-pointer truncate ${
              activeTab === 'catalog' || activeTab === 'career' || activeTab === 'chat'
                ? 'bg-[#18153B] text-[#FACC15] shadow-[2px_2px_0px_0px_#000] -translate-y-0.5'
                : 'bg-[#FAF7F2] text-black hover:bg-gray-100'
            }`}
          >
            2. OPTIMIZE
          </button>

          <button
            onClick={() => handleTabClick('report')}
            className={`py-1.5 px-1 text-center border-2 border-black font-black uppercase transition-all cursor-pointer truncate ${
              activeTab === 'report'
                ? 'bg-[#18153B] text-[#FACC15] shadow-[2px_2px_0px_0px_#000] -translate-y-0.5'
                : 'bg-[#FAF7F2] text-black hover:bg-gray-100'
            }`}
          >
            3. COMPLY &amp; FILE
          </button>
        </nav>
      )}

      {/* ========================================================================= */}
      {/* 3. MOBILE ACTION DRAWER (< 1024px)                                         */}
      {/* Slides down when user clicks Hamburger Menu icon                          */}
      {/* ========================================================================= */}
      {mobileMenuOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs lg:hidden animate-in fade-in duration-150"
            onClick={() => setMobileMenuOpen(false)}
          />

          {/* Drawer Menu Panel */}
          <div className="fixed top-14 left-0 right-0 z-50 bg-[#FFFDF9] border-b-4 border-black shadow-[0px_10px_25px_rgba(0,0,0,0.4)] p-4 max-h-[calc(100vh-3.5rem)] overflow-y-auto lg:hidden animate-in slide-in-from-top-2 duration-200 font-mono">
            {/* Active Taxpayer Identity Card */}
            {currentUser && (
              <div className="p-3 bg-[#FAF7F2] border-2 border-black shadow-[2px_2px_0px_0px_#000] mb-3 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-black text-sm text-[#18153B]">{displayName}</span>
                    <span className="bg-[#3730A3] text-white text-[9px] font-black px-1.5 py-0.2 border border-black uppercase">
                      {activeProfile?.persona?.toUpperCase() || 'SALARIED'}
                    </span>
                  </div>
                  <span className="text-[10px] text-gray-600 block mt-0.5">
                    {currentUser.email} • Readiness: {readiness?.overall_score || 0}%
                  </span>
                </div>

                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onLogout();
                  }}
                  className="p-1.5 bg-rose-100 hover:bg-rose-200 border border-black text-rose-800 text-[10px] font-black uppercase flex items-center gap-1 cursor-pointer"
                  title="Lock Vault"
                >
                  <LogOut className="w-3 h-3" />
                  <span>LOCK</span>
                </button>
              </div>
            )}

            {/* Quick Actions Grid */}
            <div className="grid grid-cols-2 gap-2 text-xs font-black mb-3">
              {/* AI BYOK Keys */}
              {onOpenBYOKModal && (
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenBYOKModal();
                  }}
                  className="p-2.5 bg-white hover:bg-[#FACC15] text-black border-2 border-black shadow-[2px_2px_0px_0px_#000] flex items-center gap-2 cursor-pointer active:translate-x-0.5 active:translate-y-0.5 transition-colors"
                >
                  <Key className="w-4 h-4 text-[#3730A3] flex-shrink-0" />
                  <div className="text-left">
                    <span className="block leading-tight">AI KEYS</span>
                    <span className="text-[9px] text-gray-500 font-semibold">BYOK Models</span>
                  </div>
                </button>
              )}

              {/* Vault Data */}
              {onOpenLifecycleModal && (
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenLifecycleModal();
                  }}
                  className="p-2.5 bg-white hover:bg-[#FACC15] text-black border-2 border-black shadow-[2px_2px_0px_0px_#000] flex items-center gap-2 cursor-pointer active:translate-x-0.5 active:translate-y-0.5 transition-colors"
                >
                  <Database className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <div className="text-left">
                    <span className="block leading-tight">VAULT DATA</span>
                    <span className="text-[9px] text-gray-500 font-semibold">Export &amp; Reset</span>
                  </div>
                </button>
              )}

              {/* Household Tax Hub */}
              {onOpenHousehold && (
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenHousehold();
                  }}
                  className="p-2.5 bg-[#FAF7F2] hover:bg-[#FACC15] text-black border-2 border-black shadow-[2px_2px_0px_0px_#000] flex items-center gap-2 cursor-pointer active:translate-x-0.5 active:translate-y-0.5 transition-colors col-span-2 sm:col-span-1"
                >
                  <Users className="w-4 h-4 text-[#3730A3] flex-shrink-0" />
                  <div className="text-left">
                    <span className="block leading-tight">HOUSEHOLD HUB</span>
                    <span className="text-[9px] text-gray-500 font-semibold">Joint Tax Arbitrage</span>
                  </div>
                </button>
              )}

              {/* Tour */}
              {onOpenTour && (
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenTour();
                  }}
                  className="p-2.5 bg-[#A7F3D0] hover:bg-[#6EE7B7] text-black border-2 border-black shadow-[2px_2px_0px_0px_#000] flex items-center gap-2 cursor-pointer active:translate-x-0.5 active:translate-y-0.5 transition-colors col-span-2 sm:col-span-1"
                >
                  <Sparkles className="w-4 h-4 text-emerald-800 flex-shrink-0" />
                  <div className="text-left">
                    <span className="block leading-tight">PLATFORM TOUR</span>
                    <span className="text-[9px] text-emerald-950 font-semibold">Guided Walkthrough</span>
                  </div>
                </button>
              )}
            </div>

            {/* Workflow Navigation Links List */}
            <div className="border-t-2 border-black pt-3 space-y-1 text-xs">
              <span className="text-[10px] font-black uppercase text-gray-500 block mb-1">
                JUMP TO WORKFLOW STEP:
              </span>
              {navItems.map((item) => {
                const isActive = activeTab === item.key;
                return (
                  <button
                    key={item.key}
                    onClick={() => handleTabClick(item.key)}
                    className={`w-full p-2 border flex items-center justify-between font-bold cursor-pointer transition-colors ${
                      isActive
                        ? 'bg-[#FACC15] border-black font-black shadow-[2px_2px_0px_0px_#000]'
                        : 'bg-white border-black/30 hover:bg-[#FAF7F2] hover:border-black'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {item.icon}
                      <span>{item.fullLabel}</span>
                    </div>
                    {item.badge !== undefined && (
                      <span className="bg-red-500 text-white font-mono text-[10px] px-1.5 py-0.2 rounded-full border border-black">
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Close Button */}
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="w-full mt-3 bg-black text-white p-2 border-2 border-black font-black text-xs uppercase cursor-pointer"
            >
              CLOSE MENU
            </button>
          </div>
        </>
      )}
    </header>
  );
};
