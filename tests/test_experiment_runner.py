import csv
import statistics
import tempfile
import unittest
from pathlib import Path

from utils.experiment_runner import (
    ExperimentConfig,
    build_factorial_design,
    generate_preferences,
    run_experiment,
    write_experiments,
)


class ExperimentDesignTests(unittest.TestCase):

    def test_factorial_design_contains_every_combination(self):
        configs = build_factorial_design(seeds=(7, 8))
        self.assertEqual(len(configs), 3 * 3 * 3 * 1 * 2)
        self.assertEqual({config.seed for config in configs}, {7, 8})

    def test_preference_levels_are_reproducible_and_control_the_mean(self):
        for level, lower, upper in (
            ("homogeneous", 0.5, 0.5),
            ("low", 0.4, 0.6),
            ("high", 0.2, 0.8),
        ):
            with self.subTest(level=level):
                first = generate_preferences(level, 91, seed=12)
                second = generate_preferences(level, 91, seed=12)
                self.assertEqual(first, second)
                self.assertTrue(all(lower <= value <= upper for value in first))
                self.assertAlmostEqual(statistics.fmean(first), 0.5)

    def test_different_seeds_change_diverse_preferences(self):
        first = generate_preferences("high", 20, seed=1)
        second = generate_preferences("high", 20, seed=2)
        self.assertNotEqual(first, second)


class ExperimentExecutionTests(unittest.TestCase):

    @staticmethod
    def small_config(seed=1):
        return ExperimentConfig(
            seed=seed,
            preference_diversity="high",
            mobility=1,
            behaviour="random",
            social_influence=True,
            width=4,
            height=4,
            vacancy_rate=0.25,
            max_iterations=2,
        )

    def test_run_experiment_records_required_metrics(self):
        summary, history = run_experiment(self.small_config())
        required = {
            "final_segregation_index",
            "iterations",
            "stabilised",
            "final_satisfaction_rate",
            "total_preference_updates",
        }
        self.assertTrue(required.issubset(summary))
        self.assertEqual(len(history), summary["iterations"])
        self.assertAlmostEqual(summary["initial_preference_mean"], 0.5)

    def test_csv_has_one_summary_row_per_run_and_is_not_overwritten(self):
        configs = [self.small_config(seed=1), self.small_config(seed=2)]
        with tempfile.TemporaryDirectory() as directory:
            summary_path = Path(directory) / "results.csv"
            history_path = Path(directory) / "history.csv"
            completed = write_experiments(
                configs,
                summary_path,
                history_path,
            )
            self.assertEqual(completed, 2)
            with summary_path.open(encoding="utf-8") as result_file:
                rows = list(csv.DictReader(result_file))
            self.assertEqual(len(rows), 2)
            self.assertEqual({int(row["seed"]) for row in rows}, {1, 2})

            with self.assertRaises(FileExistsError):
                write_experiments(configs, summary_path, history_path)


if __name__ == "__main__":
    unittest.main()
