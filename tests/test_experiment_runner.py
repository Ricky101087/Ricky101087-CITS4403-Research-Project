import csv
import statistics
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from utils.experiment_runner import (
    ExperimentConfig,
    build_factorial_design,
    design_settings,
    generate_preferences,
    run_experiment,
    write_experiments,
)


class ExperimentConfigValidationTests(unittest.TestCase):

    def test_max_iterations_rejects_booleans_and_nonpositive_or_nonintegers(self):
        for value in (True, False, 0, -1, 1.5, None, "10"):
            with self.subTest(max_iterations=value):
                with self.assertRaisesRegex(ValueError, "max_iterations"):
                    ExperimentConfig(
                        seed=1, preference_diversity="homogeneous",
                        mobility=1, behaviour="random", max_iterations=value,
                    )

    def test_mobility_requires_a_supported_integer_not_a_boolean(self):
        for value in (True, False, 1.0, 2, -1, None, "1"):
            with self.subTest(mobility=value):
                with self.assertRaisesRegex(ValueError, "mobility"):
                    ExperimentConfig(
                        seed=1, preference_diversity="homogeneous",
                        mobility=value, behaviour="random",
                    )


class ExperimentDesignTests(unittest.TestCase):

    def test_formal_designs_use_ten_seeds_and_500_iteration_cap(self):
        # Building the configuration list does not execute any simulations.
        for name, expected_runs in (("pilot", 270), ("main", 270), ("social", 540)):
            with self.subTest(design=name):
                configs, _ = design_settings(name)
                self.assertEqual(len(configs), expected_runs)
                self.assertEqual({config.seed for config in configs}, set(range(10)))
                self.assertEqual({config.max_iterations for config in configs}, {500})

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
            "stabilisation_time",
            "final_satisfaction_rate",
            "total_preference_updates",
        }
        self.assertTrue(required.issubset(summary))
        self.assertEqual(len(history), summary["iterations"])
        self.assertAlmostEqual(summary["initial_preference_mean"], 0.5)

    @staticmethod
    def stopping_config(stable, max_iterations=3):
        # On a 2x2 grid all agents are neighbours. A single group is satisfied
        # immediately; one A and one B keep moving without becoming satisfied.
        return ExperimentConfig(
            seed=1, preference_diversity="homogeneous", mobility=1,
            behaviour="random", width=2, height=2, vacancy_rate=0.5,
            group_split=1.0 if stable else 0.5,
            max_iterations=max_iterations,
        )

    def test_stabilisation_time_is_recorded_for_a_stable_run(self):
        summary, history = run_experiment(self.stopping_config(stable=True))
        self.assertTrue(summary["stabilised"])
        self.assertEqual(summary["iterations"], 1)
        self.assertEqual(summary["stabilisation_time"], 1)
        self.assertEqual(history[0]["moves"], 0)

    def test_stabilising_on_the_cap_is_still_an_observed_stabilisation(self):
        summary, _ = run_experiment(
            self.stopping_config(stable=True, max_iterations=1)
        )
        self.assertTrue(summary["stabilised"])
        self.assertEqual(summary["stabilisation_time"], 1)

    def test_capped_run_has_no_observed_stabilisation_time(self):
        summary, history = run_experiment(self.stopping_config(stable=False))
        self.assertFalse(summary["stabilised"])
        self.assertEqual(summary["iterations"], 3)
        self.assertIsNone(summary["stabilisation_time"])
        self.assertEqual([entry["moves"] for entry in history], [2, 2, 2])

    def test_csv_uses_blank_stabilisation_time_for_capped_runs(self):
        configs = [
            self.stopping_config(stable=True),
            replace(self.stopping_config(stable=False), seed=2),
        ]
        with tempfile.TemporaryDirectory() as directory:
            summary_path = Path(directory) / "results.csv"
            history_path = Path(directory) / "history.csv"
            write_experiments(configs, summary_path, history_path)
            with summary_path.open(encoding="utf-8", newline="") as result_file:
                rows = list(csv.DictReader(result_file))
        self.assertEqual(rows[0]["stabilised"], "True")
        self.assertEqual(rows[0]["stabilisation_time"], "1")
        self.assertEqual(rows[1]["stabilised"], "False")
        self.assertEqual(rows[1]["iterations"], "3")
        self.assertEqual(rows[1]["stabilisation_time"], "")

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
