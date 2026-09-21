import React, { useState, useRef, useEffect } from 'react';
import {
  Users,
  Briefcase,
  Laptop,
  Heart,
  TrendingUp,
  Building,
  ChevronDown,
  Copy,
  Check,
  UserPlus,
  Sparkles,
  Command,
  Edit2,
  LogOut,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ArrowRight,
  Database,
  Key,
} from 'lucide-react';
import type { User, TaxpayerProfile, ProfileReadinessResponse } from '../types';

interface ProfileCommandHubProps {
  currentUser: User | null;
  profiles: TaxpayerProfile[];
  activeProfile: TaxpayerProfile | null;
  readiness: ProfileReadinessResponse | null;
  onSelectProfile: (profileId: number) => void;
  onOpenAddProfile: () => void;
  onOpenEditProfile: (profile: TaxpayerProfile) => void;
  onOpenHousehold: () => void;
  onOpenCommandPalette: () => void;
  onOpenLifecycleModal?: () => void;
  onOpenBYOKModal?: () => void;
  onLogout: () => void;
}

export const ProfileCommandHub: React.FC<ProfileCommandHubProps> = ({
  currentUser,
  profiles,
  activeProfile,
  readiness,
  onSelectProfile,
  onOpenAddProfile,
  onOpenEditProfile,
  onOpenHousehold,
  onOpenCommandPalette,
  onOpenLifecycleModal,
  onOpenBYOKModal,
  onLogout,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [copiedPan, setCopiedPan] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleCopyPan = (panText: string) => {
    navigator.clipboard.writeText(panText);
    setCopiedPan(true);
    setTimeout(() => setCopiedPan(false), 2000);
  };

  const getPersonaIcon = (persona?: string) => {
    switch (persona) {
      case 'freelancer_44ada':
        return <Laptop className="w-4 h-4 text-emerald-700" />;
      case 'senior_citizen':
        return <Heart className="w-4 h-4 text-rose-700" />;
      case 'investor':
        return <TrendingUp className="w-4 h-4 text-blue-700" />;
      case 'huf':
        return <Building className="w-4 h-4 text-amber-700" />;
      default:
        return <Briefcase className="w-4 h-4 text-[#3730A3]" />;
    }
  };

  const getPersonaBadge = (persona?: string) => {
    switch (persona) {
      case 'freelancer_44ada':
        return '44ADA';
      case 'senior_citizen':
        return 'SENIOR';
      case 'investor':
        return 'ITR-2';
      case 'huf':
        return 'HUF';
      default:
        return 'ITR-1';
    }
  };

  const displayName =
    activeProfile?.name ||
    currentUser?.full_name ||
    currentUser?.email.split('@')[0] ||
    'Taxpayer';

  const displayPan = activeProfile?.pan || currentUser?.pan;
  const readinessPercent = readiness?.overall_score ?? activeProfile?.readiness_score ?? 0;

  return (
    <div ref={containerRef} className="relative font-mono">
      {/* 1. INTERACTIVE NAVBAR TRIGGER BUTTON */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 sm:gap-2 bg-[#FFFDF9] hover:bg-white text-black px-2 sm:px-2.5 py-1 sm:py-1.5 border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer transition-all flex-shrink-0"
        title="Open Taxpayer Identity & Household Command Hub"
      >
        {/* Persona Icon */}
        <div className="p-0.5 sm:p-1 bg-[#FAF7F2] border border-black flex-shrink-0">
          {getPersonaIcon(activeProfile?.persona)}
        </div>

        {/* Name & Tag */}
        <div className="text-left flex items-center gap-1 max-w-[85px] sm:max-w-[125px] truncate">
          <span className="font-black text-xs text-[#18153B] truncate">
            {displayName}
          </span>
          <span className="bg-[#3730A3] text-white text-[9px] px-1 py-0.2 border border-black font-black uppercase hidden md:inline-block">
            {getPersonaBadge(activeProfile?.persona)}
          </span>
        </div>

        {/* Live Filing Readiness Score Pill */}
        <div
          className={`flex items-center gap-1 px-1.5 py-0.5 border border-black text-[10px] font-black ${
            readinessPercent >= 75
              ? 'bg-emerald-200 text-emerald-950'
              : readinessPercent >= 50
              ? 'bg-amber-200 text-amber-950'
              : 'bg-rose-200 text-rose-950'
          }`}
          title={`Filing Readiness: ${readinessPercent}%`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              readinessPercent >= 75 ? 'bg-emerald-600 animate-pulse' : 'bg-amber-600'
            }`}
          />
          <span>{readinessPercent}%</span>
        </div>

        <ChevronDown
          className={`w-3.5 h-3.5 text-gray-700 transition-transform duration-200 flex-shrink-0 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* 2. THE NEO-BRUTALIST COMMAND HUB DROPDOWN */}
      {isOpen && (
        <div className="fixed sm:absolute inset-x-2 sm:inset-x-auto sm:right-0 top-14 sm:top-full mt-1 sm:mt-2 sm:w-[420px] max-w-[calc(100vw-1rem)] bg-[#FFFDF9] border-4 border-black shadow-[6px_6px_0px_0px_#000000] sm:shadow-[8px_8px_0px_0px_#000000] z-50 flex flex-col max-h-[85vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-150">
          {/* Header Strip */}
          <div className="bg-[#18153B] text-white p-3.5 border-b-3 border-black flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-1 bg-[#FACC15] text-black border border-black font-black text-[10px]">
                HUB
              </div>
              <div>
                <h4 className="font-black text-xs uppercase font-['Space_Grotesk'] text-[#FACC15]">
                  TAXPAYER IDENTITY &amp; COMMAND
                </h4>
                <p className="text-[10px] text-gray-300">
                  {currentUser?.email}
                </p>
              </div>
            </div>

            <button
              onClick={onOpenCommandPalette}
              className="flex items-center gap-1 bg-black/40 hover:bg-black text-[#FACC15] px-2 py-1 border border-white/20 text-[10px] font-black cursor-pointer"
              title="Open Command Palette (Ctrl+K)"
            >
              <Command className="w-3 h-3" />
              <span>Ctrl+K</span>
            </button>
          </div>

          {/* Active Taxpayer Profile Card */}
          <div className="p-4 bg-[#FAF7F2] border-b-2 border-black space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 bg-[#3730A3] text-white flex items-center justify-center font-black text-sm border-2 border-black shadow-[1px_1px_0px_0px_#000]">
                  {displayName.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-black text-sm text-[#18153B]">{displayName}</span>
                    <span className="bg-[#FACC15] text-black text-[9px] font-black px-1.5 py-0.2 border border-black uppercase">
                      {activeProfile?.relationship || 'SELF'}
                    </span>
                  </div>
                  <span className="text-[10px] text-gray-600 font-bold block">
                    Persona: {activeProfile?.persona?.toUpperCase() || 'SALARIED (ITR-1)'}
                  </span>
                </div>
              </div>

              {activeProfile && (
                <button
                  onClick={() => {
                    onOpenEditProfile(activeProfile);
                    setIsOpen(false);
                  }}
                  className="p-1.5 bg-white hover:bg-gray-100 border border-black text-gray-700 hover:text-black cursor-pointer shadow-[1px_1px_0px_0px_#000]"
                  title="Edit Active Profile"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* PAN with 1-Click Copy */}
            {displayPan ? (
              <div className="flex items-center justify-between bg-white border border-black px-2.5 py-1 text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] text-gray-500 font-bold">PAN:</span>
                  <span className="font-mono font-black text-[#18153B] tracking-wider">
                    {displayPan}
                  </span>
                </div>
                <button
                  onClick={() => handleCopyPan(displayPan)}
                  className="flex items-center gap-1 text-[10px] text-gray-700 hover:text-black cursor-pointer font-bold"
                  title="Copy PAN"
                >
                  {copiedPan ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-600" />
                      <span className="text-emerald-700">COPIED</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>COPY</span>
                    </>
                  )}
                </button>
              </div>
            ) : (
              <div className="text-[11px] text-amber-800 bg-amber-50 border border-black p-1.5 font-bold">
                ⚠️ PAN not added. Click edit icon to add PAN for exact statutory tax reporting.
              </div>
            )}

            {/* Live Filing Readiness Scorecard */}
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center justify-between text-[10px] font-bold">
                <span className="uppercase text-gray-700 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-[#3730A3]" />
                  <span>TAX FILING READINESS:</span>
                </span>
                <span className="font-black text-[#3730A3]">{readinessPercent}% READY</span>
              </div>
              <div className="w-full bg-gray-200 h-2 border border-black">
                <div
                  className={`h-full transition-all duration-300 ${
                    readinessPercent >= 75
                      ? 'bg-emerald-500'
                      : readinessPercent >= 50
                      ? 'bg-[#FACC15]'
                      : 'bg-rose-400'
                  }`}
                  style={{ width: `${readinessPercent}%` }}
                />
              </div>

              {/* Checklist Mini Grid */}
              {readiness?.milestones && (
                <div className="grid grid-cols-2 gap-1 pt-1 text-[10px]">
                  {readiness.milestones.map((m, idx) => (
                    <div
                      key={idx}
                      className={`p-1 border flex items-center gap-1 font-bold ${
                        m.is_complete
                          ? 'bg-emerald-50 border-emerald-500 text-emerald-950'
                          : 'bg-gray-50 border-gray-300 text-gray-500'
                      }`}
                    >
                      {m.is_complete ? (
                        <CheckCircle2 className="w-3 h-3 text-emerald-600 flex-shrink-0" />
                      ) : (
                        <Clock className="w-3 h-3 text-gray-400 flex-shrink-0" />
                      )}
                      <span className="truncate">{m.name}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Multi-Taxpayer Switcher Section */}
          <div className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-black uppercase text-gray-600 flex items-center gap-1">
                <Users className="w-3.5 h-3.5 text-[#3730A3]" />
                <span>SWITCH TAXPAYER WORKSPACE ({profiles.length}):</span>
              </span>
              <button
                onClick={() => {
                  onOpenAddProfile();
                  setIsOpen(false);
                }}
                className="flex items-center gap-1 text-[10px] font-black text-[#3730A3] hover:underline cursor-pointer"
              >
                <UserPlus className="w-3 h-3" />
                <span>+ ADD MEMBER</span>
              </button>
            </div>

            <div className="max-h-48 overflow-y-auto space-y-1.5">
              {profiles.map((p) => {
                const isActive = activeProfile?.id === p.id;
                return (
                  <div
                    key={p.id}
                    className={`p-2.5 border-2 flex items-center justify-between transition-all ${
                      isActive
                        ? 'bg-[#FACC15]/20 border-black shadow-[2px_2px_0px_0px_#000]'
                        : 'bg-white border-black/30 hover:border-black hover:bg-[#FAF7F2]'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      {getPersonaIcon(p.persona)}
                      <div className="truncate">
                        <div className="flex items-center gap-1.5">
                          <span className="font-black text-xs text-[#18153B] truncate">{p.name}</span>
                          <span className="bg-gray-100 border border-black text-[9px] px-1 py-0.2 uppercase font-black">
                            {p.relationship}
                          </span>
                        </div>
                        <span className="text-[10px] text-gray-500 font-semibold block">
                          {p.persona.toUpperCase()} {p.pan ? `• ${p.pan}` : ''}
                        </span>
                      </div>
                    </div>

                    {isActive ? (
                      <span className="bg-emerald-200 text-emerald-950 font-black text-[9px] px-2 py-0.5 border border-black uppercase flex-shrink-0">
                        ACTIVE
                      </span>
                    ) : (
                      <button
                        onClick={() => {
                          onSelectProfile(p.id);
                          setIsOpen(false);
                        }}
                        className="bg-white hover:bg-[#FACC15] text-black border border-black px-2.5 py-1 text-[10px] font-black uppercase shadow-[1px_1px_0px_0px_#000] cursor-pointer active:translate-x-0.5 active:translate-y-0.5 flex-shrink-0"
                      >
                        SWITCH
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Household Tax Optimizer Teaser Strip */}
          <div className="p-3 bg-[#18153B] text-white border-t-2 border-black flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#FACC15] flex-shrink-0" />
              <div>
                <span className="text-[10px] font-black text-[#FACC15] uppercase block">
                  HOUSEHOLD TAX OPTIMIZER
                </span>
                <span className="text-[10px] text-gray-300 block">
                  Joint family deduction arbitrage &amp; aggregate tax
                </span>
              </div>
            </div>

            <button
              onClick={() => {
                onOpenHousehold();
                setIsOpen(false);
              }}
              className="bg-[#FACC15] hover:bg-yellow-400 text-black px-2.5 py-1 border border-black text-[10px] font-black uppercase shadow-[2px_2px_0px_0px_#000] cursor-pointer flex items-center gap-1"
            >
              <span>VIEW HUB</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          {/* Quick Vault & AI Settings Strip */}
          {(onOpenLifecycleModal || onOpenBYOKModal) && (
            <div className="p-2.5 bg-white border-t-2 border-black grid grid-cols-2 gap-2 text-[10px] font-black">
              {onOpenLifecycleModal && (
                <button
                  onClick={() => {
                    onOpenLifecycleModal();
                    setIsOpen(false);
                  }}
                  className="flex items-center justify-center gap-1.5 bg-[#FAF7F2] hover:bg-[#FACC15] text-black px-2 py-1.5 border border-black shadow-[1px_1px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer uppercase transition-colors"
                  title="Data Export, Reset & Right-to-Erasure"
                >
                  <Database className="w-3.5 h-3.5 text-amber-700 flex-shrink-0" />
                  <span className="truncate">VAULT DATA</span>
                </button>
              )}
              {onOpenBYOKModal && (
                <button
                  onClick={() => {
                    onOpenBYOKModal();
                    setIsOpen(false);
                  }}
                  className="flex items-center justify-center gap-1.5 bg-[#FAF7F2] hover:bg-[#FACC15] text-black px-2 py-1.5 border border-black shadow-[1px_1px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer uppercase transition-colors"
                  title="Configure personal AI keys"
                >
                  <Key className="w-3.5 h-3.5 text-[#3730A3] flex-shrink-0" />
                  <span className="truncate">AI KEYS (BYOK)</span>
                </button>
              )}
            </div>
          )}

          {/* Footer Shortcuts */}
          <div className="p-2.5 bg-[#FAF7F2] border-t-2 border-black flex items-center justify-between text-[11px] font-bold">
            <button
              onClick={() => {
                onOpenCommandPalette();
                setIsOpen(false);
              }}
              className="flex items-center gap-1 text-gray-700 hover:text-black cursor-pointer"
            >
              <Command className="w-3.5 h-3.5" />
              <span>Command Palette</span>
            </button>

            <button
              onClick={() => {
                onLogout();
                setIsOpen(false);
              }}
              className="flex items-center gap-1 text-rose-700 hover:text-rose-900 cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Lock Vault</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
