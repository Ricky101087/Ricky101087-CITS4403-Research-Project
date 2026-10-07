import unittest
from unittest.mock import patch

from src.agent import Agent
from src.grid import Grid


class AgentValidationTests(unittest.TestCase):
    def test_group_must_be_a_or_b(self):
        for value in ["C", "", None, ["A"]]:
            with self.subTest(group=value):
                with self.assertRaises(ValueError):
                    Agent(value, 0, 0, 0.5, 1, "random")

    def test_preference_must_be_numeric_and_in_range(self):
        for value in [-0.1, 1.1, "0.5", None, True]:
            with self.subTest(preference=value):
                with self.assertRaises(ValueError):
                    Agent("A", 0, 0, value, 1, "random")

    def test_mobility_must_be_a_non_negative_integer(self):
        for value in [-1, 1.5, "1", None, True]:
            with self.subTest(mobility=value):
                with self.assertRaises(ValueError):
                    Agent("A", 0, 0, 0.5, value, "random")

    def test_behaviour_must_be_supported(self):
        for value in ["nearest", "", None, ["random"]]:
            with self.subTest(behaviour=value):
                with self.assertRaises(ValueError):
                    Agent("A", 0, 0, 0.5, 1, value)


class AgentSimilarityTests(unittest.TestCase):
    def test_similarity_is_zero_without_occupied_neighbours(self):
        grid = Grid(width=3, height=3, vacancy_rate=0.1)
        agent = Agent("A", 1, 1, 0.5, 1, "random")
        grid.set_cell(1, 1, agent)

        self.assertEqual(agent.similarity_score(grid), 0.0)

    def test_similarity_ignores_empty_cells(self):
        grid = Grid(width=3, height=3, vacancy_rate=0.1)
        agent = Agent("A", 1, 1, 0.5, 1, "random")
        same = Agent("A", 0, 0, 0.5, 1, "random")
        different = Agent("B", 0, 1, 0.5, 1, "random")
        grid.set_cell(1, 1, agent)
        grid.set_cell(0, 0, same)
        grid.set_cell(0, 1, different)

        self.assertEqual(agent.similarity_score(grid), 0.5)

    def test_similarity_equal_to_preference_is_satisfied(self):
        grid = Grid(width=3, height=3, vacancy_rate=0.1)
        agent = Agent("A", 1, 1, 0.5, 1, "random")
        grid.set_cell(1, 1, agent)
        grid.set_cell(0, 0, Agent("A", 0, 0, 0.5, 1, "random"))
        grid.set_cell(0, 1, Agent("B", 0, 1, 0.5, 1, "random"))

        self.assertTrue(agent.is_satisfied(grid))


class AgentDestinationTests(unittest.TestCase):
    def setUp(self):
        self.grid = Grid(width=5, height=5, vacancy_rate=0.1)
        self.grid.set_cell(2, 1, Agent("B", 2, 1, 0.5, 1, "random"))
        self.grid.set_cell(0, 1, Agent("A", 0, 1, 0.5, 1, "random"))
        self.grid.set_cell(1, 0, Agent("A", 1, 0, 0.5, 1, "random"))

    def test_random_behaviour_chooses_an_available_destination(self):
        agent = Agent("A", 2, 2, 0.5, 1, "random")
        self.grid.set_cell(2, 2, agent)
        available = agent.available_destinations(self.grid)

        with patch("src.agent.random.choice", return_value=available[0]) as choice:
            destination = agent.choose_destination(self.grid)

        self.assertIn(destination, available)
        choice.assert_called_once_with(available)

    def test_improving_behaviour_only_chooses_a_better_destination(self):
        agent = Agent("A", 2, 2, 0.5, 2, "improving")
        self.grid.set_cell(2, 2, agent)
        current_score = agent.similarity_score(self.grid)

        destination = agent.choose_destination(self.grid)

        self.assertIsNotNone(destination)
        self.assertGreater(
            agent.similarity_score_at(self.grid, *destination),
            current_score,
        )

    def test_best_fit_behaviour_chooses_a_highest_scoring_destination(self):
        agent = Agent("A", 2, 2, 0.5, 2, "best_fit")
        self.grid.set_cell(2, 2, agent)
        available = agent.available_destinations(self.grid)
        best_score = max(
            agent.similarity_score_at(self.grid, row, col)
            for row, col in available
        )

        destination = agent.choose_destination(self.grid)

        self.assertEqual(
            agent.similarity_score_at(self.grid, *destination),
            best_score,
        )


class AgentMovementTests(unittest.TestCase):
    def test_satisfied_agent_does_not_move(self):
        grid = Grid(width=3, height=3, vacancy_rate=0.1)
        agent = Agent("A", 1, 1, 0.0, 1, "random")
        grid.set_cell(1, 1, agent)

        self.assertFalse(agent.step(grid))
        self.assertIs(grid.get_cell(1, 1), agent)

    def test_step_moves_agent_and_updates_coordinates(self):
        grid = Grid(width=3, height=3, vacancy_rate=0.1)
        agent = Agent("A", 1, 1, 1.0, 1, "random")
        grid.set_cell(1, 1, agent)

        with patch.object(agent, "choose_destination", return_value=(0, 0)):
            moved = agent.step(grid)

        self.assertTrue(moved)
        self.assertTrue(grid.is_empty(1, 1))
        self.assertIs(grid.get_cell(0, 0), agent)
        self.assertEqual((agent.row, agent.col), (0, 0))


if __name__ == "__main__":
    unittest.main()
