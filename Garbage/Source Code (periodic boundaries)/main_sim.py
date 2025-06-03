import pandas as pd
import numpy as np
from counter import Counter
import matplotlib.pyplot as plt
import pandas as pd

class IntegratedSimulator:
    def __init__(self, vehicle_simulator, pedestrian_simulator):
        self.vehicle_simulator = vehicle_simulator
        self.pedestrian_simulator = pedestrian_simulator
        self.counter = Counter()
        self.current_time = 0
        self.unloaded_passengers = []
        self.jeep_spatial_speeds = []
        self.truck_spatial_speeds = []
        self.vehicle_spatial_speeds = []
        self.throughput = 0
        self.passenger_throughput = 0
        self.actual_density = 0
        self.actual_truck_fraction = 0
        self.actual_truck_occupancy_fraction = 0


    def populate_the_road(self, jeep_lane_change_prob, truck_lane_change_prob, adjacent_sidewalk, timestep, transient_time, stop_to_stop_distance, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows):
        "This method makes sure all vehicles are spawned on the road"
        if (self.vehicle_simulator.spawned_vehicles < self.vehicle_simulator.total_vehicles) and (self.vehicle_simulator.unsuccessful_vehicle_placement_tries < self.vehicle_simulator.total_vehicles): #(self.vehicle_simulator.road.length/3)): #Feb 19 2025: The 2nd condition is too strict. #If not all vehicles have been spawned yet
            #Alternate between spawning trucks and jeeps
            truck_length, jeep_length = 7, 3
            truck_width, jeep_width = 2, 2            
            if np.random.rand() < 0.5: #Equal chances of both vehicle types to be placed
                if (self.vehicle_simulator.spawned_trucks < self.vehicle_simulator.total_trucks):
                    # for x_position in range(self.road.road_length):
                    self.vehicle_simulator.place_vehicles('truck', truck_length, truck_width, truck_lane_change_prob, adjacent_sidewalk, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows)
                    
            else:
                if (self.vehicle_simulator.spawned_jeeps < self.vehicle_simulator.total_jeeps):
                    # for x_position in range(self.road.road_length):
                    self.vehicle_simulator.place_vehicles('jeep', jeep_length, jeep_width, jeep_lane_change_prob, adjacent_sidewalk, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows)

            for vehicle in self.vehicle_simulator.vehicles:
                vehicle.speed = 0
        else: #self.vehicle_simulator.unsuccessful_vehicle_placement_tries > (self.vehicle_simulator.total_vehicles * 2): # After certain number of tries, the vehicle cannot be placed and we stopped populating the road
            self.integrated_simulation_step(timestep, transient_time)
        #else:
            #self.integrated_simulation_ste, #Commented out: February 19, 2025 (3:02 PM)

    def integrated_simulation_step(self, timestep, transient_time): #Integrated Simulation Step
        np.random.shuffle(self.vehicle_simulator.vehicles)
        np.random.shuffle(self.pedestrian_simulator.passengers)
        
        for vehicle in self.vehicle_simulator.vehicles:
            if vehicle.current_row == 1: # We  dont have to check for speed because vehicles cannot straddle if their v = 0
                vehicle.finish_lane_change()
                for passenger in vehicle.passengers_within_vehicle:
                    passenger.update_riding_status(vehicle)
                    # print(f"Passenger {passenger.passenger_id}'s riding status is {passenger.riding_status}")

            elif np.random.rand() < vehicle.lane_changing_prob:
                vehicle.accelerate()
                vehicle.lane_changing()
                # print(f"{vehicle.vehicle_type} {vehicle.vehicle_id}: Overshot a destination? --- {vehicle.overshot_destination}. Lane change trials  = {vehicle.lane_change_trials_for_passengers}")
                for passenger in vehicle.passengers_within_vehicle:
                    passenger.update_riding_status(vehicle)
                    # print(f"Passenger {passenger.passenger_id}'s riding status is {passenger.riding_status}")

                vehicle.decelerate()
                # print(f"{vehicle.vehicle_type} {vehicle.vehicle_id} has {len(vehicle.passengers_within_vehicle)} before calling unloading method.")

                vehicle.unloading(self.unloaded_passengers)
                for passenger in self.unloaded_passengers:
                    passenger.calculate_riding_time()
                    # print(f"Passenger {passenger.passenger_id}'s riding status is {passenger.riding_status} and the riding time is {passenger.riding_time}.")
                # print(f"{vehicle.vehicle_type} {vehicle.vehicle_id} has {len(vehicle.passengers_within_vehicle)} after calling unloading method.")
                vehicle.loading()
                for passenger in vehicle.passengers_within_vehicle:
                    passenger.update_riding_status(vehicle)
                    passenger.calculate_waiting_time()
                    #print(f"Passenger {passenger.passenger_id}'s riding status is {passenger.riding_status} and the waiting time is {passenger.waiting_time}.")
                
                vehicle.random_slowdown()
                vehicle.move() #Move the vehicle
                for passenger in vehicle.passengers_within_vehicle:
                    passenger.update_riding_status(vehicle)
                vehicle.temporal_speeds.append(vehicle.speed)
            
            
            else:
                vehicle.accelerate()
                for passenger in vehicle.passengers_within_vehicle:
                    passenger.update_riding_status(vehicle)
                    # print(f"Passenger {passenger.passenger_id}'s riding status is {passenger.riding_status}")
                    
                vehicle.decelerate() 

                vehicle.unloading(self.unloaded_passengers)
                for passenger in self.unloaded_passengers:
                    passenger.calculate_riding_time()
                    # print(f"Passenger {passenger.passenger_id}'s riding status is {passenger.riding_status} and the riding time is {passenger.riding_time}.")
                    self.pedestrian_simulator.update_sidewalk_occupancy()
                vehicle.loading()
                for passenger in vehicle.passengers_within_vehicle:
                    passenger.update_riding_status(vehicle)
                    passenger.calculate_waiting_time()
                    # print(f"Passenger {passenger.passenger_id}'s riding status is {passenger.riding_status} and the waiting time is {passenger.waiting_time}.")            
                vehicle.random_slowdown()
                vehicle.move()

                for passenger in vehicle.passengers_within_vehicle:
                    passenger.update_riding_status(vehicle)
                
                vehicle.temporal_speeds.append(vehicle.speed)

            self.vehicle_simulator.update_occupancy(timestep)
            # Count vehicles passing through the monitored position (e.g., position 99)
            self.counter.count_vehicle(vehicle)
            self.counter.count_passenger(vehicle)

        #Collect individual speeds of vehicles per timestep (To compute the spatial mean speed per timestep)
        if timestep >= transient_time:
            self.vehicle_spatial_speeds.append(vehicle.speed) #include the vehicle's speed on the list of all the vehicle's speed
            if vehicle.vehicle_type == "jeep":
                self.jeep_spatial_speeds.append(vehicle.speed)
            else:
                self.truck_spatial_speeds.append(vehicle.speed)

        
        self.vehicle_simulator.occupancy_history.append((timestep, self.vehicle_simulator.road.occupancy.copy()))
        for passenger_list in self.pedestrian_simulator.sidewalk.passengers:
            for passenger in passenger_list:
                passenger.switch_sidewalk_position()
                self.pedestrian_simulator.update_occupancy()

    def run_simulation(self, max_timesteps, truck_lane_change_prob, jeep_lane_change_prob, transient_time, density, truck_fraction, stop_to_stop_distance, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows, visualize=False):
        timestep = 0
        # Initialize or reset relevant data
        #self.vehicle_simulator.update_occupancy()
        #self.pedestrian_simulator.update_sidewalk_occupancy()
        self.vehicle_simulator.initialize_vehicles(density, truck_fraction)
        
        data_vehicles = []
        data_timestep = []
        data_passengers = []
        data_jeep = []
        data_trucks = []
        data_spatio_temporal = None

        self.pedestrian_simulator.generate_stops(stop_to_stop_distance)
        #print(f"The stops generated")
        while timestep < max_timesteps:
            # Update both simulators at each timestep
            if timestep < transient_time:
                self.current_time = timestep
                self.pedestrian_simulator.current_time = timestep
                self.vehicle_simulator.current_time = timestep
                #print(f"Implementing rules for timestep {timestep}")
                
                self.pedestrian_simulator.generate_passengers(self.vehicle_simulator, timestep)
                self.populate_the_road(jeep_lane_change_prob, truck_lane_change_prob, self.pedestrian_simulator.sidewalk, timestep, transient_time, stop_to_stop_distance, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows)  # Update vehicles
                for passenger in self.pedestrian_simulator.passengers:
                    passenger.current_time = timestep

            # Collect data after transient period
            else: #timestep >= transient_time:
                self.current_time = timestep
                self.pedestrian_simulator.current_time = timestep
                self.vehicle_simulator.current_time = timestep

                self.pedestrian_simulator.generate_passengers(self.vehicle_simulator, timestep)
                self.populate_the_road(jeep_lane_change_prob, truck_lane_change_prob,  self.pedestrian_simulator.sidewalk,timestep, transient_time, stop_to_stop_distance, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows) # Update vehicles
                for passenger in self.pedestrian_simulator.passengers:
                    passenger.current_time = timestep
                
                #Collect data for Travel speed of each vehicle
                if timestep == transient_time:
                    for vehicle in self.vehicle_simulator.vehicles:
                        self.starting_rear_bumper_position = vehicle.rear_bumper_position
                elif timestep == max_timesteps - 1:
                    for vehicle in self.vehicle_simulator.vehicles:
                        self.end_rear_bumper_position = vehicle.rear_bumper_position

                #Data for each timestep
                self.throughput = self.counter.calculate_vehicle_throughput()
                self.passenger_throughput = self.counter.calculate_passenger_throughput()
                self.actual_density = (self.vehicle_simulator.spawned_vehicles_occupancy) / (self.vehicle_simulator.road.length * self.vehicle_simulator.road.width)
                self.actual_truck_fraction = self.vehicle_simulator.spawned_trucks / self.vehicle_simulator.spawned_vehicles
                self.actual_truck_occupancy_fraction = (self.vehicle_simulator.spawned_trucks*14)/ (self.vehicle_simulator.road.length * self.vehicle_simulator.road.width)
                vehicle_spatial_mean_speed = np.mean(self.vehicle_spatial_speeds)
                jeep_spatial_mean_speed = np.mean(self.jeep_spatial_speeds)
                truck_spatial_mean_speed = np.mean(self.truck_spatial_speeds)
                
                data_timestep.append({
                    "Timestep": timestep,
                    "Actual Density": self.actual_density,
                    "Actual Truck Fraction": self.actual_truck_fraction,
                    "Throughput": self.throughput,
                    "Passenger Throughput":self.passenger_throughput,
                    "Jeep Spatial Mean Speed":jeep_spatial_mean_speed,
                    "Truck Spatial Mean Speed":truck_spatial_mean_speed,
                    "Vehicle Spatial Mean Speed":vehicle_spatial_mean_speed,
                    "Truck Occupancy Fraction":self.actual_truck_occupancy_fraction})
            if visualize:
                #self.visualize(timestep)
                self.visualize_combined(timestep)


            
            timestep += 1
            # Collect passenger data(after running the whole simulation)
        occupancy_data = []
        for timestep, occupancy_grid in self.vehicle_simulator.occupancy_history:
            # print(f"The number of rows on the road based on occupancy grid is {occupancy_grid.shape[1]}")
            for y in range(occupancy_grid.shape[1]):  # Loop over each row (y-axis)
                occupancy_data.append([timestep, y] + occupancy_grid[:, y].tolist())  # Store row-wise data

        # Create DataFrame
        road_length = self.vehicle_simulator.road.length
        columns = ["Timestep", "Road Row"] + [f"Pos {x}" for x in range(road_length)]
        data_spatio_temporal = pd.DataFrame(occupancy_data, columns=columns)

        for passenger in self.pedestrian_simulator.passengers:
            riding_time = passenger.riding_time
            waiting_time = passenger.waiting_time
            #total_simulation_time = max_timesteps - transient_time
            #passenger_travel_speed = passenger.calculate_riding_speed(total_simulation_time)
            data_passengers.append({
                "Passenger ID": passenger.passenger_id,
                "Riding Time": riding_time,
                "Waiting Time": waiting_time,
                "Riding Status":passenger.riding_status})
                #"Passenger Travel Speed":passenger_travel_speed})

            #Collect vehicle data
            
        for vehicle in self.vehicle_simulator.vehicles:
            vehicle.mean_temporal_speed = np.mean(vehicle.temporal_speeds)
            #total_simulation_time = max_timesteps - transient_time
            #travel_speed = vehicle.calculate_simulation_travel_speed(total_simulation_time) #distance/total time
            data_vehicles.append({"Vehicle ID":vehicle.vehicle_id,
                                        "Mean Speed Across Time":vehicle.mean_temporal_speed,
                                        "Actual Density":self.actual_density, 
                                        "Truck Occupancy Fraction":self.actual_truck_occupancy_fraction})

            if vehicle.vehicle_type == "jeep":
                data_jeep.append({"Jeep ID":vehicle.vehicle_id,
                                        "Mean Speed Across Time":vehicle.mean_temporal_speed,
                                        "Actual Density":self.actual_density, 
                                        "Truck Occupancy Fraction":self.actual_truck_occupancy_fraction})
            else:
                data_trucks.append({"Truck ID":vehicle.vehicle_id,
                                        "Mean Speed Across Time":vehicle.mean_temporal_speed,
                                        "Actual Density":self.actual_density, 
                                        "Truck Occupancy Fraction":self.actual_truck_occupancy_fraction})

        # Return the results in a dataframe
        results_timestep = pd.DataFrame(data_timestep)
        results_vehicles = pd.DataFrame(data_vehicles)
        results_passengers = pd.DataFrame(data_passengers)
        results_spatio_temporal = pd.DataFrame(data_spatio_temporal)
        return results_timestep, results_passengers, results_vehicles, results_spatio_temporal
    
    # def save_to_csv(self, data_frame):
    #     data_frame.to_csv("{}")
    #     return

    def visualize(self, timestep):
        """Visualize both the vehicle and pedestrian data at a specific timestep."""
        # Vehicle simulation visualization
        self.vehicle_simulator.visualize(timestep)

        # Pedestrian simulation visualization
        self.pedestrian_simulator.visualize(timestep)


    def visualize_combined(self, step_count):
        """Visualize the road and sidewalk occupancy in a single figure."""
        fig, axs = plt.subplots(
            2, 1, figsize=(20, 8), 
            gridspec_kw={'height_ratios': [2, 1]},  # Road is taller than the sidewalk
            sharex=True)

        # Road visualization (Top subplot)
        axs[0].imshow(self.vehicle_simulator.road.occupancy.T, cmap=self.vehicle_simulator.cmap, norm=self.vehicle_simulator.norm, origin='lower')
        axs[0].set_title(f'Step {step_count}')
        # axs[0].set_ylabel('Lane')
        # axs[0].set_yticks(range(0, self.vehicle_simulator.road.width, 1))

        # Sidewalk visualization (Bottom subplot)
        axs[1].imshow(self.pedestrian_simulator.sidewalk.occupancy.T, cmap=self.pedestrian_simulator.cmap, norm=self.pedestrian_simulator.norm, origin='lower')
        #axs[1].set_title('Sidewalk Occupancy')
        #axs[1].set_xlabel('Position (cells)')
        #axs[1].set_ylabel('Sidewalk Width')
        axs[1].set_yticks(range(0, self.pedestrian_simulator.sidewalk.width, 1))

        # Align x-axis and improve layout
        plt.xticks(range(0, self.vehicle_simulator.road.length, 1))
        plt.tight_layout()
        plt.show()