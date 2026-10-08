import sys
import os
import random
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.simulation import Simulation


class SimulationInitTests(unittest.TestCase):

    def test_grid_dimensions(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1)
        self.assertEqual(sim.grid.width, 10)
        self.assertEqual(sim.grid.height, 10)

    def test_agent_count_respects_vacancy(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1)
        expected = int(100 * 0.9)
        self.assertEqual(len(sim.agents), expected)

    def test_group_split(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1, group_split=0.5)
        num_a = sum(1 for a in sim.agents if a.group == "A")
        num_b = sum(1 for a in sim.agents if a.group == "B")
        self.assertEqual(num_a + num_b, len(sim.agents))
        self.assertAlmostEqual(num_a / len(sim.agents), 0.5, delta=0.05)

    def test_group_split_rejects_invalid_values(self):
        for value in (
            -0.1, -0.001, 1.1, True, False, None, "0.5",
            float("nan"), float("inf"), float("-inf"),
        ):
            with self.subTest(group_split=value):
                with self.assertRaisesRegex(ValueError, "group_split"):
                    Simulation(width=3, height=3, group_split=value)

    def test_group_split_endpoints_preserve_population(self):
        for split, expected_group in ((0, "B"), (1, "A")):
            with self.subTest(group_split=split):
                sim = Simulation(
                    width=2, height=2, vacancy_rate=0.25,
                    group_split=split, seed=1,
                )
                self.assertEqual(len(sim.agents), 3)
                self.assertTrue(
                    all(agent.group == expected_group for agent in sim.agents)
                )

    def test_max_iterations_rejects_invalid_values(self):
        for value in (0, -1, True, False, 1.5, None, "10"):
            with self.subTest(max_iterations=value):
                with self.assertRaisesRegex(ValueError, "max_iterations"):
                    Simulation(width=3, height=3, max_iterations=value)

    def test_zero_population_is_rejected_before_running(self):
        for size, vacancy_rate in ((1, 0.1), (2, 0.99)):
            with self.subTest(size=size, vacancy_rate=vacancy_rate):
                with self.assertRaisesRegex(ValueError, "no room for agents"):
                    Simulation(
                        width=size, height=size, vacancy_rate=vacancy_rate,
                    )

    def test_agent_positions_are_on_grid(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1)
        for agent in sim.agents:
            self.assertTrue(sim.grid.is_valid(agent.row, agent.col))
            self.assertIs(sim.grid.get_cell(agent.row, agent.col), agent)

    def test_initial_state(self):
        sim = Simulation()
        self.assertEqual(sim.iterations, 0)
        self.assertEqual(sim.history, [])
        self.assertFalse(sim.stabilised)

    def test_social_influence_defaults_to_disabled(self):
        sim = Simulation()
        self.assertFalse(sim.social_influence)
        self.assertEqual(sim.influence_strength, 0.10)

    def test_social_influence_configuration(self):
        sim = Simulation(social_influence=True, influence_strength=0.25)
        self.assertTrue(sim.social_influence)
        self.assertEqual(sim.influence_strength, 0.25)

    def test_invalid_social_influence_configuration(self):
        with self.assertRaises(ValueError):
            Simulation(social_influence=1)
        for invalid_strength in (-0.1, 1.1, "high", True):
            with self.subTest(influence_strength=invalid_strength):
                with self.assertRaises(ValueError):
                    Simulation(influence_strength=invalid_strength)

    def test_preference_sequence_is_assigned_to_agents(self):
        preferences = [0.2, 0.5, 0.8]
        sim = Simulation(
            width=2,
            height=2,
            vacancy_rate=0.25,
            preference=preferences,
            seed=1,
        )
        self.assertEqual(
            [agent.preference for agent in sim.agents],
            preferences,
        )

    def test_preference_sequence_must_match_agent_count(self):
        with self.assertRaisesRegex(ValueError, "exactly 3 values"):
            Simulation(
                width=2,
                height=2,
                vacancy_rate=0.25,
                preference=[0.2, 0.8],
            )

    def test_preference_sequence_values_are_validated(self):
        with self.assertRaisesRegex(ValueError, "between 0.0 and 1.0"):
            Simulation(
                width=2,
                height=2,
                vacancy_rate=0.25,
                preference=[0.2, 0.5, 1.1],
            )


