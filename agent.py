class Agent:
    def __init__(self, group: str, row: int, col: int):
        self.group = group
        self.row = row
        self.col = col

    def similarity_score(self, grid) -> float:
        """Return proportion of occupied neighbours that share this agent's group.

        Returns 0.0 if there are no occupied neighbours.
        """
        neighbours = grid.get_moore_neighbours(self.row, self.col)
        occupied = []
        for r, c in neighbours:
            if not grid.is_empty(r, c):
                occupied.append(grid.get_cell(r, c))
        if not occupied:
            return 0.0
        same = 0
        for agent in occupied:
            if agent.group == self.group:
                same += 1
        return same / len(occupied)

    def is_satisfied(self, grid) -> bool:
        raise NotImplementedError

    def step(self, grid):
        raise NotImplementedError   