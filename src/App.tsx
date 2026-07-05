import { useCallback, useState } from 'react';
import {
  Database,
  FileDown,
  LayoutDashboard,
  MessageSquare,
  Sparkles,
  Upload as UploadIcon,
  X,
} from 'lucide-react';
import UploadScreen from './components/UploadScreen';
import WorkflowTimeline from './components/WorkflowTimeline';
import ChatPanel from './components/ChatPanel';
import {
  CategoryPanel,
  CategoryPiePanel,
  CorrelationPanel,
  ExecutivePanel,
  ForecastPanel,
  MetricsPanel,
  ModelComparisonChart,
  ModelPanel,
  ProblemsPanel,
  RecommendationsPanel,
  TrendChart,
} from './components/Panels';
import { analyze, type AnalysisResult } from './lib/analyze';
import { parseFile, type DatasetProfile } from './lib/dataset';
import { generateReport } from './lib/report';

type View = 'overview' | 'problems' | 'predictions' | 'recommendations' | 'chat';

const NAV: { id: View; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'problems', label: 'Problems & Causes', icon: Database },
  { id: 'predictions', label: 'Predictions', icon: Sparkles },
  { id: 'recommendations', label: 'Recommendations', icon: FileDown },
  { id: 'chat', label: 'Ask AI', icon: MessageSquare },
];

export default function App() {
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>('overview');
  const [workflowDone, setWorkflowDone] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleFile = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    setWorkflowDone(false);
    try {
      const p = await parseFile(file);
      if (p.rowCount === 0) throw new Error('The file appears to be empty.');
      const a = analyze(p);
      setProfile(p);
      setAnalysis(a);
      setView('overview');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to parse file.');
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = () => {
    setProfile(null);
    setAnalysis(null);
    setError(null);
    setWorkflowDone(false);
  };

  if (!profile || !analysis) {
    return <UploadScreen onFile={handleFile} loading={loading} error={error} />;
  }

  return (
    <div className="relative min-h-screen bg-ink-950 bg-ai-radial">
      <div className="pointer-events-none fixed inset-0 bg-grid-faint [background-size:40px_40px] opacity-30" />

      {/* Mobile sidebar toggle */}
      <button
        onClick={() => setSidebarOpen(true)}
        className="fixed left-4 top-4 z-40 grid h-10 w-10 place-items-center rounded-xl border border-white/10 bg-ink-900/80 backdrop-blur lg:hidden"
      >
        <LayoutDashboard className="h-5 w-5 text-white" />
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 transform border-r border-white/10 bg-ink-900/80 backdrop-blur-xl transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between px-5 py-5">
            <div className="flex items-center gap-2.5">
              <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-accent-500 shadow-glow">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <p className="text-sm font-bold text-white">DecisionAI</p>
                <p className="text-[10px] text-slate-400">AI Business Analyst</p>
              </div>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-white/5 lg:hidden"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <nav className="flex-1 space-y-1 px-3">
            {NAV.map((n) => (
              <button
                key={n.id}
                onClick={() => {
                  setView(n.id);
                  setSidebarOpen(false);
                }}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  view === n.id
                    ? 'bg-gradient-to-r from-brand-500/20 to-accent-500/10 text-white ring-1 ring-brand-500/30'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                }`}
              >
                <n.icon className="h-4 w-4" />
                {n.label}
              </button>
            ))}
          </nav>

          <div className="space-y-2 px-3 py-4">
            <button
              onClick={() => generateReport(profile, analysis, profile.summary.split('File analyzed: ')[1] ?? 'dataset')}
              className="btn-primary w-full"
            >
              <FileDown className="h-4 w-4" />
              Export PDF Report
            </button>
            <button onClick={reset} className="btn-ghost w-full">
              <UploadIcon className="h-4 w-4" />
              New Dataset
            </button>
          </div>
        </div>
      </aside>

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main */}
      <main className="lg:pl-64">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          {/* Top bar */}
          <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="sm:pl-12 lg:pl-0">
              <h1 className="text-xl font-bold text-white sm:text-2xl">
                {view === 'overview' && 'Executive Dashboard'}
                {view === 'problems' && 'Problems & Root Causes'}
                {view === 'predictions' && 'Predictions & Forecasts'}
                {view === 'recommendations' && 'Business Recommendations'}
                {view === 'chat' && 'Ask the AI Analyst'}
              </h1>
              <p className="mt-0.5 text-xs text-slate-400">
                {profile.rowCount.toLocaleString()} rows · {profile.colCount} columns ·{' '}
                {profile.numericCols.length} numeric · {profile.categoricalCols.length} categorical
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => generateReport(profile, analysis, profile.summary.split('File analyzed: ')[1] ?? 'dataset')}
                className="btn-ghost hidden sm:inline-flex"
              >
                <FileDown className="h-4 w-4" />
                Export Report
              </button>
            </div>
          </div>

          {/* Dataset summary banner */}
          <div className="mb-6 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3">
            <p className="text-sm leading-relaxed text-slate-300">{profile.summary}</p>
          </div>

          {/* Content */}
          {!workflowDone ? (
            <div className="mx-auto max-w-md py-10">
              <WorkflowTimeline active onComplete={() => setWorkflowDone(true)} />
            </div>
          ) : (
            <div className="animate-fade-up">
              {view === 'overview' && (
                <div className="grid gap-4 lg:grid-cols-3">
                  <ExecutivePanel a={analysis} />
                  <MetricsPanel a={analysis} />
                  <TrendChart a={analysis} />
                  <ModelPanel a={analysis} />
                  <CategoryPanel a={analysis} />
                  <CorrelationPanel a={analysis} />
                  <ModelComparisonChart a={analysis} />
                  <CategoryPiePanel a={analysis} />
                </div>
              )}

              {view === 'problems' && (
                <div className="grid gap-4 lg:grid-cols-3">
                  <div className="lg:col-span-2">
                    <ProblemsPanel a={analysis} />
                  </div>
                  <div className="space-y-4">
                    <MetricsPanel a={analysis} />
                    <CorrelationPanel a={analysis} />
                  </div>
                </div>
              )}

              {view === 'predictions' && (
                <div className="grid gap-4 lg:grid-cols-3">
                  <ForecastPanel a={analysis} />
                  <ModelPanel a={analysis} />
                  <ModelComparisonChart a={analysis} />
                  <TrendChart a={analysis} />
                  <CategoryPanel a={analysis} />
                </div>
              )}

              {view === 'recommendations' && (
                <div className="grid gap-4 lg:grid-cols-3">
                  <div className="lg:col-span-2">
                    <RecommendationsPanel a={analysis} />
                  </div>
                  <div className="space-y-4">
                    <div className="card p-5">
                      <p className="section-title">Executive Snapshot</p>
                      <p className="mt-2 text-sm leading-relaxed text-slate-300">
                        {analysis.executive.narrative}
                      </p>
                      <div className="mt-3 space-y-2">
                        <p className="section-title text-bad-400/80">Major Risks</p>
                        {analysis.executive.majorRisks.map((r) => (
                          <p key={r} className="text-xs text-slate-300">• {r}</p>
                        ))}
                      </div>
                      <div className="mt-3 space-y-2">
                        <p className="section-title text-ok-400/80">Opportunities</p>
                        {analysis.executive.topOpportunities.map((r) => (
                          <p key={r} className="text-xs text-slate-300">• {r}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {view === 'chat' && (
                <div className="mx-auto max-w-3xl">
                  <ChatPanel profile={profile} analysis={analysis} />
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
