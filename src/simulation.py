import random
from collections.abc import Sequence
from .grid import Grid
from .agent import Agent

class Simulation:

    def __init__(
        self,
        width: int = 40,
        height: int = 40,
        vacancy_rate: float = 0.10,
        group_split: float = 0.50,
        preference: float | Sequence[float] = 0.50,
        mobility: int = 5,
        behaviour: str = "random",
        social_influence: bool = False,
        influence_strength: float = 0.10,
        max_iterations: int = 500,
        seed=None
    ):
        if (
            isinstance(width, bool)
            or not isinstance(width, int)
            or width < 1
        ):
            raise ValueError("width must be a positive integer")

        if (
            isinstance(height, bool)
            or not isinstance(height, int)
            or height < 1
        ):
            raise ValueError("height must be a positive integer")

        if (
            isinstance(group_split, bool)
            or not isinstance(group_split, (int, float))
            or not 0.0 <= group_split <= 1.0
        ):
            raise ValueError("group_split must be between 0.0 and 1.0")

        if (
            isinstance(max_iterations, bool)
            or not isinstance(max_iterations, int)
            or max_iterations < 1
        ):
            raise ValueError("max_iterations must be a positive integer")

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
        self.rng = random.Random(seed)
        self.social_influence = social_influence
        self.influence_strength = float(influence_strength)
        self.last_preference_updates = 0

        self.grid = Grid(width, height, vacancy_rate, rng=self.rng)

        num_agents = int(self.grid.total_cells() * (1 - vacancy_rate))
        if num_agents == 0:
            raise ValueError(
                "vacancy_rate leaves no room for agents; lower vacancy_rate or increase grid size"
            )
        num_a = int(num_agents * group_split)
        preferences = self._normalise_preferences(preference, num_agents)

        self.agents = []
        for index in range(num_a):
            self.agents.append(
                Agent(
                    "A", 0, 0, preferences[index], mobility, behaviour,
                    rng=self.rng,
                )
            )
        for index in range(num_a, num_agents):
            self.agents.append(
                Agent(
                    "B", 0, 0, preferences[index], mobility, behaviour,
                    rng=self.rng,
                )
            )

        self.grid.populate(self.agents)

    @staticmethod
    def _normalise_preferences(preference, count: int) -> list[float]:
        """Return one validated preference value for every agent."""
        if (
            isinstance(preference, (int, float))
            and not isinstance(preference, bool)
        ):
            values = [preference] * count
        elif (
            isinstance(preference, Sequence)
            and not isinstance(preference, (str, bytes, bytearray))
        ):
            values = list(preference)
            if len(values) != count:
                raise ValueError(
                    f"preference sequence must contain exactly {count} values"
                )
        else:
            raise ValueError(
                "preference must be a number or a sequence of numbers"
            )

        normalised = []
        for value in values:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0.0 <= value <= 1.0
            ):
                raise ValueError(
                    "each preference must be a number between 0.0 and 1.0"
                )
            normalised.append(float(value))
        return normalised

    def run_one_step(self):
        self.rng.shuffle(self.agents)
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
        if not self.agents:
            return 0.0
        total = 0
        for agent in self.agents:
            total += agent.similarity_score(self.grid)
        return total / len(self.agents)

    def satisfaction_rate(self):
        if not self.agents:
            return 0.0
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
