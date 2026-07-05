import { useRef, useState } from 'react';
import { Upload, FileSpreadsheet, Sparkles, Brain, TrendingUp, AlertTriangle, MessageSquare, FileDown } from 'lucide-react';

interface Props {
  onFile: (file: File) => void;
  loading: boolean;
  error: string | null;
}

const FEATURES = [
  { icon: Brain, title: 'Autonomous Analysis', desc: 'Detects problems, root causes & patterns with no configuration.' },
  { icon: TrendingUp, title: 'Predictive Forecasting', desc: 'Selects the best ML model and projects your next quarter.' },
  { icon: AlertTriangle, title: 'Risk Detection', desc: 'Flags critical metrics and quantifies business impact.' },
  { icon: MessageSquare, title: 'Conversational Insights', desc: 'Ask questions about your data in plain English.' },
];

export default function UploadScreen({ onFile, loading, error }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onFile(f);
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-ink-950 bg-ai-radial">
      <div className="pointer-events-none absolute inset-0 bg-grid-faint [background-size:40px_40px] opacity-40" />
      <div className="relative mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-6 py-16">
        {/* Logo */}
        <div className="mb-8 flex items-center gap-3 animate-fade-up">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 shadow-glow">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">DecisionAI</h1>
            <p className="text-xs text-slate-400">AI Business Analyst & Data Scientist</p>
          </div>
        </div>

        {/* Hero */}
        <div className="mb-10 text-center animate-fade-up" style={{ animationDelay: '60ms' }}>
          <h2 className="mx-auto max-w-2xl text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl">
            Your autonomous <span className="text-gradient">AI business consultant</span>
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-slate-400">
            Upload a dataset. DecisionAI independently analyzes it, discovers business problems,
            predicts outcomes, and recommends actions — like hiring an experienced analyst.
          </p>
        </div>

        {/* Dropzone */}
        <div
          className="w-full max-w-xl animate-fade-up"
          style={{ animationDelay: '120ms' }}
          onDragOver={(e) => {
            e.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={handleDrop}
        >
          <button
            onClick={() => inputRef.current?.click()}
            disabled={loading}
            className={`group relative flex w-full flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-all duration-300 ${
              drag
                ? 'border-brand-400 bg-brand-500/10 shadow-glow'
                : 'border-white/15 bg-white/[0.03] hover:border-brand-400/50 hover:bg-white/[0.05]'
            }`}
          >
            {loading ? (
              <>
                <div className="h-12 w-12 animate-spin-slow rounded-full border-2 border-brand-400/30 border-t-brand-400" />
                <div>
                  <p className="text-sm font-semibold text-white">Analyzing your dataset…</p>
                  <p className="mt-1 text-xs text-slate-400">Running the AI agent workflow</p>
                </div>
              </>
            ) : (
              <>
                <div className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-brand-500/20 to-accent-500/20 ring-1 ring-white/10 transition group-hover:scale-105">
                  <Upload className="h-7 w-7 text-brand-300" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">
                    Drop your dataset here, or <span className="text-brand-300">browse</span>
                  </p>
                  <p className="mt-1 flex items-center justify-center gap-2 text-xs text-slate-400">
                    <FileSpreadsheet className="h-3.5 w-3.5" /> CSV or Excel · up to ~50k rows
                  </p>
                </div>
              </>
            )}
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx,.xls,text/csv"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onFile(f);
            }}
          />
          {error && (
            <p className="mt-3 rounded-lg border border-bad-500/30 bg-bad-500/10 px-3 py-2 text-center text-xs text-bad-400">
              {error}
            </p>
          )}
        </div>

        {/* Features */}
        <div className="mt-14 grid w-full max-w-4xl grid-cols-2 gap-4 sm:grid-cols-4 animate-fade-up" style={{ animationDelay: '180ms' }}>
          {FEATURES.map((f) => (
            <div key={f.title} className="card p-4">
              <f.icon className="h-5 w-5 text-brand-300" />
              <h3 className="mt-3 text-sm font-semibold text-white">{f.title}</h3>
              <p className="mt-1 text-xs leading-relaxed text-slate-400">{f.desc}</p>
            </div>
          ))}
        </div>

        {/* Workflow hint */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-500 animate-fade-up" style={{ animationDelay: '240ms' }}>
          {['Upload', 'Understand', 'Detect Problems', 'Root Cause', 'Predict', 'Recommend', 'Report'].map((s, i) => (
            <span key={s} className="flex items-center gap-2">
              <span className="chip">{s}</span>
              {i < 6 && <span className="text-slate-600">→</span>}
            </span>
          ))}
        </div>

        <div className="mt-8 flex items-center gap-2 text-xs text-slate-500">
          <FileDown className="h-3.5 w-3.5" />
          Downloadable PDF executive report included
        </div>
      </div>
    </div>
  );
}
