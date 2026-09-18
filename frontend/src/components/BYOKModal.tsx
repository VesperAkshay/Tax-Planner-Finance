import React, { useState, useEffect } from 'react';
import {
  Key,
  X,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Zap,
  Eye,
  EyeOff,
  Trash2,
  Lock,
  HardDrive,
  RefreshCw,
  Sparkles,
  ExternalLink,
} from 'lucide-react';
import { api } from '../api/client';
import type { BYOKConfig } from '../types';

interface BYOKModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfigUpdated?: (config: BYOKConfig) => void;
}

interface ProviderPreset {
  id: string;
  name: string;
  badge: string;
  badgeColor: string;
  icon: string;
  docUrl: string;
  baseUrl?: string;
  defaultModel: string;
  models: { id: string; label: string; tag: string }[];
  note: string;
}

const PROVIDER_PRESETS: ProviderPreset[] = [
  {
    id: 'openrouter',
    name: 'OpenRouter',
    badge: 'FREE TIER AVAILABLE',
    badgeColor: 'bg-emerald-300 text-black',
    icon: '🌐',
    docUrl: 'https://openrouter.ai/keys',
    defaultModel: 'openrouter/free',
    models: [
      { id: 'openrouter/free', label: 'openrouter/free (Auto Free Router)', tag: '100% FREE' },
      { id: 'meta-llama/llama-3.3-70b-instruct', label: 'Llama 3.3 70B Instruct', tag: 'RECOMMENDED' },
      { id: 'deepseek/deepseek-chat', label: 'DeepSeek Chat', tag: 'ULTRA-LOW' },
    ],
    note: 'Access 100+ AI models through a single key with auto-fallback to free tiers.',
  },
  {
    id: 'groq',
    name: 'Groq Cloud',
    badge: 'FASTEST / FREE TIER',
    badgeColor: 'bg-amber-300 text-black',
    icon: '⚡',
    docUrl: 'https://console.groq.com/keys',
    defaultModel: 'llama-3.3-70b-versatile',
    models: [
      { id: 'llama-3.3-70b-versatile', label: 'llama-3.3-70b-versatile (70B)', tag: 'RECOMMENDED' },
      { id: 'llama-3.1-8b-instant', label: 'llama-3.1-8b-instant (8B)', tag: 'SUB-100MS' },
    ],
    note: 'Ultra-low latency inference powered by LPUs. Generous developer free tier.',
  },
  {
    id: 'openai',
    name: 'OpenAI',
    badge: 'INDUSTRY BENCHMARK',
    badgeColor: 'bg-blue-300 text-black',
    icon: '🤖',
    docUrl: 'https://platform.openai.com/api-keys',
    defaultModel: 'gpt-4o-mini',
    models: [
      { id: 'gpt-4o-mini', label: 'gpt-4o-mini (Fast & Economical)', tag: 'RECOMMENDED' },
      { id: 'gpt-4o', label: 'gpt-4o (High Intelligence)', tag: 'FLAGSHIP' },
      { id: 'o3-mini', label: 'o3-mini (Advanced Reasoning)', tag: 'REASONING' },
    ],
    note: 'Standard industry models. gpt-4o-mini costs fractions of a cent per tax inquiry.',
  },
  {
    id: 'gemini',
    name: 'Google Gemini',
    badge: 'GENEROUS FREE QUOTA',
    badgeColor: 'bg-purple-300 text-black',
    icon: '✨',
    docUrl: 'https://aistudio.google.com/app/apikey',
    defaultModel: 'gemini-1.5-flash',
    models: [
      { id: 'gemini-1.5-flash', label: 'gemini-1.5-flash (High Speed)', tag: 'RECOMMENDED FREE' },
      { id: 'gemini-1.5-pro', label: 'gemini-1.5-pro (Deep Context)', tag: 'HIGH ACCURACY' },
      { id: 'gemini-2.5-flash', label: 'gemini-2.5-flash (Next-Gen)', tag: 'LATEST' },
    ],
    note: 'Free tier available via Google AI Studio with up to 15 RPM at zero cost.',
  },
  {
    id: 'anthropic',
    name: 'Anthropic Claude',
    badge: 'SUPERIOR REASONING',
    badgeColor: 'bg-orange-300 text-black',
    icon: '🎭',
    docUrl: 'https://console.anthropic.com/settings/keys',
    defaultModel: 'claude-3-5-haiku-latest',
    models: [
      { id: 'claude-3-5-haiku-latest', label: 'claude-3-5-haiku-latest (Fast)', tag: 'RECOMMENDED' },
      { id: 'claude-3-5-sonnet-latest', label: 'claude-3-5-sonnet-latest', tag: 'FLAGSHIP' },
      { id: 'claude-3-7-sonnet-latest', label: 'claude-3-7-sonnet-latest', tag: 'HYBRID REASONING' },
    ],
    note: 'Top-tier statutory tax explanation formatting and structured precision.',
  },
  {
    id: 'custom',
    name: 'Custom / Local (Ollama / vLLM)',
    badge: 'SELF-HOSTED',
    badgeColor: 'bg-gray-300 text-black',
    icon: '💻',
    docUrl: 'https://ollama.com',
    baseUrl: 'http://localhost:11434/v1',
    defaultModel: 'llama3:latest',
    models: [
      { id: 'llama3:latest', label: 'llama3:latest', tag: 'OLLAMA' },
      { id: 'mistral:latest', label: 'mistral:latest', tag: 'OLLAMA' },
    ],
    note: 'Connect your local Ollama, vLLM, or private OpenAI-compatible inference proxy.',
  },
];

