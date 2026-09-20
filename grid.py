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