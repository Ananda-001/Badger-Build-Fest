"""Turn engine outputs into short human-readable strings and markdown tables."""
from __future__ import annotations

from typing import Mapping, Sequence

__all__ = [
    "pct", "pp",
    "describe_threshold", "describe_band", "bands_table", "thresholds_table",
    "describe_compare", "compare_table", "describe_gate", "gate_table",
]


def pct(x: float | None, digits: int = 1) -> str:
    """0.9723 -> '97.2%'; None -> '–'."""
    return "–" if x is None else f"{100 * x:.{digits}f}%"


def pp(x: float | None, digits: int = 1, already_pp: bool = False) -> str:
    """Signed percentage points: 0.055 -> '+5.5 pp' (or pass already_pp=True)."""
    if x is None:
        return "–"
    v = x if already_pp else 100 * x
    return f"{v:+.{digits}f} pp"


def _need(need_n: int | None) -> str:
    if need_n is None:
        return "–"
    return "0" if need_n == 0 else f"~{need_n}"


def _md(headers: Sequence[str], rows: Sequence[Sequence]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


# ---------------------------------------------------------------- bands
def describe_threshold(res: Mapping | None, target: float = 0.95, label: str = "") -> str:
    """One line for an :func:`auto_threshold` result.

    e.g. "Auto-act at confidence ≥ 0.91: precision 97.2% (proven ≥ 95.1%, n=214)"
    """
    prefix = f"{label}: " if label else ""
    if res is None:
        return f"{prefix}No confidence level is proven ≥ {pct(target)} precise yet; suggest only."
    return (f"{prefix}Auto-act at confidence ≥ {res['threshold']:.2f}: precision {pct(res['precision'])} "
            f"(proven ≥ {pct(res['lower'])}, n={res['n']})")


def describe_band(band: Mapping) -> str:
    """e.g. "0.85–0.95: 93.1% precise (proven ≥ 88.0%, n=58) → suggest; ~140 more to prove"."""
    s = (f"{band['lo_conf']:.2f}–{band['hi_conf']:.2f}: {pct(band['precision'])} precise "
         f"(proven ≥ {pct(band['lower'])}, n={band['n']}) → {band['action']}")
    if band["action"] != "auto" and band.get("need_n"):
        s += f"; ~{band['need_n']} more to prove"
    return s


def bands_table(bands: Sequence[Mapping] | Mapping[str, Sequence[Mapping]]) -> str:
    """Markdown table of :func:`precision_bands` output (or the by-relation dict)."""
    by_rel = isinstance(bands, Mapping)
    groups = bands.items() if by_rel else [(None, bands)]
    headers = (["relation"] if by_rel else []) + ["confidence", "n", "precision", "proven ≥", "action", "more needed"]
    rows = []
    for rel, bs in groups:
        for b in bs:
            rows.append(([rel] if by_rel else []) + [
                f"{b['lo_conf']:.2f}–{b['hi_conf']:.2f}", b["n"], pct(b["precision"]),
                pct(b["lower"]), b["action"], _need(b["need_n"])])
    return _md(headers, rows)


def thresholds_table(results: Mapping[str, Mapping | None]) -> str:
    """Markdown table of :func:`auto_threshold_by_relation` output."""
    rows = []
    for rel, r in results.items():
        if r is None:
            rows.append([rel, "none proven", "–", "–", "–"])
        else:
            rows.append([rel, f"≥ {r['threshold']:.2f}", r["n"], pct(r["precision"]), pct(r["lower"])])
    return _md(["relation", "auto at confidence", "n", "precision", "proven ≥"], rows)


# ---------------------------------------------------------------- compare
def describe_compare(res: Mapping, name_a: str = "reference", name_b: str = "candidate") -> str:
    """e.g. "CERTIFY: candidate is within 2.0 pp of reference (−0.4 pp, proven ≥ −1.7 pp) at −61.0% cost, n=400"."""
    v, n = res["verdict"], res["n"]
    if res["quality_pp"] is None:
        return f"{v}: no paired items yet."
    q = (f"{pp(res['quality_pp'], already_pp=True)} "
         f"[{pp(res['quality_lo_pp'], already_pp=True)}, {pp(res['quality_hi_pp'], already_pp=True)}]")
    c = "cost unknown" if res["cost_rel"] is None else (
        f"cost {res['cost_rel']:+.1%} [{res['cost_lo']:+.1%}, {res['cost_hi']:+.1%}]")
    if v == "CERTIFY":
        head = f"{name_b} can replace {name_a} (within {100 * res['margin']:.1f} pp, cheaper)"
    elif v == "REJECT":
        head = f"{name_b} cannot replace {name_a}: {res['reason']}"
    else:
        more = f"; ~{res['need_n']} more items needed" if res["need_n"] else ""
        head = f"not enough evidence yet ({res['reason']}){more}"
    return f"{v}: {head}. Quality {q}, {c}, n={n}."


def compare_table(res: Mapping, name_a: str = "A", name_b: str = "B") -> str:
    rows = [
        ["accuracy " + name_a, pct(res["acc_a"])],
        ["accuracy " + name_b, pct(res["acc_b"])],
        [f"quality ({name_b} − {name_a})",
         f"{pp(res['quality_pp'], already_pp=True)} (bounds {pp(res['quality_lo_pp'], already_pp=True)}"
         f" … {pp(res['quality_hi_pp'], already_pp=True)})"],
        ["cost change", "–" if res["cost_rel"] is None else
         f"{res['cost_rel']:+.1%} (bounds {res['cost_lo']:+.1%} … {res['cost_hi']:+.1%})"],
        [f"{name_b} right, {name_a} wrong", res["b_only_right"]],
        [f"{name_a} right, {name_b} wrong", res["a_only_right"]],
        ["n (paired items)", res["n"]],
        ["verdict", f"**{res['verdict']}**"],
        ["more items needed", _need(res["need_n"])],
    ]
    return _md(["", "value"], rows)


# ---------------------------------------------------------------- gate
def describe_gate(res: Mapping) -> str:
    """e.g. "KEEP: fixes 11, breaks 0 (accuracy 81.0% → 86.5%, +5.5 pp, proven ≥ +2.1 pp, n=200)"."""
    bound = (f"proven ≤ {pp(res['upper'])}" if res["verdict"] == "DISCARD"
             else f"proven ≥ {pp(res['lower'])}")
    s = (f"{res['verdict']}: fixes {res['fixed']}, breaks {res['broke']} "
         f"(accuracy {pct(res['acc_before'])} → {pct(res['acc_after'])}, {pp(res['delta'])}, "
         f"{bound}, n={res['n']})")
    if res["verdict"] == "UNPROVEN" and res["need_n"]:
        s += f"; ~{res['need_n']} more items needed"
    return s


def gate_table(res: Mapping) -> str:
    rows = [
        ["fixes (wrong → right)", res["fixed"]],
        ["breaks (right → wrong)", res["broke"]],
        ["accuracy before", pct(res["acc_before"])],
        ["accuracy after", pct(res["acc_after"])],
        ["change", f"{pp(res['delta'])} (bounds {pp(res['lower'])} … {pp(res['upper'])})"],
        ["n (held-out items)", res["n"]],
        ["verdict", f"**{res['verdict']}**"],
        ["more items needed", _need(res["need_n"])],
    ]
    return _md(["", "value"], rows)
