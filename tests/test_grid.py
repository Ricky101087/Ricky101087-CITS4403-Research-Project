import unittest

from src.agent import Agent
from src.grid import Grid


class GridValidationTests(unittest.TestCase):
    def test_dimensions_must_be_positive_integers(self):
        invalid_dimensions = [0, -1, 2.5, "3", True]

        for value in invalid_dimensions:
            with self.subTest(width=value):
                with self.assertRaises(ValueError):
                    Grid(width=value, height=3, vacancy_rate=0.1)

            with self.subTest(height=value):
                with self.assertRaises(ValueError):
                    Grid(width=3, height=value, vacancy_rate=0.1)

    def test_vacancy_rate_must_be_numeric_and_strictly_between_zero_and_one(self):
        for value in [0.0, 1.0, -0.1, 1.1, "0.1", True]:
            with self.subTest(vacancy_rate=value):
                with self.assertRaises(ValueError):
                    Grid(width=3, height=3, vacancy_rate=value)


class GridNeighbourTests(unittest.TestCase):
    def setUp(self):
        self.grid = Grid(width=3, height=3, vacancy_rate=0.1)

    def test_moore_neighbours_at_centre(self):
        self.assertEqual(len(self.grid.get_moore_neighbours(1, 1)), 8)

    def test_moore_neighbours_at_corner(self):
        self.assertEqual(
            set(self.grid.get_moore_neighbours(0, 0)),
            {(0, 1), (1, 0), (1, 1)},
        )

    def test_moore_neighbours_at_edge(self):
        self.assertEqual(len(self.grid.get_moore_neighbours(0, 1)), 5)


class GridMovementTests(unittest.TestCase):
    def setUp(self):
        self.grid = Grid(width=3, height=3, vacancy_rate=0.1)
        self.agent = Agent("A", 1, 1, 0.5, 1, "random")
        self.grid.set_cell(1, 1, self.agent)

    def test_move_occupant_updates_source_and_destination_cells(self):
        self.grid.move_occupant(1, 1, 0, 0)

        self.assertTrue(self.grid.is_empty(1, 1))
        self.assertIs(self.grid.get_cell(0, 0), self.agent)

    def test_cannot_move_from_empty_cell(self):
        with self.assertRaises(ValueError):
            self.grid.move_occupant(0, 0, 0, 1)

    def test_cannot_move_to_occupied_cell(self):
        other = Agent("B", 0, 0, 0.5, 1, "random")
        self.grid.set_cell(0, 0, other)

        with self.assertRaises(ValueError):
            self.grid.move_occupant(1, 1, 0, 0)

    def test_out_of_bounds_move_is_rejected(self):
        with self.assertRaises(IndexError):
            self.grid.move_occupant(1, 1, 3, 0)


class GridPopulateTests(unittest.TestCase):
    def test_populate_updates_agent_coordinates(self):
        agents = [
            Agent("A", 99, 99, 0.5, 1, "random"),
            Agent("B", 99, 99, 0.5, 1, "random"),
        ]
        grid = Grid(width=3, height=3, vacancy_rate=0.1)

        grid.populate(agents)

        for agent in agents:
            self.assertIs(
                grid.get_cell(agent.row, agent.col),
                agent,
            )

        self.assertEqual(grid.num_occupied(), len(agents))

    def test_population_cannot_exceed_capacity(self):
        grid = Grid(width=2, height=2, vacancy_rate=0.5)
        agents = [
            Agent("A", 0, 0, 0.5, 1, "random")
            for _ in range(3)
        ]

        with self.assertRaises(ValueError):
            grid.populate(agents)


if __name__ == "__main__":
    unittest.main()
