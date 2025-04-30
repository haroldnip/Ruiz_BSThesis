import numpy as np

class Road:
    def __init__(self, length, width, speed_limit, allowed_rows = None):
        self.length = length
        self.width = width
        self.speed_limit = speed_limit
        self.occupancy = np.zeros((length, width)) #Results to a vertical 2D array, get the transpose when plotting
        self.allowed_rows = allowed_rows if allowed_rows is not None else []
        self.lane_1_vehicle_occupancy = 0
        self.lane_2_vehicle_occupancy = 0

    def is_lane_change_allowed(self, target_row, vehicle_type):
        "Check if the target row is allowed for the vehicle type"
        for row, allowed_type in self.allowed_rows:
            if target_row == row and vehicle_type != allowed_type:
                return False
        return True