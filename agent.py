class Agent:
    def __init__(
        self,
        group: str,
        row: int,
        col: int,
        preference: float,
        mobility: int,
        behaviour: str
    ):
        self.group = group
        self.row = row
        self.col = col
        self.preference = preference
        self.mobility = mobility
        self.behaviour = behaviour

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

    def similarity_score_at(self, grid, row: int, col: int) -> float:
        """Return the similarity score at a possible destination."""
        neighbours = grid.get_moore_neighbours(row, col)
        occupied = []

        for r, c in neighbours:
            if not grid.is_empty(r, c):
                agent = grid.get_cell(r, c)

                # The agent's original cell becomes empty after it moves.
                if agent is not self:
                    occupied.append(agent)

        if not occupied:
            return 0.0

        same = 0
        for agent in occupied:
            if agent.group == self.group:
                same += 1

        return same / len(occupied)

    def is_satisfied(self, grid) -> bool:
        """Return True when the agent meets its similarity preference."""
        return self.similarity_score(grid) >= self.preference

    def available_destinations(self, grid):
        """Return empty cells within this agent's mobility range."""
        return grid.get_empty_cells_in_radius(
            self.row,
            self.col,
            self.mobility
        )

    def step(self, grid):
        raise NotImplementedError   