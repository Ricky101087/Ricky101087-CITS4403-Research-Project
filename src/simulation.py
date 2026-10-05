import random
from grid import Grid
from agent import Agent

class Simulation:

    def __init__(self, grid: Grid, agents: list, max_iterations: int = 500):
        self.grid = grid
        self.agents = agents
        self.max_iterations = max_iterations
        self.iterations = 0
        self.history = []
        self.stabilised = False

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