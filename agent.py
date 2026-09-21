import random

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

    def choose_destination(self, grid):
        """Choose an empty destination according to the movement behaviour."""
        destinations = self.available_destinations(grid)

        if not destinations:
            return None

        if self.behaviour == "random":
            return random.choice(destinations)

        if self.behaviour == "improving":
            current_score = self.similarity_score(grid)
            improving_destinations = []

            for row, col in destinations:
                new_score = self.similarity_score_at(grid, row, col)

                if new_score > current_score:
                    improving_destinations.append((row, col))

            if not improving_destinations:
                return None

            return random.choice(improving_destinations)

        if self.behaviour == "best_fit":
            scored_destinations = []

            for row, col in destinations:
                score = self.similarity_score_at(grid, row, col)
                scored_destinations.append((score, row, col))

            best_score = max(
                score for score, row, col in scored_destinations
            )

            best_destinations = []
            for score, row, col in scored_destinations:
                if score == best_score:
                    best_destinations.append((row, col))

            return random.choice(best_destinations)

        return None

    def step(self, grid) -> bool:
        """Perform one movement decision and return whether the agent moved."""
        if self.is_satisfied(grid):
            return False

        destination = self.choose_destination(grid)

        if destination is None:
            return False

        new_row, new_col = destination
        old_row, old_col = self.row, self.col

        grid.move_occupant(
            old_row,
            old_col,
            new_row,
            new_col
        )

        self.row = new_row
        self.col = new_col

        return True