import unittest

from agent import Agent
from grid import Grid


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


if __name__ == "__main__":
    unittest.main()