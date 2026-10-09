"""Load and verify complete, explicitly selected experiment datasets.

Validation is against the requested design, not just the rows that happen to
exist. A partial result file must never become evidence for a completed study.
"""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from pathlib import Path
from typing import Iterable, Mapping

from utils.experiment_runner import (
    HISTORY_FIELDS,
    PREFERENCE_BOUNDS,
    SUMMARY_FIELDS,
    ExperimentConfig,
    design_settings,
    make_run_id,
)


INTEGER_FIELDS = {
    "seed", "width", "height", "mobility", "max_iterations", "iterations",
    "total_moves", "total_preference_updates", "iteration", "moves",
    "preference_updates",
}
FLOAT_FIELDS = {
    "vacancy_rate", "group_split", "preference_lower", "preference_upper",
    "initial_preference_mean", "initial_preference_std", "influence_strength",
    "final_segregation_index", "final_satisfaction_rate", "final_preference_mean",
    "final_preference_std", "satisfaction_rate", "segregation_index",
}
BOOLEAN_FIELDS = {"social_influence", "stabilised"}
NULLABLE_INTEGER_FIELDS = {"stabilisation_time"}
CONDITION_FIELDS = (
    "preference_diversity", "mobility", "behaviour", "social_influence",
)


def load_csv(path: str | Path) -> list[dict[str, object]]:
    """Read typed CSV rows, rejecting malformed numbers and boolean values.

    Only an empty field represents an absent stabilisation time. In particular,
    ``nan`` is never silently treated as missing or as a valid observation.
    """
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Missing experiment CSV: {path}")
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        names = reader.fieldnames
        if not names or any(not name for name in names):
            raise ValueError(f"{path}: missing or empty CSV header")
        if len(names) != len(set(names)):
            raise ValueError(f"{path}: duplicate CSV column names")
        for line, raw in enumerate(reader, start=2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"{path}:{line}: row does not match the CSV header")
            row: dict[str, object] = {}
            for field, raw_value in raw.items():
                value = raw_value.strip()
                try:
                    if field in BOOLEAN_FIELDS:
                        if value.lower() not in {"true", "false"}:
                            raise ValueError("expected True or False")
                        row[field] = value.lower() == "true"
                    elif field in INTEGER_FIELDS:
                        row[field] = int(value)
                    elif field in NULLABLE_INTEGER_FIELDS:
                        row[field] = int(value) if value else None
                    elif field in FLOAT_FIELDS:
                        number = float(value)
                        if not math.isfinite(number):
                            raise ValueError("expected a finite number")
                        row[field] = number
                    else:
                        row[field] = value
                except (ValueError, OverflowError) as error:
                    raise ValueError(
                        f"{path}:{line}: invalid {field}={raw_value!r}: {error}"
                    ) from error
            rows.append(row)
    return rows


def _typed_row(row: Mapping[str, object], fields: Iterable[str], label: str) -> None:
    missing = set(fields) - set(row)
    if missing:
        raise ValueError(f"{label}: missing columns {sorted(missing)}")
    for field in fields:
        value = row[field]
        if field in BOOLEAN_FIELDS:
            valid = isinstance(value, bool)
        elif field in INTEGER_FIELDS:
            valid = isinstance(value, int) and not isinstance(value, bool)
        elif field in NULLABLE_INTEGER_FIELDS:
            valid = value is None or (
                isinstance(value, int) and not isinstance(value, bool)
            )
        elif field in FLOAT_FIELDS:
            valid = (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
            )
        else:
            valid = isinstance(value, str) and bool(value)
        if not valid:
            raise ValueError(f"{label}: invalid type or non-finite value for {field}")


def _range(row: Mapping[str, object], field: str, low: float, high: float,
           label: str) -> None:
    if not low <= row[field] <= high:
        raise ValueError(f"{label}: {field} must be in [{low}, {high}]")


def _close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError(f"{label}: expected {expected}, found {actual}")


