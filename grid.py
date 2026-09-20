import random


class Grid:
    """
    A 2D grid environment for the Schelling segregation model.

    Cells hold either None (empty) or an occupant object assigned later.
    Coordinates are (row, col) with (0, 0) at the top-left.
    """

    def __init__(self, width: int = 40, height: int = 40, vacancy_rate: float = 0.10):
        """
        Initialise an empty grid.
       
        width        : number of columns
        height       : number of rows
        vacancy_rate : fraction of cells that remain empty (default 10%)
        """
        if not (0.0 < vacancy_rate < 1.0):
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

        Raises IndexError if (row, col) is out of bounds.
        """
        if not self.is_valid(row, col):
            raise IndexError(
                f"Position ({row}, {col}) is out of bounds"
            )
        return self._cells[row][col]

    def set_cell(self, row: int, col: int, occupant):
        """Set the occupant at (row, col) to occupant.
        
        Raises IndexError if (row, col) is out of bounds.
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
        """Return a list of empty (row, col) positions within *radius* of (row, col)."""
        cells = self.get_cells_in_radius(row, col, radius)
        empty_cells = []
        for r, c in cells:
            if self.is_empty(r, c):
                empty_cells.append((r, c))
        return empty_cells
