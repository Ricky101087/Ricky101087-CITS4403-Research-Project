import random
from grid import Grid
from agent import Agent

class Simulation:

    def __init__(self, grid: Grid, agents: list, max_iterations: int = 500, seed=None):
        self.grid = grid
        self.agents = agents
        self.max_iterations = max_iterations
        self.iterations = 0
        self.history = []
        self.stabilised = False
        self.seed = seed

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
        if self.seed is not None:
            random.seed(self.seed)
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