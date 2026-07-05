import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { AnalysisResult } from './analyze';
import type { DatasetProfile } from './dataset';

function fmt(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toFixed(1);
}

const BRAND: [number, number, number] = [51, 102, 255];
const ACCENT: [number, number, number] = [106, 60, 255];

export function generateReport(
  profile: DatasetProfile,
  analysis: AnalysisResult,
  fileName: string,
) {
  const doc = new jsPDF({ unit: 'pt', format: 'a4' });
  const pageW = doc.internal.pageSize.getWidth();
  const margin = 40;
  let y = 0;

  const ensure = (need: number) => {
    if (y + need > doc.internal.pageSize.getHeight() - margin) {
      doc.addPage();
      y = margin;
    }
  };

  // Header band
  doc.setFillColor(11, 16, 32);
  doc.rect(0, 0, pageW, 90, 'F');
  doc.setFillColor(...BRAND);
  doc.rect(0, 86, pageW, 4, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(22);
  doc.text('DecisionAI', margin, 42);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(11);
  doc.setTextColor(180, 195, 230);
  doc.text('AI Business Analyst — Executive Report', margin, 62);
  doc.setFontSize(9);
  doc.text(new Date().toLocaleString(), pageW - margin, 42, { align: 'right' });
  doc.text(`Source: ${fileName}`, pageW - margin, 58, { align: 'right' });
  y = 120;

  // Executive summary
  doc.setTextColor(20, 25, 50);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  doc.text('Executive Summary', margin, y);
  y += 8;
  doc.setDrawColor(...BRAND);
  doc.setLineWidth(2);
  doc.line(margin, y, margin + 60, y);
  y += 16;

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  doc.setTextColor(60, 70, 90);
  const narrative = doc.splitTextToSize(analysis.executive.narrative, pageW - margin * 2);
  doc.text(narrative, margin, y);
  y += narrative.length * 12 + 8;

  // Health & risk scores
  autoTable(doc, {
    startY: y,
    head: [['Metric', 'Value']],
    body: [
      ['Overall Health', analysis.executive.overallHealth.toUpperCase()],
      ['Health Score', `${analysis.executive.healthScore}/100`],
      ['Risk Score', `${analysis.executive.riskScore}/100`],
      ['Problems Detected', String(analysis.problems.length)],
      ['Forecasts Generated', String(analysis.predictions.length)],
      ['Model', analysis.model.name],
      ['Model R²', analysis.model.r2.toFixed(2)],
    ],
    theme: 'grid',
    headStyles: { fillColor: BRAND, textColor: 255, fontSize: 10 },
    bodyStyles: { fontSize: 10, textColor: [40, 50, 70] },
    margin: { left: margin, right: margin },
  });
  y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 20;

  // Dataset summary
  ensure(60);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  doc.setTextColor(20, 25, 50);
  doc.text('Dataset Summary', margin, y);
  y += 16;
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  doc.setTextColor(60, 70, 90);
  const ds = doc.splitTextToSize(profile.summary, pageW - margin * 2);
  doc.text(ds, margin, y);
  y += ds.length * 12 + 8;

  autoTable(doc, {
    startY: y,
    head: [['Property', 'Value']],
    body: [
      ['Rows', profile.rowCount.toLocaleString()],
      ['Columns', String(profile.colCount)],
      ['Numeric columns', profile.numericCols.join(', ') || '—'],
      ['Categorical columns', profile.categoricalCols.join(', ') || '—'],
      ['Date columns', profile.dateCols.join(', ') || '—'],
      ['Missing cells', `${profile.totalMissingPct.toFixed(1)}%`],
      ['Duplicate rows', `${profile.duplicatePct.toFixed(1)}%`],
    ],
    theme: 'striped',
    headStyles: { fillColor: ACCENT, textColor: 255, fontSize: 10 },
    bodyStyles: { fontSize: 9, textColor: [40, 50, 70] },
    margin: { left: margin, right: margin },
  });
  y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 20;

  // Problems
  ensure(80);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  doc.setTextColor(20, 25, 50);
  doc.text('Detected Problems & Root Cause Analysis', margin, y);
  y += 6;
  autoTable(doc, {
    startY: y + 10,
    head: [['Problem', 'Severity', 'Affected Area', 'Confidence', 'Root Causes']],
    body: analysis.problems.map((p) => [
      p.name,
      p.severity,
      p.affectedArea,
      `${p.confidence.toFixed(0)}%`,
      p.rootCauses.map((c) => `${c.cause} (${c.importance})`).join('\n'),
    ]),
    theme: 'grid',
    headStyles: { fillColor: BRAND, textColor: 255, fontSize: 9 },
    bodyStyles: { fontSize: 8, textColor: [40, 50, 70], cellPadding: 4 },
    columnStyles: { 4: { cellWidth: 180 } },
    margin: { left: margin, right: margin },
  });
  y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 20;

  // Predictions
  if (analysis.predictions.length) {
    ensure(80);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(14);
    doc.setTextColor(20, 25, 50);
    doc.text('Predictions', margin, y);
    y += 6;
    autoTable(doc, {
      startY: y + 10,
      head: [['Metric', 'Predicted Value', 'Risk', 'Confidence', 'Summary']],
      body: analysis.predictions.map((p) => [
        p.metric,
        p.predictedValue,
        p.riskLevel,
        `${p.confidence.toFixed(0)}%`,
        p.summary,
      ]),
      theme: 'grid',
      headStyles: { fillColor: ACCENT, textColor: 255, fontSize: 9 },
      bodyStyles: { fontSize: 8, textColor: [40, 50, 70] },
      margin: { left: margin, right: margin },
    });
    y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 20;
  }

  // Model performance
  ensure(80);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  doc.setTextColor(20, 25, 50);
  doc.text('Model Performance', margin, y);
  y += 6;
  autoTable(doc, {
    startY: y + 10,
    head: [['Model', 'R²', 'RMSE', 'MAE', 'Accuracy']],
    body: [
      [analysis.model.name, analysis.model.r2.toFixed(2), analysis.model.rmse.toFixed(2), analysis.model.mae.toFixed(2), `${analysis.model.accuracy.toFixed(1)}%`],
      ...analysis.model.compared
        .filter((c) => c.name !== analysis.model.name.split(' (')[0])
        .map((c) => [c.name, c.r2.toFixed(2), c.rmse.toFixed(2), '—', '—']),
    ],
    theme: 'striped',
    headStyles: { fillColor: BRAND, textColor: 255, fontSize: 9 },
    bodyStyles: { fontSize: 9, textColor: [40, 50, 70] },
    margin: { left: margin, right: margin },
  });
  y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 20;

  // Feature importance
  if (analysis.model.featureImportance.length) {
    ensure(60);
    autoTable(doc, {
      startY: y,
      head: [['Feature', 'Importance (%)']],
      body: analysis.model.featureImportance.map((f) => [f.feature, String(f.importance)]),
      theme: 'striped',
      headStyles: { fillColor: ACCENT, textColor: 255, fontSize: 9 },
      bodyStyles: { fontSize: 9, textColor: [40, 50, 70] },
      margin: { left: margin, right: margin },
    });
    y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 20;
  }

  // Recommendations
  ensure(80);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  doc.setTextColor(20, 25, 50);
  doc.text('Business Recommendations', margin, y);
  y += 6;
  autoTable(doc, {
    startY: y + 10,
    head: [['Issue', 'Action', 'Priority', 'Expected Impact', 'Difficulty']],
    body: analysis.recommendations.map((r) => [
      r.issue,
      r.action,
      r.priority,
      r.expectedImpact,
      r.difficulty,
    ]),
    theme: 'grid',
    headStyles: { fillColor: BRAND, textColor: 255, fontSize: 9 },
    bodyStyles: { fontSize: 8, textColor: [40, 50, 70], cellPadding: 4 },
    margin: { left: margin, right: margin },
  });
  y = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 20;

  // Category breakdown
  if (analysis.categoryBreakdown.length) {
    ensure(60);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(14);
    doc.setTextColor(20, 25, 50);
    doc.text('Category Breakdown', margin, y);
    y += 6;
    autoTable(doc, {
      startY: y + 10,
      head: [['Category', 'Metric', 'Value']],
      body: analysis.categoryBreakdown.map((c) => [c.category, c.metric, fmt(c.value)]),
      theme: 'striped',
      headStyles: { fillColor: ACCENT, textColor: 255, fontSize: 9 },
      bodyStyles: { fontSize: 9, textColor: [40, 50, 70] },
      margin: { left: margin, right: margin },
    });
  }

  // Footer page numbers
  const pages = doc.getNumberOfPages();
  for (let i = 1; i <= pages; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(150, 160, 180);
    doc.text(
      `DecisionAI Report — generated ${new Date().toLocaleString()} — page ${i}/${pages}`,
      pageW / 2,
      doc.internal.pageSize.getHeight() - 20,
      { align: 'center' },
    );
  }

  doc.save(`DecisionAI_Report_${new Date().toISOString().slice(0, 10)}.pdf`);
}
