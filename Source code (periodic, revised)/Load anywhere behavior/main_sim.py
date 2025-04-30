import pandas as pd
import numpy as np
from counter import Counter
import matplotlib.pyplot as plt

class IntegratedSimulator:
    def __init__(self, vehicle_simulator, pedestrian_simulator):
        self.vehicle_simulator = vehicle_simulator
        self.pedestrian_simulator = pedestrian_simulator
        self.counter = Counter()
        self.current_time = 0
        self.jeep_spatial_speeds = []
        self.truck_spatial_speeds = []
        self.vehicle_spatial_speeds = []
        self.throughput = 0
        self.passenger_throughput = 0
        self.jeep_throughput = 0
        self.truck_throughput = 0
        self.actual_density = 0
        self.actual_truck_fraction = 0
        self.actual_truck_occupancy_fraction = 0


    def populate_the_road(self,  adjacent_sidewalk, timestep, transient_time, stop_to_stop_distance, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows):
        "This method makes sure all vehicles are spawned on the road"
        if (self.vehicle_simulator.spawned_vehicles < self.vehicle_simulator.total_vehicles) and (self.vehicle_simulator.unsuccessful_vehicle_placement_tries < (self.vehicle_simulator.total_vehicles*2)): #(self.vehicle_simulator.road.length/3)): #Feb 19 2025: The 2nd condition is too strict. #If not all vehicles have been spawned yet
            #Alternate between spawning trucks and jeeps
            truck_length, jeep_length = 7, 3
            truck_width, jeep_width = 2, 2            
            if np.random.rand() < 0.5: #Equal chances of both vehicle types to be placed
                if (self.vehicle_simulator.spawned_trucks < self.vehicle_simulator.total_trucks):
                    # for x_position in range(self.road.road_length):
                    self.vehicle_simulator.place_vehicles('truck', truck_length, truck_width, adjacent_sidewalk, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows)
                    
            else:
                if (self.vehicle_simulator.spawned_jeeps < self.vehicle_simulator.total_jeeps):
                    # for x_position in range(self.road.road_length):
                    self.vehicle_simulator.place_vehicles('jeep', jeep_length, jeep_width,  adjacent_sidewalk, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows)

            for vehicle in self.vehicle_simulator.vehicles:
                vehicle.speed = 0
        else: #self.vehicle_simulator.unsuccessful_vehicle_placement_tries > (self.vehicle_simulator.total_vehicles * 2): # After certain number of tries, the vehicle cannot be placed and we stopped populating the road
            self.integrated_simulation_step(timestep, transient_time)
        #else:
            #self.integrated_simulation_ste, #Commented out: February 19, 2025 (3:02 PM)

    def integrated_simulation_step(self, timestep, transient_time): #Integrated Simulation Step
        np.random.shuffle(self.vehicle_simulator.vehicles)
        np.random.shuffle(self.pedestrian_simulator.passengers)
        
        if len(self.vehicle_simulator.vehicles) > 0:
            for vehicle in self.vehicle_simulator.vehicles:
                if vehicle.current_row == 1: # We  dont have to check for speed because vehicles cannot straddle if their v = 0
                    vehicle.finish_lane_change()
                    self.inform_driver_of_destination(vehicle)

                elif np.random.rand() < vehicle.lane_changing_prob:
                    vehicle.accelerate()
                    vehicle.lane_changing()
                    vehicle.decelerate()
                    if vehicle.vehicle_type == "jeep":
                        vehicle.unloading(timestep)
                        vehicle.loading(timestep)
                    vehicle.random_slowdown()
                    vehicle.move() #Move the vehicle
                    self.inform_driver_of_destination(vehicle)
            
                else:
                    vehicle.accelerate() 
                    vehicle.decelerate() 
                    if vehicle.vehicle_type == "jeep":
                        vehicle.unloading(timestep)
                        vehicle.loading(timestep)
                    vehicle.random_slowdown()
                    vehicle.move()
                    self.inform_driver_of_destination(vehicle)
                for passenger in vehicle.passengers_within_vehicle:
                    passenger.determine_if_overshot_destination(vehicle)   
                if timestep >= transient_time:     
                    vehicle.temporal_speeds.append(vehicle.speed)
                self.pedestrian_simulator.update_occupancy(timestep)
                self.vehicle_simulator.update_occupancy(timestep)
                #print(f"Passenger destinations of {vehicle.vehicle_type} {vehicle.vehicle_id} are {vehicle.destination_stops}")
                # Count vehicles passing through the monitored position (e.g., position 99)

                #if timestep >= transient_time: #Collect data at transient to determine convergence
                self.counter.count_vehicle(vehicle)
                self.counter.count_passenger(vehicle)
                self.counter.count_jeeps(vehicle)
                self.counter.count_trucks(vehicle)

            self.vehicle_simulator.occupancy_history.append((timestep, self.vehicle_simulator.road.occupancy.copy()))
            self.pedestrian_simulator.sidewalk_occupancy_history.append((timestep, self.pedestrian_simulator.sidewalk.occupancy.copy()))
        #if timestep >= transient_time: #Collect data at transient to determine convergence
        if len(self.vehicle_simulator.vehicles) > 0:
            self.vehicle_spatial_speeds.append(vehicle.speed) #include the vehicle's speed on the list of all the vehicle's speed
            if vehicle.vehicle_type == "jeep":
                self.jeep_spatial_speeds.append(vehicle.speed)
            else:
                self.truck_spatial_speeds.append(vehicle.speed)

        for stop in self.pedestrian_simulator.sidewalk.stops:
            if stop:
                stop_interest = stop[0]
                #print(f"For Stop at {stop_interest.position}, the loading list is {stop_interest.loading_list} with {len(stop_interest.loading_list)} elements.")
                pass
    #Compute riding times once, not everytime step. Just compute it at the end.

    def inform_driver_of_destination(self, vehicle):
        for passenger in vehicle.passengers_within_vehicle:
            passenger.determine_crossing_edge_status(vehicle)
            if passenger.informed_the_driver:
                continue
            passenger.determine_if_just_boarded(vehicle)
            #print(f"Passenger {passenger.passenger_id} just boarded??? --- {passenger.just_boarded}")
            if passenger.just_boarded is False:
                vehicle.destination_stops.append(passenger.destination_stop)
                passenger.informed_the_driver = True
                #print(f"Passenger {passenger.passenger_id} informed the driver that his destination is at {passenger.destination_stop}.")
        return

    def calculate_riding_time(self, timestep):
        for passenger in self.pedestrian_simulator.in_transit_passengers:
            passenger.riding_time = timestep - passenger.jeep_boarding_time
        for passenger in self.pedestrian_simulator.alighted_passengers:
            passenger.riding_time  = passenger.arrived_at_destination_time - passenger.jeep_boarding_time
        return

    def calculate_waiting_time(self, timestep):
        for passenger in self.pedestrian_simulator.waiting_passengers:
            passenger.waiting_time = timestep - passenger.sidewalk_entry_time
        for passenger in self.pedestrian_simulator.in_transit_passengers:
            passenger.waiting_time = passenger.jeep_boarding_time - passenger.sidewalk_entry_time
        for passenger in self.pedestrian_simulator.alighted_passengers:
            passenger.waiting_time  = passenger.jeep_boarding_time - passenger.sidewalk_entry_time
        return


    def run_simulation(self, max_timesteps,  transient_time, density, truck_fraction, stop_to_stop_distance, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows, visualize=False):
        timestep = 0
        # Initialize or reset relevant data
        self.vehicle_simulator.initialize_vehicles(density, truck_fraction)
        
        data_vehicles = []
        data_timestep = []
        data_passengers = []
        data_jeep = []
        data_trucks = []
        data_spatio_temporal = None
        data_sidewalk_spatio_temporal = None
        #data_temporal_speeds = []

        self.pedestrian_simulator.generate_stops(stop_to_stop_distance)
        #print(f"The stops generated")
        while timestep < max_timesteps:
            # Update both simulators at each timestep
            if timestep < transient_time:
                #print(f"Implementing rules for timestep {timestep}")
                self.current_time = timestep
                self.pedestrian_simulator.current_time = timestep
                self.vehicle_simulator.current_time = timestep
                
                self.pedestrian_simulator.generate_passengers(self.vehicle_simulator, timestep)
                self.populate_the_road( self.pedestrian_simulator.sidewalk, timestep, transient_time, stop_to_stop_distance, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows)  # Update vehicles
                for passenger in self.pedestrian_simulator.passengers:
                    passenger.current_time = timestep

            # Collect data after transient period
            else: #timestep >= transient_time:
                #print(f"Implementing rules for timestep {timestep}")
                self.current_time = timestep
                self.pedestrian_simulator.current_time = timestep
                self.vehicle_simulator.current_time = timestep

                self.pedestrian_simulator.generate_passengers(self.vehicle_simulator, timestep)
                self.populate_the_road(  self.pedestrian_simulator.sidewalk,timestep, transient_time, stop_to_stop_distance, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows) # Update vehicles
                for passenger in self.pedestrian_simulator.passengers:
                    passenger.current_time = timestep
                
                #Collect data for Travel speed of each vehicle
                if timestep == transient_time:
                    for vehicle in self.vehicle_simulator.vehicles:
                        self.starting_rear_bumper_position = vehicle.rear_bumper_position
                elif timestep == max_timesteps - 1:
                    for vehicle in self.vehicle_simulator.vehicles:
                        self.end_rear_bumper_position = vehicle.rear_bumper_position

            #Collect data for each timestep (even at transient, just discard at data processing)
            self.throughput = self.counter.calculate_vehicle_throughput()
            self.passenger_throughput = self.counter.calculate_passenger_throughput()
            self.jeep_throughput = self.counter.calculate_jeep_throughput()
            self.truck_throughput = self.counter.calculate_truck_throughput()
            self.actual_density = (self.vehicle_simulator.spawned_vehicles_occupancy) / (self.vehicle_simulator.road.length * self.vehicle_simulator.road.width)
            self.actual_truck_fraction = (self.vehicle_simulator.spawned_trucks / self.vehicle_simulator.spawned_vehicles) if (self.vehicle_simulator.spawned_vehicles > 0) else 0
            self.actual_truck_occupancy_fraction = (self.vehicle_simulator.spawned_trucks*14)/ ((self.vehicle_simulator.spawned_trucks*14)+(self.vehicle_simulator.spawned_jeeps*6)) if (self.vehicle_simulator.spawned_vehicles > 0) else 0
            vehicle_spatial_mean_speed = np.mean(self.vehicle_spatial_speeds) if (self.vehicle_simulator.spawned_vehicles > 0) else 0
            jeep_spatial_mean_speed = np.mean(self.jeep_spatial_speeds) if (self.vehicle_simulator.spawned_vehicles > 0) else 0
            truck_spatial_mean_speed = np.mean(self.truck_spatial_speeds) if (self.vehicle_simulator.spawned_vehicles > 0) else 0
                
            data_timestep.append({
                "Timestep": timestep,
                "Actual Density": self.actual_density,
                "Actual Truck Fraction": self.actual_truck_fraction,
                "Throughput": self.throughput,
                "Passenger Throughput":self.passenger_throughput,
                "Jeep Throughput":self.jeep_throughput,
                "Truck Throughput":self.truck_throughput,
                "Jeep Spatial Mean Speed":jeep_spatial_mean_speed,
                "Truck Spatial Mean Speed":truck_spatial_mean_speed,
                "Vehicle Spatial Mean Speed":vehicle_spatial_mean_speed,
                "Truck Occupancy Fraction":self.actual_truck_occupancy_fraction})
            if visualize:
                #self.visualize(timestep)
                self.visualize_combined(timestep)
            
            timestep += 1
        
        self.calculate_riding_time(timestep)
        self.calculate_waiting_time(timestep)

        #Collect spatio-temporal data of the road
        occupancy_data = []
        for timestep, occupancy_grid in self.vehicle_simulator.occupancy_history:
            # print(f"The number of rows on the road based on occupancy grid is {occupancy_grid.shape[1]}")
            for y in range(occupancy_grid.shape[1]):  # Loop over each row (y-axis)
                occupancy_data.append([timestep, y] + occupancy_grid[:, y].tolist())  # Store row-wise data
        road_length = self.vehicle_simulator.road.length
        columns = ["Timestep", "Road Row"] + [f"Pos {x}" for x in range(road_length)]
        data_spatio_temporal = pd.DataFrame(occupancy_data, columns=columns) #Create DataFrame


        #Collect spatio-temporal data of the sidewalk
        sidewalk_occupancy_data = []
        for timestep, occupancy_row in self.pedestrian_simulator.sidewalk_occupancy_history:
            sidewalk_occupancy_data.append([timestep] + occupancy_row.tolist())  # Directly store row data

        sidewalk_length = self.pedestrian_simulator.sidewalk.length
        sidewalk_columns = ["Timestep"]+[f"Pos {x}" for x in range(sidewalk_length)]  #Create DataFrame
        data_sidewalk_spatio_temporal = pd.DataFrame(sidewalk_occupancy_data, columns=sidewalk_columns)


        # Collect passenger data(after running the whole simulation)
        for passenger in self.pedestrian_simulator.passengers:
            # if (passenger.jeep_boarding_time > transient_time and passenger.arrived_at_destination_time > transient_time):
            riding_time = passenger.riding_time
            waiting_time = passenger.waiting_time
            spawning_time = passenger.sidewalk_entry_time
            boarding_time = passenger.jeep_boarding_time
            alighting_time = passenger.arrived_at_destination_time
            if passenger in self.pedestrian_simulator.waiting_passengers:
                status = "Waiting"
            elif passenger in self.pedestrian_simulator.in_transit_passengers:
                status = "In-Transit"
            elif passenger in self.pedestrian_simulator.alighted_passengers:
                status = "Alighted"
            else:
                status = "Unknown"  # Fallback case, should not normally happen

            data_passengers.append({
                "Passenger ID": passenger.passenger_id,
                "Riding Time": riding_time,
                "Waiting Time": waiting_time,
                "Riding Status":status,
                "Spawning Time": spawning_time,
                "Boarding Time": boarding_time,
                "Alighting Time": alighting_time})
                #"Passenger Travel Speed":passenger_travel_speed})
        #max_speed_timesteps = max([len(vehicle.temporal_speeds) for vehicle in self.vehicle_simulator.vehicles])
        #Collect vehicle data
        for vehicle in self.vehicle_simulator.vehicles:
            vehicle.mean_temporal_speed = np.mean(vehicle.temporal_speeds)

            data_vehicles.append({"Vehicle ID":vehicle.vehicle_id, "Vehicle Type":vehicle.vehicle_type,
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

            #For temporal speeds csv file
            # row = {"Vehicle ID": vehicle.vehicle_id,"Vehicle Type": vehicle.vehicle_type}
            # for t in range(max_speed_timesteps):
            #     row[f"Timestep {t}"] = vehicle.temporal_speeds[t] if t < len(vehicle.temporal_speeds) else None
            # data_temporal_speeds.append(row)

        # Return the results in a dataframe
        results_timestep = pd.DataFrame(data_timestep)
        results_vehicles = pd.DataFrame(data_vehicles)
        results_passengers = pd.DataFrame(data_passengers)
        results_spatio_temporal = pd.DataFrame(data_spatio_temporal)
        results_sidewalk_spatio_temporal = pd.DataFrame(data_sidewalk_spatio_temporal)
        return results_timestep, results_passengers, results_vehicles, results_spatio_temporal, results_sidewalk_spatio_temporal#, results_temporal_speeds

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