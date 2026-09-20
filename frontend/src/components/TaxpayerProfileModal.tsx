import React, { useState, useEffect } from 'react';
import {
  X,
  UserPlus,
  Briefcase,
  Laptop,
  Heart,
  TrendingUp,
  Building,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import type { TaxpayerProfile } from '../types';

interface TaxpayerProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (profileData: Partial<TaxpayerProfile>) => Promise<void>;
  editingProfile?: TaxpayerProfile | null;
}

export const TaxpayerProfileModal: React.FC<TaxpayerProfileModalProps> = ({
  isOpen,
  onClose,
  onSave,
  editingProfile,
}) => {
  const [name, setName] = useState('');
  const [relationship, setRelationship] = useState('spouse');
  const [pan, setPan] = useState('');
  const [ageCategory, setAgeCategory] = useState<'general' | 'senior' | 'super_senior'>('general');
  const [persona, setPersona] = useState<string>('salaried');
  const [isDefault, setIsDefault] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editingProfile) {
      setName(editingProfile.name || '');
      setRelationship(editingProfile.relationship || 'self');
      setPan(editingProfile.pan || '');
      setAgeCategory((editingProfile.age_category as any) || 'general');
      setPersona(editingProfile.persona || 'salaried');
      setIsDefault(editingProfile.is_default || false);
    } else {
      setName('');
      setRelationship('spouse');
      setPan('');
      setAgeCategory('general');
      setPersona('salaried');
      setIsDefault(false);
    }
    setError(null);
  }, [editingProfile, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError('Taxpayer name is required.');
      return;
    }

    const cleanPan = pan.trim().toUpperCase();
    if (cleanPan && !/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(cleanPan)) {
      setError('Invalid PAN format. Must be 10 characters: 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F).');
      return;
    }

    setIsSaving(true);
    try {
      await onSave({
        name: name.trim(),
        relationship,
        pan: cleanPan || null,
        age_category: ageCategory,
        persona,
        is_default: isDefault,
      });
      onClose();
    } catch (err: unknown) {
      const msg = (err as any)?.detail || (err instanceof Error ? err.message : 'Failed to save profile.');
      setError(msg);
    } finally {
      setIsSaving(false);
    }
  };

  const personaOptions = [
    {
      id: 'salaried',
      label: 'Salaried (ITR-1)',
      icon: <Briefcase className="w-4 h-4 text-[#3730A3]" />,
      desc: '₹75,000 Standard Deduction, HRA Section 10(13A), Form 16',
    },
    {
      id: 'freelancer_44ada',
      label: 'Freelancer / Consultant (44ADA)',
      icon: <Laptop className="w-4 h-4 text-emerald-700" />,
      desc: '50% Presumptive Profit, zero bookkeeping under ₹75 Lakhs',
    },
    {
      id: 'senior_citizen',
      label: 'Senior Citizen (60+)',
      icon: <Heart className="w-4 h-4 text-rose-700" />,
      desc: '₹50,000 Section 80TTB interest deduction, ₹50,000 80D health',
    },
    {
      id: 'investor',
      label: 'Investor & Trader (ITR-2)',
      icon: <TrendingUp className="w-4 h-4 text-blue-700" />,
      desc: 'STCG (20%), LTCG (12.5% > ₹1.25L), Loss Harvesting',
    },
    {
      id: 'huf',
      label: 'Hindu Undivided Family (HUF)',
      icon: <Building className="w-4 h-4 text-amber-700" />,
      desc: 'Separate legal entity, dedicated ₹1.5L 80C pool & slabs',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto font-mono">
      <div className="bg-[#FFFDF9] border-4 border-black w-full max-w-lg shadow-[8px_8px_0px_0px_#000000] flex flex-col animate-in fade-in zoom-in-95 duration-150 my-8">
        {/* Header */}
        <div className="bg-[#18153B] text-white p-4 border-b-3 border-black flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-[#FACC15] text-black border border-black">
              <UserPlus className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-black text-base uppercase font-['Space_Grotesk'] text-[#FACC15]">
                {editingProfile ? 'EDIT TAXPAYER PROFILE' : 'ADD FAMILY TAXPAYER PROFILE'}
              </h3>
              <p className="text-[11px] text-gray-300">
                Enterprise Multi-Taxpayer Vault Scoping (FY 2025–26)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-[#FACC15] p-1 border border-white/20 hover:border-[#FACC15] cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          {error && (
            <div className="bg-red-100 border-2 border-black p-3 text-red-900 font-bold flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Name & Relationship */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-black uppercase text-gray-700 mb-1">
                Full Name: *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Priya Sharma"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-[#FAF7F2] border-2 border-black p-2 font-bold outline-none shadow-[2px_2px_0px_0px_#000]"
              />
            </div>

            <div>
              <label className="block text-[10px] font-black uppercase text-gray-700 mb-1">
                Relationship:
              </label>
              <select
                value={relationship}
                onChange={(e) => {
                  const val = e.target.value;
                  setRelationship(val);
                  if (val === 'parent') {
                    setAgeCategory('senior');
                    setPersona('senior_citizen');
                  }
                }}
                className="w-full bg-[#FAF7F2] border-2 border-black p-2 font-bold outline-none shadow-[2px_2px_0px_0px_#000]"
              >
                <option value="self">Self (Primary)</option>
                <option value="spouse">Spouse</option>
                <option value="parent">Parent (Father / Mother)</option>
                <option value="child">Child / Dependent</option>
                <option value="huf">HUF (Family Entity)</option>
                <option value="client">Client / Other</option>
              </select>
            </div>
          </div>

          {/* PAN & Age Category */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-black uppercase text-gray-700 mb-1">
                Permanent Account Number (PAN):
              </label>
              <input
                type="text"
                maxLength={10}
                placeholder="ABCDE1234F"
                value={pan}
                onChange={(e) => setPan(e.target.value.toUpperCase())}
                className="w-full bg-[#FAF7F2] border-2 border-black p-2 font-mono font-black uppercase tracking-wider outline-none shadow-[2px_2px_0px_0px_#000]"
              />
            </div>

            <div>
              <label className="block text-[10px] font-black uppercase text-gray-700 mb-1">
                Age Category (Statutory Exemption):
              </label>
              <select
                value={ageCategory}
                onChange={(e) => setAgeCategory(e.target.value as any)}
                className="w-full bg-[#FAF7F2] border-2 border-black p-2 font-bold outline-none shadow-[2px_2px_0px_0px_#000]"
              >
                <option value="general">General (Age &lt; 60)</option>
                <option value="senior">Senior Citizen (Age 60–79)</option>
                <option value="super_senior">Super Senior Citizen (Age 80+)</option>
              </select>
            </div>
          </div>

          {/* Taxpayer Persona Selection */}
          <div>
            <label className="block text-[10px] font-black uppercase text-gray-700 mb-1.5">
              Taxpayer Persona &amp; Statutory Track:
            </label>
            <div className="space-y-2">
              {personaOptions.map((opt) => (
                <label
                  key={opt.id}
                  className={`flex items-start gap-2.5 p-2.5 border-2 border-black cursor-pointer transition-all ${
                    persona === opt.id
                      ? 'bg-[#FACC15]/20 border-black shadow-[3px_3px_0px_0px_#000]'
                      : 'bg-white hover:bg-[#FAF7F2]'
                  }`}
                >
                  <input
                    type="radio"
                    name="persona"
                    value={opt.id}
                    checked={persona === opt.id}
                    onChange={() => setPersona(opt.id)}
                    className="mt-0.5 accent-[#3730A3]"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-1.5 font-black text-xs text-black">
                      {opt.icon}
                      <span>{opt.label}</span>
                    </div>
                    <p className="text-[11px] text-gray-600 font-semibold font-['Plus_Jakarta_Sans'] mt-0.5">
                      {opt.desc}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Default Profile Checkbox */}
          <div className="pt-1">
            <label className="flex items-center gap-2 cursor-pointer select-none text-xs font-bold text-gray-800">
              <input
                type="checkbox"
                checked={isDefault}
                onChange={(e) => setIsDefault(e.target.checked)}
                className="w-4 h-4 accent-[#3730A3] border border-black cursor-pointer"
              />
              <span>Set as default active profile when logging in</span>
            </label>
          </div>

          {/* Footer Buttons */}
          <div className="p-3 bg-[#FAF7F2] border-t-2 border-black flex items-center justify-end gap-3 pt-3 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="bg-white hover:bg-gray-100 text-black px-4 py-2 border-2 border-black font-black uppercase text-xs shadow-[2px_2px_0px_0px_#000] cursor-pointer"
            >
              CANCEL
            </button>

            <button
              type="submit"
              disabled={isSaving}
              className="bg-[#FACC15] hover:bg-yellow-400 text-black px-6 py-2 border-2 border-black font-black uppercase text-xs shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{isSaving ? 'SAVING...' : editingProfile ? 'UPDATE PROFILE' : 'CREATE TAXPAYER'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
