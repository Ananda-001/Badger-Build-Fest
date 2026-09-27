"""Confidence bands: where is the agent's precision PROVEN good enough to act?

Input everywhere is a list of judgment dicts (see docs/SCHEMA.md), of which we
use three fields:

    relation    the predicted relation ("duplicate" | "part_of" | "related").
                Judgments predicting "none" are not actions and are skipped.
    confidence  the model's confidence in [0, 1].
    correct     bool, whether the prediction matched ground truth. Judgments
                with correct=None (unlabelled) are skipped.

Precision here means: of the predictions the agent WOULD act on, the fraction
that are right. Every decision uses a one-sided lower confidence bound (exact
Clopper-Pearson by default), so "auto" means "precision is at least `target`,
with confidence 1 - alpha", not merely "the point estimate looks high".
"""
from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

from .bounds import lower_bound, lower_bound_array

__all__ = [
    "precision_bands",
    "precision_bands_by_relation",
    "auto_threshold",
    "auto_threshold_by_relation",
    "extra_needed",
    "RELATIONS",
]

RELATIONS = ("duplicate", "part_of", "related")
DEFAULT_FIXED_EDGES = (0.5, 0.7, 0.85, 0.95, 1.0)


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def _actions(judgments: Iterable[dict], relation: str | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Return (confidence, correct) arrays for labelled, non-"none" predictions."""
    conf, ok = [], []
    for j in judgments:
        rel = j.get("relation")
        if rel is None or rel == "none" or j.get("correct") is None:
            continue
        if relation is not None and rel != relation:
            continue
        conf.append(float(j["confidence"]))
        ok.append(bool(j["correct"]))
    return np.asarray(conf, dtype=float), np.asarray(ok, dtype=bool)


def extra_needed(k: int, n: int, target: float, alpha: float = 0.05,
                 method: str = "cp", cap: int = 10_000_000) -> int | None:
    """Approximate extra examples needed for the lower bound to reach `target`.

    Assumes the observed precision k/n stays the same as more data arrives, and
    finds the smallest total N with lower_bound(p*N, N) >= target. Returns
    0 if already there, None if the observed precision is not above target
    (more data at this precision can never prove it) or N would exceed `cap`.
    """
    if n == 0:
        return None
    p = k / n
    if p <= target:
        return None
    if lower_bound(k, n, alpha, method) >= target:
        return 0

    def ok(N: int) -> bool:
        return lower_bound(p * N, N, alpha, method) >= target

    lo, hi = n, max(2 * n, 1)
    while not ok(hi):  # exponential search for an N that is enough
        lo, hi = hi, hi * 2
        if hi > cap:
            return None
    while hi - lo > 1:  # binary search for the smallest such N
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi - n


def _quantile_edges(conf: np.ndarray, min_per_band: int, max_bands: int) -> list[float]:
    """Edges at confidence quantiles, aiming for >= min_per_band items per band."""
    if conf.size == 0:
        return [0.0, 1.0]
    n_bands = max(1, min(max_bands, conf.size // min_per_band))
    qs = np.quantile(conf, np.linspace(0.0, 1.0, n_bands + 1))
    edges = [float(conf.min())]
    for q in qs[1:-1]:
        # Ties can make quantiles coincide; drop duplicate edges.
        if edges[-1] < q < conf.max():
            edges.append(float(q))
    edges.append(float(conf.max()))  # all-tied data gives one band [c, c]
    return edges


# ----------------------------------------------------------------------------
# per-band view
# ----------------------------------------------------------------------------
def precision_bands(judgments: Sequence[dict], target: float = 0.95, alpha: float = 0.05,
                    edges: Sequence[float] | None = None, *, min_per_band: int = 20,
                    max_bands: int = 5, useful_floor: float = 0.5, method: str = "cp",
                    relation: str | None = None) -> list[dict]:
    """Split predictions into confidence bands and decide an action per band.

    Bands are [lo, hi) except the last, which is [lo, hi]. With ``edges=None``
    the edges are confidence quantiles chosen so each band has about
    ``min_per_band`` (default 20) items or more, up to ``max_bands`` bands.
    With fixed edges (e.g. [0.5, 0.7, 0.85, 0.95, 1.0]) predictions outside
    [edges[0], edges[-1]] are ignored.

    Each band is a dict:
        lo_conf, hi_conf  band limits
        n, k              predictions in the band, and how many were correct
        precision         k / n (None if n == 0)
        lower             one-sided (1 - alpha) lower bound on precision
        action            "auto"    if lower >= target (proven good enough)
                          "suggest" if precision >= useful_floor (show to a human)
                          "silent"  otherwise (not worth anyone's attention)
        need_n            extra examples needed for lower to reach target at
                          the observed precision (0 if auto, None if the
                          precision is not above target)

    Note: each band is tested on its own. For the single number the product
    uses ("act above this confidence"), use :func:`auto_threshold`.
    """
    conf, ok = _actions(judgments, relation)
    if edges is None:
        edges = _quantile_edges(conf, min_per_band, max_bands)
    edges = [float(e) for e in edges]
    if len(edges) < 2 or any(b < a for a, b in zip(edges, edges[1:])):
        raise ValueError("edges must be a non-decreasing list of at least 2 values")

    bands = []
    for i, (lo, hi) in enumerate(zip(edges, edges[1:])):
        last = i == len(edges) - 2
        mask = (conf >= lo) & ((conf <= hi) if last else (conf < hi))
        n = int(mask.sum())
        k = int(ok[mask].sum())
        prec = k / n if n else None
        low = lower_bound(k, n, alpha, method)
        if n and low >= target:
            action = "auto"
        elif prec is not None and prec >= useful_floor:
            action = "suggest"
        else:
            action = "silent"
        bands.append({
            "lo_conf": lo, "hi_conf": hi, "n": n, "k": k,
            "precision": prec, "lower": low, "action": action,
            "need_n": extra_needed(k, n, target, alpha, method),
        })
    return bands


def precision_bands_by_relation(judgments: Sequence[dict], target: float = 0.95,
                                alpha: float = 0.05, edges: Sequence[float] | None = None,
                                relations: Sequence[str] = RELATIONS, **kw) -> dict[str, list[dict]]:
    """:func:`precision_bands` computed separately for each predicted relation."""
    return {r: precision_bands(judgments, target, alpha, edges, relation=r, **kw) for r in relations}


# ----------------------------------------------------------------------------
# cumulative view: one cutoff for the product
# ----------------------------------------------------------------------------
def _start_size(mistakes: int, target: float, alpha: float, method: str, n_max: int) -> int | None:
    """Smallest n at which a record with `mistakes` errors (n - mistakes correct) proves target."""
    n = np.arange(mistakes + 1, n_max + 1)
    if n.size == 0:
        return None
    ok = lower_bound_array(n - mistakes, n, alpha, method) >= target
    return int(n[np.argmax(ok)]) if ok.any() else None


def auto_threshold(judgments: Sequence[dict], target: float = 0.95, alpha: float = 0.05, *,
                   method: str = "cp", relation: str | None = None,
                   tolerate: Sequence[int] = (0, 3), sequential: bool = True) -> dict | None:
    """Lowest confidence cutoff at which acting automatically is PROVEN safe.

    For a cutoff t, the "auto set" is every prediction with confidence >= t.
    A cutoff qualifies when the one-sided lower bound on the auto set's
    precision is >= target. Returns the lowest cutoff we may trust, or None.

    Why not simply "the lowest cutoff that passes"? Looking at hundreds of
    cutoffs and keeping the best is a multiple-testing trap: when the true
    precision sits just under the target, some cutoff passes by luck far more
    often than alpha. So by default (``sequential=True``) we use a
    FIXED-SEQUENCE procedure, which keeps the overall error rate <= alpha:

      * cutoffs (the distinct confidence values) are tested from the HIGHEST
        down, i.e. the smallest, most confident set first;
      * the walk goes down while cutoffs keep qualifying and stops at the
        first one that fails; every cutoff at or above the answer qualifies.

    Where the walk starts matters. Starting at the smallest set that could
    pass with a perfect record (59 items for 95%) means one confident mistake
    at the very top ends the walk at once. Starting later (a set big enough to
    pass with a few mistakes) is robust to that, but cannot find a threshold
    in small data. ``tolerate=(0, 3)`` runs one walk from each kind of start
    (0 and 3 mistakes tolerated), splits alpha evenly between them
    (Bonferroni), and returns the lowest cutoff any walk reached. Start points
    depend only on counts, never on which items are correct, so this stays
    valid. Use ``tolerate=(0,)`` for the plain single walk.

    ``sequential=False`` returns the lowest passing cutoff whose set is large
    enough to pass with a perfect record, ignoring everything above it. It
    finds more, but its false-auto rate can exceed alpha (roughly 7% at
    alpha=0.05 when the true precision is 1 point under target, in our
    simulations). Useful for exploration, not for switching on auto mode.

    Returns {threshold, n, k, precision, lower, target, alpha} or None; `lower`
    is the bound at the level actually used (alpha / len(tolerate) if sequential).
    """
    conf, ok = _actions(judgments, relation)
    if conf.size == 0:
        return None

    order = np.argsort(-conf, kind="stable")
    conf_s, ok_s = conf[order], ok[order]
    cum_k = np.cumsum(ok_s)
    # Index of the last item of each distinct-confidence group, in descending
    # order, so candidate set i = all items with confidence >= conf_s[ends[i]].
    ends = np.flatnonzero(np.r_[conf_s[1:] != conf_s[:-1], True])
    ns, ks = ends + 1, cum_k[ends]

    starts = tuple(tolerate) if sequential else (0,)
    level = alpha / len(starts) if sequential else alpha
    lows = lower_bound_array(ks, ns, level, method)
    passed = lows >= target

    best = None  # index into ends of the lowest trusted cutoff
    for mistakes in starts:
        n0 = _start_size(mistakes, target, level, method, conf.size)
        if n0 is None:
            continue
        idx = np.flatnonzero(ns >= n0)
        if not sequential:
            hits = idx[passed[idx]]
            reached = int(hits[-1]) if hits.size else None
        else:
            fails = idx[~passed[idx]]
            stop = fails[0] if fails.size else len(ns)  # first failure ends the walk
            walked = idx[idx < stop]
            reached = int(walked[-1]) if walked.size else None
        if reached is not None and (best is None or reached > best):
            best = reached
    if best is None:
        return None
    n, k = int(ns[best]), int(ks[best])
    return {"threshold": float(conf_s[ends[best]]), "n": n, "k": k, "precision": k / n,
            "lower": float(lows[best]), "target": target, "alpha": alpha}


def auto_threshold_by_relation(judgments: Sequence[dict], target: float = 0.95, alpha: float = 0.05,
                               relations: Sequence[str] = RELATIONS, **kw) -> dict[str, dict | None]:
    """:func:`auto_threshold` computed separately for each predicted relation."""
    return {r: auto_threshold(judgments, target, alpha, relation=r, **kw) for r in relations}
