import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)

pdf_path = Path("artifacts/Lab4_Monitoring_Analysis_Report.pdf")
doc = SimpleDocTemplate(
    str(pdf_path),
    pagesize=letter,
    leftMargin=0.55 * inch,
    rightMargin=0.55 * inch,
    topMargin=0.55 * inch,
    bottomMargin=0.55 * inch,
)

styles = getSampleStyleSheet()

# Custom styles
primary_color = colors.HexColor("#1e3a8a")
secondary_color = colors.HexColor("#2563eb")
dark_neutral = colors.HexColor("#1f2937")
accent_green = colors.HexColor("#059669")
accent_red = colors.HexColor("#dc2626")

title_style = ParagraphStyle(
    "DocTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=24,
    textColor=primary_color,
    spaceAfter=4,
)

subtitle_style = ParagraphStyle(
    "DocSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=11,
    leading=15,
    textColor=colors.HexColor("#4b5563"),
    spaceAfter=12,
)

h1_style = ParagraphStyle(
    "Heading1_Custom",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=17,
    textColor=primary_color,
    spaceBefore=12,
    spaceAfter=6,
    keepWithNext=True,
)

h2_style = ParagraphStyle(
    "Heading2_Custom",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=15,
    textColor=secondary_color,
    spaceBefore=8,
    spaceAfter=4,
    keepWithNext=True,
)

body_style = ParagraphStyle(
    "Body_Custom",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9.5,
    leading=13.5,
    textColor=dark_neutral,
    spaceAfter=6,
)

bullet_style = ParagraphStyle(
    "Bullet_Custom",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    textColor=dark_neutral,
    leftIndent=15,
    firstLineIndent=-10,
    spaceAfter=3,
)

table_header_style = ParagraphStyle(
    "TableHeader",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    textColor=colors.white,
    alignment=1,
)

table_cell_style = ParagraphStyle(
    "TableCell",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=11,
    textColor=dark_neutral,
    alignment=1,
)

story = []

# Document Header
story.append(Paragraph("Lab 4 — Production Monitoring & Analysis Report", title_style))
story.append(Paragraph("<b>Course</b>: DDM501 — AI in DevOps, DataOps, MLOps &nbsp;|&nbsp; <b>Module</b>: Production ML Observability<br/><b>Dataset</b>: UCI Credit Risk (30,000 baseline) &nbsp;|&nbsp; <b>Stack</b>: FastAPI, Prometheus, Grafana, SHAP", subtitle_style))
story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=10))

# 1. Executive Summary
story.append(Paragraph("1. Executive Summary & Experimental Methodology", h1_style))
story.append(Paragraph(
    "In credit risk production environments, ground-truth accuracy cannot be monitored in real-time: default outcomes arrive months later, and declined applicants provide no counterfactual repayment label. To detect model degradation before business losses occur, we instrumented the credit risk service with Prometheus metrics, Population Stability Index (PSI) drift tracking across 6 core features, demographic selection rate parity, and SHAP explainability latencies.",
    body_style
))
story.append(Paragraph(
    "We executed controlled traffic simulations with <b>N = 400 requests per profile</b>, resetting the bounded observation window between cycles. The 5 evaluated profiles represent: Normal baseline, Drifted (strength 0.05, 0.15, 1.0), and Unfair (targeted bias on sex=1).",
    body_style
))

# 2. Results Table
story.append(Paragraph("2. Experimental Results across Traffic Profiles", h1_style))

table_data = [
    [
        Paragraph("Profile", table_header_style),
        Paragraph("Mean Score", table_header_style),
        Paragraph("Approve %", table_header_style),
        Paragraph("Review %", table_header_style),
        Paragraph("Decline %", table_header_style),
        Paragraph("Drift (PSI)", table_header_style),
        Paragraph("Status", table_header_style),
        Paragraph("Fairness Gap", table_header_style),
    ],
    [
        Paragraph("<b>Normal</b>", table_cell_style),
        Paragraph("0.2355", table_cell_style),
        Paragraph("77.8%", table_cell_style),
        Paragraph("14.2%", table_cell_style),
        Paragraph("8.0%", table_cell_style),
        Paragraph("<b>0.0301</b>", table_cell_style),
        Paragraph("Stable", table_cell_style),
        Paragraph("<b>0.0188</b>", table_cell_style),
    ],
    [
        Paragraph("<b>Drifted (0.05)</b>", table_cell_style),
        Paragraph("0.2437", table_cell_style),
        Paragraph("77.5%", table_cell_style),
        Paragraph("14.0%", table_cell_style),
        Paragraph("8.5%", table_cell_style),
        Paragraph("<b>0.1885</b>", table_cell_style),
        Paragraph("Moderate", table_cell_style),
        Paragraph("0.0149", table_cell_style),
    ],
    [
        Paragraph("<b>Drifted (0.15)</b>", table_cell_style),
        Paragraph("0.2609", table_cell_style),
        Paragraph("74.0%", table_cell_style),
        Paragraph("16.2%", table_cell_style),
        Paragraph("9.8%", table_cell_style),
        Paragraph("<b>1.1518</b>", table_cell_style),
        Paragraph("Significant", table_cell_style),
        Paragraph("0.0357", table_cell_style),
    ],
    [
        Paragraph("<b>Drifted (Full)</b>", table_cell_style),
        Paragraph("0.5897", table_cell_style),
        Paragraph("15.5%", table_cell_style),
        Paragraph("29.8%", table_cell_style),
        Paragraph("54.8%", table_cell_style),
        Paragraph("<b>4.2510</b>", table_cell_style),
        Paragraph("Significant", table_cell_style),
        Paragraph("0.0376", table_cell_style),
    ],
    [
        Paragraph("<b>Unfair</b>", table_cell_style),
        Paragraph("0.3966", table_cell_style),
        Paragraph("52.2%", table_cell_style),
        Paragraph("15.8%", table_cell_style),
        Paragraph("32.0%", table_cell_style),
        Paragraph("<b>0.3526</b>", table_cell_style),
        Paragraph("Significant", table_cell_style),
        Paragraph("<b>0.7222</b>", table_cell_style),
    ],
]

