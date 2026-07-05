import type { AnalysisResult } from './analyze';
import type { DatasetProfile } from './dataset';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  ts: number;
}

function fmt(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toFixed(1);
}

const SUGGESTED = [
  'Why are profits decreasing?',
  "Which products should we discontinue?",
  "Forecast next quarter's sales.",
  'Which region is underperforming?',
  'What should management prioritize?',
  'How can profits be increased?',
];

export { SUGGESTED as SUGGESTED_QUESTIONS };

export function answerQuestion(
  q: string,
  profile: DatasetProfile,
  analysis: AnalysisResult,
): string {
  const question = q.toLowerCase();
  const has = (...keys: string[]) => keys.some((k) => question.includes(k));

  // Why are profits decreasing / why is X decreasing
  if (has('why') && (has('profit', 'sales', 'revenue', 'declining', 'decreasing', 'dropping'))) {
    const metricWord = has('profit')
      ? 'profit'
      : has('sales', 'revenue')
        ? 'sales'
        : has('revenue')
          ? 'revenue'
          : null;
    const target = metricWord
      ? analysis.problems.find(
          (p) => p.metric.toLowerCase().includes(metricWord) && /declining/i.test(p.name),
        )
      : null;
    const problem = target ?? analysis.problems.find((p) => /declining/i.test(p.name));
    if (problem) {
      const causes = problem.rootCauses
        .map((c, i) => `${i + 1}. ${c.cause} (importance ${c.importance}) — ${c.evidence}`)
        .join('\n');
      return `${problem.name} is driven by the following root causes, ranked by importance:\n\n${causes}\n\nConfidence: ${problem.confidence.toFixed(0)}%.`;
    }
    return 'No clear declining trend was detected in the key metrics. The business appears stable on the dimensions analyzed.';
  }

  // Which products to discontinue
  if (has('discontinue', 'drop', 'cut', 'remove') || (has('which') && has('product', 'category', 'item'))) {
    if (analysis.categoryBreakdown.length) {
      const sorted = [...analysis.categoryBreakdown].sort((a, b) => a.value - b.value);
      const bottom = sorted.slice(0, Math.min(3, sorted.length));
      const lines = bottom.map((b) => `- ${b.category}: ${fmt(b.value)} ${b.metric}`).join('\n');
      return `Based on ${analysis.categoryBreakdown[0].metric} contribution, the lowest-performing segments are:\n\n${lines}\n\nThese are candidates for review, targeted promotion, or discontinuation. Consider the bottom 10% of SKUs within these segments first.`;
    }
    return 'No category or product dimension was detected in the dataset to evaluate discontinuation.';
  }

  // Forecast
  if (has('forecast', 'predict', 'next quarter', 'next month', 'future', 'projection')) {
    if (analysis.predictions.length) {
      const lines = analysis.predictions
        .map(
          (p) =>
            `- ${p.metric}: ${p.predictedValue} (${p.summary.match(/\([+-]?[\d.]+%\)/)?.[0] ?? ''}) — confidence ${p.confidence.toFixed(0)}%, risk ${p.riskLevel}`,
        )
        .join('\n');
      return `Here are the model-based forecasts for the next periods:\n\n${lines}\n\nModel used: ${analysis.model.name} (R² ${analysis.model.r2.toFixed(2)}).`;
    }
    return 'No time dimension was detected, so forecasting could not be generated. Upload data with a date column for forecasts.';
  }

  // Underperforming region / segment
  if (has('underperform', 'worst', 'lowest', 'weakest') || (has('which') && has('region', 'segment'))) {
    if (analysis.categoryBreakdown.length) {
      const sorted = [...analysis.categoryBreakdown].sort((a, b) => a.value - b.value);
      const bottom = sorted[0];
      const top = sorted[sorted.length - 1];
      return `The weakest segment is ${bottom.category} with ${fmt(bottom.value)} ${bottom.metric}, compared to ${top.category} at ${fmt(top.value)}. This segment is flagged as underperforming and appears in the detected problems list.`;
    }
    return 'No segment/region breakdown is available in this dataset.';
  }

  // Prioritize
  if (has('prioritize', 'priority', 'focus', 'should management', 'what should')) {
    const high = analysis.recommendations.filter((r) => r.priority === 'High').slice(0, 3);
    if (high.length) {
      const lines = high.map((r, i) => `${i + 1}. ${r.action} (Impact: ${r.expectedImpact})`).join('\n');
      return `Management should prioritize these high-impact actions:\n\n${lines}`;
    }
    return analysis.executive.immediateActions.map((a, i) => `${i + 1}. ${a}`).join('\n');
  }

  // Increase profits
  if (has('increase') && has('profit', 'revenue', 'sales', 'margin')) {
    const recs = analysis.recommendations
      .filter((r) => /profit|revenue|sales|margin|discount/i.test(r.issue) || r.priority === 'High')
      .slice(0, 4);
    if (recs.length) {
      const lines = recs
        .map((r, i) => `${i + 1}. ${r.action}\n   Expected impact: ${r.expectedImpact} (${r.estimatedImprovement})`)
        .join('\n\n');
      return `To improve profitability, I recommend:\n\n${lines}`;
    }
    return 'Focus on reducing costs in the flagged expense categories and doubling down on the top-performing segments identified in the dashboard.';
  }

  // Health / overall
  if (has('health', 'overall', 'how is', 'summary', 'status')) {
    return `${analysis.executive.narrative}\n\nMajor risks: ${analysis.executive.majorRisks.join('; ')}.\nTop opportunities: ${analysis.executive.topOpportunities.join('; ')}.`;
  }

  // Risks
  if (has('risk', 'threat', 'danger')) {
    const lines = analysis.problems
      .filter((p) => p.severity !== 'healthy')
      .map((p) => `- ${p.name} (${p.severity}, confidence ${p.confidence.toFixed(0)}%) — ${p.businessImpact}`)
      .join('\n');
    return `Detected risks:\n\n${lines || 'No significant risks detected.'}`;
  }

  // Recommendations
  if (has('recommend', 'suggest', 'advice', 'action', 'improve')) {
    const lines = analysis.recommendations
      .slice(0, 5)
      .map((r, i) => `${i + 1}. ${r.action} [${r.priority} priority, ${r.difficulty}]`)
      .join('\n');
    return `Here are my prioritized recommendations:\n\n${lines}`;
  }

  // Dataset
  if (has('dataset', 'data', 'columns', 'rows', 'what is', 'describe')) {
    return profile.summary;
  }

  // Model
  if (has('model', 'algorithm', 'accuracy', 'performance')) {
    return `The selected model is ${analysis.model.name} (${analysis.model.taskType}). Performance: R² ${analysis.model.r2.toFixed(2)}, RMSE ${analysis.model.rmse.toFixed(2)}, MAE ${analysis.model.mae.toFixed(2)}, accuracy ${analysis.model.accuracy.toFixed(1)}%. Compared against: ${analysis.model.compared.map((c) => `${c.name} (R² ${c.r2.toFixed(2)})`).join(', ')}.`;
  }

  // Default
  const summary = [
    `I analyzed your dataset of ${profile.rowCount.toLocaleString()} rows and ${profile.colCount} columns.`,
    analysis.problems.length
      ? `I detected ${analysis.problems.length} business problem(s).`
      : 'No major problems were detected.',
    `Business health score: ${analysis.executive.healthScore}/100.`,
  ].join(' ');
  return `${summary}\n\nYou can ask me about declining metrics, forecasts, underperforming segments, risks, or recommendations. Try: "${SUGGESTED[0]}"`;
}
