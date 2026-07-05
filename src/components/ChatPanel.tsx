import { useEffect, useRef, useState } from 'react';
import { Send, Sparkles, User } from 'lucide-react';
import { answerQuestion, SUGGESTED_QUESTIONS, type ChatMessage } from '../lib/chat';
import type { AnalysisResult } from '../lib/analyze';
import type { DatasetProfile } from '../lib/dataset';

interface Props {
  profile: DatasetProfile;
  analysis: AnalysisResult;
}

export default function ChatPanel({ profile, analysis }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: `I've finished analyzing your dataset. Ask me anything — for example, why profits are decreasing, which segments to discontinue, or what to prioritize.`,
      ts: Date.now(),
    },
  ]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, typing]);

  const send = (text: string) => {
    const q = text.trim();
    if (!q || typing) return;
    const userMsg: ChatMessage = { role: 'user', content: q, ts: Date.now() };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setTyping(true);
    const reply = answerQuestion(q, profile, analysis);
    window.setTimeout(() => {
      setMessages((m) => [...m, { role: 'assistant', content: reply, ts: Date.now() }]);
      setTyping(false);
    }, 450 + Math.random() * 400);
  };

  return (
    <div className="card flex h-[560px] flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3">
        <div className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-brand-500 to-accent-500">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">Conversational AI</h3>
          <p className="text-[11px] text-slate-400">Ask questions about your data</p>
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex gap-2.5 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`grid h-7 w-7 shrink-0 place-items-center rounded-lg ${
                m.role === 'user'
                  ? 'bg-white/10'
                  : 'bg-gradient-to-br from-brand-500 to-accent-500'
              }`}
            >
              {m.role === 'user' ? (
                <User className="h-4 w-4 text-slate-200" />
              ) : (
                <Sparkles className="h-4 w-4 text-white" />
              )}
            </div>
            <div
              className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
                m.role === 'user'
                  ? 'bg-brand-500/15 text-slate-100'
                  : 'bg-white/[0.04] text-slate-200 ring-1 ring-white/10'
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {typing && (
          <div className="flex gap-2.5">
            <div className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-brand-500 to-accent-500">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <div className="flex items-center gap-1 rounded-2xl bg-white/[0.04] px-4 py-3 ring-1 ring-white/10">
              <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-brand-400" style={{ animationDelay: '0ms' }} />
              <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-brand-400" style={{ animationDelay: '200ms' }} />
              <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-brand-400" style={{ animationDelay: '400ms' }} />
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-white/10 p-3">
        <div className="mb-2 flex flex-wrap gap-1.5">
          {SUGGESTED_QUESTIONS.slice(0, 4).map((q) => (
            <button
              key={q}
              onClick={() => send(q)}
              disabled={typing}
              className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] text-slate-300 transition hover:border-brand-400/40 hover:bg-brand-500/10 hover:text-brand-200 disabled:opacity-50"
            >
              {q}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="flex items-center gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your data…"
            className="input flex-1"
            disabled={typing}
          />
          <button type="submit" disabled={typing || !input.trim()} className="btn-primary px-3.5 py-2.5">
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
