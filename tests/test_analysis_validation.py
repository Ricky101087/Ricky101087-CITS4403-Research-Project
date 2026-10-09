import copy
import csv
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from utils.analysis_validation import load_csv, load_dataset, validate_dataset
from utils.experiment_runner import (
    HISTORY_FIELDS,
    SUMMARY_FIELDS,
    ExperimentConfig,
    build_factorial_design,
    run_experiment,
)


class DatasetValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configs = build_factorial_design(
            seeds=(0, 1), social_conditions=(False, True),
            preference_levels=("homogeneous", "high"), mobility_levels=(1,),
            behaviours=("random",), width=4, height=4, vacancy_rate=0.25,
            max_iterations=2,
        )
        cls.summary = []
        cls.history = []
        for config in cls.configs:
            summary, history = run_experiment(config)
            cls.summary.append(summary)
            cls.history.extend(history)

    def fresh(self):
        return copy.deepcopy(self.summary), copy.deepcopy(self.history)

    def test_complete_design_and_shuffled_history_are_accepted(self):
        result = validate_dataset(self.summary, reversed(self.history), self.configs)
        self.assertEqual(result["runs"], 8)
        self.assertEqual(result["history_rows"], len(self.history))
        self.assertEqual(result["seeds"], [0, 1])
        self.assertEqual(set(result["condition_counts"].values()), {2})
        self.assertEqual(result["stabilised_runs"] + result["capped_runs"], 8)

    def test_missing_condition_or_entire_seed_is_rejected(self):
        datasets = (self.summary[:-1], [row for row in self.summary if row["seed"] != 1])
        for summary in datasets:
            with self.subTest(rows=len(summary)), self.assertRaisesRegex(ValueError, "missing runs"):
                validate_dataset(summary, self.history, self.configs)

    def test_single_valid_row_is_not_a_complete_dataset(self):
        with self.assertRaisesRegex(ValueError, "missing runs"):
            validate_dataset(self.summary[:1], self.history, self.configs)

    def test_duplicate_run_or_expected_configuration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate summary"):
            validate_dataset(self.summary + self.summary[:1], self.history, self.configs)
        with self.assertRaisesRegex(ValueError, "duplicate configurations"):
            validate_dataset(self.summary, self.history, self.configs + self.configs[:1])

    def test_empty_expected_design_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            validate_dataset([], [], [])

    def test_relabelled_configuration_or_mixed_caps_are_rejected(self):
        for field, value in (("mobility", 3), ("max_iterations", 150), ("width", 10)):
            summary, history = self.fresh()
            summary[0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "configuration mismatch"):
                validate_dataset(summary, history, self.configs)
        changed_design = [replace(config, max_iterations=150) for config in self.configs]
        with self.assertRaisesRegex(ValueError, "requested design"):
            validate_dataset(self.summary, self.history, changed_design)

    def test_missing_duplicate_and_unexpected_history_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete history"):
            validate_dataset(self.summary, self.history[1:], self.configs)
        with self.assertRaisesRegex(ValueError, "duplicate history"):
            validate_dataset(self.summary, self.history + self.history[:1], self.configs)
        summary, history = self.fresh()
        history[0]["run_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "unexpected run ID"):
            validate_dataset(summary, history, self.configs)

    def test_history_configuration_is_reconciled(self):
        summary, history = self.fresh()
        history[0]["seed"] = 99
        with self.assertRaisesRegex(ValueError, "history configuration mismatch"):
            validate_dataset(summary, history, self.configs)

    def test_final_metric_and_cumulative_totals_are_reconciled(self):
        for field in ("final_segregation_index", "total_moves"):
            summary, history = self.fresh()
            summary[0][field] += 0.001 if field == "final_segregation_index" else 1
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_dataset(summary, history, self.configs)

    def test_nonfinite_out_of_range_and_boolean_numbers_are_rejected(self):
        for field, value in (
            ("final_segregation_index", float("nan")),
            ("final_preference_std", float("inf")),
            ("final_satisfaction_rate", 1.1),
            ("seed", True),
            ("social_influence", 0),
            ("stabilised", "False"),
            ("iterations", 0),
        ):
            summary, history = self.fresh()
            summary[0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_dataset(summary, history, self.configs)

    def test_history_nonfinite_and_population_exceeding_counts_are_rejected(self):
        for field, value in (("segregation_index", float("inf")), ("moves", 13), ("preference_updates", -1)):
            summary, history = self.fresh()
            history[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_dataset(summary, history, self.configs)

    def test_stable_run_records_time_and_inactive_final_history(self):
        config = ExperimentConfig(
            seed=0, preference_diversity="homogeneous", mobility=1,
            behaviour="random", width=2, height=2, vacancy_rate=0.25,
            group_split=1, max_iterations=2,
        )
        summary, history = run_experiment(config)
        self.assertTrue(summary["stabilised"])
        self.assertEqual(validate_dataset([summary], history, [config])["stabilised_runs"], 1)
        summary["stabilisation_time"] = None
        with self.assertRaisesRegex(ValueError, "stabilisation_time"):
            validate_dataset([summary], history, [config])

    def test_capped_run_must_have_no_stabilisation_time(self):
        summary, history = self.fresh()
        capped = next(row for row in summary if not row["stabilised"])
        capped["stabilisation_time"] = capped["iterations"]
        with self.assertRaisesRegex(ValueError, "null stabilisation_time"):
            validate_dataset(summary, history, self.configs)

    def test_non_stabilised_run_cannot_end_before_the_cap(self):
        summary, history = self.fresh()
        capped = next(row for row in summary if not row["stabilised"])
        capped["iterations"] = 1
        with self.assertRaisesRegex(ValueError, "stopped before max_iterations"):
            validate_dataset(summary, history, self.configs)

    def test_required_columns_checked_on_every_row(self):
        summary, history = self.fresh()
        del summary[-1]["stabilisation_time"]
        with self.assertRaisesRegex(ValueError, "missing columns"):
            validate_dataset(summary, history, self.configs)


class DatasetLoadingTests(unittest.TestCase):
    def write_csv(self, path, fields, rows):
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_invalid_boolean_or_nonfinite_csv_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            for field, value in (("stabilised", "not-true"), ("seed", "1.0"),
                                 ("final_segregation_index", "NaN"),
                                 ("stabilisation_time", "nan")):
                self.write_csv(path, [field], [{field: value}])
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, "invalid"):
                    load_csv(path)

    def test_nullable_time_and_booleans_are_typed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            self.write_csv(path, ["stabilised", "stabilisation_time"],
                           [{"stabilised": False, "stabilisation_time": None}])
            self.assertEqual(load_csv(path), [{"stabilised": False, "stabilisation_time": None}])

    def test_duplicate_columns_and_truncated_rows_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.csv"
            for rows in ((["seed", "seed"], [1, 2]), (["seed", "iterations"], [1])):
                with path.open("w", newline="", encoding="utf-8") as output:
                    csv.writer(output).writerows(rows)
                with self.subTest(rows=rows), self.assertRaises(ValueError):
                    load_csv(path)

    def test_missing_main_never_falls_back_to_pilot(self):
        with tempfile.TemporaryDirectory() as directory:
            self.write_csv(Path(directory) / "pilot_results.csv", ["run_id"], [{"run_id": "pilot"}])
            with self.assertRaisesRegex(ValueError, "main_experiment_results.csv"):
                load_dataset(directory, design="main")

    def test_explicit_cap_override_and_matching_pair(self):
        config = ExperimentConfig(
            seed=0, preference_diversity="homogeneous", mobility=1,
            behaviour="random", width=2, height=2, vacancy_rate=0.25,
            group_split=1,
        )
        legacy_config = replace(config, max_iterations=150)
        summary, history = run_experiment(legacy_config)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            self.write_csv(directory / "pilot_results.csv", SUMMARY_FIELDS, [summary])
            self.write_csv(directory / "pilot_history.csv", HISTORY_FIELDS, history)
            with patch("utils.analysis_validation.design_settings", return_value=([config], "pilot")):
                with self.assertRaisesRegex(ValueError, "requested design"):
                    load_dataset(directory, design="pilot")
                loaded, loaded_history, metadata = load_dataset(
                    directory, design="pilot", max_iterations=150,
                )
                self.assertEqual(loaded, [summary])
                self.assertEqual(loaded_history, history)
                self.assertEqual(metadata["max_iterations"], [150])
                self.assertEqual(metadata["runs"], 1)

    def test_invalid_cap_override_rejected(self):
        for value in (True, 0, -1, 1.5):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "positive integer"):
                load_dataset("not-used", max_iterations=value)


if __name__ == "__main__":
    unittest.main()