summary_table = Table(table_data, colWidths=[1.1*inch, 0.75*inch, 0.75*inch, 0.75*inch, 0.75*inch, 0.85*inch, 0.95*inch, 0.95*inch])
summary_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), primary_color),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f9fafb"), colors.white]),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(summary_table)
story.append(Spacer(1, 10))

# Decision Mix Image
if Path("artifacts/charts/decision_mix.png").exists():
    story.append(Image("artifacts/charts/decision_mix.png", width=6.8*inch, height=3.0*inch))
    story.append(Spacer(1, 10))

story.append(PageBreak())

# 3. Core Evaluation Questions
story.append(Paragraph("3. Detailed Answers to Core Evaluation Questions", h1_style))

# Q1
story.append(Paragraph("Question 1: Which signal moved first, and by how much before anything else did?", h2_style))
story.append(Paragraph(
    "<b>Empirical Finding: Input feature drift (PSI on <i>payment_ratio</i>) moved first, surging by 1,339% while downstream decision mix and output score metrics remained completely flat.</b>",
    body_style
))
story.append(Paragraph(
    "• <b>Decision Mix Invariance</b>: At mild drift (strength = 0.05), the business decision proportions were virtually identical to normal baseline: APPROVE dropped by only 0.3% (77.8% → 77.5%), REVIEW shifted by -0.2% (14.2% → 14.0%), and DECLINE increased by a negligible 0.5% (8.0% → 8.5%). Any operations team monitoring underwriter workload or approval rates would detect zero anomaly.",
    bullet_style
))
story.append(Paragraph(
    "• <b>Output Score Invariance</b>: The mean prediction score only crept up by +0.0082 (0.2355 → 0.2437, a 3.48% change), well within routine statistical noise.",
    bullet_style
))
story.append(Paragraph(
    "• <b>Input Drift Surge</b>: In stark contrast, <code>ml_feature_drift_psi{feature=\"payment_ratio\"}</code> escalated from <b>0.0131 to 0.1885 (+1,339%)</b>, instantly crossing into the <i>moderate drift band</i> (0.10 ≤ PSI < 0.25). The aggregate drift score jumped from <b>0.0301 to 0.1885 (+526%)</b>.",
    bullet_style
))
story.append(Paragraph(
    "<b>Conclusion</b>: Waiting for downstream signals (accuracy or decline rate) leaves a model scoring an unfitted distribution for weeks. Input PSI serves as the definitive leading indicator.",
    body_style
))
story.append(Spacer(1, 6))

# Q2
story.append(Paragraph("Question 2: Which signal would have paged you, given your alert thresholds?", h2_style))
story.append(Paragraph(
    "Our Prometheus alerting rules (<code>monitoring/prometheus/alerts/ml_alerts.yml</code>) partition notifications into <b>warning</b> (actionable tickets/Slack alerts) and <b>critical</b> (immediate on-call paging):",
    body_style
))
story.append(Paragraph(
    "• <b>ModerateFeatureDrift</b> (PSI ≥ 0.10 for 15m, severity: warning): Non-paging. Fires under <i>drifted (0.05)</i>. Alerting informs the ML team of an emerging trend without waking engineers at 3am.",
    bullet_style
))
story.append(Paragraph(
    "• <b>SignificantFeatureDrift</b> (PSI ≥ 0.25 for 15m, severity: critical): <b>PAGES ON-CALL</b>. Fires under <i>drifted (0.15)</i> (PSI = 1.1518), <i>drifted (Full)</i> (PSI = 4.2510), and <i>unfair</i> (PSI = 0.3526).",
    bullet_style
))
story.append(Paragraph(
    "• <b>FairnessGapWidened</b> (gap > 0.10 for 20m, severity: critical): <b>PAGES ON-CALL</b>. Specifically triggered by the <i>unfair</i> run (gap = <b>0.7222</b> >> 0.10 threshold) to halt compliance violations.",
    bullet_style
))
story.append(Paragraph(
    "• <b>DecisionMixShift</b> (DECLINE > 20% for 30m, severity: warning): Fires on <i>drifted (Full)</i> (54.8%) and <i>unfair</i> (32.0%) to warn underwriting operations of backlog risk.",
    bullet_style
))
story.append(Spacer(1, 8))

