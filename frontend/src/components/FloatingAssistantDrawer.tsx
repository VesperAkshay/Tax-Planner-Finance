import React, { useState, useRef, useEffect } from 'react';
import {
  MessageSquareCode,
  X,
  Send,
  Bot,
  ShieldCheck,
  Maximize2,
} from 'lucide-react';
import { api } from '../api/client';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
}

interface FloatingAssistantDrawerProps {
  isOpen: boolean;
  onToggle: () => void;
  onNavigateToView?: (view: string) => void;
}

export const FloatingAssistantDrawer: React.FC<FloatingAssistantDrawerProps> = ({
  isOpen,
  onToggle,
  onNavigateToView,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "Hello! I am Mr. Planner, your statutory tax co-pilot for FY 2025–26. Ask me anything about Chapter VI-A deductions, New vs Old regime, HRA exemption rules, or offer letter restructuring.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputText.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputText('');
    setLoading(true);

    try {
      const history = [...messages, userMsg].map((m) => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text,
      }));
      const response = await api.sendChatMessage(text, history);
      const assistantMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: 'assistant',
        text: response.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: unknown) {
      const errorMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: 'assistant',
        text: e instanceof Error ? e.message : 'Failed to reach Mr. Planner. Please try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    'How does 80CCD(2) save tax in New Regime?',
    'Can I claim rent paid to parents for HRA?',
    'What is Form 12B and why does it save interest?',
  ];

  return (
    <>
      {/* ===================================================================== */}
      {/* 1. FLOATING DOCKED BUTTON TRIGGER                                     */}
      {/* ===================================================================== */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="fixed bottom-5 right-5 z-40 bg-[#18153B] hover:bg-[#252055] text-white border-3 border-black px-4 py-2.5 shadow-[5px_5px_0px_0px_#000] flex items-center gap-2 font-mono text-xs font-black uppercase tracking-wider cursor-pointer active:translate-x-0.5 active:translate-y-0.5 transition-all group"
          title="Open ambient Mr. Planner AI assistant"
        >
          <div className="relative">
            <MessageSquareCode className="w-4 h-4 text-[#FACC15]" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full animate-ping" />
          </div>
          <span className="font-['Space_Grotesk']">Ask Mr. Planner</span>
        </button>
      )}

      {/* ===================================================================== */}
      {/* 2. SLIDE-OVER ASSISTANT DRAWER                                        */}
      {/* ===================================================================== */}
      {isOpen && (
        <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[420px] md:w-[460px] bg-[#FAF7F2] border-l-4 border-black shadow-[-8px_0px_0px_0px_rgba(0,0,0,0.8)] flex flex-col font-mono text-xs animate-slide-left select-none">
          {/* Header */}
          <div className="bg-[#18153B] text-white p-3.5 border-b-3 border-black flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="bg-[#FACC15] text-black p-1 border border-black font-black">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h4 className="font-['Space_Grotesk'] font-black text-sm tracking-wide text-white">
                  Mr. Planner AI Co-Pilot
                </h4>
                <div className="flex items-center gap-1.5 text-[10px] text-gray-300">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                  <span>Statutory RAG • Zero LLM Math</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              {onNavigateToView && (
                <button
                  onClick={() => {
                    onNavigateToView('chat');
                    onToggle();
                  }}
                  className="bg-white/10 hover:bg-white/20 text-white border border-white/30 px-2 py-1 flex items-center gap-1 font-mono text-[10px] cursor-pointer"
                  title="Expand to Fullscreen AI Chat View"
                >
                  <Maximize2 className="w-3 h-3 text-[#FACC15]" />
                  <span>Full View</span>
                </button>
              )}

              <button
                onClick={onToggle}
                className="bg-white text-black hover:bg-gray-200 border-2 border-black p-1 font-bold shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 cursor-pointer"
                title="Close Assistant"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Quick Questions Carousel */}
          <div className="bg-amber-50 p-2.5 border-b-2 border-black overflow-x-auto flex gap-1.5 shrink-0">
            {quickPrompts.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                disabled={loading}
                className="bg-white hover:bg-amber-100 text-black border border-black px-2 py-1 text-[10px] font-bold shrink-0 truncate max-w-[200px] cursor-pointer shadow-[1px_1px_0px_0px_#000]"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Messages Stream */}
          <div className="flex-1 p-3 space-y-3 overflow-y-auto select-text font-sans text-xs">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'assistant' && (
                  <div className="w-6 h-6 rounded bg-[#18153B] text-[#FACC15] flex items-center justify-center shrink-0 border border-black mt-1 font-mono font-bold text-[10px]">
                    AI
                  </div>
                )}

                <div
                  className={`max-w-[85%] p-3 border-2 border-black shadow-[2px_2px_0px_0px_#000] ${
                    msg.sender === 'user'
                      ? 'bg-[#18153B] text-white font-mono text-[11px]'
                      : 'bg-white text-gray-900 leading-relaxed'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                  <span
                    className={`text-[9px] font-mono block mt-1 text-right ${
                      msg.sender === 'user' ? 'text-gray-400' : 'text-gray-500'
                    }`}
                  >
                    {msg.timestamp}
                  </span>
                </div>

                {msg.sender === 'user' && (
                  <div className="w-6 h-6 rounded bg-[#FACC15] text-black flex items-center justify-center shrink-0 border border-black mt-1 font-mono font-bold text-[10px]">
                    ME
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex gap-2 items-center text-gray-600 font-mono text-[11px] animate-pulse">
                <div className="w-6 h-6 rounded bg-[#18153B] text-[#FACC15] flex items-center justify-center border border-black font-bold text-[10px]">
                  AI
                </div>
                <div className="p-2.5 bg-white border border-black">
                  Analyzing statutory tax rules...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-3 bg-white border-t-3 border-black shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex gap-2"
            >
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Ask about 80C, 80D, HRA, NPS..."
                disabled={loading}
                className="flex-1 px-3 py-2 border-2 border-black font-mono text-xs focus:bg-amber-50 focus:outline-none"
              />
              <button
                type="submit"
                disabled={loading || !inputText.trim()}
                className="bg-[#FACC15] hover:bg-yellow-400 text-black border-2 border-black px-3 py-2 font-mono font-bold shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-50 cursor-pointer"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
