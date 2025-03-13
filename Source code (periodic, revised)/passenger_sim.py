import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from passenger import Passenger
from sidewalk import Sidewalk
from stop import Stop

class Passenger_Simulator:
    def __init__(self, sidewalk:Sidewalk, passenger_arrival_rate, road_designation, max_passengers_per_cell, vehicle_simulator):
        self.sidewalk = sidewalk
        self.road_designation = road_designation
        self.passenger_arrival_rate = passenger_arrival_rate
        self.passengers = []
        self.current_time = 0
        self.sidewalk_occupancy_history = []

        self.total_passengers = 0
        self.total_passengers_loaded = 0
        self.total_passengers_unloaded = 0
        self.max_passengers_per_cell = max_passengers_per_cell
        self.vehicle_simulator = vehicle_simulator

        self.cmap = mcolors.LinearSegmentedColormap.from_list("white_to_dark_red", ["white", "darkred"])
        self.norm = mcolors.Normalize(vmin=0, vmax=5)  # Normalize the range of values to 0-5
        self.waiting_passengers = []
        self.in_transit_passengers = []
        self.alighted_passengers = []

    def update_occupancy(self, timestep):
        """
        Update sidewalk occupancy values based on the number of passengers present
        at each cell. The value in each cell represents the number of passengers.
        """
        # Reset the sidewalk occupancy matrix to zeros
        self.sidewalk.occupancy.fill(0)                 
        for x_position in range(self.sidewalk.length):
            number_of_passengers_present = len(self.sidewalk.stops[x_position][0].loading_list)
            # print(f"The number of passengers present at position {x_position} is {number_of_passengers_present}.")
            self.sidewalk.occupancy[x_position] = number_of_passengers_present        # Count passengers for each cell
        # print(f"Hence, sidewalk occupancy is {self.sidewalk.occupancy}.")
        #self.sidewalk_occupancy_history.append(self.sidewalk.occupancy.copy())

    def generate_stops(self, stop_to_stop_distance):
        """
        Generate stops at regular intervals along the sidewalk.

        Args:
            stop_to_stop_distance (int): Distance between consecutive stops.
        """
        stop_id = 0 # Boarding stops have stop_id = 0
        for position in range(0, self.sidewalk.length, stop_to_stop_distance):
            new_stop = Stop(position, stop_id)
            self.sidewalk.stops[position].append(new_stop)
        #print(f"The  stops generated are {self.sidewalk.stops}")

    def generate_passengers(self, vehicle_simulator, current_time_pass):#Put an algorithm that generates passengers only on designated stops
        """Generate new passengers based on the arrival rate and places them on the sidewalk."""
        for position in range(0, self.sidewalk.length):
            #print(f"The position being checked for additional passenger is {col}")
            #print(f"The stops at position {position} is {self.sidewalk.boarding_stops[position]}")
            if len(self.sidewalk.stops[position]) != 0: #We spawn passengers on sidewalk cells with designated stops only (Here, we check for the presence of a stop)
                
                if self.sidewalk.frozen_cells[position]:# **Skip frozen cells**
                    continue
                
                if np.random.random() < self.passenger_arrival_rate:
                    if self.sidewalk.occupancy[position, 0] < self.sidewalk.max_passengers_per_cell:
                        distance_within_sight_param = 4
                        destination = None 
                        set_of_stops = self.sidewalk.stops
                        
                        for stop_list in set_of_stops:
                            for stop in stop_list:
                                if stop.position == position:
                                    destination = stop #Dirac-delta distribution of distances

                        # print(f"The destination position for the passenger initiated at position {position} is {position}")
                        new_passenger = Passenger(current_time_pass, self.sidewalk, 
                        self.road_designation, position, distance_within_sight_param, 
                        destination, vehicle_simulator, self)
                        # print(f"Passenger {new_passenger.passenger_id}'s destinations at {new_passenger.destination_stop}")
                        self.passengers.append(new_passenger)
                        # print(f"The passenger list after the passenger is placed at {position} is {self.passengers}")
                        #self.sidewalk.passengers[position].append(new_passenger)
                        #print(f"The sidewalk list where passenger is at position {col} is {self.sidewalk.passengers[col]}")
                        self.sidewalk.stops[position][0].loading_list.append(new_passenger)
                        # print(f"Passenger {new_passenger.passenger_id} is added to Stop at {self.sidewalk.stops[position][0].position}. The loading list is {self.sidewalk.stops[position][0].loading_list}.")
                        self.waiting_passengers.append(new_passenger)
                        self.update_occupancy(self.current_time)
                        #print(f"Passenger added at position {col}.")
                        #print(f"Passenger {new_passenger.passenger_id} was added to position {position}, where the destination is at {destination_position}.")
        # print(f"Time {self.current_time}: {len(self.passengers)} passengers generated.")

    def visualize(self, step_count):
        """Visualize the sidewalk occupancy using a colormap."""
        plt.figure(figsize=(20, 6))
        plt.imshow(self.sidewalk.occupancy.T, cmap=self.cmap, norm=self.norm, origin='lower')
        #plt.colorbar(label='Number of Passengers')
        plt.title(f"Timestep {step_count}")
        plt.xlabel("Sidewalk Position (cells)")
        #plt.ylabel("Sidewalk Width (rows)")
        plt.xticks(range(0, self.sidewalk.length, 1))
        plt.yticks(range(0, self.sidewalk.width, 1))
        plt.tight_layout()
        plt.show()