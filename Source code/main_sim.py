import pandas as pd
import numpy as np
from counter import Counter

class IntegratedSimulator:
    def __init__(self, vehicle_simulator, pedestrian_simulator):
        self.vehicle_simulator = vehicle_simulator
        self.pedestrian_simulator = pedestrian_simulator
        self.counter = Counter()
        self.current_time = 0
        self.unloaded_passengers = []

    def populate_the_road(self, jeep_lane_change_prob, truck_lane_change_prob, adjacent_sidewalk, boarding_time, stop_to_stop_distance, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows):
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
            self.integrated_simulation_step(boarding_time)
        #else:
            #self.integrated_simulation_step(boarding_time) #Commented out: February 19, 2025 (3:02 PM)

    def integrated_simulation_step(self, boarding_time): #Integrated Simulation Step
        np.random.shuffle(self.vehicle_simulator.vehicles)
        np.random.shuffle(self.pedestrian_simulator.passengers)
        
        for vehicle in self.vehicle_simulator.vehicles:
            if vehicle.current_row == 1: # We  dont have to check for speed because vehicles cannot straddle if their v = 0
                vehicle.finish_lane_change() 
                self.vehicle_simulator.update_occupancy()

            elif np.random.rand() < vehicle.lane_changing_prob:
                vehicle.accelerate()
                vehicle.lane_changing()
                vehicle.decelerate()
                vehicle.unloading(self.unloaded_passengers)
                for passenger in self.unloaded_passengers:
                    passenger.calculate_riding_time()
                    print(f"Passenger {passenger.passenger_id}'s riding status is {passenger.riding_status} and the riding time is {passenger.riding_time}.")
                    #self.pedestrian_simulator.update_sidewalk_occupancy()
                vehicle.loading()
                for passenger in vehicle.passengers_within_vehicle:
                    passenger.update_riding_status(vehicle)
                    passenger.calculate_waiting_time()
                    print(f"Passenger {passenger.passenger_id}'s riding status is {passenger.riding_status} and the waiting time is {passenger.waiting_time}.")
                
                vehicle.random_slowdown()
                vehicle.move() #Move the vehicle
            else:
                vehicle.accelerate()
                vehicle.decelerate() 
                vehicle.unloading(self.unloaded_passengers)
                for passenger in self.unloaded_passengers:
                    passenger.calculate_riding_time()
                    print(f"Passenger {passenger.passenger_id}'s riding status is {passenger.riding_status} and the riding time is {passenger.riding_time}.")
                    self.pedestrian_simulator.update_sidewalk_occupancy()
                vehicle.loading()
                for passenger in vehicle.passengers_within_vehicle:
                    passenger.update_riding_status(vehicle)
                    passenger.calculate_waiting_time()
                    print(f"Passenger {passenger.passenger_id}'s riding status is {passenger.riding_status} and the waiting time is {passenger.waiting_time}.")            
                vehicle.random_slowdown()
                vehicle.move()


            self.vehicle_simulator.update_occupancy()
            # Count vehicles passing through the monitored position (e.g., position 99)
            self.counter.count_vehicle(vehicle)
            self.counter.count_passenger(vehicle)
        
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
        data_passengers = []
        #data_measurements = []

        self.pedestrian_simulator.generate_stops(stop_to_stop_distance)
        #print(f"The stops generated")
        while timestep < max_timesteps:
            # Update both simulators at each timestep
            if timestep < transient_time:
                self.current_time = timestep
                self.pedestrian_simulator.current_time = timestep
                self.vehicle_simulator.current_time = timestep
                print(f"Implementing rules for timestep {timestep}")
                
                self.pedestrian_simulator.generate_passengers(self.vehicle_simulator, timestep)
                self.populate_the_road(jeep_lane_change_prob, truck_lane_change_prob, self.pedestrian_simulator.sidewalk, timestep, stop_to_stop_distance, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows)  # Update vehicles
                for passenger in self.pedestrian_simulator.passengers:
                    passenger.current_time = timestep

            # Collect data after transient period
            elif timestep >= transient_time:
                self.current_time = timestep
                self.pedestrian_simulator.current_time = timestep
                self.vehicle_simulator.current_time = timestep

                self.pedestrian_simulator.generate_passengers(self.vehicle_simulator, timestep)
                self.populate_the_road(jeep_lane_change_prob, truck_lane_change_prob,  self.pedestrian_simulator.sidewalk,timestep, stop_to_stop_distance, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows) # Update vehicles
                for passenger in self.pedestrian_simulator.passengers:
                    passenger.current_time = timestep
                    
                throughput = self.counter.calculate_vehicle_throughput()
                passenger_throughput = self.counter.calculate_passenger_throughput()
                actual_density = (self.vehicle_simulator.spawned_vehicles_occupancy) / (self.vehicle_simulator.road.length * self.vehicle_simulator.road.width)
                actual_truck_fraction = self.vehicle_simulator.spawned_trucks / self.vehicle_simulator.spawned_vehicles
                actual_truck_occupancy_fraction = (self.vehicle_simulator.spawned_trucks*14)/ (self.vehicle_simulator.road.length * self.vehicle_simulator.road.width)
                
                data_vehicles.append({
                    "Timestep": timestep,
                    "Actual Density": actual_density,
                    "Actual Truck Fraction": actual_truck_fraction,
                    "Throughput": throughput,
                    "Passenger Throughput":passenger_throughput,
                    "Truck Occupancy Fraction":actual_truck_occupancy_fraction
                })

                # Collect passenger data
                for passenger in self.pedestrian_simulator.passengers:
                    riding_time = passenger.riding_time
                    waiting_time = passenger.waiting_time
                    data_passengers.append({
                        "Passenger ID": passenger.passenger_id,
                        "Riding Time": riding_time,
                        "Waiting Time": waiting_time
                    })

            if visualize:
                self.visualize(timestep)

            timestep += 1

        # Return the results in a dataframe
        results_vehicles = pd.DataFrame(data_vehicles)
        results_passengers = pd.DataFrame(data_passengers)

        return results_vehicles, results_passengers

    def visualize(self, timestep):
        """Visualize both the vehicle and pedestrian data at a specific timestep."""
        # Vehicle simulation visualization
        self.vehicle_simulator.visualize(timestep)

        # Pedestrian simulation visualization
        self.pedestrian_simulator.visualize(timestep)
        