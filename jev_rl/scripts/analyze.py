"""Agreement of Jev rewards (B1/B2) with gold matches, plus run ranking."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reward import FIELDS, gold_match, reward_for
from trafficslm.data import load_split
from trafficslm.metrics import bootstrap_ci
from trafficslm.schema import parse_report

HERE = Path(__file__).resolve().parents[1]
RESULTS = HERE / "results"
DEFAULT_CACHE = RESULTS / "cache"
DEFAULT_LOG = RESULTS / "test_runs.log"
DESIGNS = ("b1", "b2")
PRED_FILE = {"validation": "predictions.jsonl", "test": "predictions_test.jsonl"}


def auroc(scores: list[float], labels: list[bool]) -> float | None:
    """Rank-based AUROC (Mann-Whitney), tied scores get averaged ranks."""
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    rank_sum = sum(r for r, y in zip(ranks, labels) if y)
    return (rank_sum - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def spearman(a: list[float], b: list[float]) -> float | None:
    def rk(x):
        s = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and x[s[j + 1]] == x[s[i]]:
                j += 1
            for k in range(i, j + 1):
                r[s[k]] = (i + j) / 2
            i = j + 1
        return r
    ra, rb = rk(a), rk(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra)
    vb = sum((y - mb) ** 2 for y in rb)
    return cov / (va * vb) ** 0.5 if va and vb else None


def score_run(run_dir: Path, split: str, cache_dir: Path, design: str) -> list[dict]:
    gold = {r.id: r for r in load_split(split)}
    rows = []
    with open(Path(run_dir) / PRED_FILE[split], encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            p = json.loads(line)
            g = gold[p["id"]]
            rew = reward_for(g.text, p["raw"], cache_dir, design)
            rows.append({"id": p["id"], "reward": rew,
                         "parseable": parse_report(p["raw"]) is not None,
                         "match": gold_match(g, parse_report(p["raw"]))})
    return rows


def _fmt(v):
    return "n/a" if v is None else f"{v:.3f}"


def _row_auroc(rows: list[dict], f: str) -> float | None:
    return auroc([r["reward"][f] for r in rows], [r["match"][f] for r in rows])


def _macro(rows: list[dict], f: str) -> float | None:
    """Mean of per-run AUROCs (runs where AUROC is undefined are skipped)."""
    vals = [v for run in sorted({r["run"] for r in rows})
            if (v := _row_auroc([r for r in rows if r["run"] == run], f)) is not None]
    return sum(vals) / len(vals) if vals else None


def cluster_ci(rows: list[dict], metric, n_boot: int = 1000, seed: int = 0) -> tuple[float, float]:
    """Bootstrap CI resampling item ids (all rows of an item move together)."""
    ids = sorted({r["id"] for r in rows})
    by_id = {i: [r for r in rows if r["id"] == i] for i in ids}

    def on_idx(idx: list[int]) -> float:
        v = metric([r for k in idx for r in by_id[ids[k]]])
        return float("nan") if v is None else v
    return bootstrap_ci(on_idx, len(ids), n_boot=n_boot, seed=seed)


def _cell(rows: list[dict], f: str, metric=None) -> str:
    metric = metric or (lambda rs: _row_auroc(rs, f))
    a = metric(rows)
    if a is None:
        return "n/a (one class)"
    lo, hi = cluster_ci(rows, metric)
    return f"{a:.3f} [{lo:.3f}, {hi:.3f}]"


def _parseable(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["parseable"]]


def build_report(split: str, runs: list[str], scored: dict) -> str:
    for run in runs:
        for d in DESIGNS:
            for r in scored[run][d]:
                r["run"] = run
    out = [f"# Jev agreement ({split})", "",
           "AUROC of reward vs gold match per field (95% CI from bootstrap resampling item ids). "
           "Probabilities are rounded to 2 decimals; ties get averaged ranks.", "",
           "**Headline figures are parseable-only**: rows whose output does not parse get reward 0 "
           "and match False by construction, so they are separable trivially. AUROC that includes "
           "unparseable rows is shown for completeness but is NOT comparable across runs, because "
           "runs differ in parse rate and base rate. Pooled figures stack the same items once per "
           "run, so CIs resample item ids (cluster bootstrap).", ""]
    out += ["## Unparseable outputs per run", "", "| run | unparseable / total |", "|---|---|"]
    for run in runs:
        rows = scored[run]["b1"]
        out.append(f"| {run} | {len(rows) - len(_parseable(rows))} / {len(rows)} |")
    out.append("")
    for run in runs:
        out += [f"## {run}", "",
                "| field | gold acc | B1 AUROC (parseable) | B2 AUROC (parseable) | B1 AUROC (all rows) | B2 AUROC (all rows) |",
                "|---|---|---|---|---|---|"]
        for f in FIELDS:
            b1, b2 = scored[run]["b1"], scored[run]["b2"]
            acc = sum(r["match"][f] for r in b1) / len(b1)
            out.append(f"| {f} | {acc:.3f} | {_cell(_parseable(b1), f)} | {_cell(_parseable(b2), f)} "
                       f"| {_cell(b1, f)} | {_cell(b2, f)} |")
        out.append("")
    pooled = {d: [r for run in runs for r in scored[run][d]] for d in DESIGNS}
    out += ["## Macro-averaged over runs (mean of per-run parseable-only AUROC)", "",
            "| field | B1 AUROC | B2 AUROC |", "|---|---|---|"]
    for f in FIELDS:
        m = lambda rs, f=f: _macro(rs, f)
        out.append(f"| {f} | {_cell(_parseable(pooled['b1']), f, m)} | {_cell(_parseable(pooled['b2']), f, m)} |")
    out += ["", "## Pooled over runs, parseable-only (secondary; mixes between-run differences)", "",
            "| field | B1 AUROC | B2 AUROC |", "|---|---|---|"]
    for f in FIELDS:
        out.append(f"| {f} | {_cell(_parseable(pooled['b1']), f)} | {_cell(_parseable(pooled['b2']), f)} |")
    out += ["", "## Pooled over runs, all rows (not comparable across runs; confounded by parseability)", "",
            "| field | B1 AUROC | B2 AUROC |", "|---|---|---|"]
    for f in FIELDS:
        out.append(f"| {f} | {_cell(pooled['b1'], f)} | {_cell(pooled['b2'], f)} |")
    out.append("")
    # ranking
    gold_mean = {}
    for run in runs:
        rows = scored[run]["b1"]
        gold_mean[run] = sum(sum(r["match"][f] for f in FIELDS) / len(FIELDS) for r in rows) / len(rows)
    out += ["## Run ranking: mean composite reward vs gold mean field accuracy", "",
            "| run | gold mean field acc | B1 mean composite | B2 mean composite |", "|---|---|---|---|"]
    comp = {d: {} for d in DESIGNS}
    for run in runs:
        for d in DESIGNS:
            comp[d][run] = sum(r["reward"]["composite"] for r in scored[run][d]) / len(scored[run][d])
        out.append(f"| {run} | {gold_mean[run]:.3f} | {comp['b1'][run]:.3f} | {comp['b2'][run]:.3f} |")
    out.append("")
    g = [gold_mean[r] for r in runs]
    gorder = sorted(runs, key=lambda r: -gold_mean[r])
    out.append(f"Gold order (best first): {' > '.join(gorder)}")
    for d in DESIGNS:
        c = [comp[d][r] for r in runs]
        order = sorted(runs, key=lambda r: -comp[d][r])
        n = len(runs)
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        agree = sum((g[i] - g[j]) * (c[i] - c[j]) > 0 for i, j in pairs)
        out.append(f"- {d.upper()} order: {' > '.join(order)}; Spearman {_fmt(spearman(g, c))}; "
                   f"pairwise order agreement {agree}/{len(pairs)}")
    if len(runs) < 2:
        caution = "Caution: a single run was scored, so no ranking across runs can be assessed."
    else:
        caution = (f"Caution: with only {len(runs)} runs and near-tied pairs (see the table), Spearman values are not a "
                   "meaningful difference between designs; the ranking evidence is weak for both.")
    out += ["", caution, ""]
    return "\n".join(out)


def main(argv: list[str] | None = None, log_path: Path = DEFAULT_LOG,
         cache_dir: Path = DEFAULT_CACHE) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=list(PRED_FILE), required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--experiments", default="experiments")
    args = ap.parse_args(argv)
    runs = [r for r in args.runs.split(",") if r]
    if args.split == "test":
        if not args.final:
            sys.exit("--split test requires --final")
        done = set(Path(log_path).read_text().split()) if Path(log_path).exists() else set()
        repeat = [r for r in runs if r in done]
        if repeat:
            sys.exit(f"refusing: already scored on test: {repeat}")
    scored = {run: {d: score_run(Path(args.experiments) / run, args.split, cache_dir, d)
                    for d in DESIGNS} for run in runs}
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{args.split}_agreement.md"
    path.write_text(build_report(args.split, runs, scored), encoding="utf-8")
    if args.split == "test":
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n".join(runs) + "\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