class SimulationStepTests(unittest.TestCase):

    def test_run_one_step_returns_int(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1)
        moved = sim.run_one_step()
        self.assertIsInstance(moved, int)
        self.assertGreaterEqual(moved, 0)

    def test_agent_positions_valid_after_step(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1)
        sim.run_one_step()
        for agent in sim.agents:
            self.assertTrue(sim.grid.is_valid(agent.row, agent.col))
            self.assertIs(sim.grid.get_cell(agent.row, agent.col), agent)

    def test_social_influence_is_disabled_by_default(self):
        sim = Simulation(width=2, height=2, vacancy_rate=0.25, mobility=0)
        original_preferences = [agent.preference for agent in sim.agents]
        sim.run_one_step()
        self.assertEqual(
            [agent.preference for agent in sim.agents],
            original_preferences
        )

    def test_social_influence_uses_simultaneous_updates(self):
        sim = Simulation(
            width=2,
            height=2,
            vacancy_rate=0.25,
            mobility=0,
            social_influence=True,
            influence_strength=0.5,
            seed=1
        )
        sim.agents[0].preference = 0.0
        sim.agents[1].preference = 1.0
        sim.agents[2].preference = 1.0

        updated = sim.apply_social_influence()

        self.assertEqual(updated, 3)
        self.assertAlmostEqual(sim.agents[0].preference, 0.5)
        self.assertAlmostEqual(sim.agents[1].preference, 0.75)
        self.assertAlmostEqual(sim.agents[2].preference, 0.75)

    def test_run_one_step_applies_social_influence(self):
        sim = Simulation(
            width=2,
            height=2,
            vacancy_rate=0.25,
            mobility=0,
            social_influence=True,
            influence_strength=0.5,
            seed=1
        )
        first, second, third = sim.agents
        first.preference = 0.0
        second.preference = 1.0
        third.preference = 1.0

        moved = sim.run_one_step()

        self.assertEqual(moved, 0)
        self.assertEqual(sim.last_preference_updates, 3)
        self.assertAlmostEqual(first.preference, 0.5)
        self.assertAlmostEqual(second.preference, 0.75)
        self.assertAlmostEqual(third.preference, 0.75)

    def test_social_influence_leaves_isolated_agent_unchanged(self):
        sim = Simulation(
            width=3,
            height=3,
            vacancy_rate=8 / 9,
            social_influence=True,
            influence_strength=0.5,
            seed=1
        )
        agent = sim.agents[0]
        agent.preference = 0.4

        updated = sim.apply_social_influence()

        self.assertEqual(updated, 0)
        self.assertEqual(agent.preference, 0.4)


class SimulationStoppingTests(unittest.TestCase):

    def test_stops_at_max_iterations(self):
        # Opposite-group agents on a 2x2 grid can always reach an empty cell,
        # but neither can acquire a same-group neighbour by moving.
        sim = Simulation(
            width=2, height=2, vacancy_rate=0.5, preference=0.5,
            mobility=1, behaviour="random", max_iterations=3, seed=1,
        )
        sim.run()
        self.assertEqual(sim.iterations, 3)
        self.assertFalse(sim.stabilised)
        self.assertEqual([entry["moves"] for entry in sim.history], [2, 2, 2])

    def test_stabilised_flag_set_when_no_moves(self):
        sim = Simulation(
            width=2, height=2, vacancy_rate=0.25, preference=0.0,
            max_iterations=3, seed=1,
        )
        sim.run()
        self.assertTrue(sim.stabilised)
        self.assertEqual(sim.iterations, 1)
        self.assertEqual(sim.history[0]["moves"], 0)
        self.assertEqual(sim.history[0]["preference_updates"], 0)

    def test_history_length_matches_iterations(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1, max_iterations=5)
        sim.run()
        self.assertEqual(len(sim.history), sim.iterations)

    def test_social_influence_prevents_early_stopping_while_preferences_change(self):
        sim = Simulation(
            width=2,
            height=2,
            vacancy_rate=0.25,
            mobility=0,
            social_influence=True,
            influence_strength=0.5,
            max_iterations=2,
            seed=1
        )
        sim.agents[0].preference = 0.0
        sim.agents[1].preference = 1.0
        sim.agents[2].preference = 1.0

        sim.run()

        self.assertEqual(sim.iterations, 2)
        self.assertFalse(sim.stabilised)
        self.assertTrue(all(entry["moves"] == 0 for entry in sim.history))
        self.assertTrue(
            all(entry["preference_updates"] > 0 for entry in sim.history)
        )


