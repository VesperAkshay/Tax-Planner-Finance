import React from 'react';
import ReactMarkdown from 'react-markdown';
import { AlertTriangle } from 'lucide-react';

interface ChatMessageRendererProps {
  content: string;
  isUser: boolean;
}

/**
 * Normalizes raw LLM markdown output to ensure clean spacing,
 * header line breaks, and list formatting even when the model emits compressed text.
 */
function normalizeMarkdown(text: string): string {
  if (!text) return '';

  let normalized = text;

  // Ensure double newlines before bold section headers like **Your Verified Numbers** or **Filing Steps**
  // when preceded by text without newlines
  normalized = normalized.replace(/([^\n])\s+(\*\*([A-Z][A-Za-z0-9\s–—:-]+)\*\*)/g, '$1\n\n### $3');

  // Convert standalone **Header Title** at line starts to markdown ### Header Title
  normalized = normalized.replace(/(^|\n)\*\*([A-Z][A-Za-z0-9\s–—:-]+)\*\*(\s*)/g, '$1### $2\n');

  // Ensure bullet points are on newlines
  normalized = normalized.replace(/([^\n])\s+-\s+\*\*/g, '$1\n- **');
  normalized = normalized.replace(/([^\n])\s+-\s+([A-Z])/g, '$1\n- $2');

  return normalized;
}

export const ChatMessageRenderer: React.FC<ChatMessageRendererProps> = ({ content, isUser }) => {
  if (isUser) {
    return <div className="whitespace-pre-wrap">{content}</div>;
  }

  // Check if content contains a CA disclaimer
  const disclaimerPattern = /(?:⚠️\s*)?\*{0,2}Disclaimer\*{0,2}:?\s*([\s\S]*)$/i;
  const match = content.match(disclaimerPattern);

  let mainContent = content;
  let disclaimerText: string | null = null;

  if (match) {
    mainContent = content.substring(0, match.index).trim();
    disclaimerText = match[1].replace(/^\*/, '').replace(/\*$/, '').trim();
    // Default disclaimer fallback if trimmed too aggressively
    if (!disclaimerText) {
      disclaimerText =
        'This analysis is an automated suggestion based on Income Tax Act rules (FY 2025–26). Please consult a qualified Chartered Accountant (CA) or certified tax professional for official tax filing and personalized planning.';
    }
  }

  const cleanMarkdown = normalizeMarkdown(mainContent);

  return (
    <div className="space-y-3 font-['Space_Grotesk'] text-sm leading-relaxed">
      <div className="chat-markdown-body">
        <ReactMarkdown
          components={{
            h1: ({ children }) => (
              <h1 className="text-base md:text-lg font-black uppercase text-[#18153B] mt-4 mb-2 pb-1 border-b-2 border-black">
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-sm md:text-base font-black uppercase text-[#18153B] mt-3.5 mb-1.5 pb-0.5 border-b border-black">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-xs md:text-sm font-black uppercase tracking-wider text-[#3730A3] mt-3 mb-1.5 flex items-center gap-1.5">
                <span className="inline-block w-2 h-2 bg-[#FACC15] border border-black"></span>
                {children}
              </h3>
            ),
            p: ({ children }) => <p className="my-1.5 leading-relaxed text-gray-900">{children}</p>,
            ul: ({ children }) => <ul className="my-2 space-y-1 pl-2 text-gray-900">{children}</ul>,
            ol: ({ children }) => (
              <ol className="my-2 space-y-1 pl-4 list-decimal marker:font-bold text-gray-900">{children}</ol>
            ),
            li: ({ children }) => (
              <li className="flex items-start gap-2 leading-relaxed">
                <span className="text-[#3730A3] font-bold select-none mt-0.5">•</span>
                <div className="flex-1">{children}</div>
              </li>
            ),
            strong: ({ children }) => <strong className="font-bold text-black">{children}</strong>,
            em: ({ children }) => <em className="italic text-gray-800">{children}</em>,
            code: ({ children }) => (
              <code className="bg-[#FAF7F2] text-[#3730A3] font-mono px-1.5 py-0.5 border border-black text-xs font-bold shadow-[1px_1px_0px_0px_#000]">
                {children}
              </code>
            ),
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-[#3730A3] pl-3 py-1 bg-amber-50/50 my-2 italic text-gray-800 text-xs">
                {children}
              </blockquote>
            ),
          }}
        >
          {cleanMarkdown}
        </ReactMarkdown>
      </div>

      {disclaimerText && (
        <div className="mt-3 p-3 bg-[#FEF3C7] border-2 border-black shadow-[2px_2px_0px_0px_#000] text-xs font-mono text-gray-800 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-700 flex-shrink-0 mt-0.5 stroke-[2.5]" />
          <div className="flex-1">
            <span className="font-black uppercase tracking-wider text-amber-900 block mb-0.5 text-[11px]">
              Statutory Advisory & CA Disclaimer
            </span>
            <p className="leading-snug text-amber-950 font-medium">
              {disclaimerText}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
