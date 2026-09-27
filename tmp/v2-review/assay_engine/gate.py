"""Keep a learned change only if it PROVABLY helps.

A "change" is anything the agent learns, e.g. new few-shot examples distilled
from human corrections. We score the same held-out items before and after the
change. Items the change leaves alone tell us nothing; what matters is

    fixed  = items that went wrong -> right
    broke  = items that went right -> wrong

Given m = fixed + broke discordant items, the accuracy change is
(fixed - broke) / n. Conditional on m, fixed ~ Binomial(m, pi) and the change
is (m / n) * (2 * pi - 1). We put an exact one-sided Clopper-Pearson bound on
pi and map it through that formula (the exact McNemar / sign-test approach),
so it stays valid with a handful of discordant items, e.g. "fixes 11,
breaks 0" is already a significant improvement.
"""
from __future__ import annotations

import math
from typing import Mapping

from .bounds import lower_bound, upper_bound

__all__ = ["gate_change"]


def _as_mapping(x) -> dict:
    """Accept {item: bool}, [{item|key, correct}], or [bool] (keyed by position)."""
    if isinstance(x, Mapping):
        return {k: bool(v) for k, v in x.items()}
    x = list(x)
    if x and isinstance(x[0], Mapping):
        return {r.get("item", r.get("key")): bool(r["correct"]) for r in x}
    return {i: bool(v) for i, v in enumerate(x)}


def gate_change(before, after, margin: float = 0.0, alpha: float = 0.05) -> dict:
    """Decide whether to keep a change, from paired before/after correctness.

    ``before`` / ``after``: correctness of the same held-out items, as
    {item: bool}, a list of {item, correct} dicts, or two equal-length lists of
    bools. Only items present in both are used.

    Verdict (bounds are one-sided at level 1 - alpha):
      "KEEP"     lower bound of (after - before) accuracy > margin
      "DISCARD"  upper bound < 0 (it provably hurts)
      "UNPROVEN" otherwise; need_n estimates the extra items needed.

    Returns {verdict, n, fixed, broke, fixed_items, broke_items, acc_before,
    acc_after, delta, lower, upper, need_n, margin, alpha}; delta/lower/upper
    are fractions (x100 for percentage points).
    """
    b, a = _as_mapping(before), _as_mapping(after)
    if not isinstance(before, Mapping) and not isinstance(after, Mapping) and len(b) != len(a):
        raise ValueError("before and after must describe the same items")
    items = [k for k in b if k in a]
    n = len(items)
    fixed_items = [k for k in items if not b[k] and a[k]]
    broke_items = [k for k in items if b[k] and not a[k]]
    f, br = len(fixed_items), len(broke_items)
    m = f + br

    out = {"verdict": "UNPROVEN", "n": n, "fixed": f, "broke": br,
           "fixed_items": fixed_items, "broke_items": broke_items,
           "acc_before": None, "acc_after": None, "delta": 0.0,
           "lower": 0.0, "upper": 0.0, "need_n": None, "margin": margin, "alpha": alpha}
    if n == 0:
        return out

    out["acc_before"] = sum(b[k] for k in items) / n
    out["acc_after"] = sum(a[k] for k in items) / n
    delta = (f - br) / n
    scale = m / n
    lo = scale * (2 * lower_bound(f, m, alpha) - 1) if m else 0.0
    hi = scale * (2 * upper_bound(f, m, alpha) - 1) if m else 0.0
    out.update(delta=delta, lower=lo, upper=hi)

    if lo > margin:
        out["verdict"] = "KEEP"
    elif hi < 0:
        out["verdict"] = "DISCARD"
    else:
        # Scale n by (current half-width / needed half-width)^2, aiming for
        # the verdict the point estimate points to.
        if delta > margin:
            factor = ((delta - lo) / (delta - margin)) ** 2
        elif delta < 0:
            factor = ((hi - delta) / (-delta)) ** 2
        else:
            factor = None
        if factor is not None:
            out["need_n"] = max(1, math.ceil(n * factor) - n)
    return out
