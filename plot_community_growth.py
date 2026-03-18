"""Plot community growth metrics for agentscope-ai/copaw GitHub project."""

import json
from collections import Counter
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

# Load data
with open("/tmp/gh_data.json") as f:
    data = json.load(f)

# --- Chart 1: Cumulative contributors over time ---
contributor_first = data["contributor_first"]
first_dates = sorted(contributor_first.values())
dates_contributors = []
cumulative = 0
for date_str in first_dates:
    cumulative += 1
    dates_contributors.append((datetime.strptime(date_str, "%Y-%m-%d"), cumulative))

# --- Chart 2: Cumulative closed PRs over time ---
pr_dates = data["pr_closed_dates"]
pr_counter = Counter(pr_dates)
sorted_pr_dates = sorted(pr_counter.keys())
cumulative_prs = []
total = 0
for d in sorted_pr_dates:
    total += pr_counter[d]
    cumulative_prs.append((datetime.strptime(d, "%Y-%m-%d"), total))

# --- Style: mobile-friendly, modern dark theme ---
plt.rcParams.update({
    "figure.facecolor": "#0d1117",
    "axes.facecolor": "#161b22",
    "axes.edgecolor": "#30363d",
    "axes.labelcolor": "#c9d1d9",
    "text.color": "#c9d1d9",
    "xtick.color": "#8b949e",
    "ytick.color": "#8b949e",
    "grid.color": "#21262d",
    "grid.alpha": 0.8,
    "font.family": "sans-serif",
    "font.size": 13,
})

# Tall portrait layout for mobile (roughly 9:16 aspect)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 13), gridspec_kw={"hspace": 0.35})

fig.text(
    0.5, 0.96,
    "CoPaw Community Growth",
    ha="center", fontsize=22, fontweight="bold", color="white",
)
fig.text(
    0.5, 0.935,
    "agentscope-ai/copaw  |  Since Open Source (Feb 27, 2026)",
    ha="center", fontsize=11, color="#8b949e",
)


def style_ax(ax, color, gradient_color):
    """Apply consistent styling to an axis."""
    ax.grid(True, axis="y", linewidth=0.5)
    ax.grid(False, axis="x")
    ax.tick_params(axis="both", length=0, pad=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#30363d")


# ── Plot 1: Contributors ──
x1 = [p[0] for p in dates_contributors]
y1 = [p[1] for p in dates_contributors]
color1 = "#58a6ff"
ax1.plot(x1, y1, color=color1, linewidth=2.5, solid_capstyle="round")
ax1.fill_between(x1, y1, alpha=0.08, color=color1)
ax1.scatter([x1[-1]], [y1[-1]], color=color1, s=80, zorder=5, edgecolors="white", linewidths=1.5)

# Big number callout
ax1.text(
    0.03, 0.92, f"{y1[-1]}",
    transform=ax1.transAxes, fontsize=42, fontweight="bold", color=color1,
    va="top",
)
ax1.text(
    0.03, 0.72, "contributors",
    transform=ax1.transAxes, fontsize=15, color="#8b949e", va="top",
)
ax1.set_ylabel("")
ax1.set_title("Contributors Over Time", fontsize=15, fontweight="bold", pad=14, loc="left")
ax1.yaxis.set_major_locator(mticker.MaxNLocator(integer=True, nbins=6))
style_ax(ax1, color1, color1)

# ── Plot 2: Closed PRs ──
x2 = [p[0] for p in cumulative_prs]
y2 = [p[1] for p in cumulative_prs]
color2 = "#f78166"
ax2.plot(x2, y2, color=color2, linewidth=2.5, solid_capstyle="round")
ax2.fill_between(x2, y2, alpha=0.08, color=color2)
ax2.scatter([x2[-1]], [y2[-1]], color=color2, s=80, zorder=5, edgecolors="white", linewidths=1.5)

# Big number callout
ax2.text(
    0.03, 0.92, f"{y2[-1]}",
    transform=ax2.transAxes, fontsize=42, fontweight="bold", color=color2,
    va="top",
)
ax2.text(
    0.03, 0.72, "PRs closed",
    transform=ax2.transAxes, fontsize=15, color="#8b949e", va="top",
)
ax2.set_ylabel("")
ax2.set_title("PRs Closed Over Time", fontsize=15, fontweight="bold", pad=14, loc="left")
ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True, nbins=6))
style_ax(ax2, color2, color2)

# Format x-axis dates
for ax in (ax1, ax2):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha="center", fontsize=11)

plt.savefig("community_growth.png", dpi=180, bbox_inches="tight", pad_inches=0.5)
print("Saved community_growth.png")
