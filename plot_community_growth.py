"""Plot community growth metrics for agentscope-ai/copaw GitHub project."""

import json
from collections import Counter
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load data
with open("/tmp/gh_data.json") as f:
    data = json.load(f)

# --- Chart 1: Cumulative contributors over time ---
contributor_first = data["contributor_first"]
# Sort contributors by their first contribution date
first_dates = sorted(contributor_first.values())
# Build cumulative series
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

# --- Plotting ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
fig.suptitle(
    "CoPaw (agentscope-ai/copaw) Community Growth\nSince Open Source (Feb 27, 2026)",
    fontsize=15,
    fontweight="bold",
    y=0.98,
)

# Plot 1: Contributors
x1 = [p[0] for p in dates_contributors]
y1 = [p[1] for p in dates_contributors]
ax1.step(x1, y1, where="post", color="#2563eb", linewidth=2.5)
ax1.fill_between(x1, y1, step="post", alpha=0.15, color="#2563eb")
ax1.set_ylabel("Cumulative Contributors", fontsize=12)
ax1.set_title("Number of Contributors Over Time", fontsize=13)
ax1.grid(True, alpha=0.3)
ax1.scatter(x1, y1, color="#2563eb", s=20, zorder=5)
# Annotate latest value
ax1.annotate(
    f"{y1[-1]} contributors",
    xy=(x1[-1], y1[-1]),
    xytext=(10, 10),
    textcoords="offset points",
    fontsize=10,
    fontweight="bold",
    color="#2563eb",
    arrowprops=dict(arrowstyle="->", color="#2563eb"),
)

# Plot 2: Closed PRs
x2 = [p[0] for p in cumulative_prs]
y2 = [p[1] for p in cumulative_prs]
ax2.step(x2, y2, where="post", color="#dc2626", linewidth=2.5)
ax2.fill_between(x2, y2, step="post", alpha=0.15, color="#dc2626")
ax2.set_ylabel("Cumulative Closed PRs", fontsize=12)
ax2.set_xlabel("Date", fontsize=12)
ax2.set_title("Number of PRs Closed Over Time", fontsize=13)
ax2.grid(True, alpha=0.3)
ax2.scatter(x2, y2, color="#dc2626", s=20, zorder=5)
# Annotate latest value
ax2.annotate(
    f"{y2[-1]} PRs closed",
    xy=(x2[-1], y2[-1]),
    xytext=(10, 10),
    textcoords="offset points",
    fontsize=10,
    fontweight="bold",
    color="#dc2626",
    arrowprops=dict(arrowstyle="->", color="#dc2626"),
)

# Format x-axis
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax2.xaxis.set_major_locator(mdates.DayLocator(interval=2))
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right")

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("community_growth.png", dpi=150, bbox_inches="tight")
print("Saved community_growth.png")
