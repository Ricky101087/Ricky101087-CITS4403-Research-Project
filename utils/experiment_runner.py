"""Reproducible factorial experiments for the extended Schelling model.

The summary CSV contains one row per simulation run.  A second history CSV
contains one row per iteration so that convergence plots can be reproduced.
Existing files are never replaced unless ``--overwrite`` is supplied.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import random
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from src.simulation import Simulation


PREFERENCE_BOUNDS = {
    "homogeneous": (0.50, 0.50),
    "low": (0.40, 0.60),
    "high": (0.20, 0.80),
}
MOBILITY_LEVELS = (1, 3, 5)
BEHAVIOURS = ("random", "improving", "best_fit")
PILOT_SEEDS = tuple(range(10))
FINAL_SEEDS = tuple(range(30))


@dataclass(frozen=True)
class ExperimentConfig:
    seed: int
    preference_diversity: str
    mobility: int
    behaviour: str
    social_influence: bool = False
    influence_strength: float = 0.10
    width: int = 40
    height: int = 40
    vacancy_rate: float = 0.10
    group_split: float = 0.50
    max_iterations: int = 500

    def __post_init__(self) -> None:
        if self.preference_diversity not in PREFERENCE_BOUNDS:
            raise ValueError(
                "preference_diversity must be homogeneous, low, or high"
            )
        if self.mobility not in MOBILITY_LEVELS:
            raise ValueError("mobility must be one of 1, 3, or 5")
        if self.behaviour not in BEHAVIOURS:
            raise ValueError(
                "behaviour must be random, improving, or best_fit"
            )
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("seed must be an integer")
        if not isinstance(self.max_iterations, int) or self.max_iterations <= 0:
            raise ValueError("max_iterations must be a positive integer")


SUMMARY_FIELDS = (
    "run_id",
    "seed",
    "width",
    "height",
    "vacancy_rate",
    "group_split",
    "preference_diversity",
    "preference_lower",
    "preference_upper",
    "initial_preference_mean",
    "initial_preference_std",
    "mobility",
    "behaviour",
    "social_influence",
    "influence_strength",
    "max_iterations",
    "final_segregation_index",
    "iterations",
    "stabilised",
    "final_satisfaction_rate",
    "total_moves",
    "total_preference_updates",
    "final_preference_mean",
    "final_preference_std",
)

HISTORY_FIELDS = (
    "run_id",
    "seed",
    "preference_diversity",
    "mobility",
    "behaviour",
    "social_influence",
    "influence_strength",
    "iteration",
    "moves",
    "preference_updates",
    "satisfaction_rate",
    "segregation_index",
)


def make_run_id(config: ExperimentConfig) -> str:
    """Return a stable identifier derived only from the run configuration."""
    payload = json.dumps(asdict(config), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def generate_preferences(level: str, count: int, seed: int) -> list[float]:
    """Generate a reproducible preference vector with mean exactly 0.5.

    Diverse conditions use symmetric pairs around 0.5.  This controls the
    population mean while changing only the amount of preference variation.
    """
    if level not in PREFERENCE_BOUNDS:
        raise ValueError("Unknown preference diversity level")
    if count < 0:
        raise ValueError("count must be non-negative")
    if level == "homogeneous":
        return [0.5] * count

    lower, upper = PREFERENCE_BOUNDS[level]
    max_deviation = upper - 0.5
    rng = random.Random(f"preference:{level}:{seed}")
    preferences: list[float] = []
    for _ in range(count // 2):
        deviation = rng.uniform(0.0, max_deviation)
        preferences.extend((0.5 - deviation, 0.5 + deviation))
    if count % 2:
        preferences.append(0.5)
    rng.shuffle(preferences)

    # Guard against future changes to the configured bounds.
    if any(value < lower or value > upper for value in preferences):
        raise RuntimeError("Generated preference fell outside configured bounds")
    return preferences


def build_factorial_design(
    seeds: Sequence[int],
    social_conditions: Sequence[bool] = (False,),
    preference_levels: Sequence[str] = tuple(PREFERENCE_BOUNDS),
    mobility_levels: Sequence[int] = MOBILITY_LEVELS,
    behaviours: Sequence[str] = BEHAVIOURS,
    **simulation_options,
) -> list[ExperimentConfig]:
    """Return every requested factor combination for every supplied seed."""
    return [
        ExperimentConfig(
            seed=seed,
            preference_diversity=preference_level,
            mobility=mobility,
            behaviour=behaviour,
            social_influence=social_influence,
            **simulation_options,
        )
        for preference_level, mobility, behaviour, social_influence, seed in
        itertools.product(
            preference_levels,
            mobility_levels,
            behaviours,
            social_conditions,
            seeds,
        )
    ]


def run_experiment(
    config: ExperimentConfig,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Run one configuration and return its summary and iteration history."""
    simulation = Simulation(
        width=config.width,
        height=config.height,
        vacancy_rate=config.vacancy_rate,
        group_split=config.group_split,
        preference=0.5,
        mobility=config.mobility,
        behaviour=config.behaviour,
        social_influence=config.social_influence,
        influence_strength=config.influence_strength,
        max_iterations=config.max_iterations,
        seed=config.seed,
    )

    initial_preferences = generate_preferences(
        config.preference_diversity,
        len(simulation.agents),
        config.seed,
    )
    for agent, preference in zip(simulation.agents, initial_preferences):
        agent.preference = preference

    simulation.run()
    run_id = make_run_id(config)
    final_preferences = [agent.preference for agent in simulation.agents]
    final_state = simulation.history[-1]
    lower, upper = PREFERENCE_BOUNDS[config.preference_diversity]

    summary = {
        "run_id": run_id,
        **asdict(config),
        "preference_lower": lower,
        "preference_upper": upper,
        "initial_preference_mean": statistics.fmean(initial_preferences),
        "initial_preference_std": statistics.pstdev(initial_preferences),
        "final_segregation_index": final_state["segregation_index"],
        "iterations": simulation.iterations,
        "stabilised": simulation.stabilised,
        "final_satisfaction_rate": final_state["satisfaction_rate"],
        "total_moves": sum(entry["moves"] for entry in simulation.history),
        "total_preference_updates": sum(
            entry["preference_updates"] for entry in simulation.history
        ),
        "final_preference_mean": statistics.fmean(final_preferences),
        "final_preference_std": statistics.pstdev(final_preferences),
    }

    history = [
        {
            "run_id": run_id,
            "seed": config.seed,
            "preference_diversity": config.preference_diversity,
            "mobility": config.mobility,
            "behaviour": config.behaviour,
            "social_influence": config.social_influence,
            "influence_strength": config.influence_strength,
            "iteration": iteration,
            **entry,
        }
        for iteration, entry in enumerate(simulation.history, start=1)
    ]
    return summary, history


