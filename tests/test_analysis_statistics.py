import itertools
import unittest

from utils.analysis_statistics import (
    bootstrap_mean, condition_summaries, grouped_estimates, paired_effect,
    seed_estimate,
)


def records(social=False):
    return [
        dict(seed=seed, preference_diversity=diversity, mobility=mobility,
             behaviour=behaviour, social_influence=enabled,
             value=float(seed % 2) if enabled or not social else 0.0)
        for seed, diversity, mobility, behaviour, enabled in itertools.product(
            range(10), ("homogeneous", "low", "high"), (1, 3, 5),
            ("random", "improving", "best_fit"), (False, True) if social else (False,),
        )
    ]


class SeedBlockStatisticsTests(unittest.TestCase):
    def test_fixed_conditions_do_not_inflate_replication(self):
        rows = records()
        estimate = seed_estimate(rows, "value")
        direct = bootstrap_mean([float(seed % 2) for seed in range(10)])
        self.assertEqual(estimate.n_runs, 270)
        self.assertEqual(estimate.n_seeds, 10)
        self.assertEqual((estimate.mean, estimate.lower, estimate.upper),
                         (direct.mean, direct.lower, direct.upper))

    def test_grouped_marginals_use_ten_seed_blocks(self):
        estimates = grouped_estimates(records(), "mobility", "value", [1, 3, 5])
        self.assertEqual([key for key, _ in estimates], [1, 3, 5])
        for _, estimate in estimates:
            self.assertEqual((estimate.n_seeds, estimate.n_runs), (10, 90))

    def test_missing_seed_condition_and_duplicate_rows_are_rejected(self):
        rows = records()
        with self.assertRaisesRegex(ValueError, "same fixed"):
            seed_estimate(rows[1:], "value")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            seed_estimate(rows + [rows[0]], "value")

    def test_social_pairs_are_bootstrapped_by_seed_not_pair_count(self):
        estimate = paired_effect(records(social=True), "value")
        direct = bootstrap_mean([float(seed % 2) for seed in range(10)])
        self.assertEqual((estimate.n_seeds, estimate.n_runs), (10, 270))
        self.assertEqual((estimate.mean, estimate.lower, estimate.upper),
                         (direct.mean, direct.lower, direct.upper))

    def test_missing_or_duplicate_pair_fails(self):
        rows = records(social=True)
        with self.assertRaisesRegex(ValueError, "Missing on/off"):
            paired_effect(rows[1:], "value")
        with self.assertRaisesRegex(ValueError, "Duplicate side"):
            paired_effect(rows + [rows[0]], "value")

    def test_different_caps_cannot_be_paired(self):
        rows = records(social=True)
        rows[0]["max_iterations"] = 150
        with self.assertRaisesRegex(ValueError, "Missing on/off"):
            paired_effect(rows, "value")

    def test_balanced_mixed_protocols_cannot_be_pooled(self):
        rows = records()
        mixed = [dict(row, max_iterations=cap) for row in rows for cap in (150, 500)]
        with self.assertRaisesRegex(ValueError, "Mixed experimental protocol"):
            seed_estimate(mixed, "value")
        with self.assertRaisesRegex(ValueError, "Mixed experimental protocol"):
            condition_summaries(mixed)

    def test_identical_social_outcomes_have_zero_effect(self):
        rows = records(social=True)
        for row in rows:
            row["value"] = float(row["seed"] % 2)
        estimate = paired_effect(rows, "value")
        self.assertEqual((estimate.mean, estimate.lower, estimate.upper), (0, 0, 0))

    def test_group_comparisons_reject_different_protocols(self):
        rows = [dict(row, max_iterations=150 if row["mobility"] == 1 else 500)
                for row in records()]
        with self.assertRaisesRegex(ValueError, "Mixed experimental protocol"):
            grouped_estimates(rows, "mobility", "value")
        # Explicitly selecting a single protocol remains valid.
        selected = grouped_estimates(rows, "mobility", "value",
                                     filters={"max_iterations": 500})
        self.assertEqual([key for key, _ in selected], [3, 5])

    def test_bootstrap_is_deterministic_and_does_not_change_global_rng(self):
        import random
        before = random.getstate()
        self.assertEqual(bootstrap_mean([1, 2, 3]), bootstrap_mean([1, 2, 3]))
        self.assertEqual(before, random.getstate())

    def test_single_seed_has_unavailable_not_zero_uncertainty(self):
        result = bootstrap_mean([0.5])
        self.assertIsNone(result.lower)
        self.assertIsNone(result.upper)

    def test_invalid_values_fail(self):
        for value in (float("nan"), float("inf"), None):
            rows = records()
            rows[0]["value"] = value
            with self.assertRaises(ValueError):
                seed_estimate(rows, "value")
        with self.assertRaises(ValueError):
            bootstrap_mean([])

    def test_stopping_and_conditional_stabilisation_are_separate(self):
        base = dict(preference_diversity="high", mobility=1, behaviour="random",
                    social_influence=False, final_segregation_index=0.5,
                    final_satisfaction_rate=0.5)
        rows = [dict(base, seed=0, iterations=2, stabilised=True, stabilisation_time=2),
                dict(base, seed=1, iterations=500, stabilised=False, stabilisation_time=None)]
        summary = condition_summaries(rows)[0]
        self.assertEqual(summary["stable_runs"], 1)
        self.assertEqual(summary["capped_runs"], 1)
        self.assertEqual(summary["stabilised_fraction"], 0.5)
        self.assertEqual(summary["mean_stopping_time"], 251)
        self.assertEqual(summary["mean_stabilisation_time_if_stable"], 2)

    def test_no_stable_runs_returns_no_conditional_time(self):
        rows = [dict(seed=0, preference_diversity="high", mobility=1,
                     behaviour="random", social_influence=False,
                     final_segregation_index=0.5, final_satisfaction_rate=0.5,
                     iterations=500, stabilised=False, stabilisation_time=None)]
        self.assertIsNone(condition_summaries(rows)[0]["mean_stabilisation_time_if_stable"])


if __name__ == "__main__":
    unittest.main()