def validate_dataset(
    summary_rows: Iterable[Mapping[str, object]],
    history_rows: Iterable[Mapping[str, object]],
    expected_configs: Iterable[ExperimentConfig],
) -> dict[str, object]:
    """Require the complete requested design and reconcile every run's history.

    The exact expected run IDs enforce factor combinations, seeds, grid size,
    iteration cap and other configuration parameters. This is structural and
    numerical validation; it does not assert scientific correctness of a model.
    """
    configs = list(expected_configs)
    if not configs:
        raise ValueError("The expected experiment design is empty")
    expected = {make_run_id(config): config for config in configs}
    if len(expected) != len(configs):
        raise ValueError("The expected design contains duplicate configurations")

    summaries = {}
    for index, row in enumerate(summary_rows, start=1):
        label = f"Summary row {index}"
        _typed_row(row, SUMMARY_FIELDS, label)
        run_id = row["run_id"]
        if run_id in summaries:
            raise ValueError(f"Duplicate summary run ID: {run_id}")
        summaries[run_id] = row
    missing = set(expected) - set(summaries)
    unexpected = set(summaries) - set(expected)
    if missing or unexpected:
        raise ValueError(
            "Dataset does not match the requested design: "
            f"{len(missing)} missing runs, {len(unexpected)} unexpected runs. "
            "Check seeds, factor coverage and configuration (including max_iterations). "
            f"Missing examples: {sorted(missing)[:3]}; "
            f"unexpected examples: {sorted(unexpected)[:3]}"
        )

    histories = defaultdict(dict)
    history_count = 0
    for index, row in enumerate(history_rows, start=1):
        label = f"History row {index}"
        _typed_row(row, HISTORY_FIELDS, label)
        run_id = row["run_id"]
        if run_id not in expected:
            raise ValueError(f"History contains unexpected run ID: {run_id}")
        iteration = row["iteration"]
        if iteration in histories[run_id]:
            raise ValueError(f"{run_id}: duplicate history iteration {iteration}")
        histories[run_id][iteration] = row
        history_count += 1

    for run_id, config in expected.items():
        row = summaries[run_id]
        config_values = asdict(config)
        for field, value in config_values.items():
            if row[field] != value:
                raise ValueError(f"{run_id}: configuration mismatch for {field}")
        # The ID has already been checked against the hash of this expected
        # configuration. Comparing every recorded field also prevents relabelled
        # runs, without changing hashes when CSV parses a valid 1 as float 1.0.

        agents = int(config.width * config.height * (1 - config.vacancy_rate))
        if agents < 1:
            raise ValueError(f"{run_id}: configuration has no agents")
        _range(row, "iterations", 1, config.max_iterations, run_id)
        for field in (
            "final_segregation_index", "final_satisfaction_rate",
            "initial_preference_mean", "final_preference_mean",
        ):
            _range(row, field, 0, 1, run_id)
        for field in ("initial_preference_std", "final_preference_std"):
            _range(row, field, 0, 0.5, run_id)
        lower, upper = PREFERENCE_BOUNDS[config.preference_diversity]
        _close(row["preference_lower"], lower, f"{run_id}: preference_lower")
        _close(row["preference_upper"], upper, f"{run_id}: preference_upper")
        _close(row["initial_preference_mean"], 0.5, f"{run_id}: initial preference mean")
        _range(row, "initial_preference_std", 0, (upper - lower) / 2, run_id)
        for field in ("total_moves", "total_preference_updates"):
            _range(row, field, 0, agents * row["iterations"], run_id)

        if row["stabilised"]:
            if row["stabilisation_time"] != row["iterations"]:
                raise ValueError(f"{run_id}: stabilisation_time must equal iterations")
        elif row["stabilisation_time"] is not None:
            raise ValueError(f"{run_id}: a non-stabilised run needs null stabilisation_time")
        elif row["iterations"] != config.max_iterations:
            raise ValueError(f"{run_id}: non-stabilised run stopped before max_iterations")

        run_history = histories[run_id]
        required_iterations = set(range(1, row["iterations"] + 1))
        if set(run_history) != required_iterations:
            raise ValueError(
                f"{run_id}: incomplete history; expected iterations 1..{row['iterations']}"
            )
        for iteration, entry in run_history.items():
            for field in set(config_values) & set(HISTORY_FIELDS):
                if entry[field] != row[field]:
                    raise ValueError(f"{run_id}: history configuration mismatch for {field}")
            for field in ("moves", "preference_updates"):
                _range(entry, field, 0, agents, f"{run_id}, iteration {iteration}")
            for field in ("segregation_index", "satisfaction_rate"):
                _range(entry, field, 0, 1, f"{run_id}, iteration {iteration}")
            if (
                iteration < row["iterations"]
                and entry["moves"] == entry["preference_updates"] == 0
            ):
                raise ValueError(f"{run_id}: history continues after a stable iteration")
        final = run_history[row["iterations"]]
        stopped_stable = final["moves"] == final["preference_updates"] == 0
        if row["stabilised"] != stopped_stable:
            raise ValueError(f"{run_id}: stabilised flag disagrees with final history")
        _close(row["final_segregation_index"], final["segregation_index"],
               f"{run_id}: final segregation")
        _close(row["final_satisfaction_rate"], final["satisfaction_rate"],
               f"{run_id}: final satisfaction")
        for summary_field, history_field in (
            ("total_moves", "moves"),
            ("total_preference_updates", "preference_updates"),
        ):
            total = sum(entry[history_field] for entry in run_history.values())
            if row[summary_field] != total:
                raise ValueError(f"{run_id}: {summary_field} disagrees with history")
        if not config.social_influence or config.influence_strength == 0:
            if row["total_preference_updates"] != 0:
                raise ValueError(f"{run_id}: preference updates recorded with influence disabled")
            _close(row["final_preference_mean"], row["initial_preference_mean"],
                   f"{run_id}: unchanged preference mean")
            _close(row["final_preference_std"], row["initial_preference_std"],
                   f"{run_id}: unchanged preference variation")

    condition_counts = Counter(
        tuple(row[field] for field in CONDITION_FIELDS) for row in summaries.values()
    )
    stabilised = sum(row["stabilised"] for row in summaries.values())
    return {
        "runs": len(summaries),
        "expected_runs": len(configs),
        "history_rows": history_count,
        "seeds": sorted({config.seed for config in configs}),
        "stabilised_runs": stabilised,
        "capped_runs": len(summaries) - stabilised,
        "condition_counts": dict(condition_counts),
    }


def load_dataset(
    directory: str | Path,
    design: str = "main",
    max_iterations: int | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    """Load exactly the chosen design's matching summary/history CSV pair.

    An older pilot with a 150-step cap must be selected explicitly with
    ``design='pilot', max_iterations=150``. No fallback to pilot or smoke data
    takes place when the selected dataset is missing or incomplete.
    """
    configs, stem = design_settings(design)
    if max_iterations is not None:
        if isinstance(max_iterations, bool) or not isinstance(max_iterations, int) or max_iterations < 1:
            raise ValueError("max_iterations must be a positive integer")
        configs = [replace(config, max_iterations=max_iterations) for config in configs]
    directory = Path(directory)
    summary_path = directory / f"{stem}_results.csv"
    history_path = directory / f"{stem}_history.csv"
    summary = load_csv(summary_path)
    history = load_csv(history_path)
    validation = validate_dataset(summary, history, configs)
    validation.update({
        "design": design,
        "summary_path": str(summary_path),
        "history_path": str(history_path),
        "max_iterations": sorted({config.max_iterations for config in configs}),
    })
    return summary, history, validation
