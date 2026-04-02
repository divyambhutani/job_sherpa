"""
chart_generator.py
Generates all matplotlib charts used in the JobSherpa PDF report.
Each function returns a base64-encoded PNG string for embedding in HTML.
"""

import io
import base64
import math
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — required for Cloud Run
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np


# ── Brand Colors ─────────────────────────────────────────────────────────────
BG         = "#0f0f1a"
CARD       = "#1a1a2e"
BLUE       = "#4285F4"
GREEN      = "#34A853"
RED        = "#EA4335"
GOLD       = "#FBBC05"
TEXT       = "#ffffff"
TEXT_SEC   = "#a0a0c0"
PURPLE     = "#9c27b0"
ORANGE     = "#FF6D00"


def _fig_to_base64(fig) -> str:
    """Convert a matplotlib figure to a base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=BG, edgecolor="none")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


# ── Chart 1: Score Dial (Speedometer) ────────────────────────────────────────
def generate_score_dial(score: int) -> str:
    """
    Generate a speedometer/gauge chart for the overall match score.
    Score 0-100. Red < 50, Yellow 50-75, Green > 75.
    """
    fig, ax = plt.subplots(figsize=(6, 4), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # Draw colored arc segments
    theta_start = math.pi        # 180 degrees
    theta_end   = 0              # 0 degrees
    total_range = theta_start - theta_end

    segments = [
        (0,  50,  RED),
        (50, 75,  GOLD),
        (75, 100, GREEN),
    ]

    for seg_start, seg_end, color in segments:
        t_start = theta_start - (seg_start / 100) * total_range
        t_end   = theta_start - (seg_end   / 100) * total_range
        theta   = np.linspace(t_start, t_end, 100)
        ax.fill_between(theta, 0.65, 1.0, color=color, alpha=0.85)

    # Needle
    needle_angle = theta_start - (score / 100) * total_range
    ax.annotate(
        "",
        xy=(needle_angle, 0.9),
        xytext=(needle_angle, 0.0),
        arrowprops=dict(arrowstyle="-|>", color=TEXT, lw=2.5),
    )

    # Score text in center
    ax.text(
        0, 0, f"{score}",
        ha="center", va="center",
        fontsize=36, fontweight="bold", color=TEXT,
        transform=ax.transData,
    )
    ax.text(
        0, -0.25, "Match Score",
        ha="center", va="center",
        fontsize=11, color=TEXT_SEC,
        transform=ax.transData,
    )

    ax.set_ylim(0, 1)
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.axis("off")

    return _fig_to_base64(fig)


# ── Chart 2: Radar / Spider Chart ────────────────────────────────────────────
def generate_radar_chart(candidate_scores: dict, required_scores: dict) -> str:
    """
    Generate a radar/spider chart with two overlapping shapes:
    - Blue: candidate profile
    - Red: job requirement

    Args:
        candidate_scores: {dimension: score 0-100}
        required_scores:  {dimension: score 0-100}
    Both dicts must have the same keys.
    """
    labels = list(candidate_scores.keys())
    N = len(labels)

    candidate_vals = [candidate_scores[k] for k in labels]
    required_vals  = [required_scores[k]  for k in labels]

    # Repeat first value to close the polygon
    candidate_vals += candidate_vals[:1]
    required_vals  += required_vals[:1]

    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(CARD)

    # Grid styling
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(
        [l.replace("_", " ").title() for l in labels],
        color=TEXT, fontsize=9,
    )
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], color=TEXT_SEC, fontsize=7)
    ax.set_ylim(0, 100)
    ax.grid(color=TEXT_SEC, alpha=0.2)
    ax.spines["polar"].set_color(TEXT_SEC)

    # Required shape (red) — draw first so blue appears on top
    ax.plot(angles, required_vals, color="#FF6B6B", linewidth=2.5, linestyle="--", alpha=0.9)
    ax.fill(angles, required_vals, color="#FF6B6B", alpha=0.2)

    # Candidate shape (bright blue) — drawn on top
    ax.plot(angles, candidate_vals, color="#64B5F6", linewidth=2.5, alpha=1.0)
    ax.fill(angles, candidate_vals, color="#64B5F6", alpha=0.35)

    # Legend
    legend = [
        mpatches.Patch(color="#64B5F6", alpha=0.8, label="Your Profile"),
        mpatches.Patch(color="#FF6B6B", alpha=0.5, label="Job Requirement"),
    ]
    ax.legend(
        handles=legend,
        loc="upper right",
        bbox_to_anchor=(1.3, 1.1),
        facecolor=CARD,
        edgecolor=TEXT_SEC,
        labelcolor=TEXT,
        fontsize=9,
    )

    return _fig_to_base64(fig)


# ── Chart 3: ATS Score Bar ────────────────────────────────────────────────────
def generate_ats_bar(ats_score: int) -> str:
    """
    Generate a horizontal bar showing the ATS score.
    """
    fig, ax = plt.subplots(figsize=(7, 1.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # Background track
    ax.barh(0, 100, color=CARD, height=0.5)

    # Score bar
    color = GREEN if ats_score >= 75 else (GOLD if ats_score >= 50 else RED)
    ax.barh(0, ats_score, color=color, height=0.5)

    # Label
    ax.text(
        ats_score + 1, 0, f"{ats_score}/100",
        va="center", ha="left", color=TEXT, fontsize=11, fontweight="bold",
    )
    ax.text(
        -1, 0, "ATS Score",
        va="center", ha="right", color=TEXT_SEC, fontsize=9,
    )

    ax.set_xlim(-15, 115)
    ax.axis("off")

    return _fig_to_base64(fig)


# ── Chart 4: Salary Range Bar ─────────────────────────────────────────────────
def generate_salary_range(
    india_min: str, india_median: str, india_max: str, india_estimate: str,
    global_min: str, global_median: str, global_max: str,
) -> str:
    """
    Generate side-by-side salary range bars for India and Global.
    Values are strings like "₹18L" or "$110K".
    """
    fig, axes = plt.subplots(1, 2, figsize=(10, 3))
    fig.patch.set_facecolor(BG)

    datasets = [
        {
            "ax": axes[0],
            "title": "India (INR)",
            "min": india_min, "median": india_median,
            "max": india_max, "estimate": india_estimate,
            "color": BLUE,
        },
        {
            "ax": axes[1],
            "title": "Global (USD)",
            "min": global_min, "median": global_median,
            "max": global_max, "estimate": None,
            "color": PURPLE,
        },
    ]

    for d in datasets:
        ax = d["ax"]
        ax.set_facecolor(CARD)
        ax.set_title(d["title"], color=TEXT, fontsize=11, fontweight="bold", pad=10)

        labels = ["Min", "Median", "Max"]
        values = [d["min"], d["median"], d["max"]]
        colors = [d["color"] + "88", d["color"], d["color"] + "aa"]

        bars = ax.barh(labels, [1, 1, 1], color=colors, height=0.5)

        for i, (label, val) in enumerate(zip(labels, values)):
            ax.text(
                0.5, i, val,
                ha="center", va="center",
                color=TEXT, fontsize=11, fontweight="bold",
            )

        if d["estimate"]:
            ax.text(
                0.5, -0.7,
                f"Your estimate: {d['estimate']}",
                ha="center", va="center",
                color=GOLD, fontsize=9, fontstyle="italic",
            )

        ax.set_xlim(0, 1)
        ax.set_ylim(-1, 3)
        ax.axis("off")

    plt.tight_layout()
    return _fig_to_base64(fig)


# ── Chart 5: CTC Breakdown Donut ─────────────────────────────────────────────
def generate_ctc_donut(fixed: float, variable: float, esop: float) -> str:
    """
    Generate a donut chart showing CTC breakdown.
    Args: percentages as floats (e.g. 70, 15, 15)
    """
    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    sizes  = [fixed, variable, esop]
    labels = [f"Fixed\n{fixed:.0f}%", f"Variable\n{variable:.0f}%", f"ESOP/RSU\n{esop:.0f}%"]
    colors = [BLUE, GREEN, GOLD]

    wedges, texts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        startangle=90,
        wedgeprops={"width": 0.5, "edgecolor": BG, "linewidth": 2},
        textprops={"color": TEXT, "fontsize": 9},
    )

    ax.text(
        0, 0, "CTC\nBreakdown",
        ha="center", va="center",
        color=TEXT, fontsize=10, fontweight="bold",
    )

    return _fig_to_base64(fig)


# ── Chart 6: Interview Timeline ───────────────────────────────────────────────
def generate_interview_timeline(rounds: list[dict]) -> str:
    """
    Generate a horizontal timeline of interview rounds.

    Args:
        rounds: list of {name, duration, difficulty}
        difficulty: "easy" | "medium" | "hard" | "very_hard"
    """
    difficulty_colors = {
        "easy":      GREEN,
        "medium":    GOLD,
        "hard":      ORANGE,
        "very_hard": RED,
    }

    n = len(rounds)
    fig, ax = plt.subplots(figsize=(max(10, n * 2.5), 3))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # Draw connecting line
    ax.plot([0, n - 1], [0, 0], color=TEXT_SEC, linewidth=2, zorder=1)

    for i, round_ in enumerate(rounds):
        diff  = round_.get("difficulty", "medium").lower()
        color = difficulty_colors.get(diff, GOLD)
        name  = round_.get("name", f"Round {i+1}")
        dur   = round_.get("duration", "")

        # Circle node
        circle = plt.Circle((i, 0), 0.3, color=color, zorder=2)
        ax.add_patch(circle)

        # Round number inside circle
        ax.text(
            i, 0, str(i + 1),
            ha="center", va="center",
            color=TEXT, fontsize=10, fontweight="bold", zorder=3,
        )

        # Round name above
        ax.text(
            i, 0.6, name,
            ha="center", va="bottom",
            color=TEXT, fontsize=8, fontweight="bold",
        )

        # Duration below
        ax.text(
            i, -0.6, dur,
            ha="center", va="top",
            color=TEXT_SEC, fontsize=7,
        )

    # Offer star at end
    ax.text(
        n - 0.2, 0.15, "🎯",
        ha="left", va="center", fontsize=16,
    )

    # Difficulty legend
    legend_handles = [
        mpatches.Patch(color=GREEN,  label="Easy"),
        mpatches.Patch(color=GOLD,   label="Medium"),
        mpatches.Patch(color=ORANGE, label="Hard"),
        mpatches.Patch(color=RED,    label="Very Hard"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper right",
        facecolor=CARD,
        edgecolor=TEXT_SEC,
        labelcolor=TEXT,
        fontsize=8,
    )

    ax.set_xlim(-0.8, n + 0.3)
    ax.set_ylim(-1.2, 1.4)
    ax.axis("off")

    return _fig_to_base64(fig)


# ── Chart 7: Confidence Dots ──────────────────────────────────────────────────
def generate_confidence_chart(confidence_data: list[dict]) -> str:
    """
    Generate a dot-based confidence chart for sources page.

    Args:
        confidence_data: list of {section, confidence, sources_count}
        confidence: "LOW" | "FAIR" | "HIGH"
    """
    confidence_map = {"LOW": 1, "FAIR": 3, "HIGH": 5}
    colors_map     = {"LOW": RED, "FAIR": GOLD, "HIGH": GREEN}

    n   = len(confidence_data)
    fig, ax = plt.subplots(figsize=(8, max(2, n * 0.8)))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    for i, item in enumerate(confidence_data):
        y          = n - i - 1
        section    = item.get("section", "")
        confidence = item.get("confidence", "FAIR").upper()
        src_count  = item.get("sources_count", 0)
        dots       = confidence_map.get(confidence, 3)
        color      = colors_map.get(confidence, GOLD)

        # Section label
        ax.text(0, y, section, color=TEXT, fontsize=10, va="center")

        # Dots
        for d in range(5):
            dot_color = color if d < dots else CARD
            circle = plt.Circle((4.5 + d * 0.4, y), 0.13,
                                 color=dot_color, zorder=2)
            ax.add_patch(circle)

        # Confidence label
        ax.text(
            7, y, f"{confidence} · {src_count} sources",
            color=TEXT_SEC, fontsize=9, va="center",
        )

    ax.set_xlim(-0.5, 10)
    ax.set_ylim(-0.5, n)
    ax.axis("off")

    return _fig_to_base64(fig)