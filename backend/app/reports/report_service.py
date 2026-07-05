"""PDF report generation using ReportLab."""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger("app.reports")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SectionTitle", fontSize=14, spaceAfter=10, spaceBefore=14, textColor=colors.HexColor("#1a365d")))
    styles.add(ParagraphStyle(name="BodyText2", fontSize=9, spaceAfter=6, leading=13))
    return styles


def _kv_table(data: list, styles) -> Table:
    t = Table(data, colWidths=[2 * inch, 4 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f7fafc")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def generate_pdf_report(
    dataset_id: str,
    summary: Dict[str, Any],
    kpis: Dict[str, Any],
    issues: list,
    root_causes: Dict[str, Any],
    predictions: Dict[str, Any],
    recommendations: list,
    executive: Dict[str, Any],
    quality_score: float = 0,
    health_score: float = 0,
) -> Dict[str, Any]:
    """Generate a professional PDF report and return its path + URL."""
    report_dir = Path(settings.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    filename = f"decisionai_report_{dataset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = report_dir / filename
    styles = _styles()

    doc = SimpleDocTemplate(str(filepath), pagesize=A4, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    story = []

    # Title
    story.append(Paragraph("DecisionAI - Business Intelligence Report", styles["Title"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    # Executive Summary
    story.append(Paragraph("Executive Summary", styles["SectionTitle"]))
    es_text = executive.get("business_health", "No summary available.")
    story.append(Paragraph(es_text[:2000], styles["BodyText2"]))
    story.append(Spacer(1, 0.15 * inch))

    # Dataset Summary
    story.append(Paragraph("Dataset Summary", styles["SectionTitle"]))
    ds_data = [
        ["Rows", str(summary.get("row_count", "N/A"))],
        ["Columns", str(summary.get("column_count", "N/A"))],
        ["Missing Values", str(summary.get("missing_values", {}).get("total", 0))],
        ["Duplicates", str(summary.get("duplicates", 0))],
        ["Quality Score", f"{quality_score}/100"],
        ["Health Score", f"{health_score}/100"],
    ]
    story.append(_kv_table(ds_data, styles))
    story.append(Spacer(1, 0.15 * inch))

    # KPIs
    story.append(Paragraph("Business KPIs", styles["SectionTitle"]))
    kpi_rows = [["KPI", "Current", "Change %", "Trend"]]
    for name, val in kpis.items():
        if isinstance(val, dict) and "current" in val:
            kpi_rows.append([name, str(val.get("current", "")), f"{val.get('change_pct', 0)}%", val.get("trend", "")])
    if len(kpi_rows) > 1:
        kpi_table = Table(kpi_rows, colWidths=[2 * inch, 1.5 * inch, 1.2 * inch, 1.3 * inch])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
        ]))
        story.append(kpi_table)
    story.append(Spacer(1, 0.15 * inch))

    # Business Diagnosis
    story.append(Paragraph("Business Diagnosis", styles["SectionTitle"]))
    for issue in issues[:10]:
        story.append(Paragraph(
            f"<b>{issue.get('issue', '')}</b> - Severity: {issue.get('severity', '')} | Impact: {issue.get('business_impact', '')}",
            styles["BodyText2"],
        ))
    story.append(Spacer(1, 0.15 * inch))

    # Root Cause Analysis
    story.append(Paragraph("Root Cause Analysis", styles["SectionTitle"]))
    explanation = root_causes.get("business_explanation", "No root cause analysis available.")
    story.append(Paragraph(explanation[:2000], styles["BodyText2"]))
    story.append(Spacer(1, 0.15 * inch))

    # Predictions
    story.append(Paragraph("ML Predictions", styles["SectionTitle"]))
    pred_text = f"Best Model: {predictions.get('best_model', 'N/A')}<br/>Task: {predictions.get('task_type', 'N/A')}"
    story.append(Paragraph(pred_text, styles["BodyText2"]))
    metrics = predictions.get("metrics", {})
    if metrics:
        story.append(Paragraph(f"Metrics: {metrics}", styles["BodyText2"]))
    story.append(Spacer(1, 0.15 * inch))

    # Recommendations
    story.append(Paragraph("Recommendations", styles["SectionTitle"]))
    for rec in recommendations[:10]:
        story.append(Paragraph(
            f"<b>{rec.get('title', rec.get('priority', 'Recommendation'))}</b> - Priority: {rec.get('priority', 'N/A')} | ROI: {rec.get('estimated_roi', 'N/A')}",
            styles["BodyText2"],
        ))
    story.append(Spacer(1, 0.15 * inch))

    # Footer
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Generated by DecisionAI - Autonomous AI Business Analyst", styles["Normal"]))

    doc.build(story)
    file_size = filepath.stat().st_size
    logger.info("PDF report generated: %s (%d bytes)", filepath, file_size)

    return {
        "file_path": str(filepath),
        "filename": filename,
        "file_size_bytes": file_size,
        "download_url": f"{settings.api_v1_prefix}/reports/download/{filename}",
    }
