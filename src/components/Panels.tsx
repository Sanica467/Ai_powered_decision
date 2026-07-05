import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useState } from 'react';
import { Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, Cpu, Lightbulb, Minus, Target, TrendingUp } from 'lucide-react';
import type { AnalysisResult, BusinessProblem, Prediction, Recommendation } from '../lib/analyze';
import { HealthBadge, ScoreRing, healthColor } from './ui';

const CHART_AXIS = { stroke: '#64748b', fontSize: 11 };
const CHART_GRID = 'rgba(255,255,255,0.06)';
const TOOLTIP_STYLE = {
  backgroundColor: '#0f1528',
  border: '1px solid rgba(255,255,255,0.12)',
  borderRadius: 12,
  fontSize: 12,
  color: '#e6ebf5',
};

const PALETTE = ['#5a8cff', '#7c5cff', '#34d399', '#fbbf24', '#f87171', '#22d3ee', '#f472b6'];

function Panel({
  title,
  icon: Icon,
  children,
  className = '',
  action,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className={`card p-5 ${className}`}>
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-brand-300" />
          <h3 className="text-sm font-semibold text-white">{title}</h3>
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}

export function ExecutivePanel({ a }: { a: AnalysisResult }) {
  const { executive: ex } = a;
  return (
    <Panel title="Executive Summary" icon={Activity} className="lg:col-span-2">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
        <div className="flex items-center gap-5">
          <ScoreRing value={ex.healthScore} label="Health" sublabel="/ 100" />
          <ScoreRing
            value={ex.riskScore}
            label="Risk"
            sublabel="/ 100"
            color={ex.riskScore >= 50 ? '#f87171' : ex.riskScore >= 25 ? '#fbbf24' : '#34d399'}
          />
        </div>
        <div className="flex-1">
          <p className="text-sm leading-relaxed text-slate-300">{ex.narrative}</p>
          <div className="mt-3">
            <HealthBadge status={ex.overallHealth} />
          </div>
        </div>
      </div>
      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-bad-500/20 bg-bad-500/5 p-3">
          <p className="section-title text-bad-400/80">Major Risks</p>
          <ul className="mt-2 space-y-1.5">
            {ex.majorRisks.map((r) => (
              <li key={r} className="flex items-start gap-1.5 text-xs text-slate-300">
                <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0 text-bad-400" />
                {r}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border border-ok-500/20 bg-ok-500/5 p-3">
          <p className="section-title text-ok-400/80">Top Opportunities</p>
          <ul className="mt-2 space-y-1.5">
            {ex.topOpportunities.map((r) => (
              <li key={r} className="flex items-start gap-1.5 text-xs text-slate-300">
                <TrendingUp className="mt-0.5 h-3 w-3 shrink-0 text-ok-400" />
                {r}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border border-brand-500/20 bg-brand-500/5 p-3">
          <p className="section-title text-brand-300">Immediate Actions</p>
          <ul className="mt-2 space-y-1.5">
            {ex.immediateActions.map((r) => (
              <li key={r} className="flex items-start gap-1.5 text-xs text-slate-300">
                <Target className="mt-0.5 h-3 w-3 shrink-0 text-brand-300" />
                {r}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Panel>
  );
}

export function MetricsPanel({ a }: { a: AnalysisResult }) {
  return (
    <Panel title="Business Health" icon={Activity}>
      <div className="space-y-2.5">
        {a.metrics.length === 0 && (
          <p className="text-xs text-slate-500">No time-series metrics detected.</p>
        )}
        {a.metrics.map((m) => {
          const c = healthColor[m.status];
          const Arrow = m.trend === 'up' ? ArrowUpRight : m.trend === 'down' ? ArrowDownRight : Minus;
          const arrowColor = m.trend === 'up' ? 'text-ok-400' : m.trend === 'down' ? 'text-bad-400' : 'text-slate-500';
          return (
            <div
              key={m.name}
              className={`flex items-center justify-between rounded-xl border ${c.border} ${c.bg} px-3 py-2.5`}
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-white">{m.name}</p>
                <p className="text-xs text-slate-400">{m.detail}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="stat-num text-sm text-white">{m.value}</span>
                <Arrow className={`h-4 w-4 ${arrowColor}`} />
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

export function TrendChart({ a }: { a: AnalysisResult }) {
  if (a.trends.length === 0) return null;
  const main = a.trends[0];
  const data = main.points.map((p) => ({ label: p.label, [main.name]: p.value }));
  return (
    <Panel title={`${main.name} Trend`} icon={TrendingUp} className="lg:col-span-2">
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#5a8cff" stopOpacity={0.5} />
              <stop offset="100%" stopColor="#5a8cff" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={CHART_GRID} vertical={false} />
          <XAxis dataKey="label" tick={CHART_AXIS} axisLine={false} tickLine={false} />
          <YAxis tick={CHART_AXIS} axisLine={false} tickLine={false} width={50} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Area
            type="monotone"
            dataKey={main.name}
            stroke="#5a8cff"
            strokeWidth={2}
            fill="url(#trendGrad)"
          />
        </AreaChart>
      </ResponsiveContainer>
      <div className="mt-2 flex items-center gap-4 text-xs text-slate-400">
        <span>Start: <span className="stat-num text-slate-200">{main.first.toFixed(1)}</span></span>
        <span>Latest: <span className="stat-num text-slate-200">{main.last.toFixed(1)}</span></span>
        <span className={main.changePct >= 0 ? 'text-ok-400' : 'text-bad-400'}>
          {main.changePct >= 0 ? '+' : ''}{main.changePct.toFixed(1)}%
        </span>
      </div>
    </Panel>
  );
}

export function ForecastPanel({ a }: { a: AnalysisResult }) {
  if (a.predictions.length === 0) return null;
  return (
    <Panel title="Business Predictions" icon={Target} className="lg:col-span-2">
      <div className="space-y-4">
        {a.predictions.map((p: Prediction) => (
          <PredictionCard key={p.metric} p={p} />
        ))}
      </div>
    </Panel>
  );
}

function PredictionCard({ p }: { p: Prediction }) {
  const data = p.forecast.map((f) => ({ label: f.label, value: f.value }));
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3">
      <div className="mb-2 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-white">{p.metric}</p>
          <p className="text-xs text-slate-400">{p.summary}</p>
        </div>
        <div className="flex items-center gap-2">
          <HealthBadge status={p.riskLevel} />
          <span className="chip text-slate-300">conf. {p.confidence.toFixed(0)}%</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={120}>
        <LineChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={CHART_GRID} vertical={false} />
          <XAxis dataKey="label" tick={CHART_AXIS} axisLine={false} tickLine={false} />
          <YAxis tick={CHART_AXIS} axisLine={false} tickLine={false} width={48} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Line type="monotone" dataKey="value" stroke="#7c5cff" strokeWidth={2} dot={{ r: 3, fill: '#7c5cff' }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CategoryPanel({ a }: { a: AnalysisResult }) {
  if (a.categoryBreakdown.length === 0) return null;
  const data = a.categoryBreakdown.map((c) => ({ name: c.category, value: c.value }));
  return (
    <Panel title={`Breakdown by ${data[0] ? 'Category' : 'Segment'}`} icon={Activity}>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={CHART_GRID} horizontal={false} />
          <XAxis type="number" tick={CHART_AXIS} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="name"
            tick={CHART_AXIS}
            axisLine={false}
            tickLine={false}
            width={90}
          />
          <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Panel>
  );
}

export function ProblemsPanel({ a }: { a: AnalysisResult }) {
  return (
    <Panel title="Detected Problems" icon={AlertTriangle} className="lg:col-span-2">
      {a.problems.length === 0 ? (
        <p className="text-sm text-slate-400">No significant business problems detected.</p>
      ) : (
        <div className="space-y-3">
          {a.problems.map((p: BusinessProblem) => (
            <ProblemCard key={p.id} p={p} />
          ))}
        </div>
      )}
    </Panel>
  );
}

function ProblemCard({ p }: { p: BusinessProblem }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3.5">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-start justify-between gap-3 text-left"
      >
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-white">{p.name}</p>
            <HealthBadge status={p.severity} />
          </div>
          <p className="mt-1 text-xs text-slate-400">
            <span className="text-slate-500">Area:</span> {p.affectedArea} ·{' '}
            <span className="text-slate-500">Impact:</span> {p.businessImpact}
          </p>
        </div>
        <span className="chip text-slate-300 shrink-0">conf. {p.confidence.toFixed(0)}%</span>
      </button>
      {open && (
        <div className="mt-3 border-t border-white/10 pt-3 animate-fade-up">
          <p className="section-title mb-2">Root Cause Analysis</p>
          <div className="space-y-2">
            {p.rootCauses.map((c, i) => (
              <div key={i} className="rounded-lg bg-white/[0.03] p-2.5">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium text-slate-200">{c.cause}</p>
                  <span className="stat-num text-xs text-brand-300">{c.importance}</span>
                </div>
                <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand-500 to-accent-500"
                    style={{ width: `${c.importance}%` }}
                  />
                </div>
                <p className="mt-1.5 text-[11px] text-slate-500">{c.evidence}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      <p className="mt-2 text-[11px] text-slate-500">{open ? 'Tap to collapse' : 'Tap to view root causes'}</p>
    </div>
  );
}

export function ModelPanel({ a }: { a: AnalysisResult }) {
  const m = a.model;
  return (
    <Panel title="Model Performance" icon={Cpu}>
      <div className="mb-3">
        <p className="text-sm font-semibold text-white">{m.name}</p>
        <p className="text-xs text-slate-400">{m.taskType}</p>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <Metric label="Accuracy" value={`${m.accuracy.toFixed(1)}%`} />
        <Metric label="R² Score" value={m.r2.toFixed(2)} />
        <Metric label="RMSE" value={m.rmse.toFixed(2)} />
        <Metric label="MAE" value={m.mae.toFixed(2)} />
      </div>
      {m.featureImportance.length > 0 && (
        <div className="mt-4">
          <p className="section-title mb-2">Feature Importance</p>
          <div className="space-y-1.5">
            {m.featureImportance.map((f) => (
              <div key={f.feature}>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300">{f.feature}</span>
                  <span className="stat-num text-slate-400">{f.importance}%</span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-accent-500 to-brand-500"
                    style={{ width: `${f.importance}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Panel>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.03] p-2.5">
      <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className="stat-num mt-0.5 text-base text-white">{value}</p>
    </div>
  );
}

export function RecommendationsPanel({ a }: { a: AnalysisResult }) {
  return (
    <Panel title="Business Recommendations" icon={Lightbulb} className="lg:col-span-2">
      {a.recommendations.length === 0 ? (
        <p className="text-sm text-slate-400">No recommendations — business is operating well.</p>
      ) : (
        <div className="space-y-2.5">
          {a.recommendations.map((r: Recommendation, i) => (
            <RecommendationCard key={i} r={r} />
          ))}
        </div>
      )}
    </Panel>
  );
}

function RecommendationCard({ r }: { r: Recommendation }) {
  const priorityColor =
    r.priority === 'High'
      ? 'border-bad-500/30 bg-bad-500/5 text-bad-400'
      : r.priority === 'Medium'
        ? 'border-warn-500/30 bg-warn-500/5 text-warn-400'
        : 'border-slate-500/30 bg-slate-500/5 text-slate-300';
  const diffColor =
    r.difficulty === 'Easy'
      ? 'text-ok-400'
      : r.difficulty === 'Medium'
        ? 'text-warn-400'
        : 'text-bad-400';
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs text-slate-500">For: {r.issue}</p>
          <p className="mt-1 text-sm font-medium text-white">{r.action}</p>
        </div>
        <span className={`chip shrink-0 ${priorityColor}`}>{r.priority}</span>
      </div>
      <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
        <span>Impact: <span className="text-slate-200">{r.expectedImpact}</span></span>
        <span>Est. gain: <span className="text-ok-400">{r.estimatedImprovement}</span></span>
        <span>Difficulty: <span className={diffColor}>{r.difficulty}</span></span>
      </div>
    </div>
  );
}

export function CorrelationPanel({ a }: { a: AnalysisResult }) {
  if (a.correlationInsights.length === 0) return null;
  return (
    <Panel title="Statistical Insights" icon={Activity}>
      <ul className="space-y-2">
        {a.correlationInsights.map((c) => (
          <li key={c} className="flex items-start gap-2 text-xs text-slate-300">
            <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-brand-400" />
            {c}
          </li>
        ))}
      </ul>
    </Panel>
  );
}

export function ModelComparisonChart({ a }: { a: AnalysisResult }) {
  const data = a.model.compared.map((c) => ({ name: c.name, R2: c.r2 }));
  return (
    <Panel title="Model Comparison" icon={Cpu}>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={CHART_GRID} vertical={false} />
          <XAxis dataKey="name" tick={CHART_AXIS} axisLine={false} tickLine={false} interval={0} angle={-15} textAnchor="end" height={50} />
          <YAxis tick={CHART_AXIS} axisLine={false} tickLine={false} width={40} domain={[0, 1]} />
          <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar dataKey="R2" radius={[6, 6, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Panel>
  );
}

export function CategoryPiePanel({ a }: { a: AnalysisResult }) {
  if (a.categoryBreakdown.length === 0) return null;
  const data = a.categoryBreakdown.slice(0, 6).map((c) => ({ name: c.category, value: c.value }));
  return (
    <Panel title="Share of Total" icon={Activity}>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={45}
            outerRadius={80}
            paddingAngle={2}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={PALETTE[i % PALETTE.length]} stroke="rgba(11,16,32,0.8)" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
        </PieChart>
      </ResponsiveContainer>
    </Panel>
  );
}