def write_experiments(
    configs: Iterable[ExperimentConfig],
    summary_path: Path,
    history_path: Path,
    overwrite: bool = False,
) -> int:
    """Run configurations and write reproducible CSV files.

    Both destinations are checked before any work begins.  Without explicit
    permission to overwrite, an existing result file raises FileExistsError.
    """
    summary_path = Path(summary_path)
    history_path = Path(history_path)
    existing = [path for path in (summary_path, history_path) if path.exists()]
    if existing and not overwrite:
        names = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            f"Refusing to overwrite existing result file(s): {names}"
        )

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with (
        summary_path.open("w", newline="", encoding="utf-8") as summary_file,
        history_path.open("w", newline="", encoding="utf-8") as history_file,
    ):
        summary_writer = csv.DictWriter(summary_file, fieldnames=SUMMARY_FIELDS)
        history_writer = csv.DictWriter(history_file, fieldnames=HISTORY_FIELDS)
        summary_writer.writeheader()
        history_writer.writeheader()

        for config in configs:
            summary, history = run_experiment(config)
            summary_writer.writerow(summary)
            history_writer.writerows(history)
            summary_file.flush()
            history_file.flush()
            count += 1
            print(f"Completed {count}: {summary['run_id']}")
    return count


def design_settings(name: str) -> tuple[list[ExperimentConfig], str]:
    """Build one of the documented pilot, main, social, or smoke designs."""
    if name == "pilot":
        return build_factorial_design(PILOT_SEEDS), "pilot"
    if name == "main":
        return build_factorial_design(FINAL_SEEDS), "main_experiment"
    if name == "social":
        return (
            build_factorial_design(
                FINAL_SEEDS,
                social_conditions=(False, True),
            ),
            "social_influence",
        )
    if name == "smoke":
        configs = build_factorial_design(
            seeds=(0, 1),
            social_conditions=(False, True),
            preference_levels=("homogeneous", "high"),
            mobility_levels=(1,),
            behaviours=("random",),
            width=10,
            height=10,
            max_iterations=10,
        )
        return configs, "smoke"
    raise ValueError(f"Unknown design: {name}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--design",
        choices=("smoke", "pilot", "main", "social"),
        default="smoke",
        help="Experiment design to run (default: smoke)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Directory for summary and history CSV files",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Explicitly replace existing result files",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    configs, stem = design_settings(args.design)
    summary_path = args.output_dir / f"{stem}_results.csv"
    history_path = args.output_dir / f"{stem}_history.csv"
    print(f"Design: {args.design}")
    print(f"Runs: {len(configs)}")
    print(f"Summary: {summary_path}")
    print(f"History: {history_path}")
    return write_experiments(
        configs,
        summary_path,
        history_path,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
