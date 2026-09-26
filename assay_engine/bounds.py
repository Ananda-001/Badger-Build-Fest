"""Confidence intervals for a binomial proportion (k successes out of n).

Two families are provided:

* Wilson score: a closed-form interval that behaves well for small n and for
  proportions near 0 or 1. Approximate, but usually close to nominal coverage.
* Clopper-Pearson ("exact"): built by inverting the binomial test. Coverage is
  guaranteed to be at least the nominal level, so it is conservative. This is
  the default for anything that decides whether the agent may act on its own.

Conventions used throughout this package:

* ``alpha`` is the total error rate. A two-sided interval puts alpha/2 in each
  tail; a one-sided bound puts all of alpha in its single tail.
* With n == 0 nothing is known, so every interval is (0.0, 1.0).
"""
from __future__ import annotations

import math

import numpy as np
from scipy import stats

__all__ = [
    "wilson_interval",
    "clopper_pearson_interval",
    "lower_bound",
    "upper_bound",
    "proportion_interval",
    "lower_bound_array",
]

METHODS = ("cp", "wilson")


def _check(k: float, n: float, alpha: float) -> None:
    if n < 0 or k < 0 or k > n:
        raise ValueError(f"need 0 <= k <= n, got k={k}, n={n}")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")


def _wilson_bounds(k: float, n: float, z: float) -> tuple[float, float]:
    """Wilson score interval for a given z (shared by one- and two-sided)."""
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def wilson_interval(k: float, n: float, alpha: float = 0.05) -> tuple[float, float]:
    """Two-sided Wilson score interval at confidence 1 - alpha."""
    _check(k, n, alpha)
    if n == 0:
        return 0.0, 1.0
    z = stats.norm.ppf(1.0 - alpha / 2.0)
    return _wilson_bounds(k, n, z)


def _cp_lower(k: float, n: float, tail: float) -> float:
    # Lower limit: the p at which P(X >= k | p) == tail  ->  Beta(k, n-k+1) quantile.
    if k <= 0:
        return 0.0
    return float(stats.beta.ppf(tail, k, n - k + 1))


def _cp_upper(k: float, n: float, tail: float) -> float:
    # Upper limit: the p at which P(X <= k | p) == tail  ->  Beta(k+1, n-k) quantile.
    if k >= n:
        return 1.0
    return float(stats.beta.ppf(1.0 - tail, k + 1, n - k))


def clopper_pearson_interval(k: float, n: float, alpha: float = 0.05) -> tuple[float, float]:
    """Two-sided Clopper-Pearson (exact) interval at confidence 1 - alpha."""
    _check(k, n, alpha)
    if n == 0:
        return 0.0, 1.0
    return _cp_lower(k, n, alpha / 2.0), _cp_upper(k, n, alpha / 2.0)


def lower_bound(k: float, n: float, alpha: float = 0.05, method: str = "cp") -> float:
    """One-sided lower confidence bound: P(true p >= bound) >= 1 - alpha.

    ``method`` is "cp" (Clopper-Pearson, default, conservative) or "wilson".
    Non-integer k is accepted (useful for "what if we had more data" maths).
    """
    _check(k, n, alpha)
    if n == 0:
        return 0.0
    if method == "cp":
        return _cp_lower(k, n, alpha)
    if method == "wilson":
        return _wilson_bounds(k, n, stats.norm.ppf(1.0 - alpha))[0]
    raise ValueError(f"method must be one of {METHODS}, got {method!r}")


def upper_bound(k: float, n: float, alpha: float = 0.05, method: str = "cp") -> float:
    """One-sided upper confidence bound: P(true p <= bound) >= 1 - alpha."""
    _check(k, n, alpha)
    if n == 0:
        return 1.0
    if method == "cp":
        return _cp_upper(k, n, alpha)
    if method == "wilson":
        return _wilson_bounds(k, n, stats.norm.ppf(1.0 - alpha))[1]
    raise ValueError(f"method must be one of {METHODS}, got {method!r}")


def proportion_interval(k: float, n: float, alpha: float = 0.05, method: str = "cp") -> tuple[float, float]:
    """Two-sided interval by name: method is "cp" or "wilson"."""
    if method == "cp":
        return clopper_pearson_interval(k, n, alpha)
    if method == "wilson":
        return wilson_interval(k, n, alpha)
    raise ValueError(f"method must be one of {METHODS}, got {method!r}")


def lower_bound_array(k, n, alpha: float = 0.05, method: str = "cp"):
    """Vectorised :func:`lower_bound` for numpy arrays of k and n (same rules)."""
    k = np.asarray(k, dtype=float)
    n = np.asarray(n, dtype=float)
    out = np.zeros(np.broadcast(k, n).shape)
    k, n = np.broadcast_to(k, out.shape), np.broadcast_to(n, out.shape)
    pos = (n > 0) & (k > 0)
    if method == "cp":
        out[pos] = stats.beta.ppf(alpha, k[pos], n[pos] - k[pos] + 1)
    elif method == "wilson":
        z = stats.norm.ppf(1.0 - alpha)
        nn, p = n[n > 0], k[n > 0] / n[n > 0]
        denom = 1.0 + z * z / nn
        centre = (p + z * z / (2.0 * nn)) / denom
        half = z * np.sqrt(p * (1.0 - p) / nn + z * z / (4.0 * nn * nn)) / denom
        out[n > 0] = np.maximum(0.0, centre - half)
    else:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    return out
