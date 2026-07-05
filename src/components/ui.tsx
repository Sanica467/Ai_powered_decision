import type { Health } from '../lib/analyze';

export const healthColor: Record<Health, { text: string; bg: string; border: string; dot: string; label: string }> = {
  healthy: {
    text: 'text-ok-400',
    bg: 'bg-ok-500/10',
    border: 'border-ok-500/30',
    dot: 'bg-ok-400',
    label: 'Healthy',
  },
  attention: {
    text: 'text-warn-400',
    bg: 'bg-warn-500/10',
    border: 'border-warn-500/30',
    dot: 'bg-warn-400',
    label: 'Needs Attention',
  },
  critical: {
    text: 'text-bad-400',
    bg: 'bg-bad-500/10',
    border: 'border-bad-500/30',
    dot: 'bg-bad-400',
    label: 'Critical',
  },
};

export function HealthBadge({ status, className = '' }: { status: Health; className?: string }) {
  const c = healthColor[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${c.bg} ${c.border} ${c.text} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}

export function ScoreRing({
  value,
  size = 120,
  stroke = 10,
  label,
  sublabel,
  color,
}: {
  value: number;
  size?: number;
  stroke?: number;
  label?: string;
  sublabel?: string;
  color?: string;
}) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (value / 100) * circ;
  const ringColor =
    color ?? (value >= 75 ? '#34d399' : value >= 50 ? '#fbbf24' : '#f87171');
  return (
    <div className="relative inline-flex flex-col items-center" style={{ width: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={ringColor}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="stat-num text-2xl text-white">{Math.round(value)}</span>
        {label && <span className="text-[10px] uppercase tracking-wider text-slate-400">{label}</span>}
        {sublabel && <span className="text-[10px] text-slate-500">{sublabel}</span>}
      </div>
    </div>
  );
}
