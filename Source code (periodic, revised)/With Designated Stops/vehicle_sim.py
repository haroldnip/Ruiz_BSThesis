import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from vehicle import Vehicle
from road import Road
from counter import Counter

class IntraRoadSimulator:
    def __init__(self, road: Road):
        """This method stores the input agents and initializes output data"""
        self.road = road  # Store the road instance
        self.vehicles = []  # List to store vehicle instances
        self.occupancy_history = [] # List to store the history of road occupancy states
        self.current_time = 0

        self.total_vehicles = 0
        self.total_trucks = 0
        self.total_jeeps = 0

        self.spawned_trucks = 0
        self.spawned_jeeps = 0
        self.spawned_vehicles = 0 
        self.spawned_vehicles_occupancy = 0
        self.unsuccessful_vehicle_placement_tries = 0
        # Initialize the throughput counter for a specific position (e.g., position 99)
        self.throughput_counter = Counter()  # Change position as needed
        self.cmap = mcolors.ListedColormap(['white', 'gray', 'black'])
        self.norm = mcolors.BoundaryNorm(boundaries=np.arange(0, 4), ncolors=3)
        self.jeep_spatial_speeds = [] #mean speed of jeepneys for each timestep 
        self.truck_spatial_speeds = []  #mean speed of trucks for each timestep 


    def update_occupancy(self, timestep):
        """This method updates road occupancy based on vehicle position and length"""
        self.road.occupancy.fill(0)
        for vehicle in self.vehicles:
            x_start = vehicle.rear_bumper_position
            x_end = (vehicle.rear_bumper_position + vehicle.length) % self.road.length #from vehicle rear bumper(position|) to front, minus 1. takes account of toroidal boundaries
            y_start = vehicle.current_row
            y_end = min(vehicle.current_row + vehicle.width, self.road.width)
            if x_start < x_end:
                if vehicle.vehicle_type == "jeep":
                    self.road.occupancy[x_start:x_end, y_start:y_end] = 1
                else:
                    self.road.occupancy[x_start:x_end, y_start:y_end] = 2
            else:
                if vehicle.vehicle_type == "jeep":
                    self.road.occupancy[x_start:, y_start:y_end] = 1
                    self.road.occupancy[:x_end, y_start:y_end] = 1
                else:
                    self.road.occupancy[x_start:, y_start:y_end] = 2
                    self.road.occupancy[:x_end, y_start:y_end] = 2
        
        
    # def compute_lane_occupancy(self):
    #     """Computes the occupancy fraction for each lane."""
    #     total_cells_per_lane = self.road.length * 2  # Each lane is 2 cells wide

    #     lane_1 = self.road.occupancy[:, 0:2]  # First lane (2-cell width)
    #     lane_2 = self.road.occupancy[:, 2:4]  # Second lane (2-cell width)

    #     lane_1_occupancy = np.count_nonzero(lane_1 > 0) / total_cells_per_lane
    #     lane_2_occupancy = np.count_nonzero(lane_2 > 0) / total_cells_per_lane

    #     return lane_1_occupancy, lane_2_occupancy


    def compute_lane_occupancy(self, lane_start_row):
        """Computes the occupancy fraction for a given lane."""
        lane_width = 2  # Each lane is 2 cells wide
        total_cells = self.road.length * lane_width  # Total number of cells in this lane

        row_end = lane_start_row + lane_width
        lane_cells = self.road.occupancy[:, lane_start_row:row_end]  # Extract the lane region
        
        # Compute the occupancy fraction for this lane
        occupancy_fraction = np.count_nonzero(lane_cells > 0) / total_cells

        return occupancy_fraction  # Returns the occupancy fraction for the given lane


    def place_one_vehicle(self, vehicle_initial_rear_bumper_position, vehicle_initial_row, vehicle_type, length, width, safe_stopping_speed, safe_deceleration, adjacent_sidewalk):
         #This position that position is correct and already determined
        
        speed = np.random.randint(0,5)
        randomize_lane_change_prob = np.random.rand()
        if self.road.occupancy[vehicle_initial_rear_bumper_position:(vehicle_initial_rear_bumper_position+length), vehicle_initial_row:(vehicle_initial_row+width)].sum() == 0:
            new_vehicle = Vehicle(vehicle_initial_rear_bumper_position, speed, self.road.speed_limit,
                    length, width, self.road, vehicle_type, vehicle_initial_row, 
                    randomize_lane_change_prob, adjacent_sidewalk, safe_stopping_speed, safe_deceleration)
            # Add new vehicle to list of vehicles present in the road
            self.vehicles.append(new_vehicle)
            # Mark the road occupancy record to set where the new vehicle was
            # placed as occupied.
            if vehicle_type == 'jeep':
                self.road.occupancy[vehicle_initial_rear_bumper_position:(vehicle_initial_rear_bumper_position+length), vehicle_initial_row:(vehicle_initial_row + width)] = 1
                self.spawned_jeeps +=1
                self.spawned_vehicles_occupancy += 6
                return True
            else: # Vehicle type is truck
                self.road.occupancy[vehicle_initial_rear_bumper_position:(vehicle_initial_rear_bumper_position+length), vehicle_initial_row:(vehicle_initial_row+width)] = 2
                self.spawned_trucks +=1
                self.spawned_vehicles_occupancy += 14
                return True
        else:
            raise Exception("Vehicle cannot be placed")
            return False

    def place_vehicles(self, vehicle_type, length, width, adjacent_sidewalk, 
                    safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows):  
        """
        Places vehicles in the least occupied allowed row.
        """
        row_options = jeepney_allowed_rows if vehicle_type == 'jeep' else truck_allowed_rows

        # Pick a random starting row
        row = np.random.choice(row_options)

        # Compute occupancy for each allowed row
        row_occupancies = {r: self.compute_lane_occupancy(r) for r in row_options}

        # Choose the row with the least occupancy
        row = min(row_occupancies, key=row_occupancies.get)

        for x_position in range(self.road.length - length + 1):
            if self.road.occupancy[x_position:x_position + length, row:row + width].sum() == 0:
                # Place the vehicle
                self.place_one_vehicle(x_position, row, vehicle_type, length, width, 
                                    safe_stopping_speed, safe_deceleration, adjacent_sidewalk)                        
                self.spawned_vehicles += 1
                return  # Exit after placing the vehicle

        self.unsuccessful_vehicle_placement_tries += 1  # Count failed placement attempts


    # def place_vehicles(self, vehicle_type, length, width, adjacent_sidewalk, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows): #will aternate the placing 
    #     row_options = jeepney_allowed_rows if vehicle_type == 'jeep' else truck_allowed_rows

    #     self.road.lane_1_vehicle_occupancy, self.road.lane_2_vehicle_occupancy = self.compute_lane_occupancy()

    #     row = np.random.choice(row_options)
    #     for x_position in range(self.road.length - length + 1):
    #         if self.road.occupancy[x_position:x_position + length, row:row + width].sum() == 0:
    #             ## pick the row of which to place the vehicle
    #             ## it is safe to add the vehicle
    #             self.place_one_vehicle(x_position, row, vehicle_type, length, width, safe_stopping_speed, safe_deceleration, adjacent_sidewalk)                        
    #             ## next placement will be on the other row
    #             self.spawned_vehicles += 1
    #             #print(f"Placed {vehicle_type} at position {x_position} on row {row}.")
    #             return  # Exit the method after successfully placing the vehicle
    #         else:
    #             #print(f"Waiting: Desired position occupied, no space to place a new {vehicle_type}.")
    #             pass

    #     self.unsuccessful_vehicle_placement_tries += 1   #Number of times a vehicle is tried to be placed but there are no space available    
    #     #print(f"No space available for {vehicle_type}")

    def initialize_vehicles(self, density, truck_fraction):
        "The number of trucks and jeepneys are determined"
        A, B = 7 * 2, 3 * 2
        L, W = self.road.length, self.road.width
        N = int((density * L * W)*((truck_fraction/A) + ((1 - truck_fraction)/ B)))
        truck_count = int(N * truck_fraction)
        jeep_count = N - truck_count

        self.total_vehicles = N
        self.total_trucks = truck_count
        self.total_jeeps = jeep_count

        self.spawned_vehicles = self.spawned_jeeps + self.spawned_trucks
        return

    def visualize(self, step_count):
        plt.figure(figsize=(20, 6))
        plt.imshow(self.road.occupancy.T, cmap=self.cmap, norm=self.norm, origin='lower')
        plt.title(f'Step {step_count}')
        plt.xlabel('Road Length')
        plt.ylabel('Lane')
        plt.xticks(range(0, self.road.length, 1))
        plt.yticks(range(0, self.road.width, 1))
        plt.tight_layout()
        plt.show()