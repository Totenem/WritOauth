"""Statistical primitives for authorship comparison.

Three feature kinds need three different treatments, and the old engine used
one (relative deviation against a bare mean) for everything:

* scalars       -> shrinkage z-score against mean + stdev
* counts        -> Anscombe-transformed Poisson z (sparse, often all-zero)
* distributions -> Jensen-Shannon divergence scaled by within-author spread

Everything ends up as a z, so one kernel converts z -> 0-100 for all of them
and profile aggregation happens in z-space.
"""

from __future__ import annotations

import math

# Prior strength for the shrinkage estimator, in "pseudo-observations".
# nu0 = 3 means the prior carries the weight of three baseline papers, so a
# student with 3 real papers is scored half on their own variance and half
# on the prior.
PRIOR_STRENGTH = 3.0

# Kernel width. |z| = k scores ~61, |z| = 2k scores ~13.5.
KERNEL_K = 2.0


def shrunk_sigma(
    sample_stdev: float | None,
    n: int,
    prior_sigma: float,
    floor: float,
) -> float:
    """Blend the student's own variability with a per-feature prior.

    A plain sample stdev is unusable at small n: two baseline papers landing
    0.3 words apart on mean sentence length give sigma = 0.21, so a perfectly
    normal third paper would score |z| = 20.

        sigma_eff = sqrt( (nu0*sigma0^2 + (n-1)*s^2) / (nu0 + n - 1) )

    At n = 1 the sample term vanishes and this is exactly `prior_sigma`, so
    there is no special case to write. By n >= 10 the prior is negligible.
    """
    prior_term = PRIOR_STRENGTH * prior_sigma * prior_sigma
    if sample_stdev is None or n < 2:
        blended = math.sqrt(prior_term / PRIOR_STRENGTH)
    else:
        sample_term = (n - 1) * sample_stdev * sample_stdev
        blended = math.sqrt((prior_term + sample_term) / (PRIOR_STRENGTH + n - 1))
    return max(blended, floor)


def scalar_z(
    value: float,
    baseline_mean: float,
    sample_stdev: float | None,
    n: int,
    prior_sigma: float,
    floor: float,
) -> float:
    """Signed z-score. Sign is kept for the explanation; scoring uses |z|."""
    sigma = shrunk_sigma(sample_stdev, n, prior_sigma, floor)
    if sigma <= 0:
        return 0.0
    return (value - baseline_mean) / sigma


def count_z(events: int, baseline_rate_per_word: float, submission_words: int) -> float:
    """Anscombe-transformed Poisson z for sparse event counts.

        z = 2*( sqrt(k + 3/8) - sqrt(mu + 3/8) )

    A Gaussian z is wrong here: the common case is zero errors in every
    baseline paper, where the sample stdev is 0 and z is undefined. This
    handles every degenerate case correctly, including the one that matters
    most for ghostwriting - an established error habit *disappearing*
    (mu = 8, k = 0 -> z ~ -5.2), which a naive implementation scores as a
    perfect match.
    """
    if submission_words <= 0:
        return 0.0
    expected = max(0.0, baseline_rate_per_word) * submission_words
    return 2.0 * (math.sqrt(events + 0.375) - math.sqrt(expected + 0.375))


def jensen_shannon(p: dict[str, float], q: dict[str, float]) -> float:
    """Jensen-Shannon divergence in bits, bounded [0, 1].

    Symmetric and finite even when a bin is missing from one side, which
    plain KL divergence is not.

    Deliberately *not* additively smoothed. JSD is already well-defined with
    zero bins, because the mixture m = (p+q)/2 is >= p/2 wherever p > 0.
    Adding the usual 0.5/|bins| pseudo-count would inject ~33% of the total
    mass as noise and compress every distribution feature toward zero -
    disjoint distributions would score 0.35 instead of the correct 1.0.
    """
    keys = set(p) | set(q)
    if not keys:
        return 0.0

    p_norm = _normalize(p, keys)
    q_norm = _normalize(q, keys)

    divergence = 0.0
    for key in keys:
        p_i, q_i = p_norm[key], q_norm[key]
        m_i = 0.5 * (p_i + q_i)
        if p_i > 0:
            divergence += 0.5 * p_i * math.log2(p_i / m_i)
        if q_i > 0:
            divergence += 0.5 * q_i * math.log2(q_i / m_i)
    return max(0.0, min(1.0, divergence))


def _normalize(dist: dict[str, float], keys: set[str]) -> dict[str, float]:
    raw = {k: max(0.0, dist.get(k, 0.0)) for k in keys}
    total = sum(raw.values())
    if total <= 0:
        # An empty distribution (e.g. a paper with no transitions at all)
        # compares as uniform rather than blowing up.
        uniform = 1.0 / len(keys)
        return {k: uniform for k in keys}
    return {k: v / total for k, v in raw.items()}


def kernel(z: float, k: float = KERNEL_K) -> float:
    """Map a z-score to a 0-100 consistency score.

        score = 100 * exp(-0.5 * (|z|/k)^2)

    Smooth, monotone and saturating. The previous engine used
    `max(0, 100 - relative_deviation*100)`, which clipped hard: every
    deviation from 100% to 1000% read as exactly 0.0, discarding
    information precisely where the signal is strongest.
    """
    if k <= 0:
        return 0.0
    ratio = abs(z) / k
    return 100.0 * math.exp(-0.5 * ratio * ratio)


def weighted_rms(values: list[tuple[float, float]]) -> float:
    """Weighted root-mean-square of z-scores: sqrt(sum(w*z^2)/sum(w)).

    Aggregating *scores* by weighted mean dilutes the signal - seven features
    at 100 and one at 20 averages to 90, i.e. the engine shrugs at a 5-sigma
    anomaly. RMS in z-space keeps large deviations visible.

    Note this assumes independence; the features are correlated, so it
    over-counts somewhat. The statistically correct fix (Mahalanobis with a
    full covariance matrix) needs far more baseline papers than a student
    will ever have, so the mitigation is to drop near-duplicate features and
    split weight across correlated pairs instead.
    """
    total_weight = sum(w for w, _ in values)
    if total_weight <= 0:
        return 0.0
    total = sum(w * z * z for w, z in values)
    return math.sqrt(total / total_weight)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stdev(values: list[float]) -> float | None:
    """Sample standard deviation (ddof=1); None when undefined."""
    if len(values) < 2:
        return None
    avg = mean(values)
    variance = sum((v - avg) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)
