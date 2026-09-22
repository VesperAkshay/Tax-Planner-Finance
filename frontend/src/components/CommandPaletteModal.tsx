import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  UploadCloud,
  PieChart,
  GitCompare,
  BookOpen,
  MessageSquareCode,
  FileCheck2,
  Users,
  Key,
  Database,
  UserPlus,
  Sparkles,
  ChevronRight,
  Briefcase,
} from 'lucide-react';
import type { TabKey } from './Navbar';
import type { TaxpayerProfile } from '../types';

interface CommandPaletteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTab: (tab: TabKey) => void;
  profiles: TaxpayerProfile[];
  activeProfile: TaxpayerProfile | null;
  onSelectProfile: (profileId: number) => void;
  onOpenAddProfile: () => void;
  onOpenHousehold: () => void;
  onOpenBYOK: () => void;
  onOpenLifecycle: () => void;
  onOpenTour: () => void;
}

interface PaletteItem {
  id: string;
  category: 'Tabs' | 'Profiles' | 'Actions' | 'Tools';
  label: string;
  sublabel?: string;
  icon: React.ReactNode;
  action: () => void;
}

export const CommandPaletteModal: React.FC<CommandPaletteModalProps> = ({
  isOpen,
  onClose,
  onSelectTab,
  profiles,
  activeProfile,
  onSelectProfile,
  onOpenAddProfile,
  onOpenHousehold,
  onOpenBYOK,
  onOpenLifecycle,
  onOpenTour,
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const items: PaletteItem[] = [
    // Tabs
    {
      id: 'tab-upload',
      category: 'Tabs',
      label: '1. Ingest Docs (Bank & Salary Statements)',
      sublabel: 'Upload CSV/PDF statements and salary slips',
      icon: <UploadCloud className="w-4 h-4 text-blue-700" />,
      action: () => onSelectTab('upload'),
    },
    {
      id: 'tab-snapshot',
      category: 'Tabs',
      label: '2. Financial Snapshot & ML Analytics',
      sublabel: 'Inflow, outflow, and 50/30/20 budget diagnostic',
      icon: <PieChart className="w-4 h-4 text-amber-700" />,
      action: () => onSelectTab('snapshot'),
    },
    {
      id: 'tab-reconciliation',
      category: 'Tabs',
      label: '3. Salary Slip vs Bank Reconciliation',
      sublabel: 'Audit net pay matches against salary credits',
      icon: <GitCompare className="w-4 h-4 text-indigo-700" />,
      action: () => onSelectTab('reconciliation'),
    },
    {
      id: 'tab-catalog',
      category: 'Tabs',
      label: '4. Statutory Deductions Catalog (Chapter VI-A)',
      sublabel: 'Declare 80C, 80D, 80CCD(1B), 80E, HRA',
      icon: <BookOpen className="w-4 h-4 text-emerald-700" />,
      action: () => onSelectTab('catalog'),
    },
    {
      id: 'tab-career',
      category: 'Tabs',
      label: '5. Career Switch & Offer Letter Decoder',
      sublabel: 'Decode offer traps, simulate mid-year switch & Form 12B',
      icon: <Briefcase className="w-4 h-4 text-[#18153B]" />,
      action: () => onSelectTab('career'),
    },
    {
      id: 'tab-chat',
      category: 'Tabs',
      label: '6. Mr. Planner AI Conversational Strategist',
      sublabel: 'Ask complex tax queries with legal RAG citations',
      icon: <MessageSquareCode className="w-4 h-4 text-[#3730A3]" />,
      action: () => onSelectTab('chat'),
    },
    {
      id: 'tab-report',
      category: 'Tabs',
      label: '7. Final Tax Report & Dual-Regime Audit',
      sublabel: 'Section 115BAC comparison and PDF invoice export',
      icon: <FileCheck2 className="w-4 h-4 text-purple-700" />,
      action: () => onSelectTab('report'),
    },

    // Profiles
    ...profiles.map((p) => ({
      id: `profile-${p.id}`,
      category: 'Profiles' as const,
      label: `Switch to ${p.name} (${p.relationship.toUpperCase()})`,
      sublabel: `Persona: ${p.persona.toUpperCase()} ${p.pan ? `• ${p.pan}` : ''} ${
        activeProfile?.id === p.id ? '[CURRENTLY ACTIVE]' : ''
      }`,
      icon: <Users className="w-4 h-4 text-black" />,
      action: () => onSelectProfile(p.id),
    })),

    // Tools & Actions
    {
      id: 'act-add-profile',
      category: 'Actions',
      label: 'Add Family Member / Taxpayer Profile',
      sublabel: 'Create profile for Spouse, Parent (Senior Citizen), or HUF',
      icon: <UserPlus className="w-4 h-4 text-emerald-700" />,
      action: onOpenAddProfile,
    },
    {
      id: 'act-household',
      category: 'Tools',
      label: 'Open Household Tax Optimizer & Arbitrage',
      sublabel: 'Joint family tax comparison and cross-profile deductions',
      icon: <Sparkles className="w-4 h-4 text-[#FACC15]" />,
      action: onOpenHousehold,
    },
    {
      id: 'act-byok',
      category: 'Tools',
      label: 'Configure AI Keys (BYOK)',
      sublabel: 'OpenRouter, OpenAI, Groq, Gemini personal keys',
      icon: <Key className="w-4 h-4 text-[#3730A3]" />,
      action: onOpenBYOK,
    },
    {
      id: 'act-lifecycle',
      category: 'Tools',
      label: 'Vault Data Lifecycle & Export (ZIP / Purge)',
      sublabel: '1-Click data export or right-to-erasure reset',
      icon: <Database className="w-4 h-4 text-amber-700" />,
      action: onOpenLifecycle,
    },
    {
      id: 'act-tour',
      category: 'Tools',
      label: 'Restart Interactive Platform Tour',
      sublabel: 'Guided visual spotlight walk-through',
      icon: <Sparkles className="w-4 h-4 text-emerald-700" />,
      action: onOpenTour,
    },
  ];

  const filteredItems = items.filter((item) => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (
      item.label.toLowerCase().includes(q) ||
      item.sublabel?.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q)
    );
  });

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredItems.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % Math.max(1, filteredItems.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredItems[selectedIndex]) {
        filteredItems[selectedIndex].action();
        onClose();
      }
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-start justify-center p-4 pt-16 sm:pt-24 font-mono">
      <div className="bg-[#FFFDF9] border-4 border-black w-full max-w-xl shadow-[8px_8px_0px_0px_#000000] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-100">
        {/* Search Bar Input */}
        <div className="p-3 bg-[#18153B] border-b-3 border-black flex items-center gap-3">
          <Search className="w-5 h-5 text-[#FACC15] flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search tabs, profiles, actions..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            className="w-full bg-transparent text-white font-bold text-sm outline-none placeholder:text-gray-400 font-mono"
          />
          <kbd className="hidden sm:inline-block bg-black text-[#FACC15] text-[10px] px-2 py-0.5 border border-white/20 font-black">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto divide-y divide-black/10 text-xs">
          {filteredItems.length === 0 ? (
            <div className="p-8 text-center text-gray-500 font-bold">
              No matching commands or profiles found for "{query}".
            </div>
          ) : (
            filteredItems.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => {
                    item.action();
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`p-3 flex items-center justify-between cursor-pointer transition-colors ${
                    isSelected ? 'bg-[#FACC15]/30' : 'hover:bg-[#FAF7F2]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2 border border-black ${
                        isSelected ? 'bg-[#FACC15]' : 'bg-white'
                      }`}
                    >
                      {item.icon}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-black text-black text-xs">{item.label}</span>
                        <span className="bg-gray-200 border border-black px-1 py-0.2 text-[9px] font-black uppercase text-gray-700">
                          {item.category}
                        </span>
                      </div>
                      {item.sublabel && (
                        <p className="text-[11px] text-gray-600 font-semibold mt-0.5">
                          {item.sublabel}
                        </p>
                      )}
                    </div>
                  </div>

                  {isSelected && <ChevronRight className="w-4 h-4 text-black flex-shrink-0" />}
                </div>
              );
            })
          )}
        </div>

        {/* Footer Shortcuts */}
        <div className="p-2.5 bg-[#FAF7F2] border-t-2 border-black flex items-center justify-between text-[10px] text-gray-600 font-bold">
          <div className="flex items-center gap-3">
            <span>
              <kbd className="bg-white border border-black px-1 py-0.5">↑</kbd>{' '}
              <kbd className="bg-white border border-black px-1 py-0.5">↓</kbd> Navigate
            </span>
            <span>
              <kbd className="bg-white border border-black px-1.5 py-0.5">ENTER</kbd> Select
            </span>
          </div>
          <span>
            Shortcut: <kbd className="bg-white border border-black px-1 py-0.5">Ctrl</kbd> +{' '}
            <kbd className="bg-white border border-black px-1 py-0.5">K</kbd>
          </span>
        </div>
      </div>
    </div>
  );
};