export const BYOKModal: React.FC<BYOKModalProps> = ({ isOpen, onClose, onConfigUpdated }) => {
  const [selectedProvider, setSelectedProvider] = useState<string>('openrouter');
  const [apiKey, setApiKey] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('openrouter/free');
  const [customModel, setCustomModel] = useState<string>('');
  const [useCustomModel, setUseCustomModel] = useState<boolean>(false);
  const [customBaseUrl, setCustomBaseUrl] = useState<string>('');
  const [storageMode, setStorageMode] = useState<'vault' | 'local'>('vault');
  const [showKey, setShowKey] = useState<boolean>(false);

  const [currentConfig, setCurrentConfig] = useState<BYOKConfig | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    latency_ms?: number;
    message: string;
    error?: string | null;
  } | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Load active BYOK status on open
  useEffect(() => {
    if (!isOpen) return;
    loadStatus();
  }, [isOpen]);

  const loadStatus = async () => {
    try {
      const config = await api.getBYOK();
      setCurrentConfig(config);
      if (config.has_key && config.provider) {
        setSelectedProvider(config.provider);
        if (config.model_name) setSelectedModel(config.model_name);
        if (config.custom_base_url) setCustomBaseUrl(config.custom_base_url);
        if (config.storage_mode) setStorageMode(config.storage_mode);
      }
    } catch {
      // Not authenticated or error
    }
  };

  if (!isOpen) return null;

  const currentPreset = PROVIDER_PRESETS.find((p) => p.id === selectedProvider) || PROVIDER_PRESETS[0];

  const handleProviderChange = (provId: string) => {
    setSelectedProvider(provId);
    const preset = PROVIDER_PRESETS.find((p) => p.id === provId) || PROVIDER_PRESETS[0];
    setSelectedModel(preset.defaultModel);
    setUseCustomModel(false);
    setCustomModel('');
    if (preset.baseUrl) {
      setCustomBaseUrl(preset.baseUrl);
    } else {
      setCustomBaseUrl('');
    }
    setValidationResult(null);
    setActionMessage(null);
  };

  const effectiveModel = useCustomModel && customModel.trim() ? customModel.trim() : selectedModel;

  const handleTestConnection = async () => {
    if (!apiKey.trim()) {
      setValidationResult({
        valid: false,
        message: 'Please enter an API key to test.',
        error: 'API key input cannot be empty.',
      });
      return;
    }

    setIsValidating(true);
    setValidationResult(null);
    setActionMessage(null);

    try {
      const res = await api.validateBYOK({
        provider: selectedProvider,
        api_key: apiKey.trim(),
        model_name: effectiveModel,
        custom_base_url: customBaseUrl.trim() || undefined,
      });
      setValidationResult(res);
    } catch (e: any) {
      setValidationResult({
        valid: false,
        message: 'Validation failed.',
        error: e.message || 'Connection test failed.',
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setActionMessage({ type: 'error', text: 'Please enter an API key before saving.' });
      return;
    }

    setIsSaving(true);
    setActionMessage(null);

    try {
      if (storageMode === 'local') {
        // Mode: Browser-Only Ephemeral Storage
        const localPayload = {
          provider: selectedProvider,
          api_key: apiKey.trim(),
          model_name: effectiveModel,
          custom_base_url: customBaseUrl.trim() || undefined,
        };
        localStorage.setItem('taxplanner_byok_local', JSON.stringify(localPayload));

        const updatedConfig: BYOKConfig = {
          has_key: true,
          provider: selectedProvider,
          model_name: effectiveModel,
          masked_key: `${apiKey.trim().slice(0, 7)}••••••••${apiKey.trim().slice(-4)}`,
          custom_base_url: customBaseUrl.trim() || null,
          is_active: true,
          storage_mode: 'local',
        };
        setCurrentConfig(updatedConfig);
        if (onConfigUpdated) onConfigUpdated(updatedConfig);
        setActionMessage({
          type: 'success',
          text: '✅ API key stored locally in browser session! Zero server persistence.',
        });
        setApiKey('');
      } else {
        // Mode: Database Encrypted Vault Storage
        // Clear any leftover local key first
        localStorage.removeItem('taxplanner_byok_local');

        const savedConfig = await api.saveBYOK({
          provider: selectedProvider,
          api_key: apiKey.trim(),
          model_name: effectiveModel,
          custom_base_url: customBaseUrl.trim() || undefined,
          validate_before_save: false, // already tested or user confirmed
        });

        setCurrentConfig(savedConfig);
        if (onConfigUpdated) onConfigUpdated(savedConfig);
        setActionMessage({
          type: 'success',
          text: `✅ API key encrypted with AES-128 and saved to your personal vault!`,
        });
        setApiKey('');
      }
    } catch (e: any) {
      setActionMessage({
        type: 'error',
        text: e.message || 'Failed to save API key.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to remove your custom API key? The system will revert to default AI.')) {
      return;
    }

    setIsSaving(true);
    try {
      await api.deleteBYOK();
      setCurrentConfig({ has_key: false, is_active: false });
      if (onConfigUpdated) onConfigUpdated({ has_key: false, is_active: false });
      setApiKey('');
      setValidationResult(null);
      setActionMessage({
        type: 'success',
        text: 'Custom key revoked. System reverted to default tier.',
      });
    } catch (e: any) {
      setActionMessage({
        type: 'error',
        text: e.message || 'Failed to remove API key.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/75 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#FAF7F2] border-4 border-black shadow-[10px_10px_0px_0px_#000] w-full max-w-3xl max-h-[92vh] flex flex-col my-auto font-mono text-xs">
        {/* Modal Header */}
        <div className="bg-[#18153B] text-white p-5 border-b-4 border-black flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#FACC15] border-2 border-black shadow-[2px_2px_0px_0px_#000]">
              <Key className="w-5 h-5 text-black stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-black text-lg uppercase font-['Space_Grotesk'] text-[#FACC15]">
                  AI SETTINGS &amp; BYOK
                </h3>
                <span className="bg-[#3730A3] text-white text-[10px] px-2 py-0.5 border border-white font-mono">
                  ENTERPRISE VAULT
                </span>
              </div>
              <p className="text-[11px] text-gray-300 mt-0.5">
                Bring Your Own Key: Connect your personal AI account for unrestricted high-speed tax advisory.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 bg-[#FAF7F2] hover:bg-gray-200 text-black border-2 border-black shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 bg-[#FFFDF9]">
          {/* Current Status Bar */}
          <div className="bg-[#FAF7F2] border-2 border-black p-3.5 shadow-[3px_3px_0px_0px_#000] flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div
                className={`w-3 h-3 rounded-full ${
                  currentConfig?.has_key ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'
                }`}
              />
              <div>
                <span className="font-black uppercase text-sm text-[#18153B]">
                  CURRENT AI TIER:{' '}
                  {currentConfig?.has_key
                    ? `BYOK (${currentConfig.provider?.toUpperCase()} - ${currentConfig.model_name})`
                    : 'DEFAULT SYSTEM HOST'}
                </span>
                {currentConfig?.has_key && (
                  <p className="text-[11px] text-gray-600 font-bold">
                    Key: <span className="font-mono text-black">{currentConfig.masked_key}</span> • Storage:{' '}
                    <span className="uppercase text-[#3730A3] font-black">
                      {currentConfig.storage_mode === 'local' ? 'Browser Only' : 'Encrypted Vault'}
                    </span>
                  </p>
                )}
              </div>
            </div>

            {currentConfig?.has_key && (
              <button
                onClick={handleDelete}
                disabled={isSaving}
                className="flex items-center gap-1.5 bg-red-100 hover:bg-red-200 text-red-900 border-2 border-black px-2.5 py-1 font-bold text-[11px] uppercase cursor-pointer"
                title="Revoke your custom key"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>REVOKE KEY</span>
              </button>
            )}
          </div>

          {/* Provider Selector Grid */}
          <div>
            <label className="block text-[11px] font-black uppercase text-gray-800 mb-2">
              1. CHOOSE YOUR AI PROVIDER:
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {PROVIDER_PRESETS.map((preset) => {
                const isSelected = selectedProvider === preset.id;
                return (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => handleProviderChange(preset.id)}
                    className={`p-3 border-2 border-black text-left cursor-pointer transition-all flex flex-col justify-between ${
                      isSelected
                        ? 'bg-[#FACC15] shadow-[3px_3px_0px_0px_#000] scale-[1.02]'
                        : 'bg-[#FAF7F2] hover:bg-yellow-50 shadow-[2px_2px_0px_0px_#000]'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-base">{preset.icon}</span>
                        <span className={`text-[9px] font-black px-1.5 py-0.5 border border-black uppercase ${preset.badgeColor}`}>
                          {preset.badge}
                        </span>
                      </div>
                      <div className="font-black text-xs text-[#18153B]">{preset.name}</div>
                    </div>
                  </button>
                );
              })}
            </div>
            <p className="text-[11px] text-gray-600 mt-2 font-medium">
              💡 {currentPreset.note}{' '}
              <a
                href={currentPreset.docUrl}
                target="_blank"
                rel="noreferrer"
                className="font-bold text-[#3730A3] underline inline-flex items-center gap-1 hover:text-black"
              >
                Get API key from {currentPreset.name} <ExternalLink className="w-3 h-3" />
              </a>
            </p>
          </div>

          {/* Model Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-black uppercase text-gray-800 mb-1">
                2. MODEL ID:
              </label>
              {!useCustomModel ? (
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-white border-2 border-black p-2.5 font-mono font-bold text-xs shadow-[2px_2px_0px_0px_#000] outline-none"
                >
                  {currentPreset.models.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label} ({m.tag})
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  placeholder="e.g. meta-llama/llama-3.3-70b-instruct"
                  value={customModel}
                  onChange={(e) => setCustomModel(e.target.value)}
                  className="w-full bg-white border-2 border-black p-2 font-mono font-bold text-xs shadow-[2px_2px_0px_0px_#000] outline-none"
                />
              )}
              <div className="mt-1">
                <button
                  type="button"
                  onClick={() => setUseCustomModel(!useCustomModel)}
                  className="text-[10px] text-[#3730A3] underline font-bold cursor-pointer"
                >
                  {useCustomModel ? '← Pick from recommended models' : 'Custom model identifier →'}
                </button>
              </div>
            </div>

            {/* Custom Base URL (shown for custom or optional override) */}
            <div>
              <label className="block text-[11px] font-black uppercase text-gray-800 mb-1">
                ENDPOINT URL {selectedProvider === 'custom' ? '(REQUIRED)' : '(OPTIONAL PROXY)'}:
              </label>
              <input
                type="text"
                placeholder={currentPreset.baseUrl || 'https://api.openai.com/v1'}
                value={customBaseUrl}
                onChange={(e) => setCustomBaseUrl(e.target.value)}
                className="w-full bg-white border-2 border-black p-2 font-mono text-xs font-bold shadow-[2px_2px_0px_0px_#000] outline-none"
              />
              <span className="text-[10px] text-gray-500 block mt-1">
                Default: {currentPreset.baseUrl || 'Official provider cloud'}
              </span>
            </div>
          </div>

          {/* API Key Input */}
          <div>
            <label className="block text-[11px] font-black uppercase text-gray-800 mb-1">
              3. PASTE API KEY:
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                placeholder={`e.g. ${
                  selectedProvider === 'anthropic'
                    ? 'sk-ant-api03-...'
                    : selectedProvider === 'openrouter'
                    ? 'sk-or-v1-...'
                    : 'sk-proj-...'
                }`}
                value={apiKey}
                onChange={(e) => {
                  setApiKey(e.target.value);
                  setValidationResult(null);
                  setActionMessage(null);
                }}
                className="w-full bg-white border-2 border-black p-2.5 pr-10 font-mono font-bold text-xs shadow-[2px_2px_0px_0px_#000] outline-none"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2.5 top-2.5 text-gray-600 hover:text-black cursor-pointer"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Storage Mode Selector */}
          <div>
            <label className="block text-[11px] font-black uppercase text-gray-800 mb-2">
              4. STORAGE &amp; PRIVACY PREFERENCE:
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <label
                onClick={() => setStorageMode('vault')}
                className={`p-3 border-2 border-black flex items-start gap-2.5 cursor-pointer transition-all ${
                  storageMode === 'vault'
                    ? 'bg-emerald-50 border-emerald-900 shadow-[3px_3px_0px_0px_#000]'
                    : 'bg-white hover:bg-gray-50'
                }`}
              >
                <Lock className="w-4 h-4 text-emerald-700 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-black text-xs text-black uppercase">
                    🛡️ ENCRYPTED DATABASE VAULT (RECOMMENDED)
                  </div>
                  <p className="text-[10px] text-gray-600 leading-relaxed mt-0.5">
                    Encrypted with AES-128-CBC Fernet and tied to your user ID. Accessible across all your devices and sessions.
                  </p>
                </div>
              </label>

              <label
                onClick={() => setStorageMode('local')}
                className={`p-3 border-2 border-black flex items-start gap-2.5 cursor-pointer transition-all ${
                  storageMode === 'local'
                    ? 'bg-purple-50 border-purple-900 shadow-[3px_3px_0px_0px_#000]'
                    : 'bg-white hover:bg-gray-50'
                }`}
              >
                <HardDrive className="w-4 h-4 text-[#3730A3] flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-black text-xs text-black uppercase">
                    🔒 BROWSER ONLY (ZERO SERVER STORAGE)
                  </div>
                  <p className="text-[10px] text-gray-600 leading-relaxed mt-0.5">
                    Saved strictly in this browser’s localStorage. Sent via HTTPS request headers on each prompt; never written to database.
                  </p>
                </div>
              </label>
            </div>
          </div>

          {/* Validation Status Box */}
          {validationResult && (
            <div
              className={`p-3.5 border-2 border-black font-mono text-xs flex items-start gap-2.5 shadow-[3px_3px_0px_0px_#000] ${
                validationResult.valid ? 'bg-emerald-100 text-emerald-950' : 'bg-red-100 text-red-950'
              }`}
            >
              {validationResult.valid ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-700 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-700 flex-shrink-0" />
              )}
              <div>
                <span className="font-black uppercase block">
                  {validationResult.valid ? 'AUTHENTICATION SUCCESSFUL' : 'AUTHENTICATION FAILED'}
                </span>
                <span className="font-medium">{validationResult.message}</span>
                {validationResult.error && (
                  <p className="text-[11px] text-red-900 mt-1 font-bold">
                    Error details: {validationResult.error}
                  </p>
                )}
                {validationResult.latency_ms && (
                  <span className="text-[10px] font-bold block mt-1 text-emerald-800">
                    Roundtrip Latency: {validationResult.latency_ms} ms
                  </span>
                )}
              </div>
            </div>
          )}

          {actionMessage && (
            <div
              className={`p-3 border-2 border-black font-mono text-xs font-bold shadow-[2px_2px_0px_0px_#000] ${
                actionMessage.type === 'success' ? 'bg-emerald-200 text-emerald-950' : 'bg-red-200 text-red-950'
              }`}
            >
              {actionMessage.text}
            </div>
          )}

          {/* Zero Arithmetic Guarantee Callout */}
          <div className="bg-[#FAF7F2] border-2 border-black p-3 text-[11px] text-gray-700 leading-relaxed">
            <span className="font-black text-black uppercase flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-[#3730A3]" /> ZERO ARITHMETIC GUARANTEE:
            </span>
            Custom BYOK models are strictly restricted to natural language elicitation and explanations. All tax calculations, standard deductions, and slab rates are calculated by our verified deterministic Python engine.
          </div>
        </div>

        {/* Modal Footer Strip */}
        <div className="bg-[#FAF7F2] p-4 border-t-4 border-black flex flex-wrap items-center justify-between gap-3 flex-shrink-0">
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={isValidating || !apiKey.trim()}
            className="flex items-center gap-2 bg-white hover:bg-gray-100 disabled:opacity-50 text-black border-2 border-black px-4 py-2.5 font-mono font-black uppercase text-xs shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
          >
            {isValidating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>TESTING CONNECTION...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 text-[#FACC15] fill-black stroke-black" />
                <span>TEST CONNECTION</span>
              </>
            )}
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="bg-white hover:bg-gray-100 text-black px-4 py-2.5 border-2 border-black font-mono font-bold uppercase text-xs cursor-pointer"
            >
              CLOSE
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving || !apiKey.trim()}
              className="flex items-center gap-2 bg-[#FACC15] hover:bg-yellow-400 disabled:opacity-50 text-black border-2 border-black px-5 py-2.5 font-mono font-black uppercase text-xs shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isSaving ? 'SAVING...' : 'SAVE & APPLY KEY'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
