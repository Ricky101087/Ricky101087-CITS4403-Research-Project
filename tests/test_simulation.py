import sys
import os
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


class SimulationStoppingTests(unittest.TestCase):

    def test_stops_at_max_iterations(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1, max_iterations=3)
        sim.run()
        self.assertLessEqual(sim.iterations, 3)

    def test_stabilised_flag_set_when_no_moves(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1, seed=1)
        sim.run()
        if sim.stabilised:
            last = sim.history[-1]
            self.assertEqual(last["moves"], 0)

    def test_history_length_matches_iterations(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1, max_iterations=5)
        sim.run()
        self.assertEqual(len(sim.history), sim.iterations)


class SimulationMetricsTests(unittest.TestCase):

    def test_history_entry_has_required_keys(self):
        sim = Simulation(width=10, height=10, vacancy_rate=0.1, max_iterations=1)
        sim.run()
        entry = sim.history[0]
        self.assertIn("moves", entry)
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
