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
        max_iterations: int = 500,
        seed=None
    ):
        self.max_iterations = max_iterations
        self.iterations = 0
        self.history = []
        self.stabilised = False
        self.seed = seed

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
        return moved

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
                "satisfaction_rate": self.satisfaction_rate(),
                "segregation_index": self.segregation_index()
            })
            if moved == 0:
                self.stabilised = True
                break