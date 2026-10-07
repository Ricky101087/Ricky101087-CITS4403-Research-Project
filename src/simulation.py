import random
from .grid import Grid
from .agent import Agent

class Simulation:

    def __init__(
        self,
        width: int = 40,
        height: int = 40,
        vacancy_rate: float = 0.10,
        group_split: float = 0.50,
        preference: float = 0.50,
        mobility: int = 5,
        behaviour: str = "random",
        social_influence: bool = False,
        influence_strength: float = 0.10,
        max_iterations: int = 500,
        seed=None
    ):
        if not isinstance(social_influence, bool):
            raise ValueError("social_influence must be a boolean")

        if (
            isinstance(influence_strength, bool)
            or not isinstance(influence_strength, (int, float))
            or not 0.0 <= influence_strength <= 1.0
        ):
            raise ValueError("influence_strength must be between 0.0 and 1.0")

        self.max_iterations = max_iterations
        self.iterations = 0
        self.history = []
        self.stabilised = False
        self.seed = seed
        self.social_influence = social_influence
        self.influence_strength = float(influence_strength)
        self.last_preference_updates = 0

        if seed is not None:
            random.seed(seed)

        self.grid = Grid(width, height, vacancy_rate)

        num_agents = int(self.grid.total_cells() * (1 - vacancy_rate))
        num_a = int(num_agents * group_split)
        num_b = num_agents - num_a

        self.agents = []
        for i in range(num_a):
            self.agents.append(Agent("A", 0, 0, preference, mobility, behaviour))
        for i in range(num_b):
            self.agents.append(Agent("B", 0, 0, preference, mobility, behaviour))

        self.grid.populate(self.agents)

    def run_one_step(self):
        random.shuffle(self.agents)
        moved = 0
        for agent in self.agents:
            if agent.step(self.grid):
                moved += 1
        self.last_preference_updates = self.apply_social_influence()
        return moved

    def apply_social_influence(self) -> int:
        """Move each preference toward the mean preference of occupied neighbours."""
        if not self.social_influence or self.influence_strength == 0.0:
            return 0

        updates = []
        for agent in self.agents:
            neighbours = [
                self.grid.get_cell(row, col)
                for row, col in self.grid.get_moore_neighbours(
                    agent.row, agent.col
                )
                if not self.grid.is_empty(row, col)
            ]
            if not neighbours:
                continue

            mean_preference = sum(
                neighbour.preference for neighbour in neighbours
            ) / len(neighbours)
            new_preference = agent.preference + self.influence_strength * (
                mean_preference - agent.preference
            )
            new_preference = min(1.0, max(0.0, new_preference))

            if abs(new_preference - agent.preference) > 1e-12:
                updates.append((agent, new_preference))

        for agent, new_preference in updates:
            agent.preference = new_preference

        return len(updates)

    def segregation_index(self):
        total = 0
        for agent in self.agents:
            total += agent.similarity_score(self.grid)
        return total / len(self.agents)

    def satisfaction_rate(self):
        satisfied = 0
        for agent in self.agents:
            if agent.is_satisfied(self.grid):
                satisfied += 1
        return satisfied / len(self.agents)

    def run(self):
        for i in range(self.max_iterations):
            self.iterations += 1
            moved = self.run_one_step()
            self.history.append({
                "moves": moved,
                "preference_updates": self.last_preference_updates,
                "satisfaction_rate": self.satisfaction_rate(),
                "segregation_index": self.segregation_index()
            })
            if moved == 0 and self.last_preference_updates == 0:
                self.stabilised = True
                break
