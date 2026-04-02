"""
pdf_generator.py
Renders the JobSherpa report HTML template to a PDF using WeasyPrint.
Embeds all charts as base64 images.
"""

import os
import base64
from pathlib import Path
from typing import Any
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from google.adk.tools import ToolContext
from google.genai import types

from .chart_generator import (
    generate_score_dial,
    generate_radar_chart,
    generate_ats_bar,
    generate_salary_range,
    generate_ctc_donut,
    generate_interview_timeline,
    generate_confidence_chart,
)

# Paths
REPORT_DIR   = Path(__file__).parent
TEMPLATE_DIR = REPORT_DIR / "templates"
ASSETS_DIR   = REPORT_DIR.parent / "assets"


def _safe_dict(val: Any) -> dict:
    """Ensure value is a dict, return empty dict otherwise."""
    return val if isinstance(val, dict) else {}


def _safe_list(val: Any) -> list:
    """Ensure value is a list, return empty list otherwise."""
    return val if isinstance(val, list) else []


def _normalise_dimensions(dimensions: Any) -> dict:
    """
    Gemini may return dimensions as a dict OR a list.
    Normalise to dict: {name: {score, reasoning}}
    """
    if isinstance(dimensions, dict):
        return dimensions
    if isinstance(dimensions, list):
        result = {}
        for item in dimensions:
            if isinstance(item, dict):
                name = item.get("name", item.get("dimension", f"dim_{len(result)}"))
                result[name] = {"score": item.get("score", 0), "reasoning": item.get("reasoning", "")}
        return result
    return {}


def _normalise_skills(skills: Any) -> dict:
    """Normalise skills to {must_have, nice_to_have, bonus_skills}."""
    if isinstance(skills, dict):
        return skills
    return {"must_have": {"matched": [], "missing": []},
            "nice_to_have": {"matched": [], "missing": []},
            "bonus_skills": []}


def _normalise_shining(shining: Any) -> list:
    """Flatten shining points from dict or list into a flat list of strings."""
    result = []
    if isinstance(shining, dict):
        for key, items in shining.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        result.append(item)
                    elif isinstance(item, dict):
                        result.append(item.get("description", str(item)))
    elif isinstance(shining, list):
        for item in shining:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                result.append(item.get("description", str(item)))
    return result


def _load_logo_base64() -> str:
    """Load logo from assets/logo.png as base64. Returns empty string if missing."""
    logo_path = ASSETS_DIR / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


def _build_confidence_data(report: dict) -> list[dict]:
    """Build confidence data for the sources chart."""
    interview = _safe_dict(report.get("interview_process"))
    salary    = _safe_dict(report.get("salary_intelligence"))
    return [
        {"section": "Match Analysis",    "confidence": "HIGH", "sources_count": 1},
        {"section": "Interview Process", "confidence": interview.get("confidence", "FAIR"),
         "sources_count": len(_safe_list(interview.get("source_urls")))},
        {"section": "Salary — India",    "confidence": _safe_dict(salary.get("india")).get("confidence", "FAIR"),
         "sources_count": 3},
        {"section": "Salary — Global",   "confidence": _safe_dict(salary.get("global")).get("confidence", "FAIR"),
         "sources_count": 2},
    ]


def _pct(val: Any) -> float:
    """Parse percentage value — handles '70%', '70', 70."""
    try:
        return float(str(val).replace("%", "").strip())
    except Exception:
        return 0.0


