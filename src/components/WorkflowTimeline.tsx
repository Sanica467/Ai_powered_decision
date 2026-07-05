import { useEffect, useState } from 'react';
import { Check, Loader2 } from 'lucide-react';

export interface WorkflowStep {
  label: string;
  desc: string;
}

export const WORKFLOW_STEPS: WorkflowStep[] = [
  { label: 'Dataset Uploaded', desc: 'File received and validated' },
  { label: 'Dataset Understood', desc: 'Schema, types & statistics profiled' },
  { label: 'Data Cleaned', desc: 'Missing values, duplicates & outliers assessed' },
  { label: 'Business Analysis', desc: 'Health metrics & trends computed' },
  { label: 'Problems Detected', desc: 'Issues with severity & impact scored' },
  { label: 'Root Cause Analysis', desc: 'Drivers ranked by importance' },
  { label: 'ML Model Selected', desc: 'Best algorithm auto-chosen & compared' },
  { label: 'Model Training', desc: 'Walk-forward validation completed' },
  { label: 'Prediction Generated', desc: 'Forecasts & risk levels produced' },
  { label: 'Recommendations', desc: 'Prioritized business actions created' },
  { label: 'Report Created', desc: 'Executive summary synthesized' },
];

interface Props {
  active: boolean;
  onComplete?: () => void;
}

export default function WorkflowTimeline({ active, onComplete }: Props) {
  const [current, setCurrent] = useState(active ? 0 : WORKFLOW_STEPS.length);

  useEffect(() => {
    if (!active) {
      setCurrent(WORKFLOW_STEPS.length);
      return;
    }
    setCurrent(0);
    let i = 0;
    const tick = () => {
      i++;
      setCurrent(i);
      if (i < WORKFLOW_STEPS.length) {
        timer = window.setTimeout(tick, 380 + Math.random() * 260);
      } else {
        onComplete?.();
      }
    };
    let timer = window.setTimeout(tick, 420);
    return () => window.clearTimeout(timer);
  }, [active, onComplete]);

  return (
    <div className="card p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">AI Workflow</h3>
          <p className="text-xs text-slate-400">Real-time reasoning pipeline</p>
        </div>
        <span className="chip text-brand-300">
          {current >= WORKFLOW_STEPS.length ? 'Complete' : `${current}/${WORKFLOW_STEPS.length}`}
        </span>
      </div>
      <ol className="space-y-1">
        {WORKFLOW_STEPS.map((step, i) => {
          const done = i < current;
          const running = i === current;
          const pending = i > current;
          return (
            <li
              key={step.label}
              className={`flex items-start gap-3 rounded-lg px-2.5 py-2 transition-all duration-300 ${
                running ? 'bg-brand-500/10 ring-1 ring-brand-500/30' : ''
              }`}
            >
              <div className="mt-0.5">
                {done ? (
                  <div className="grid h-5 w-5 place-items-center rounded-full bg-ok-500/20 ring-1 ring-ok-500/40">
                    <Check className="h-3 w-3 text-ok-400" />
                  </div>
                ) : running ? (
                  <Loader2 className="h-5 w-5 animate-spin text-brand-300" />
                ) : (
                  <div
                    className={`h-5 w-5 rounded-full ring-1 ${
                      pending ? 'bg-white/[0.02] ring-white/10' : ''
                    }`}
                  />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p
                  className={`text-sm font-medium ${
                    done ? 'text-slate-300' : running ? 'text-white' : 'text-slate-500'
                  }`}
                >
                  {step.label}
                </p>
                <p className={`text-xs ${running ? 'text-slate-400' : 'text-slate-600'}`}>
                  {step.desc}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
