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
        self.stops = [[] for _ in range(self.length) ] #This should be a list of lists, bcoz we will parametrize this later
        #Track frozen status of sidewalk cells
    #     self.frozen_cells = np.zeros(length, dtype=bool) #False by default

    # def freeze_cells_for_loading(self, road_positions):
    #     """Freeze sidewalk cells while a vehicle is loading passengers"""
    #     for pos in road_positions:
    #         self.frozen_cells[pos] = True #Mark sidewalk cell as frozen
    #         # print(f"Sidewalk cell {pos} freezing status is {self.frozen_cells[pos]}")

    # def unfreeze_cells(self, road_positions):
    #     """Unfreeze sidewalk cells after loading is done"""
    #     for pos in road_positions:
    #         self.frozen_cells[pos] = False #Mark sidewalk cell as unfrozen
    #         # print(f"Sidewalk cell {pos} freezing status is {self.frozen_cells[pos]}")
            