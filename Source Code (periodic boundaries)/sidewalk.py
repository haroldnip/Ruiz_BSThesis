import numpy as np

class Sidewalk:
    def __init__(self, length, width, max_passengers_per_cell = 5):
        """
        Initialize the sidewalk grid.

        Args:
            length (int): Length of the sidewalk (number of cells along its length).
            width (int): Width of the sidewalk (number of rows).
            max_passengers_per_cell (int): Maximum number of passengers allowed per cell.
        """
        self.length = length
        self.width = width
        self.max_passengers_per_cell = max_passengers_per_cell
        
        # Each cell's occupancy count is initialized to 0
        self.occupancy = np.zeros((length, width), dtype=int) #This is a vertical array (get the transpose for horizontal visualization)

        # Grid to track passenger details (e.g., lists of passengers in each cell)
        self.passengers = [[] for _ in range(length)]
        self.boarding_stops = [[] for _ in range(self.length) ] #This should be a list, bcoz we will parametrize this later
        self.alighting_stops = [[] for _ in range(self.length) ]