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

        self._cells: list[list] = [[None] * width for _ in range(height)]

    def is_valid(self, row: int, col: int) -> bool:
        """Return True if (row, col) is within grid bounds."""
        return 0 <= row < self.height and 0 <= col < self.width

    def get_cell(self, row: int, col: int):
        """Return the occupant at (row, col), or None if the cell is empty.

        Raises IndexError if (row, col) is out of bounds.
        """
        if not self.is_valid(row, col):
            raise IndexError(
                f"Position ({row}, {col}) is out of bounds for grid {self.height}x{self.width}"
            )
        return self._cells[row][col]
