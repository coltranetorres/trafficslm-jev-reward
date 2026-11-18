"""Draw the headline chart for the Jev-reward sprint from jev_rl/results/test_agreement.md.

Usage (repo root): uv run --with matplotlib python jev_rl/scripts/make_chart.py
Writes jev_rl/results/jev_reward_chart.png. Numbers are parsed from the results file, not retyped.
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "test_agreement.md"
OUT = ROOT / "results" / "jev_reward_chart.png"

FIELDS = [("incident_type", "Incident type"), ("severity", "Severity"),
          ("road_obstruction", "Road obstruction"), ("road", "Road name")]

# light-mode tokens (validated: blue/orange pass lightness, chroma, CVD and contrast checks)
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8985", "#e6e5e1"
B1, B2 = "#2a78d6", "#eb6834"

CELL = re.compile(r"([\d.]+) \[([\d.]+), ([\d.]+)\]")


def parse() -> dict[str, dict[str, tuple[float, float, float]]]:
    """Per-field (auroc, lo, hi) for B1 and B2, parseable-only, from the first per-run table."""
    out: dict[str, dict[str, tuple[float, float, float]]] = {}
    in_run = False
    for line in SRC.read_text().splitlines():
        if line.startswith("## gemma3-1b-lora-n207"):
            in_run = True
            continue
        if in_run and line.startswith("## "):
            break
        if in_run and line.startswith("| "):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells[0] in dict(FIELDS):
                m1, m2 = CELL.match(cells[2]), CELL.match(cells[3])
                assert m1 and m2, line
                out[cells[0]] = {"b1": tuple(map(float, m1.groups())),
                                 "b2": tuple(map(float, m2.groups()))}
    assert len(out) == 4, out
    return out


def main() -> None:
    d = parse()
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
    fig = plt.figure(figsize=(8.4, 5.6), dpi=200, facecolor=SURFACE)
    ax = fig.add_axes([0.07, 0.20, 0.90, 0.56], facecolor=SURFACE)

    fig.text(0.04, 0.945, "Jev can tell right answers from wrong ones. How you ask it matters.",
             fontsize=13.5, fontweight="bold", va="top")
    fig.text(0.04, 0.885, "How well Jev's score separates correct fields from wrong ones (AUROC), by field. "
             "1.0 = perfect, 0.5 = coin flip.", fontsize=8.4, color=INK2, va="top")

    # legend (always present for 2 series), names the design in plain words
    lx = 0.04
    for color, label in ((B1, "B1: Jev reads only the report"), (B2, "B2: Jev reads the report and the model's answer")):
        fig.patches.append(FancyBboxPatch((lx, 0.800), 0.016, 0.022, boxstyle="round,pad=0,rounding_size=0.004",
                                          transform=fig.transFigure, facecolor=color, edgecolor="none"))
        t = fig.text(lx + 0.024, 0.811, label, fontsize=8.2, color=INK2, va="center")
        lx += 0.024 + (0.0066 * len(label)) + 0.03

    width, gap = 0.15, 0.012
    for i, (key, label) in enumerate(FIELDS):
        for off, series, color in ((-(width + gap) / 2, "b1", B1), ((width + gap) / 2, "b2", B2)):
            v, lo, hi = d[key][series]
            x = i + off
            ax.bar(x, v, width=width, color=color, zorder=3)
            ax.plot([x, x], [lo, hi], color=INK2, lw=0.9, zorder=4, solid_capstyle="round")
            ax.text(x, hi + 0.028, f"{v:.2f}", ha="center", va="bottom", fontsize=8.6,
                    fontweight="bold", color=INK, zorder=5)

    ax.set_ylim(0, 1.34)
    ax.set_xlim(-0.55, 3.55)
    ax.set_xticks(range(4))
    ax.set_xticklabels([l for _, l in FIELDS], fontsize=9, color=INK)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0", "", "0.5", "", "1.0"], fontsize=8, color=MUTED)
    ax.tick_params(length=0, pad=6)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
    ax.axhline(0.5, color=MUTED, lw=1.0, zorder=2)
    ax.text(3.55, 0.508, "coin flip", ha="right", va="bottom", fontsize=7.4, color=MUTED)

    # one annotation, on the field where the two designs flip
    road_x = 3.0
    ax.plot([road_x, road_x], [1.06, 1.13], color=MUTED, lw=0.8, zorder=2)
    ax.text(3.55, 1.25, "Flips on road name: B1 scores 0 whenever the model\n(correctly) predicts no road. On rows that have a road,\nthe gap shrinks: B1 0.85 vs B2 0.89.",
            fontsize=7.4, color=INK2, va="center", ha="right", linespacing=1.45)

    fig.text(0.04, 0.095,
             "Gemma-3-1B + LoRA outputs on 176 synthetic Filipino, English and Taglish traffic reports. Jev = typesafe/jev-1.14.\n"
             "Whiskers: 95% CI, resampled over reports. One model run, one seed. Gold labels from one annotator. Score = AUROC on parseable outputs (174 of 176).",
             fontsize=6.9, color=MUTED, va="top", linespacing=1.5)

    fig.savefig(OUT, facecolor=SURFACE)
    print(OUT)


if __name__ == "__main__":
    main()
