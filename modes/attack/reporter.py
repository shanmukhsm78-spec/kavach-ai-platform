"""Reporter stage: render findings as Markdown + PDF.

Markdown is produced by hand (no heavy templating) and the PDF is built with
reportlab (pure-python, no system binaries), so report generation works
offline on any machine. An optional LLM pass polishes the executive summary;
if no LLM is configured the deterministic summary is used instead.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from .llm_assist import summarize_findings
from .models import SEVERITY_ORDER, Finding

_SEV_COLOR = {
    "Critical": colors.HexColor("#b91c1c"),
    "High": colors.HexColor("#ea580c"),
    "Medium": colors.HexColor("#ca8a04"),
    "Low": colors.HexColor("#2563eb"),
    "Info": colors.HexColor("#64748b"),
}


def _sort(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 0),
                  reverse=True)


def build_markdown(target: str, scan_id: str, findings: list[Finding],
                   summary: str, used_llm: bool) -> str:
    """Return the full report as a Markdown string."""
    findings = _sort(findings)
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Kavach AI Platform — Attack Mode Report",
        "",
        "> Autonomous AI pentester (Recon → Scanner → Exploit → Reporter)",
        "",
        f"- **Scan ID:** `{scan_id}`",
        f"- **Target:** {target}",
        f"- **Generated:** {now}",
        f"- **Findings:** {len(findings)}",
        f"- **Summary engine:** {'LLM-assisted' if used_llm else 'rule-based (offline)'}",
        "",
        "## Executive summary",
        "",
        summary,
        "",
        "## Findings overview",
        "",
        "| # | Severity | Title | MITRE ATT&CK |",
        "|---|----------|-------|--------------|",
    ]
    for i, f in enumerate(findings, 1):
        lines.append(
            f"| {i} | {f.severity} | {f.title} | "
            f"{f.mitre['id']} {f.mitre['name']} |"
        )
    lines += ["", "## Detailed findings", ""]
    for i, f in enumerate(findings, 1):
        lines += [
            f"### {i}. {f.title}",
            "",
            f"- **Severity:** {f.severity} — {f.cvss_qualitative}",
            f"- **Location:** {f.location}",
            f"- **MITRE ATT&CK:** {f.mitre['id']} — {f.mitre['name']} "
            f"(_{f.mitre['tactic']}_)",
            "",
            f"**Description.** {f.description}",
            "",
            f"**Evidence.** {f.evidence}",
            "",
            f"**Proof of concept (safe).** {f.exploit_proof}",
            "",
            f"**Remediation.** {f.remediation}",
            "",
        ]
    lines += [
        "---",
        "",
        "_All testing was performed non-destructively against an authorised "
        "local lab. Kavach refuses targets that resolve outside loopback / "
        "private IP ranges._",
    ]
    return "\n".join(lines)


def build_pdf(pdf_path: Path, target: str, scan_id: str,
              findings: list[Finding], summary: str, used_llm: bool) -> None:
    """Render the report to a PDF file using reportlab."""
    findings = _sort(findings)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=9,
                              leading=13, alignment=TA_LEFT, spaceAfter=4))
    h2 = ParagraphStyle("H2b", parent=styles["Heading2"], textColor=colors.HexColor("#0f172a"))

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            title=f"Kavach Attack Report {scan_id}")
    story = []
    story.append(Paragraph("Kavach AI Platform — Attack Mode Report", styles["Title"]))
    story.append(Paragraph("Autonomous AI pentester (Recon → Scanner → Exploit → Reporter)", styles["Body"]))
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    meta = (f"<b>Scan ID:</b> {scan_id}<br/><b>Target:</b> {target}<br/>"
            f"<b>Generated:</b> {now}<br/><b>Findings:</b> {len(findings)}<br/>"
            f"<b>Summary engine:</b> {'LLM-assisted' if used_llm else 'rule-based (offline)'}")
    story.append(Paragraph(meta, styles["Body"]))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Executive summary", h2))
    story.append(Paragraph(summary, styles["Body"]))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Findings overview", h2))
    data = [["#", "Severity", "Title", "MITRE ATT&CK"]]
    for i, f in enumerate(findings, 1):
        data.append([str(i), f.severity, Paragraph(f.title, styles["Body"]),
                     f"{f.mitre['id']} {f.mitre['name']}"])
    table = Table(data, colWidths=[8 * mm, 22 * mm, 75 * mm, 60 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]
    for r, f in enumerate(findings, 1):
        style.append(("TEXTCOLOR", (1, r), (1, r), _SEV_COLOR.get(f.severity, colors.black)))
    table.setStyle(TableStyle(style))
    story.append(table)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Detailed findings", h2))
    for i, f in enumerate(findings, 1):
        story.append(Paragraph(f"{i}. {f.title}", styles["Heading3"]))
        detail = (
            f"<b>Severity:</b> {f.severity} — {f.cvss_qualitative}<br/>"
            f"<b>Location:</b> {f.location}<br/>"
            f"<b>MITRE ATT&CK:</b> {f.mitre['id']} — {f.mitre['name']} "
            f"({f.mitre['tactic']})<br/><br/>"
            f"<b>Description.</b> {f.description}<br/><br/>"
            f"<b>Evidence.</b> {f.evidence}<br/><br/>"
            f"<b>Proof of concept (safe).</b> {f.exploit_proof}<br/><br/>"
            f"<b>Remediation.</b> {f.remediation}"
        )
        story.append(Paragraph(detail, styles["Body"]))
        story.append(Spacer(1, 3 * mm))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "All testing was performed non-destructively against an authorised "
        "local lab. Kavach refuses targets that resolve outside loopback / "
        "private IP ranges.", styles["Body"]))
    doc.build(story)


def write_reports(out_dir: Path, target: str, scan_id: str,
                  findings: list[Finding]) -> dict[str, str]:
    """Produce both report formats and return their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    finding_dicts = [f.to_dict() for f in _sort(findings)]
    summary, used_llm = summarize_findings(target, finding_dicts)

    md = build_markdown(target, scan_id, findings, summary, used_llm)
    md_path = out_dir / "report.md"
    md_path.write_text(md, encoding="utf-8")

    pdf_path = out_dir / "report.pdf"
    build_pdf(pdf_path, target, scan_id, findings, summary, used_llm)

    return {"markdown": str(md_path), "pdf": str(pdf_path),
            "summary": summary, "used_llm": used_llm}
