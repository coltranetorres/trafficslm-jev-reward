"""Label audit and null-road check on test (read-only, no network, needs the local cache).

Reads jev_rl/results/cache (gitignored) and data/processed/test.jsonl plus one run's stored predictions.
A cache miss raises instead of calling the API. Writes jev_rl/results/label_audit_test.md.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

sys.modules.setdefault("requests", types.ModuleType("requests"))
_d = types.ModuleType("dotenv")
_d.load_dotenv = lambda *a, **k: None
sys.modules.setdefault("dotenv", _d)

import jev_client  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
CACHE = HERE / "results" / "cache"
RUN = "gemma3-1b-lora-n207"


def cached(state, questions, cache_dir, model=jev_client.DEFAULT_MODEL):
    p = Path(cache_dir) / f"{jev_client.cache_key(model, state, questions)}.json"
    if not p.exists():
        raise RuntimeError("cache miss (this script never calls the API)")
    return json.loads(p.read_text())


import reward  # noqa: E402

reward.query_jev = cached
import analyze  # noqa: E402
from questions import choice_probs, field_questions, road_question, state_for  # noqa: E402
from trafficslm.data import load_split  # noqa: E402
from trafficslm.schema import parse_report  # noqa: E402

ENUM = ("incident_type", "severity", "road_obstruction")


def main() -> None:
    recs = {r.id: r for r in load_split("test")}
    tags = {}
    for line in open("data/processed/test.jsonl"):
        d = json.loads(line)
        tags[d["id"]] = d.get("tags", [])
    rows = []
    pred_road = {}
    for line in open(f"experiments/{RUN}/predictions_test.jsonl"):
        d = json.loads(line)
        g = recs[d["id"]]
        rep = parse_report(d["raw"])
        pred_road[d["id"]] = None if rep is None else rep.location.road
        ans = cached(state_for(g.text), field_questions(), CACHE)
        for f in ENUM:
            p = choice_probs(ans, f)
            gl = getattr(g, f)
            cl = getattr(rep, f) if rep else None
            rows.append((d["id"], f, gl, cl, p.get(gl, 0.0), p.get(cl, 0.0) if rep else None))
        if g.location.road:
            pr = float(cached(state_for(g.text), road_question(g.location.road), CACHE)["road_match"]["noul"])
            rows.append((d["id"], "road", g.location.road, rep.location.road if rep else None, pr, None))
    A = [r for r in rows if r[1] != "road" and r[3] == r[2] and r[4] < 0.1]
    B = [r for r in rows if r[1] != "road" and r[3] is not None and r[3] != r[2] and r[5] >= 0.9 and r[4] < 0.1]
    C = [r for r in rows if r[1] == "road" and r[4] < 0.1]
    out = ["# Label audit and null-road check (test, gemma3-1b-lora-n207, B1 probabilities)", "",
           "Produced by `jev_rl/scripts/label_audit.py` from the gitignored cache. Read-only.", "",
           f"- A: candidate equals gold but B1 probability of gold < 0.1: {len(A)} field cases",
           f"- B: candidate differs from gold, B1 gives candidate >= 0.9 and gold < 0.1: {len(B)} field cases",
           f"- C: gold road with B1 road_match < 0.1: {len(C)} case(s)", ""]
    for title, L in (("A", A), ("B", B), ("C", C)):
        out += [f"## {title}", "", "| id | field | gold | candidate | B1 p(gold) | tags |", "|---|---|---|---|---|---|"]
        out += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]:.2f} | {','.join(tags[r[0]]) or '-'} |" for r in L]
        out.append("")
    ids = sorted({r[0] for r in A + B})
    tagged = [i for i in ids if tags[i]]
    out += [f"Items with any disagreement in A or B: {len(ids)}; of these tagged contradictory/ambiguous/noisy: "
            f"{len(tagged)} ({', '.join(f'{i}:{tags[i][0]}' for i in tagged)})", ""]
    out += ["## Null-road rule (B1 scores a null predicted road 0.0 with no call)", ""]
    for d in ("b1", "b2"):
        sc = analyze.score_run(Path("experiments") / RUN, "test", CACHE, d)
        P = [r for r in sc if r["parseable"]]
        NN = [r for r in P if pred_road[r["id"]] is not None]
        nulls = [r for r in P if pred_road[r["id"]] is None]
        ok = [r for r in nulls if r["match"]["road"]]
        out.append(f"- {d.upper()}: road AUROC all parseable ({len(P)}) {analyze._row_auroc(P, 'road'):.3f}; "
                   f"non-null predicted road ({len(NN)}) {analyze._row_auroc(NN, 'road'):.3f}; "
                   f"null predictions {len(nulls)}, of which gold-correct (null/null) {len(ok)}")
    out.append(f"- gold road null items in test: {sum(1 for g in recs.values() if g.location.road is None)}")
    path = HERE / "results" / "label_audit_test.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
