import random


class Grid:
   
    def __init__(self, width: int = 40, height: int = 40, vacancy_rate: float = 0.10):
        """

        width        : number of columns
        height       : number of rows
        vacancy_rate : fraction of cells that remain empty (default 10%)
        """
        if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
            raise ValueError("width must be a positive integer")

        if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
            raise ValueError("height must be a positive integer")

        if (
            isinstance(vacancy_rate, bool)
            or not isinstance(vacancy_rate, (int, float))
            or not 0.0 < vacancy_rate < 1.0
        ):
            raise ValueError("vacancy_rate must be strictly between 0 and 1")

        self.width = width
        self.height = height
        self.vacancy_rate = vacancy_rate

        self._cells = []
        for i in range(height):
            row = []
            for i in range(width):
                row.append(None)
            self._cells.append(row)

    def is_valid(self, row: int, col: int) -> bool:
        """Return True if (row, col) is within grid bounds."""
        return 0 <= row < self.height and 0 <= col < self.width

    def get_cell(self, row: int, col: int):
        """Return the occupant at (row, col), or None if the cell is empty. 
        """
        if not self.is_valid(row, col):
            raise IndexError(
                f"Position ({row}, {col}) is out of bounds"
            )
        return self._cells[row][col]

    def set_cell(self, row: int, col: int, occupant):
        """Set the occupant at (row, col) to occupant.
        
        """
        if not self.is_valid(row, col):
            raise IndexError(
                f"Position ({row}, {col}) is out of bounds"
            )
        self._cells[row][col] = occupant

    def is_empty(self, row: int, col: int):

        if not self.is_valid(row,col):
            raise IndexError(
                f"Position ({row}, {col}) is out of bounds"
            )
        return self._cells[row][col] is None
    
    def empty_cells(self):
        empty = []
        for row in range(self.height):
            for col in range(self.width):
                if self.is_empty(row, col):
                    empty.append((row, col))
        return empty
    
    def num_empty(self):
        return len(self.empty_cells())  
    def num_occupied(self):
        return (self.width * self.height) - self.num_empty()
    
    def total_cells(self):
        return self.width * self.height
    
    def random_empty_cell(self):
        empty = self.empty_cells()
        if not empty:
            return None
        return random.choice(empty)

    def get_moore_neighbours(self, row: int, col: int):
        """Return a list of (row, col) positions for all valid Moore neighbours.

        Considers the 8 surrounding cells. Cells outside the grid boundary are excluded.
        """
        neighbours = []
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if self.is_valid(nr, nc):
                    neighbours.append((nr, nc))
        return neighbours

    def get_cells_in_radius(self, row: int, col: int, radius: int):
        """Return a list of (row, col) positions within *radius* of (row, col).

        Uses Chebyshev distance (square region), consistent with the Moore
        neighbourhood. The cell itself is excluded. Cells outside the grid
        boundary are excluded.
        """
        cells = []
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if self.is_valid(nr, nc):
                    cells.append((nr, nc))
        return cells

    def get_empty_cells_in_radius(self, row: int, col: int, radius: int):

        cells = self.get_cells_in_radius(row, col, radius)
        empty_cells = []
        for r, c in cells:
            if self.is_empty(r, c):
                empty_cells.append((r, c))
        return empty_cells

    def move_occupant(self, from_row: int, from_col: int, to_row: int, to_col: int):
        """Move the occupant at (from_row, from_col) to (to_row, to_col).
        """
        if not self.is_valid(from_row, from_col):
            raise IndexError(f"Source position is out of bounds")
        if not self.is_valid(to_row, to_col):
            raise IndexError(f"Destination position is out of bounds")
        if self.is_empty(from_row, from_col):
            raise ValueError(f"Source cell is empty")
        if not self.is_empty(to_row, to_col):
            raise ValueError(f"Destination cell is already occupied")

        self._cells[to_row][to_col] = self._cells[from_row][from_col]
        self._cells[from_row][from_col] = None

    def populate(self, occupants: list):
        """Randomly place occupants onto the grid.

        The number of occupants must not exceed the number of cells that
        should be occupied given the vacancy_rate:
            max_occupants = total_cells * (1 - vacancy_rate)
        """
        max_occupants = int(self.total_cells() * (1 - self.vacancy_rate))
        if len(occupants) > max_occupants:
            raise ValueError(
                f"Too many occupants "
                f"vacancy_rate={self.vacancy_rate} allows at most {max_occupants}"
            )

        all_positions = []
        for r in range(self.height):
            for c in range(self.width):
                all_positions.append((r, c))
        random.shuffle(all_positions)

        for i, occupant in enumerate(occupants):
            r, c = all_positions[i]
            self._cells[r][c] = occupant
            occupant.row = r
            occupant.col = c
