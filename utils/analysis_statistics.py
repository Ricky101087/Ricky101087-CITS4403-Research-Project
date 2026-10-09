"""Seed-block estimates for the fixed-factorial simulation experiments.

Each seed is one stochastic replicate. Fixed parameter settings within a seed
are averaged before estimating marginal uncertainty, never counted as extra
independent replicates. Intervals are deterministic percentile bootstrap CIs.
"""

from __future__ import annotations

import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping


CONDITION_FIELDS = (
    "preference_diversity", "mobility", "behaviour", "social_influence",
    "width", "height", "vacancy_rate", "group_split", "max_iterations",
    "influence_strength",
)
PROTOCOL_FIELDS = CONDITION_FIELDS[4:]


@dataclass(frozen=True)
class Estimate:
    mean: float
    lower: float | None
    upper: float | None
    n_seeds: int
    n_runs: int


def _percentile(values: list[float], probability: float) -> float:
    index = (len(values) - 1) * probability
    left = math.floor(index)
    right = math.ceil(index)
    return values[left] + (values[right] - values[left]) * (index - left)


def bootstrap_mean(
    values: Iterable[float], *, n_runs: int | None = None,
    resamples: int = 5000, seed: int = 4403,
) -> Estimate:
    """Estimate a mean from independent seed-level values with a 95% CI.

    With fewer than two seeds, uncertainty is unavailable rather than zero.
    Ten seeds yield limited precision: the bootstrap does not create new data.
    """
    values = [float(value) for value in values]
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError("The estimate requires finite observations")
    if isinstance(resamples, bool) or not isinstance(resamples, int) or resamples < 100:
        raise ValueError("resamples must be an integer of at least 100")
    count = len(values)
    mean = statistics.fmean(values)
    n_runs = count if n_runs is None else n_runs
    if count == 1:
        return Estimate(mean, None, None, count, n_runs)
    rng = random.Random(seed)
    samples = sorted(
        statistics.fmean(rng.choices(values, k=count))
        for _ in range(resamples)
    )
    return Estimate(mean, _percentile(samples, 0.025),
                    _percentile(samples, 0.975), count, n_runs)


def _condition(row: Mapping, *, omit_social: bool = False) -> tuple:
    fields = [field for field in CONDITION_FIELDS
              if not (omit_social and field == "social_influence")]
    return tuple(row.get(field) for field in fields)


def _check_protocol(rows: list[Mapping]) -> None:
    """Do not pool separate horizons, grids or other fixed protocols."""
    for field in PROTOCOL_FIELDS:
        if len({row.get(field) for row in rows}) > 1:
            raise ValueError(f"Mixed experimental protocol: {field}")


def seed_estimate(rows: Iterable[Mapping], metric: str, **bootstrap_options) -> Estimate:
    """Average the same fixed settings within each seed, then bootstrap seeds.

    Unbalanced blocks and duplicate seed/condition records are rejected. Load
    and validate the full expected experiment before calling this function.
    """
    rows = list(rows)
    _check_protocol(rows)
    blocks = defaultdict(dict)
    for row in rows:
        key = _condition(row)
        if key in blocks[row["seed"]]:
            raise ValueError("Duplicate seed/condition observation")
        value = row[metric]
        if value is None or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{metric} must contain finite numeric values")
        blocks[row["seed"]][key] = float(value)
    if not blocks:
        raise ValueError("No observations to estimate")
    expected = set(next(iter(blocks.values())))
    if any(set(block) != expected for block in blocks.values()):
        raise ValueError("Seeds do not cover the same fixed parameter settings")
    means = [statistics.fmean(blocks[seed].values()) for seed in sorted(blocks)]
    return bootstrap_mean(means, n_runs=len(rows), **bootstrap_options)


def grouped_estimates(
    rows: Iterable[Mapping], factor: str, metric: str,
    order=None, filters=None, **bootstrap_options,
) -> list[tuple[object, Estimate]]:
    """Return marginal estimates with one bootstrap observation per seed."""
    filters = filters or {}
    rows = [row for row in rows
            if all(row.get(field) == value for field, value in filters.items())]
    _check_protocol(rows)
    groups = defaultdict(list)
    for row in rows:
        groups[row[factor]].append(row)
    keys = list(groups) if order is None else [key for key in order if key in groups]
    return [(key, seed_estimate(groups[key], metric, **bootstrap_options)) for key in keys]


def paired_effect(rows: Iterable[Mapping], metric: str, **bootstrap_options) -> Estimate:
    """Estimate on-minus-off using exact pairs and independent seed blocks.

    Pairing uses the seed and every recorded experimental setting except the
    on/off switch. Missing or duplicate sides fail instead of being discarded.
    The result's n_runs counts matched pairs, not independent replicates.
    """
    pairs = {}
    for row in rows:
        enabled = row["social_influence"]
        if type(enabled) is not bool:
            raise ValueError("social_influence must be a boolean")
        key = (row["seed"], _condition(row, omit_social=True))
        sides = pairs.setdefault(key, {})
        if enabled in sides:
            raise ValueError("Duplicate side of a social-influence pair")
        sides[enabled] = row
    differences = []
    for sides in pairs.values():
        if set(sides) != {False, True}:
            raise ValueError("Missing on/off partner in social-influence comparison")
        on, off = sides[True], sides[False]
        if any(not isinstance(row[metric], (int, float))
               or not math.isfinite(row[metric]) for row in (on, off)):
            raise ValueError(f"{metric} must contain finite numeric values")
        differences.append({**off, "paired_difference": on[metric] - off[metric]})
    return seed_estimate(differences, "paired_difference", **bootstrap_options)


def condition_summaries(rows: Iterable[Mapping]) -> list[dict]:
    """Give each condition's stability rate and explicitly conditional time.

    Stopping-time means include capped runs. Conditional stabilisation-time
    means include stable runs only, with their denominator displayed alongside.
    """
    rows = list(rows)
    _check_protocol(rows)
    groups = defaultdict(list)
    for row in rows:
        key = tuple(row[field] for field in CONDITION_FIELDS[:4])
        groups[key].append(row)
    result = []
    for key in sorted(groups):
        values = groups[key]
        # Also rejects duplicate or unbalanced records in a condition.
        segregation = seed_estimate(values, "final_segregation_index")
        stable = [row for row in values if row["stabilised"]]
        result.append({
            **dict(zip(CONDITION_FIELDS[:4], key)),
            "runs": len(values), "stable_runs": len(stable),
            "capped_runs": len(values) - len(stable),
            "stabilised_fraction": len(stable) / len(values),
            "mean_stopping_time": statistics.fmean(row["iterations"] for row in values),
            "mean_stabilisation_time_if_stable": (
                statistics.fmean(row["stabilisation_time"] for row in stable)
                if stable else None
            ),
            "mean_segregation": segregation.mean,
            "segregation_ci_lower": segregation.lower,
            "segregation_ci_upper": segregation.upper,
            "mean_satisfaction": statistics.fmean(row["final_satisfaction_rate"] for row in values),
        })
    return result
