"""Plot community growth metrics — cozy aesthetic for 小红书 / RedNote sharing."""

import json
from collections import Counter
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch

# Load data
with open("/tmp/gh_data.json") as f:
    data = json.load(f)

# --- Data prep ---
contributor_first = data["contributor_first"]
first_dates = sorted(contributor_first.values())
dates_contributors = []
cumulative = 0
for date_str in first_dates:
    cumulative += 1
    dates_contributors.append((datetime.strptime(date_str, "%Y-%m-%d"), cumulative))

pr_dates = data["pr_closed_dates"]
pr_counter = Counter(pr_dates)
sorted_pr_dates = sorted(pr_counter.keys())
cumulative_prs = []
total = 0
for d in sorted_pr_dates:
    total += pr_counter[d]
    cumulative_prs.append((datetime.strptime(d, "%Y-%m-%d"), total))

# --- Cozy warm palette ---
BG = "#FFF8F0"          # warm cream
CARD_BG = "#FFFFFF"
TEXT_DARK = "#5C4033"    # warm brown
TEXT_MID = "#9C8578"     # muted brown
TEXT_LIGHT = "#C4B0A5"
ACCENT1 = "#E8A87C"     # peach / warm orange
ACCENT2 = "#D4897A"     # dusty rose
GRID = "#F0E6DD"
SHADOW = "#E8DDD4"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": CARD_BG,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT_MID,
    "text.color": TEXT_DARK,
    "xtick.color": TEXT_LIGHT,
    "ytick.color": TEXT_LIGHT,
    "grid.color": GRID,
    "grid.alpha": 1.0,
    "font.family": "sans-serif",
    "font.size": 12,
})

# 3:4 portrait — ideal for 小红书 posts
fig, axes = plt.subplots(2, 1, figsize=(8, 10.67), gridspec_kw={"hspace": 0.38})

# ── Title area ──
fig.text(
    0.5, 0.965, "CoPaw Community Growth",
    ha="center", fontsize=26, fontweight="bold", color=TEXT_DARK,
    fontfamily="sans-serif",
)
fig.text(
    0.5, 0.94, "agentscope-ai/copaw  \u00b7  open sourced Feb 27, 2026",
    ha="center", fontsize=12, color=TEXT_MID,
)


def draw_card(ax):
    """Draw a rounded card background behind the axes."""
    ax.set_facecolor(CARD_BG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="both", length=0, pad=8)
    ax.grid(True, axis="y", linewidth=0.8)
    ax.grid(False, axis="x")


def draw_metric_badge(ax, value, label, color):
    """Draw a big friendly metric number with label."""
    ax.text(
        0.97, 0.95, str(value),
        transform=ax.transAxes, fontsize=48, fontweight="bold",
        color=color, ha="right", va="top", alpha=0.85,
    )
    ax.text(
        0.97, 0.73, label,
        transform=ax.transAxes, fontsize=14,
        color=TEXT_MID, ha="right", va="top",
    )


# ── Chart 1: Contributors ──
ax1 = axes[0]
x1 = [p[0] for p in dates_contributors]
y1 = [p[1] for p in dates_contributors]

ax1.plot(x1, y1, color=ACCENT1, linewidth=3, solid_capstyle="round", zorder=3)
ax1.fill_between(x1, y1, alpha=0.12, color=ACCENT1, zorder=2)
ax1.scatter([x1[-1]], [y1[-1]], color=ACCENT1, s=100, zorder=5,
            edgecolors="white", linewidths=2.5)

draw_card(ax1)
draw_metric_badge(ax1, y1[-1], "contributors", ACCENT1)
ax1.set_title("Contributors", fontsize=16, fontweight="bold",
              color=TEXT_DARK, pad=12, loc="left")
ax1.yaxis.set_major_locator(mticker.MaxNLocator(integer=True, nbins=5))

# ── Chart 2: PRs Closed ──
ax2 = axes[1]
x2 = [p[0] for p in cumulative_prs]
y2 = [p[1] for p in cumulative_prs]

ax2.plot(x2, y2, color=ACCENT2, linewidth=3, solid_capstyle="round", zorder=3)
ax2.fill_between(x2, y2, alpha=0.12, color=ACCENT2, zorder=2)
ax2.scatter([x2[-1]], [y2[-1]], color=ACCENT2, s=100, zorder=5,
            edgecolors="white", linewidths=2.5)

draw_card(ax2)
draw_metric_badge(ax2, y2[-1], "PRs closed", ACCENT2)
ax2.set_title("Pull Requests Closed", fontsize=16, fontweight="bold",
              color=TEXT_DARK, pad=12, loc="left")
ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True, nbins=5))

# ── Date formatting ──
for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha="center", fontsize=11)

# ── Footer ──
fig.text(
    0.5, 0.015, "github.com/agentscope-ai/copaw",
    ha="center", fontsize=10, color=TEXT_LIGHT, style="italic",
)

plt.savefig("community_growth_rednote.png", dpi=200, bbox_inches="tight",
            pad_inches=0.4, facecolor=BG)
print("Saved community_growth_rednote.png")