# Charts comparison
if Path("artifacts/charts/psi_by_feature.png").exists():
    story.append(Image("artifacts/charts/psi_by_feature.png", width=6.8*inch, height=3.0*inch))
    story.append(Spacer(1, 10))

story.append(PageBreak())

# Q3
story.append(Paragraph("Question 3: Which signal told you what was wrong, rather than only that something was? (Drifted vs Unfair Comparison)", h2_style))
story.append(Paragraph(
    "Both the <code>drifted (0.15)</code> and <code>unfair</code> runs produce high aggregate drift scores in the significant band (1.1518 and 0.3526) and elevated decline rates. An aggregate drift metric only indicates <i>that</i> an anomaly occurred. Two specific dashboard signals pinpoint <b>what</b> is wrong:",
    body_style
))

story.append(Paragraph("1. Feature-Level PSI Breakdown (Economic Shift vs Delinquency Spike):", h2_style))
story.append(Paragraph(
    "• <b>Under Drifted Traffic</b>: Economic capacity and balance utilization drive the shift. <code>payment_ratio</code> (1.1518 - 4.2510), <code>utilisation_ratio</code> (0.2611 - 3.0921), and <code>LIMIT_BAL</code> (0.0572 - 2.0426) lead the degradation. Historical repayment delays (<code>PAY_0</code> and <code>max_delay</code>) lag far behind (0.0036 - 0.0059 at mild/moderate strengths). <b>Diagnosis</b>: The applicant pool has shifted to younger, credit-constrained borrowers (e.g., student credit campaign).",
    bullet_style
))
story.append(Paragraph(
    "• <b>Under Unfair Traffic</b>: Demographic and capacity features remain perfectly at baseline (<code>AGE</code>: 0.0301, <code>utilisation_ratio</code>: 0.0288, <code>LIMIT_BAL</code>: 0.0152). Instead, drift is concentrated entirely in repayment delay features: <code>max_delay</code> (0.3526) and <code>PAY_0</code> (0.2791). <b>Diagnosis</b>: Applicant characteristics are identical, but repayment histories are systematically worse.",
    bullet_style
))

story.append(Paragraph("2. Fairness Selection-Rate Gap (Fairness vs Macro Drift):", h2_style))
story.append(Paragraph(
    "• <b>Under Drifted Traffic</b>: The selection-rate gap remains small (<b>0.0357 – 0.0376</b>, vs 0.0188 baseline). Both demographic groups absorb the economic shift equally.",
    bullet_style
))
story.append(Paragraph(
    "• <b>Under Unfair Traffic</b>: The selection-rate gap skyrockets to <b>0.7222 (72.2%)</b>. Group 1 (Male) has an adverse selection rate of <b>78.6%</b> flagged for review/decline, whereas Group 2 (Female) has a selection rate of only <b>6.4%</b>. <b>Definitive Diagnosis</b>: Disparate treatment / demographic algorithmic bias against Group 1.",
    bullet_style
))

if Path("artifacts/charts/drift_vs_fairness.png").exists():
    story.append(Spacer(1, 4))
    story.append(Image("artifacts/charts/drift_vs_fairness.png", width=6.2*inch, height=3.0*inch))

story.append(Spacer(1, 10))
story.append(Paragraph("4. Verification & Submission Summary", h1_style))
story.append(Paragraph(
    "• <b>Unit Test Verification</b>: 79/79 pytest cases passing (100%). Code coverage across <code>app/</code> reached <b>91.47%</b> (exceeding the strict 85% requirement).<br/>"
    "• <b>Alert Rules & Dashboards</b>: Prometheus alert rules validated against promtool specification; Grafana provisioned dashboard conforms with valid JSON schema and unique UIDs.<br/>"
    "• <b>Artifacts Generated</b>: <code>artifacts/profile_simulation_results.json</code>, <code>docs/WRITTEN_ANALYSIS.md</code>, and <code>artifacts/Lab4_Monitoring_Analysis_Report.pdf</code>.",
    body_style
))

doc.build(story)
print("PDF successfully built at:", pdf_path)