class SimulationMetricsTests(unittest.TestCase):

    @staticmethod
    def mixed_three_agent_fixture():
        # Every occupied cell in a 2x2 grid neighbours the other two agents.
        # The two A agents each score 1/2; the single B agent scores zero.
        return Simulation(
            width=2, height=2, vacancy_rate=0.25, group_split=2 / 3,
            preference=0.5, mobility=0, seed=1,
        )

    def test_segregation_matches_hand_calculated_neighbour_fractions(self):
        sim = self.mixed_three_agent_fixture()
        self.assertAlmostEqual(sim.segregation_index(), 1 / 3)

    def test_satisfaction_matches_hand_calculated_threshold_count(self):
        sim = self.mixed_three_agent_fixture()
        self.assertAlmostEqual(sim.satisfaction_rate(), 2 / 3)

    def test_empty_agent_metrics_have_defined_values(self):
        sim = Simulation(width=2, height=2, vacancy_rate=0.5, seed=1)
        for agent in sim.agents:
            sim.grid.set_cell(agent.row, agent.col, None)
        sim.agents.clear()
        self.assertEqual(sim.segregation_index(), 0.0)
        self.assertEqual(sim.satisfaction_rate(), 0.0)

    def test_history_entry_has_required_keys(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1, max_iterations=1)
        sim.run()
        entry = sim.history[0]
        self.assertIn("moves", entry)
        self.assertIn("preference_updates", entry)
        self.assertIn("satisfaction_rate", entry)
        self.assertIn("segregation_index", entry)

    def test_satisfaction_rate_in_range(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1)
        rate = sim.satisfaction_rate()
        self.assertGreaterEqual(rate, 0.0)
        self.assertLessEqual(rate, 1.0)

    def test_segregation_index_in_range(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1)
        index = sim.segregation_index()
        self.assertGreaterEqual(index, 0.0)
        self.assertLessEqual(index, 1.0)


class SimulationSeedTests(unittest.TestCase):

    def test_simulation_does_not_change_global_random_state(self):
        random.seed(12345)
        expected = random.Random(12345).random()

        Simulation(width=10, height=10, vacancy_rate=0.1, seed=99)

        self.assertEqual(random.random(), expected)

    def test_same_seed_is_reproducible_when_constructed_before_running(self):
        sim1 = Simulation(width=10, height=10, vacancy_rate=0.1, seed=99)
        sim2 = Simulation(width=10, height=10, vacancy_rate=0.1, seed=99)

        sim1.run()
        sim2.run()

        self.assertEqual(sim1.history, sim2.history)

    def test_same_seed_produces_same_history(self):
        sim1 = Simulation(width=10, height=10, vacancy_rate=0.1, seed=99)
        sim1.run()
        sim2 = Simulation(width=10, height=10, vacancy_rate=0.1, seed=99)
        sim2.run()
        self.assertEqual(sim1.iterations, sim2.iterations)
        for e1, e2 in zip(sim1.history, sim2.history):
            self.assertAlmostEqual(e1["segregation_index"], e2["segregation_index"])
            self.assertAlmostEqual(e1["satisfaction_rate"], e2["satisfaction_rate"])

    def test_different_seeds_produce_different_results(self):
        sim1 = Simulation(width=10, height=10, vacancy_rate=0.1, seed=1)
        sim1.run()
        sim2 = Simulation(width=10, height=10, vacancy_rate=0.1, seed=2)
        sim2.run()
        self.assertFalse(
            sim1.history == sim2.history,
            "Different seeds produced identical history — unlikely unless determinism is broken"
        )


if __name__ == "__main__":
    unittest.main()
