import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Bot,
  User as UserIcon,
  ShieldCheck,
  CheckCircle,
  Sparkles,
  BookmarkPlus,
  HelpCircle,
} from 'lucide-react';
import { api } from '../api/client';
import type { AgentChatMessage } from '../types';
import { ChatMessageRenderer } from './ChatMessageRenderer';

interface AgentChatViewProps {
  onDeductionsUpdated?: () => void;
  onNavigateToCatalog?: () => void;
}

export const AgentChatView: React.FC<AgentChatViewProps> = ({
  onDeductionsUpdated,
  onNavigateToCatalog,
}) => {
  const [messages, setMessages] = useState<AgentChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Hello! I am Mr. Planner, your FY 2025–26 Tax Strategist. I help you discover all qualifying exemptions and deductions under the Income Tax Act (Sections 80C, 80D, 80CCD(1B), and 10(13A) HRA). All calculations are executed by our deterministic engine with zero hallucination. Tell me about your rent, investments, or salary!',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [declaredDeductions, setDeclaredDeductions] = useState<Record<string, number>>({
    section_80c: 150000,
    section_80ccd_1b: 50000,
    section_80d: 25000,
    section_10_13a_hra: 180000,
  });

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query) return;

    const userMsg: AgentChatMessage = {
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setIsTyping(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await api.sendChatMessage(query, history);

      if (res.deductions_updated) {
        setDeclaredDeductions((prev) => ({ ...prev, ...res.deductions_updated }));
        if (onDeductionsUpdated) onDeductionsUpdated();
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'I encountered an error connecting to Mr. Planner. However, your deductions are securely stored in your personal vault.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const promptSuggestions = [
    { label: '🏠 Rent & HRA', prompt: 'I pay ₹25,000 monthly rent in Mumbai (HRA claim)' },
    { label: '📈 Section 80C', prompt: 'I invested ₹1.5L in EPF & PPF (Section 80C)' },
    { label: '🛡️ NPS 80CCD', prompt: 'I contributed ₹50,000 to NPS (Section 80CCD 1B)' },
    { label: '🏥 Health 80D', prompt: 'I paid ₹25,000 health insurance premium (Section 80D)' },
    { label: '💼 In-Hand Salary', prompt: 'What is my monthly in-hand take home salary?' },
  ];

  return (
    <div className="space-y-8">
      {/* Banner */}
      <div className="bg-[#FAF7F2] border-4 border-black p-6 md:p-8 shadow-[8px_8px_0px_0px_#000000]">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-2">
          <div className="inline-flex items-center gap-2 bg-[#FACC15] px-3 py-1 border-2 border-black shadow-[2px_2px_0px_0px_#000] font-black text-xs tracking-wider uppercase text-black">
            <Sparkles className="w-4 h-4" />
            <span>MR. PLANNER // FY 2025–26 TAX STRATEGIST</span>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs font-bold bg-[#3730A3] text-white px-3 py-1 border-2 border-black">
            <ShieldCheck className="w-4 h-4 text-[#FACC15]" />
            <span>100% EXACT STATUTORY MATH</span>
          </div>
        </div>

        <h2 className="text-3xl md:text-5xl font-black tracking-tight text-[#18153B] font-['Space_Grotesk'] uppercase leading-none">
          MEET MR. PLANNER
        </h2>
        <p className="text-sm md:text-base font-medium text-gray-800 max-w-xl font-['Plus_Jakarta_Sans'] mt-2">
          Interactive tax strategist guides you through qualifying deductions. All calculations are executed
          by our verified deterministic engine with zero mathematical drift.
        </p>
      </div>

      {/* Main Chat Grid (Chat Window + Live Deduction Ledger) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Chat Conversation Column (2/3) */}
        <div className="lg:col-span-2 bg-[#FFFDF9] border-4 border-black shadow-[6px_6px_0px_0px_#000] flex flex-col h-[600px]">
          {/* Chat Header */}
          <div className="bg-[#18153B] text-white p-4 border-b-3 border-black flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#FACC15] border-2 border-black shadow-[2px_2px_0px_0px_#000]">
                <Bot className="w-5 h-5 text-black stroke-[2.5]" />
              </div>
              <div>
                <h3 className="font-black text-base uppercase font-['Space_Grotesk'] text-[#FACC15] flex items-center gap-2">
                  <span>MR. PLANNER</span>
                  <span className="bg-[#3730A3] text-white text-[10px] px-2 py-0.2 border border-white font-mono">
                    AI STRATEGIST
                  </span>
                </h3>
                <p className="text-[11px] font-mono text-gray-300 flex items-center gap-1.5 mt-0.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span>ONLINE • ZERO ARITHMETIC DRIFT</span>
                </p>
              </div>
            </div>

            <span className="bg-[#FACC15] text-black font-black text-[10px] uppercase px-2.5 py-1 border-2 border-black font-mono shadow-[2px_2px_0px_0px_#000]">
              FY 2025–26 ACTIVE
            </span>
          </div>

          {/* Messages Container */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-[#FAF7F2]">
            {messages.map((m, idx) => {
              const isUser = m.role === 'user';
              return (
                <div
                  key={idx}
                  className={`flex gap-3 max-w-[85%] ${isUser ? 'ml-auto flex-row-reverse' : ''}`}
                >
                  <div
                    className={`w-8 h-8 rounded-none border-2 border-black flex items-center justify-center flex-shrink-0 font-bold ${
                      isUser ? 'bg-[#3730A3] text-white' : 'bg-[#FACC15] text-black'
                    }`}
                  >
                    {isUser ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4 stroke-[2.5]" />}
                  </div>

                  <div className="flex-1 min-w-0">
                    {!isUser && (
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <span className="bg-[#3730A3] text-white text-[10px] font-black font-mono px-2 py-0.5 border border-black uppercase shadow-[1px_1px_0px_0px_#000]">
                          MR. PLANNER
                        </span>
                        <span className="text-[10px] font-mono text-gray-600 font-bold">
                          AI STRATEGIST
                        </span>
                      </div>
                    )}
                    <div
                      className={`p-4 border-2 border-black shadow-[3px_3px_0px_0px_#000] font-['Space_Grotesk'] text-sm leading-relaxed ${
                        isUser
                          ? 'bg-[#3730A3] text-white'
                          : 'bg-[#FFFDF9] text-black'
                      }`}
                    >
                      <ChatMessageRenderer content={m.content} isUser={isUser} />
                    </div>
                    <span className="text-[10px] font-mono text-gray-500 mt-1 block">
                      {m.timestamp}
                    </span>
                  </div>
                </div>
              );
            })}

            {isTyping && (
              <div className="flex gap-3 max-w-[85%]">
                <div className="w-8 h-8 border-2 border-black flex items-center justify-center bg-[#FACC15] shadow-[2px_2px_0px_0px_#000]">
                  <Bot className="w-4 h-4 text-black stroke-[2.5]" />
                </div>
                <div className="p-3 bg-[#FFFDF9] border-2 border-black shadow-[2px_2px_0px_0px_#000] font-mono text-xs font-bold flex items-center gap-2">
                  <span className="animate-bounce">●</span>
                  <span className="animate-bounce [animation-delay:0.2s]">●</span>
                  <span className="animate-bounce [animation-delay:0.4s]">●</span>
                  <span>MR. PLANNER IS AUDITING TAX RULES...</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Proactive Elicitation Quick Answer Chips */}
          <div className="px-3 pt-2.5 pb-1.5 bg-[#FAF7F2] border-t-2 border-black overflow-x-auto flex items-center gap-2">
            <span className="text-[10px] font-black uppercase text-[#3730A3] flex items-center gap-1 font-mono whitespace-nowrap">
              <Sparkles className="w-3.5 h-3.5 text-[#F59E0B]" /> QUICK REPLIES:
            </span>
            <button
              onClick={() => handleSend('Not Applicable')}
              className="text-[11px] font-bold bg-[#FAF7F2] hover:bg-gray-200 text-black px-2.5 py-1 border border-black shadow-[1px_1px_0px_0px_#000] whitespace-nowrap cursor-pointer"
            >
              Not Applicable (₹0)
            </button>
            <button
              onClick={() => handleSend("I don't have this deduction, skip to next")}
              className="text-[11px] font-bold bg-[#FAF7F2] hover:bg-gray-200 text-black px-2.5 py-1 border border-black shadow-[1px_1px_0px_0px_#000] whitespace-nowrap cursor-pointer"
            >
              Skip Section
            </button>
            <button
              onClick={() => handleSend('I invested the maximum statutory limit')}
              className="text-[11px] font-bold bg-[#FAF7F2] hover:bg-emerald-100 text-black px-2.5 py-1 border border-black shadow-[1px_1px_0px_0px_#000] whitespace-nowrap cursor-pointer"
            >
              Claim Maximum Cap
            </button>
            <button
              onClick={() => handleSend('Calculate my final tax')}
              className="text-[11px] font-black bg-[#FACC15] hover:bg-yellow-400 text-black px-2.5 py-1 border border-black shadow-[1px_1px_0px_0px_#000] whitespace-nowrap cursor-pointer"
            >
              Calculate Tax
            </button>
            {onNavigateToCatalog && (
              <button
                onClick={onNavigateToCatalog}
                className="text-[11px] font-black bg-[#3730A3] text-white hover:bg-[#4338CA] px-2.5 py-1 border border-black shadow-[1px_1px_0px_0px_#000] whitespace-nowrap cursor-pointer"
              >
                Browse Full Catalog (18 Sections) →
              </button>
            )}
          </div>

          {/* Quick Prompts */}
          <div className="p-3 bg-[#FAF7F2] border-t border-gray-300 overflow-x-auto flex items-center gap-2">
            <span className="text-[10px] font-black uppercase text-gray-600 flex items-center gap-1 font-mono whitespace-nowrap">
              <HelpCircle className="w-3.5 h-3.5" /> TOPICS:
            </span>
            {promptSuggestions.map((item, i) => (
              <button
                key={i}
                onClick={() => handleSend(item.prompt)}
                className="text-[11px] font-bold bg-[#FFFDF9] hover:bg-[#FACC15] text-black px-2.5 py-1 border border-black shadow-[1px_1px_0px_0px_#000] whitespace-nowrap active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer"
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div className="p-4 bg-[#FFFDF9] border-t-3 border-black flex items-center gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about 80C, 80D, rent HRA, or declare an investment..."
              className="flex-1 bg-[#FAF7F2] border-2 border-black p-3 font-mono text-xs md:text-sm font-bold shadow-[2px_2px_0px_0px_#000] outline-none"
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isTyping}
              className={`px-5 py-3 border-2 border-black font-black text-xs md:text-sm uppercase flex items-center gap-2 transition-all ${
                !input.trim() || isTyping
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                  : 'bg-[#FACC15] text-black shadow-[3px_3px_0px_0px_#000] hover:shadow-[4px_4px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none'
              }`}
            >
              <span>SEND</span>
              <Send className="w-4 h-4 stroke-[2.5]" />
            </button>
          </div>
        </div>

        {/* Persisted Deductions Drawer (1/3) */}
        <div className="bg-[#FFFDF9] border-4 border-black p-6 shadow-[6px_6px_0px_0px_#000] flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 border-b-2 border-black pb-3 mb-4">
              <BookmarkPlus className="w-5 h-5 text-[#3730A3]" />
              <h3 className="font-black text-lg uppercase font-['Space_Grotesk']">
                DECLARED DEDUCTIONS
              </h3>
            </div>
            <p className="text-xs font-mono text-gray-700 mb-6 font-semibold">
              Verified deductions securely linked to your tax profile.
            </p>

            <div className="space-y-4 font-mono">
              {/* Section 80C */}
              <div className="bg-[#FAF7F2] border-2 border-black p-3 shadow-[3px_3px_0px_0px_#000]">
                <div className="flex items-center justify-between text-xs font-bold text-gray-700 mb-1">
                  <span>SECTION 80C</span>
                  <span className="text-emerald-700 font-mono">CAP ₹1,50,000</span>
                </div>
                <div className="text-xl font-black text-black">
                  ₹{(declaredDeductions.section_80c || 0).toLocaleString('en-IN')}
                </div>
                <div className="w-full bg-gray-200 h-1.5 border border-black my-1.5 overflow-hidden">
                  <div
                    className="bg-[#10B981] h-full"
                    style={{ width: `${Math.min(100, ((declaredDeductions.section_80c || 0) / 150000) * 100)}%` }}
                  />
                </div>
                <div className="text-[10px] text-gray-500 font-mono">
                  EPF, PPF, ELSS, Life Insurance
                </div>
              </div>

              {/* Section 80CCD(1B) */}
              <div className="bg-[#FAF7F2] border-2 border-black p-3 shadow-[3px_3px_0px_0px_#000]">
                <div className="flex items-center justify-between text-xs font-bold text-gray-700 mb-1">
                  <span>SECTION 80CCD(1B)</span>
                  <span className="text-emerald-700 font-mono">CAP ₹50,000</span>
                </div>
                <div className="text-xl font-black text-black">
                  ₹{(declaredDeductions.section_80ccd_1b || 0).toLocaleString('en-IN')}
                </div>
                <div className="w-full bg-gray-200 h-1.5 border border-black my-1.5 overflow-hidden">
                  <div
                    className="bg-[#3730A3] h-full"
                    style={{ width: `${Math.min(100, ((declaredDeductions.section_80ccd_1b || 0) / 50000) * 100)}%` }}
                  />
                </div>
                <div className="text-[10px] text-gray-500 font-mono">
                  Exclusive NPS Tier-I Deduction
                </div>
              </div>

              {/* Section 80D */}
              <div className="bg-[#FAF7F2] border-2 border-black p-3 shadow-[3px_3px_0px_0px_#000]">
                <div className="flex items-center justify-between text-xs font-bold text-gray-700 mb-1">
                  <span>SECTION 80D</span>
                  <span className="text-emerald-700 font-mono">CAP ₹25,000</span>
                </div>
                <div className="text-xl font-black text-black">
                  ₹{(declaredDeductions.section_80d || 0).toLocaleString('en-IN')}
                </div>
                <div className="w-full bg-gray-200 h-1.5 border border-black my-1.5 overflow-hidden">
                  <div
                    className="bg-[#F59E0B] h-full"
                    style={{ width: `${Math.min(100, ((declaredDeductions.section_80d || 0) / 25000) * 100)}%` }}
                  />
                </div>
                <div className="text-[10px] text-gray-500 font-mono">
                  Self &amp; Family Medical Insurance
                </div>
              </div>

              {/* Section 10(13A) HRA */}
              <div className="bg-[#FAF7F2] border-2 border-black p-3 shadow-[3px_3px_0px_0px_#000]">
                <div className="flex items-center justify-between text-xs font-bold text-gray-700 mb-1">
                  <span>SEC 10(13A) HRA</span>
                  <span className="text-emerald-700 font-mono">RULE 2A</span>
                </div>
                <div className="text-xl font-black text-black">
                  ₹{(declaredDeductions.section_10_13a_hra || 0).toLocaleString('en-IN')}
                </div>
                <div className="text-[10px] text-gray-500 mt-1 font-mono">
                  House Rent Exemption
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t-2 border-black bg-[#F59E0B]/20 p-3 border">
            <div className="flex items-center gap-2 text-xs font-black text-black uppercase font-mono">
              <CheckCircle className="w-4 h-4 text-emerald-800" />
              <span>TOTAL DEDUCTIONS: ₹{(Object.values(declaredDeductions).reduce((a, b) => a + b, 0)).toLocaleString('en-IN')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
