"""Evaluate explicit system-name detection (registry v1 rules) on the AI-assisted reference labels.

Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/p1_mention_eval.py
Reference = coder A/B agreement, else the blind adjudicator (data/p1/mentions/). Unit = (item, system) pair.
Compared methods (same registry):
  rules_v1         : ml.src.systems.find_systems "identified" systems (the shipped method)
  no_context_rule  : same matcher but ambiguous names accepted without context (ablation)
  substring        : any name/alias as a normalised substring, no boundaries (naive baseline)
Writes results/p1/mention_metrics_registry_v<version>.json. Registry v1 was frozen (commit a3035f4) before the
labels existed -> its numbers are the unbiased estimate. Later registry versions add aliases found in v1's error
analysis on THIS sample, so their numbers are in-sample (optimistic) and are reported as such.
"""
import json
from collections import Counter
from pathlib import Path

import yaml

from sklearn.metrics import cohen_kappa_score as cohen_kappa
from ml.src.systems import Registry, find_systems, norm

ML = Path(__file__).resolve().parents[1]
D = ML / "data/p1/mentions"


def prf(pred, ref):
    tp = sum(len(pred[i] & ref[i]) for i in ref)
    fp = sum(len(pred[i] - ref[i]) for i in ref)
    fn = sum(len(ref[i] - pred[i]) for i in ref)
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = 2 * p * r / (p + r) if p and r else None
    exact = sum(pred[i] == ref[i] for i in ref) / len(ref)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p and round(p, 4), "recall": r and round(r, 4),
            "f1": f and round(f, 4), "item_exact_match": round(exact, 4)}


def main():
    sample = [json.loads(l) for l in (D / "sample.jsonl").read_text(encoding="utf-8").splitlines()]
    A = {l["id"]: l for l in json.loads((D / "coder_a.json").read_text())["labels"]}
    B = {l["id"]: l for l in json.loads((D / "coder_b.json").read_text())["labels"]}
    adj = {l["id"]: set(l["systems"]) for l in json.loads((D / "adjudication.json").read_text())["labels"]}
    ref = {}
    for r in sample:
        i = r["id"]
        a, b = set(A[i]["systems"]), set(B[i]["systems"])
        ref[i] = a if a == b else adj[i]
    cfg = yaml.safe_load((ML / "configs/systems.yaml").read_text(encoding="utf-8"))
    reg = Registry(cfg)
    cfg_nc = json.loads(json.dumps(cfg))
    for s in cfg_nc["systems"]:
        s["aliases"] = s.get("aliases", []) + s.pop("ambiguous", [])
        s.pop("exclude_after", None)
    reg_nc = Registry(cfg_nc)
    names = [(s["id"], norm(a)) for s in cfg["systems"] for a in s.get("aliases", []) + s.get("ambiguous", [])]
    pred = {"rules_v1": {}, "no_context_rule": {}, "substring": {}}
    status, possible_true, possible_all, rows = Counter(), 0, 0, []
    for r in sample:
        i, t = r["id"], r["text"]
        res = find_systems(t, reg)
        pred["rules_v1"][i] = {s["system_id"] for s in res["systems"]}
        pred["no_context_rule"][i] = {s["system_id"] for s in find_systems(t, reg_nc)["systems"]}
        pred["substring"][i] = {sid for sid, a in names if a in norm(t)}
        status[res["status"]] += 1
        poss = {p["system_id"] for p in res["possible_mentions"]} - pred["rules_v1"][i]
        possible_all += len(poss)
        possible_true += len(poss & ref[i])
        if pred["rules_v1"][i] != ref[i]:
            rows.append({"id": i, "stratum": r["stratum"], "ref": sorted(ref[i]), "pred": sorted(pred["rules_v1"][i]),
                         "possible": sorted(poss), "text": t[:160]})
    ids = [r["id"] for r in sample]
    pairs = sorted({s for i in ids for s in ref[i] | set(A[i]["systems"]) | set(B[i]["systems"])})
    ya = [int(s in A[i]["systems"]) for i in ids for s in pairs]
    yb = [int(s in B[i]["systems"]) for i in ids for s in pairs]
    out = {"label_note": "Reference = AI-assisted labels (coder A sonnet, coder B fable, adjudicator opus), NOT human gold.",
           "registry_version": cfg["version"], "n_items": len(sample),
           "strata": dict(Counter(r["stratum"] for r in sample)),
           "reference_positive_pairs": sum(len(v) for v in ref.values()),
           "items_with_reference_mention": sum(bool(v) for v in ref.values()),
           "agreement": {"items_same_system_set": sum(set(A[i]["systems"]) == set(B[i]["systems"]) for i in ids),
                         "pair_level_kappa": round(cohen_kappa(ya, yb), 4), "adjudicated_items": len(adj),
                         "items_with_uncertain_flag": sum(bool(A[i]["uncertain_ids"] or B[i]["uncertain_ids"]) for i in ids)},
           "methods": {m: prf(p, ref) for m, p in pred.items()},
           "rules_v1_status_counts": dict(status),
           "rules_v1_possible_mentions": {"n": possible_all, "true_mention_per_reference": possible_true},
           "rules_v1_errors": rows,
           "unregistered_names_by_coders": dict(Counter(u for i in ids for u in set(A[i]["unregistered"]) & set(B[i]["unregistered"])).most_common(20))}
    strat = {r["id"]: r["stratum"] for r in sample}
    out["methods_by_stratum"] = {st: {m: prf({i: p[i] for i in ids if strat[i] == st}, {i: ref[i] for i in ids if strat[i] == st})
                                      for m, p in pred.items()} for st in ("name_hit", "gov_app_no_hit")}
    out["estimate_type"] = "unbiased (registry frozen before labels)" if str(cfg["version"]) == "1" else "IN-SAMPLE / optimistic (aliases added after error analysis on this sample)"
    (ML / f"results/p1/mention_metrics_registry_v{cfg['version']}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps({k: out[k] for k in ("reference_positive_pairs", "items_with_reference_mention", "agreement", "methods",
                                          "rules_v1_status_counts", "rules_v1_possible_mentions", "unregistered_names_by_coders")}, indent=1, ensure_ascii=False))
    print(json.dumps(out["methods_by_stratum"], ensure_ascii=False))


if __name__ == "__main__":
    main()
