import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd

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

    def update_occupancy(self):
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
        self.occupancy_history.append(self.road.occupancy.copy())

    def place_one_vehicle(self, vehicle_initial_rear_bumper_position, vehicle_initial_row, vehicle_type, length, width, lane_changing_prob, safe_stopping_speed, safe_deceleration, adjacent_sidewalk):
         #This position that position is correct and already determined
        speed = np.random.randint(0,5)
        if self.road.occupancy[vehicle_initial_rear_bumper_position:(vehicle_initial_rear_bumper_position+length), vehicle_initial_row:(vehicle_initial_row+width)].sum() == 0:
            new_vehicle = Vehicle(vehicle_initial_rear_bumper_position, speed, self.road.speed_limit,
                    length, width, self.road, vehicle_type, vehicle_initial_row, 
                    lane_changing_prob, adjacent_sidewalk, safe_stopping_speed, safe_deceleration)
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

    def place_vehicles(self, vehicle_type, length, width, lane_changing_prob, adjacent_sidewalk, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows): #will aternate the placing 
        row_options = jeepney_allowed_rows if vehicle_type == 'jeep' else truck_allowed_rows

        row = np.random.choice(row_options)
        for x_position in range(self.road.length - length + 1):
            if self.road.occupancy[x_position:x_position + length, row:row + width].sum() == 0:
                ## pick the row of which to place the vehicle
                ## it is safe to add the vehicle
                self.place_one_vehicle(x_position, row, vehicle_type, length, width, lane_changing_prob, safe_stopping_speed, safe_deceleration, adjacent_sidewalk)                        
                ## next placement will be on the other row
                self.spawned_vehicles += 1
                print(f"Placed {vehicle_type} at position {x_position} on row {row}.")
                return  # Exit the method after successfully placing the vehicle
            else:
                print(f"Waiting: Desired position occupied, no space to place a new {vehicle_type}.")

        self.unsuccessful_vehicle_placement_tries += 1   #Number of times a vehicle is tried to be placed but there are no space available    
        print(f"No space available for {vehicle_type}")

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

#-------------------------------------------------------

#The following methods were saved when running vehicle-ONLY algorithm (saved for future purposes, but not used on this simulation yet)
    def populate_the_road(self, jeep_lane_change_prob, truck_lane_change_prob, adjacent_sidewalk, boarding_time, jeepney_allowed_rows, truck_allowed_rows):
        "This method makes sure all vehicles are spawned on the road"
        if (self.spawned_vehicles < self.total_vehicles) and (self.unsuccessful_vehicle_placement_tries < (self.road.road_length/3)): #If not all vehicles have been spawned yet
            #Alternate between spawning trucks and jeeps
            truck_length, jeep_length = 7, 3
            truck_width, jeep_width = 2, 2
            
            if np.random.rand() < 0.5: #Equal chances of both vehicle types to be placed
                if (self.spawned_trucks < self.total_trucks):
                    # for x_position in range(self.road.road_length):
                    self.place_vehicles('truck', truck_length, truck_width, truck_lane_change_prob, adjacent_sidewalk, jeepney_allowed_rows, truck_allowed_rows)
            else:
                if (self.spawned_jeeps < self.total_jeeps):
                    # for x_position in range(self.road.road_length):
                    self.place_vehicles('jeep', jeep_length, jeep_width, jeep_lane_change_prob, adjacent_sidewalk, jeepney_allowed_rows, truck_allowed_rows)
            #self.simulation_step()
            for vehicle in self.vehicles:
                vehicle.speed = 0
        elif self.unsuccessful_vehicle_placement_tries > (self.total_vehicles*2): # After certain number of tries, the vehicle cannot be placed and we stopped populating the road
            self.simulation_step(boarding_time)
        else:
            self.simulation_step(boarding_time)

    def run_simulation(self, max_timesteps, truck_lane_change_prob, jeep_lane_change_prob, transient_time, adjacent_sidewalk, visualize=False):
        "Run the simulation for a specified number of timesteps"
        timestep = 0
        self.update_occupancy()

        #Create a DataFrame to store the results
        data = []

        while timestep < max_timesteps:
            self.current_time = timestep
            self.populate_the_road(jeep_lane_change_prob, truck_lane_change_prob, adjacent_sidewalk, timestep)
            if timestep >= transient_time:
                self.populate_the_road(jeep_lane_change_prob, truck_lane_change_prob, adjacent_sidewalk, timestep)
                #calculate actual truck fraction and actual density
                actual_truck_fraction = self.spawned_trucks/self.spawned_vehicles
                actual_density = (self.spawned_vehicles_occupancy) / (self.road.road_length*self.road.road_width)
                actual_truck_occupancy_fraction = (self.spawned_trucks*14)/ (self.road.road_length*self.road.road_width)
                print(f"The actual density on the road is {actual_density}. Actual truck fraction is {actual_truck_fraction}.")
                throughput = self.throughput_counter.calculate_throughput()

                #Store the results in the data list
                data.append({
                    "Timestep":timestep,
                    "Actual Density": actual_density,
                    "Actual Truck Fraction":actual_truck_fraction,
                    "Throughput": throughput,
                    "Truck Occupancy": actual_truck_occupancy_fraction
                })
            else:
                self.throughput_counter.reset_counting()

            if visualize:
                print(f"Timestep {timestep}:")
                self.visualize(timestep)

            timestep += 1
        
        print(f"Simulation complete. Total vehicles passed through position 99: {self.throughput_counter.calculate_throughput()}")
        
        results_df = pd.DataFrame(data)
        return results_df

    def simulation_step(self, boarding_time):
        np.random.shuffle(self.vehicles)
        for vehicle in self.vehicles:
            if vehicle.current_row == 1: # We  dont have to check for speed because vehicles cannot straddle if their v = 0
                vehicle.handle_straddling() 
                self.update_occupancy()
            elif np.random.rand() < vehicle.lane_changing_prob:
                #print("calling lane changing method")
                # Change lane if possible
                vehicle.lane_changing()
                vehicle.accelerate()
                #print(f"ACCELERATE DEBUGGER: {vehicle.vehicle_type} {vehicle.vehicle_id} has accelerated at a speed of {vehicle.speed}")
                vehicle.load_passenger(boarding_time)
                vehicle.unloading()
                vehicle.decelerate() # Decelerate if necessar
                vehicle.braking()
                #print(f"BEFORE MOVE DEBUGGER: {vehicle.vehicle_type} {vehicle.vehicle_id} is at position {vehicle.x_position}")
                #self.throughput_counter.count_vehicle(vehicle)
               
                vehicle.move()  # Move the vehicle
                #print(f"AFTER MOVE DEBUGGER: {vehicle.vehicle_type} {vehicle.vehicle_id} is at position {vehicle.x_position}, with a speed of {vehicle.speed} at row {vehicle.current_row}")
                self.update_occupancy()  # Update the road occupancy grid
                #self.throughput_counter.count_vehicles_at_timestep(self.vehicles)
            else:
                vehicle.accelerate()
                vehicle.load_passenger(boarding_time)
                vehicle.unloading()
                vehicle.decelerate() 
                vehicle.braking()
                vehicle.move()
                self.update_occupancy() 

            # Count vehicles passing through the monitored position (e.g., position 99)
            self.throughput_counter.count_vehicle(vehicle)