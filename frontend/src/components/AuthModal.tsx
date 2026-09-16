import React, { useState } from 'react';
import { Lock, Mail, User as UserIcon, ArrowRight, ShieldCheck, AlertCircle, X } from 'lucide-react';
import { api } from '../api/client';
import type { User } from '../types';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
  initialMode?: 'login' | 'register';
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialMode = 'login',
}) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [pan, setPan] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === 'register') {
        if (!fullName.trim()) {
          throw new Error('Please enter your full name.');
        }
        if (password.length < 6) {
          throw new Error('Password must be at least 6 characters.');
        }
        const res = await api.register(email.trim(), password, fullName.trim(), pan.trim() || undefined);
        onSuccess(res.user);
        onClose();
      } else {
        const res = await api.login(email.trim(), password);
        onSuccess(res.user);
        onClose();
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
      {/* Box Container (Packaging Card) */}
      <div className="relative w-full max-w-md bg-[#FAF7F2] border-4 border-black shadow-[8px_8px_0px_0px_#000000] p-6 md:p-8">
        {/* Top Packaging Barcode & Close */}
        <div className="flex items-center justify-between border-b-3 border-black pb-3 mb-6">
          <div className="font-mono text-[10px] font-black tracking-widest text-gray-700">
            |||| || | ||||| | |||| SECURE AUTH // BATCH FY25-26
          </div>
          <button
            onClick={onClose}
            className="p-1 bg-[#FACC15] hover:bg-yellow-400 border-2 border-black active:translate-x-0.5 active:translate-y-0.5"
            aria-label="Close modal"
          >
            <X className="w-4 h-4 stroke-[3]" />
          </button>
        </div>

        {/* Tab Toggle */}
        <div className="flex border-3 border-black mb-6 bg-[#FAF7F2] shadow-[3px_3px_0px_0px_#000]">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setError(null);
            }}
            className={`flex-1 py-2.5 font-black text-xs uppercase tracking-wider transition-all ${
              mode === 'login'
                ? 'bg-[#3730A3] text-white'
                : 'bg-transparent text-black hover:bg-[#F59E0B]/20'
            }`}
          >
            SIGN IN TO VAULT
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('register');
              setError(null);
            }}
            className={`flex-1 py-2.5 font-black text-xs uppercase tracking-wider transition-all ${
              mode === 'register'
                ? 'bg-[#3730A3] text-white'
                : 'bg-transparent text-black hover:bg-[#F59E0B]/20'
            }`}
          >
            CREATE NEW ACCOUNT
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border-2 border-black p-3 mb-4 shadow-[2px_2px_0px_0px_#000] text-red-900 font-mono text-xs font-bold flex items-start gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <>
              <div>
                <label className="block text-xs font-black uppercase text-gray-800 mb-1 font-mono">
                  Full Name:
                </label>
                <div className="relative">
                  <UserIcon className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Vikram Sharma"
                    className="w-full bg-[#FFFDF9] border-2 border-black pl-10 pr-3 py-2.5 font-mono text-xs font-bold shadow-[2px_2px_0px_0px_#000] outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-black uppercase text-gray-800 mb-1 font-mono">
                  PAN (Optional):
                </label>
                <input
                  type="text"
                  value={pan}
                  onChange={(e) => setPan(e.target.value.toUpperCase())}
                  placeholder="e.g. ABCDE1234F"
                  maxLength={10}
                  className="w-full bg-[#FFFDF9] border-2 border-black px-3 py-2.5 font-mono text-xs font-bold shadow-[2px_2px_0px_0px_#000] outline-none uppercase"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-black uppercase text-gray-800 mb-1 font-mono">
              Work / Personal Email:
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full bg-[#FFFDF9] border-2 border-black pl-10 pr-3 py-2.5 font-mono text-xs font-bold shadow-[2px_2px_0px_0px_#000] outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-black uppercase text-gray-800 mb-1 font-mono">
              Password:
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-[#FFFDF9] border-2 border-black pl-10 pr-3 py-2.5 font-mono text-xs font-bold shadow-[2px_2px_0px_0px_#000] outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 border-3 border-black font-black text-xs md:text-sm tracking-wider uppercase flex items-center justify-center gap-2 transition-all mt-6 ${
              loading
                ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                : 'bg-[#FACC15] hover:bg-[#FFE600] text-black shadow-[4px_4px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none'
            }`}
          >
            {loading ? (
              <span>VERIFYING AUTH CREDENTIALS...</span>
            ) : (
              <>
                <span>{mode === 'register' ? 'INITIALIZE REAL VAULT' : 'AUTHENTICATE & ENTER'}</span>
                <ArrowRight className="w-4 h-4 stroke-[3]" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t-2 border-dashed border-black flex items-center justify-between text-[10px] font-mono text-gray-600">
          <span className="flex items-center gap-1 font-bold">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            BANK-GRADE ENCRYPTION
          </span>
          <span className="font-bold">100% EXACT STATUTORY MATH</span>
        </div>
      </div>
    </div>
  );
};