async def generate_pdf(report: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
    """
    Generate a visual PDF report and save it as a downloadable artifact.
    Call this tool as the final step after all analysis is complete.

    Args:
        report: The full structured report data as a dictionary.

    Returns:
        Dictionary with status and filename.
    """
    # ── Extract & normalise all data ─────────────────────────────────────────
    match      = _safe_dict(report.get("match_analysis"))
    interview  = _safe_dict(report.get("interview_process"))
    salary     = _safe_dict(report.get("salary_intelligence"))
    links      = _safe_dict(report.get("link_validation"))

    dimensions = _normalise_dimensions(match.get("dimensions", {}))
    skills     = _normalise_skills(match.get("skills", {}))
    shining    = _normalise_shining(match.get("shining_points", {}))
    rounds     = _safe_list(interview.get("rounds"))
    india_sal  = _safe_dict(salary.get("india"))
    global_sal = _safe_dict(salary.get("global"))
    india_band  = _safe_dict(india_sal.get("band"))
    global_band = _safe_dict(global_sal.get("band"))
    ctc         = _safe_dict(india_sal.get("ctc_breakdown"))

    overall_score = match.get("overall_score", 0)
    if not isinstance(overall_score, (int, float)):
        overall_score = 0

    # ── Build radar scores ───────────────────────────────────────────────────
    candidate_scores = {
        k: (v.get("score", 0) if isinstance(v, dict) else int(v or 0))
        for k, v in dimensions.items()
    } if dimensions else {"Core Skills": 0, "Experience": 0, "Domain": 0, "Tools": 0, "Soft Skills": 0}

    required_scores = {k: 80 for k in candidate_scores}

    # ── Generate all charts ──────────────────────────────────────────────────
    ats_data = _safe_dict(match.get("ats_analysis"))
    ats_score = int(ats_data.get("ats_score", 0))

    # If ATS score is 0, compute it from keyword overlap
    if ats_score == 0:
        resume_text = report.get("_resume_text", "").lower()
        jd_text = report.get("_jd_text", "").lower()
        matched = _safe_list(ats_data.get("matched_keywords"))
        missing = _safe_list(ats_data.get("missing_keywords"))
        if matched or missing:
            total = len(matched) + len(missing)
            ats_score = int((len(matched) / total * 100)) if total > 0 else 0
        elif resume_text and jd_text:
            # Simple word overlap score
            jd_words = set(jd_text.split())
            resume_words = set(resume_text.split())
            overlap = jd_words & resume_words
            ats_score = min(int(len(overlap) / max(len(jd_words), 1) * 150), 100)
        else:
            ats_score = overall_score  # fallback to match score

    charts = {
        "score_dial": generate_score_dial(int(overall_score)),
        "radar":      generate_radar_chart(candidate_scores, required_scores),
        "ats_bar":    generate_ats_bar(ats_score),
        "salary":     generate_salary_range(
            india_band.get("min", "N/A"), india_band.get("median", "N/A"),
            india_band.get("max", "N/A"), india_sal.get("candidate_estimate", "N/A"),
            global_band.get("min", "N/A"), global_band.get("median", "N/A"),
            global_band.get("max", "N/A"),
        ),
        "ctc_donut":  generate_ctc_donut(
            _pct(ctc.get("fixed", 70)),
            _pct(ctc.get("variable", 15)),
            _pct(ctc.get("esops_rsus", 15)),
        ),
        "timeline":   generate_interview_timeline(rounds) if rounds else generate_interview_timeline([]),
        "confidence": generate_confidence_chart(_build_confidence_data(report)),
    }

    # ── Questions per round ───────────────────────────────────────────────────
    questions_by_round = []
    for r in _safe_list(rounds):
        r = _safe_dict(r)
        qs = _safe_dict(r.get("questions"))
        questions_by_round.append({
            "round_name":   r.get("name", ""),
            "technical":    _safe_list(qs.get("technical"))[:3],
            "behavioural":  _safe_list(qs.get("behavioural"))[:2],
            "curveball":    _safe_list(qs.get("curveball"))[:1],
        })

    # ── Skills normalisation ──────────────────────────────────────────────────
    must_have   = _safe_dict(skills.get("must_have"))
    nice_to_have = _safe_dict(skills.get("nice_to_have"))

    # ── Build template context ────────────────────────────────────────────────
    context = {
        # Meta
        "candidate_name": report.get("candidate_name", "Candidate"),
        "target_company": report.get("target_company", ""),
        "target_role":    report.get("target_role", ""),
        "detected_role":  report.get("detected_role_type", ""),
        "generated_at":   datetime.now().strftime("%d %B %Y"),

        # Charts
        "chart_score_dial": charts["score_dial"],
        "chart_radar":      charts["radar"],
        "chart_ats":        charts["ats_bar"],
        "chart_salary":     charts["salary"],
        "chart_ctc":        charts["ctc_donut"],
        "chart_timeline":   charts["timeline"],
        "chart_confidence": charts["confidence"],

        # Match
        "overall_score":        overall_score,
        "dimensions":           dimensions,
        "skills_must_matched":  _safe_list(must_have.get("matched")),
        "skills_must_missing":  _safe_list(must_have.get("missing")),
        "skills_nice_matched":  _safe_list(nice_to_have.get("matched")),
        "skills_nice_missing":  _safe_list(nice_to_have.get("missing")),
        "skills_bonus":         _safe_list(skills.get("bonus_skills")),
        "ats_score":            ats_score,
        "ats_warnings":         _safe_list(ats_data.get("format_warnings")),
        "experience_fit":       _safe_dict(match.get("experience_fit")),
        "shining_points":       shining,
        "jd_flags":             _safe_dict(match.get("jd_flags")),

        # Interview
        "rounds":               rounds,
        "questions_by_round":   questions_by_round,
        "total_rounds":         interview.get("total_rounds", len(rounds)),
        "typical_timeline":     interview.get("typical_timeline", ""),
        "interview_confidence": interview.get("confidence", ""),
        "data_freshness":       interview.get("data_freshness", ""),
        "source_urls":          _safe_list(interview.get("source_urls")),

        # Salary
        "india_band":           india_band,
        "india_ctc":            ctc,
        "india_estimate":       india_sal.get("candidate_estimate", ""),
        "india_negotiability":  india_sal.get("negotiability", ""),
        "india_joining_bonus":  india_sal.get("joining_bonus", ""),
        "global_band":          global_band,
        "negotiation_tips":     _safe_list(salary.get("negotiation_tips")),

        # Links
        "link_results":      _safe_list(links.get("links")),
        "link_action_items": _safe_list(links.get("action_items")),

        # Branding
        "logo_base64": _load_logo_base64(),
        "app_name":    "JobSherpa",
    }

    # ── Render & convert ──────────────────────────────────────────────────────
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("report.html")
    html_content = template.render(**context)

    pdf_bytes = HTML(string=html_content).write_pdf()

    # Save as ADK artifact — renders as download button in UI
    artifact_part = types.Part(
        inline_data=types.Blob(
            mime_type="application/pdf",
            data=pdf_bytes,
        )
    )

    company = report.get("target_company", "report").lower().replace(" ", "_")
    filename = f"jobsherpa_{company}.pdf"

    version = await tool_context.save_artifact(
        filename=filename,
        artifact=artifact_part,
    )

    return {
        "status": "success",
        "message": f"PDF report generated! Click the download button in the chat to get your report.",
        "filename": filename,
        "version": version,
        "size_kb": round(len(pdf_bytes) / 1024, 1),
    }