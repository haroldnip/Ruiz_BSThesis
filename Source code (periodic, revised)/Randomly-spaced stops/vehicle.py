import numpy as np
from math import inf

class Vehicle:
    _id_counter = 0
    """Define vehicle attributes and rules of movement"""
    def __init__(self, rear_bumper_position, speed, max_speed, length, width, road_designation, vehicle_type, current_row, lane_change_prob, sidewalk, safe_stopping_speed, safe_deceleration):
        self.vehicle_id = Vehicle._id_counter
        Vehicle._id_counter += 1 #increment vehicle ID based on order of initialization
        self.rear_bumper_position = rear_bumper_position #rear_bumper_position along the length of the road (x rear_bumper_position)
        self.speed = speed #number of cells the vehicle will move per timestep
        self.max_speed = max_speed #maximum speed
        self.braking_prob = 0.01 #probability of random slowdown
        self.length = length #length of the vehicle is the number of cells the vehicle occupies along the length of the road
        self.width = width #width of the vehicle is the number of cells the vehicle occupies along the width of the road
        self.road_designation = road_designation 
        self.front_bumper_position = (self.rear_bumper_position + self.length - 1) % self.road_designation.length
        self.vehicle_type = vehicle_type #Truck or jeepney
        self.lane_changing_prob = lane_change_prob
        self.current_row = current_row #Position of the right side of the vehicle
        self.passengers_within_vehicle = [] #List of passengers in the vehicle
        self.lane_change_direction = None #Direction of lane changing
        self.previous_rear_bumper_position = 0 #To give memory of the previous position
        self.next_rear_bumper_position = 0 #Anticipate next position based on speed
        self.occupied_seats = len(self.passengers_within_vehicle) #Number of passengers on board
        self.capacity = 20 if self.vehicle_type == "jeep" else 0 
        self.unoccupied_seats = self.capacity - self.occupied_seats 
        self.sidewalk = sidewalk
        self.pool_of_occupied_positions = np.arange(self.rear_bumper_position, (self.rear_bumper_position + length) % self.road_designation.length, 1)
        self.total_passengers_unloaded = 0 #Number of passengers unloaded
        self.safe_stopping_speed = safe_stopping_speed #Maximum speed to be able to make a sudden stop
        self.safe_deceleration = safe_deceleration #Maximum deceleration for safety
        self.lane_change_trials_for_passengers = 0
        self.did_cross_edge = None
        self.about_to_cross_edge = None
        self.at_the_edge = False
        self.matching_stop_found = False 
        self.overshot_destination = False
        self.temporal_speeds = []
        self.mean_temporal_speed = None
        self.allow_loading = None
        self.starting_rear_bumper_position = None #To keep track on the position where the vehicle is when we started collecting data
        self.end_rear_bumper_position = None #To keep track on the position where the vehicle is when we stopped collecting data
        self.passengers_served = 0 
        self.passenger_is_coming_out = False
        self.last_loading_position = []
        self.far_lane_loadings = 0
        self.far_lane_unloadings = 0
        self.destination_stops = [] #Destinations of passengers on board
        self.previous_stop_list_ahead = []
        self.previous_stop_list_adjacent = []
        self.stop_list_adjacent_and_ahead = []
        self.stop_list_adjacent = []
        self.stop_list_ahead = []
        self.look_ahead_distance = self.speed
        self.previous_speed = None
        self.previous_front_bumper_position = None
        self.passengers_on_board = {} #Dictionary for unloading purposes
        # self.active_loading_list = []
        # self.queue_loading_list = []

    def accelerate(self):
        """Increases vehicle's speed by 1 cell, up to the maximum speed"""
        self.previous_speed = self.speed
        if self.speed < self.max_speed:
            self.speed += 1
            # print(f"{self.vehicle_type} {self.vehicle_id} accelerated to a speed of {self.speed}")

    def gap_distance(self, vehicle_row_to_be_checked):  #This is responsible for VEHICLE gap distance
        """Debugging this - make gap distance consider toroidal boundary cond. recently introduced"""
        """vehicle row to be checked: Input is row 0, you check for lane 1(row 0 and 1). Input is row 1, you check for lane at the middle (row 1 and 2). Input is row 2, you check for lane 2(rows 2 and 3)."""
        look_ahead_distance = self.speed #With t=1
        #print(f"{self.vehicle_type} {self.vehicle_id}'s maximum distance is  {look_ahead_distance}")
        gap_distance = look_ahead_distance
        
        for distance in range(1, look_ahead_distance + 1):
            start_of_space_to_be_checked = (self.rear_bumper_position + self.length + distance - 1)  % self.road_designation.length #putting the modulo operator here removes the need for separate considerations under periodic boundary conditions
            #print(f"{self.vehicle_type} {self.vehicle_id}: next rear bumper rear_bumper_position is {start_of_space_to_be_checked}")
            if np.sum(self.road_designation.occupancy[start_of_space_to_be_checked, vehicle_row_to_be_checked:vehicle_row_to_be_checked + self.width]) != 0:
                gap_distance = distance - 1 #When the vehicle is detected, that distance is already occupied, so we subtract 1 to be accurate
                #print(np.sum(self.road_designation.road_occupancy[start_of_space_to_be_checked, vehicle_row_to_be_checked:vehicle_row_to_be_checked + self.width]))
                break
        if gap_distance < 0: #For debugging
            pass
            print(f"Error, {self.vehicle_type} {self.vehicle_id} negative gap distance of {gap_distance}, at rear bumper rear_bumper_position {self.rear_bumper_position}") 
        else:
            pass
            #print(f"Vehicle {self.vehicle_id}'s gap distance from the leading vehicle is {gap_distance}")
        return gap_distance # Return the  gap distance


    def check_lane_availability(self, target_row):
        """This method checks for the adjacent lane: if determines if the cells adjacent to the vehicle are empty and the cells within its look ahead distance"""
        #print(f"{self.vehicle_type} {self.vehicle_id} checks the availability of lane {target_row/2}")
        look_ahead_distance = self.speed #Assuming t = 1
        rolled_occupancy = np.roll(self.road_designation.occupancy, -self.rear_bumper_position, axis = 0)
        #print(f"{self.vehicle_type} {self.vehicle_id} checks the availability of lane {target_row/2}: {np.sum(rolled_occupancy[0:self.length + look_ahead_distance + 1, target_row])}")
        #print(f"{self.vehicle_type} {self.vehicle_id} checks {rolled_occupancy[0: look_ahead_distance + 1, target_row].T}")
        return np.sum(rolled_occupancy[0: self.length + look_ahead_distance + 1, target_row]) #Feb 23 - included length

    def begin_straddling(self, direction):
        """This method executes the actual action of changing lanes (in particular, this methods let the vehicle begin straddling)
            This method assumes that the occupancy on the lane of interest was already checked."""
        self.speed = max(0, self.gap_distance(self.current_row)-1)
        
        if self.speed == 0:
            self.accelerate()
            #print(f"{self.vehicle_type} {self.vehicle_id} accelerates to possibly lane change. ")

        rolled_occupancy = np.roll(self.road_designation.occupancy, -self.front_bumper_position, axis = 0)

        if self.speed > 0 and np.all(rolled_occupancy[1:self.speed + 1, self.current_row])== 0: #Check on the current lane
            self.current_row += direction
            self.move()
            if self.current_row == 1:
                self.lane_change_trials_for_passengers = 0
                self.update_pool_of_occupied_positions()
                #print(f"{self.vehicle_type} {self.vehicle_id} begins straddling, it is on row {self.current_row}, positions {self.rear_bumper_position}-{self.front_bumper_position}")
        else:
            # print(f"{self.vehicle_type} {self.vehicle_id} cannot straddle. ")
            pass

        return

    def is_lane_change_allowed(self, target_row):
        "Check if the target row is restricted for the vehicle"
        for row, allowed_type in self.road_designation.allowed_rows:
            if target_row == row and self.vehicle_type not in allowed_type:
                return False
        return True

    def detect_stops_adjacent_and_ahead(self):
        if self.vehicle_type == "jeep":
            self.stop_list_adjacent = []
            self.stop_list_ahead = []
            self.stop_list_adjacent_and_ahead = []
            current_positions = self.pool_of_occupied_positions
            future_positions = [(self.rear_bumper_position + i) % self.road_designation.length for i in range(self.length, self.length + self.look_ahead_distance)]
            for position in current_positions:
                if self.sidewalk.stops[position]:  # Ensure it's not empty
                    stop_checked = self.sidewalk.stops[position][0]  # Peek instead of pop
                    self.stop_list_adjacent.append(stop_checked)
                else:
                    self.stop_list_adjacent.append(False)  # Indicate no stop found
            for position in future_positions:
                if self.sidewalk.stops[position]:  # Ensure it's not empty
                    stop_checked = self.sidewalk.stops[position][0]  # Peek instead of pop
                    self.stop_list_ahead.append(stop_checked)
                else:
                    self.stop_list_ahead.append(False)  # Indicate no stop found
        #print(f"The stop positions are {[stop.position for stop in (self.stop_list_adjacent + self.stop_list_ahead) if stop]}")


    def detect_passengers_adjacent_and_ahead(self):
        """Detects if there are passengers on stops ahead on the sidewalk."""
        if self.vehicle_type == "jeep":
            rolled_sidewalk = np.roll(self.sidewalk.occupancy, -self.rear_bumper_position)
            return np.any(rolled_sidewalk[:self.length + self.look_ahead_distance])
        return False  # Default return for non-jeep vehicles

    def will_unload_passengers(self):
        """Determines if any passenger within the vehicle wants to get off."""
        self.detect_stops_adjacent_and_ahead()
        
        self.stop_list_adjacent_and_ahead = self.stop_list_adjacent+self.stop_list_ahead
        for passenger in self.passengers_within_vehicle:
            passenger.determine_if_let_me_out(self)
            passenger.determine_if_overshot_destination(self)
        self.determine_if_overshot_destination()
        return any(
            destination in self.stop_list_adjacent_and_ahead
            for destination in self.destination_stops
        ) or any(passenger.overshot_destination for passenger in self.passengers_within_vehicle)


    def attempt_lane_change_for_passengers(self):
        """This method attempts to lane change for passengers. This assumed that passengers are to be unloaded or loaded, and capacity has not yet reached"""
        # print(f"{self.vehicle_type} {self.vehicle_id} calling attempt method.")
        if self.vehicle_type != "jeep":
            # print(f"{self.vehicle_type} {self.vehicle_id} not a jeep.")
            return

        if self.current_row == 0:
            # print(f"{self.vehicle_type} {self.vehicle_id} already on Lane 1.")
            return
        
        if self.current_row == 2:
            target_row = 0
            # print(f"{self.vehicle_type} {self.vehicle_id} will try lane changing to the right lane")
            if self.lane_change_trials_for_passengers >= 4:
                #print(f"{self.vehicle_type} {self.vehicle_id} has attempted lane changing 4 times.")
                return
            else:
                #print(f"{self.vehicle_type} {self.vehicle_id} has tried lane changing {self.lane_change_trials_for_passengers} times.")
                if self.is_lane_change_allowed(target_row):
                    # print(f"Lane change on row {target_row} is allowed. Will try doing so.")
                    self.lane_change_direction = "right"
                    road_portion_checked = self.check_lane_availability(1) #We check the middle lane
                    # print(f"{self.vehicle_type} {self.vehicle_id} checked a road portion with summed occupancy of {road_portion_checked} ")
                    if road_portion_checked == 0:
                        #print(f"{self.vehicle_type} {self.vehicle_id} can change lanes. It will now begin straddling.")
                        self.begin_straddling(-1)  # Initiates lane change
                    if self.current_row == 2:
                        self.lane_change_trials_for_passengers += 1
                        #print(f"{self.vehicle_type} {self.vehicle_id} has tried lane changing {self.lane_change_trials_for_passengers} times (incremented).")
                        return
    

    def lane_changing(self):
        """This method handles the lane changing if there are passengers to be loaded or unloaded, or just based on driver's behavior"""
        gap_distance_of_own_lane = self.gap_distance(self.current_row)
        #print(f"{self.vehicle_type} {self.vehicle_id}'s gap distance from a leading vehicle on its lane is {gap_distance_of_own_lane}")
        gap_distance_of_right_lane = self.gap_distance(self.current_row - 2) if self.current_row == 2 else gap_distance_of_own_lane
        #print(f"{self.vehicle_type} {self.vehicle_id}'s gap distance from a leading vehicle on the right lane is {gap_distance_of_right_lane}")
        gap_distance_of_left_lane = self.gap_distance(self.current_row + 2) if self.current_row == 0 else gap_distance_of_own_lane
        #print(f"{self.vehicle_type} {self.vehicle_id}'s gap distance from a leading vehicle on the left lane is {gap_distance_of_left_lane}")
        #Put a portion that handles lane changing for passengers
        # print(f"{self.vehicle_type} {self.vehicle_id} is calling lane changing method. The numbers of passengers within vehicle is {len(self.passengers_within_vehicle)}. The passengers ARE {self.passengers_within_vehicle} ")
        if (self.will_unload_passengers()) and self.vehicle_type!= "truck":
            self.attempt_lane_change_for_passengers()
            # print(f"{self.vehicle_type} {self.vehicle_id} attempted to unload passengers. It attempted {self.lane_change_trials_for_passengers} times.")  
            return
        elif self.detect_passengers_adjacent_and_ahead() and (len(self.passengers_within_vehicle) < self.capacity) and self.vehicle_type!= "truck":
            self.attempt_lane_change_for_passengers()
            # print(f"{self.vehicle_type} {self.vehicle_id} attempted to load passengers. It attempted {self.lane_change_trials_for_passengers} times.")  #if detected passengers, skip the remaining
            return
        else:
            #This portion handles vehicle lane changing based on which has more available space
            if self.speed > gap_distance_of_own_lane:
                # print(f"{self.vehicle_type} {self.vehicle_id} will try to lane change for more space")
                if self.current_row == 0 and gap_distance_of_left_lane > gap_distance_of_own_lane:
                    target_row = self.current_row + 2
                    if self.is_lane_change_allowed(target_row):
                        self.lane_change_direction = 'left'
                        self.speed = gap_distance_of_own_lane
                        road_portion_checked = self.check_lane_availability(target_row)
                        #print(f"{self.vehicle_type} {self.vehicle_id} checked a road portion with summed occupancy of {road_portion_checked} ")
                        if road_portion_checked == 0:
                            self.begin_straddling(1)
                            #print(f"{self.vehicle_type} {self.vehicle_id} is now straddling from from lane 0.")
                elif self.current_row == 2 and gap_distance_of_right_lane > gap_distance_of_own_lane:
                    target_row = self.current_row - 2
                    if self.is_lane_change_allowed(target_row):
                        self.lane_change_direction = "right"
                        self.speed = gap_distance_of_own_lane
                        road_portion_checked = self.check_lane_availability(target_row+1)
                        if road_portion_checked == 0:
                            self.begin_straddling(-1)
                            #print(f"{self.vehicle_type} {self.vehicle_id} is now straddling from from lane 1.")
                else:
                    pass
            else:
                pass
        return

    def finish_lane_change(self):
        """This method handles straddling cases, completes the straddling case"""
        if self.current_row == 1:
            #print(f"The lane change direction of {self.vehicle_type} {self.vehicle_id} is {self.lane_change_direction}")
            target_row = None
            look_ahead_distance = self.speed #With t=1
            if self.lane_change_direction == 'right':
                target_row = 0
            elif self.lane_change_direction == 'left':
                target_row = 2
            else:
                target_row = None

            if target_row is not None:
                self.front_bumper_position = self.rear_bumper_position + self.length - 1
                shifted_occupancy = np.roll(self.road_designation.occupancy, -(self.front_bumper_position + 1), axis = 0)
                # print(f"{self.vehicle_type} {self.vehicle_id}'s space ahead is {shifted_occupancy}, the front bumper is at {self.front_bumper_position}'")
                
                if self.speed > 0:
                    space_available = np.sum(shifted_occupancy[0:look_ahead_distance+1, self.current_row:self.current_row + self.width]) == 0
                    # print(f"{self.vehicle_type} {self.vehicle_id}'s space checked is {shifted_occupancy[0:look_ahead_distance+1, self.current_row:self.current_row + self.width].T}'")
                elif self.speed == 0:
                    space_available = np.sum(shifted_occupancy[0:2, self.current_row:self.current_row + self.width])== 0 #Check at least 2 cells in front
                    # print(f"{self.vehicle_type} {self.vehicle_id}'s space checked is {shifted_occupancy[0:2, self.current_row:self.current_row + self.width].T}'")
                
                if space_available:
                    # print(f"{self.vehicle_type} {self.vehicle_id}'s empty space ahead is {shifted_occupancy}'")
                    if self.speed == 0:
                        self.accelerate()
                        # print(f"{self.vehicle_type} {self.vehicle_id}'s speed is 0 so we accelerate to be able to lane change.'")
                    self.current_row = target_row
                    self.move()
                    self.lane_change_direction = None
                    # print(f"{self.vehicle_type} {self.vehicle_id}'s lane change direction is {self.lane_change_direction}.")
                else:
                    self.decelerate()
                    # print(f"{self.vehicle_type} {self.vehicle_id}'s space in front is not available'")
            else:
                # print(f"{self.vehicle_type} {self.vehicle} has no target row.")
                pass
        return


    def pedestrian_headway(self): #Remove searching algorithm (March 12, 2025)
        """Determines the distance to the nearest pedestrian ahead of the jeepney."""
        look_ahead_distance = self.speed  # Assuming t = 1
        rear_bumper = self.rear_bumper_position
        # Shift the sidewalk occupancy array so the rear bumper is at index 0
        rolled_sidewalk = np.roll(self.sidewalk.occupancy[:, 0], -rear_bumper)
        # print(f"{self.vehicle_type} {self.vehicle_id}'s rolled sidewalk is {rolled_sidewalk}.")
        # Check if any pedestrian is directly adjacent to the jeepney
        if np.any(rolled_sidewalk[:self.length] > 0):
            # print(f"A passenger is directly adjacent to {self.vehicle_type} {self.vehicle_id}.")
            # print(f"{self.vehicle_type} {self.vehicle_id}'s adjacent sidewalk is {rolled_sidewalk[:self.length]}.")
            return 0  # Passenger is directly adjacent
        # Look for the first pedestrian within the look-ahead distance **starting from the front bumper**
        pedestrian_headway_list = np.where(rolled_sidewalk[self.length : self.length + look_ahead_distance] > 0)[0]
        # The first index represents the correct distance from the **front bumper**.
        pedestrian_headway = pedestrian_headway_list[0] + 1 if pedestrian_headway_list.size > 0 else look_ahead_distance
        # print(f"{self.vehicle_type} {self.vehicle_id} has pedestrian headway: {pedestrian_headway}")
        return pedestrian_headway

    def determine_if_overshot_destination(self):
        """Determines whether at least one passenger in the vehicle has overshot their destination."""
        self.overshot_destination = any(passenger.overshot_destination for passenger in self.passengers_within_vehicle)
        if self.overshot_destination:
            print(f"A passenger of jeep {self.vehicle_id} overshot his destination.")


    def calculate_nearest_destination_distance(self): #This is not final, I stopped right here (Feb. 13, 2025, 9:26 PM)
        """This method is triggered only if the destination of the passenger is within sight.
        To be used for deceleration purposes"""
        #if the vehicle overshoot a passenger's destination, the output here is automatically zero
        #self.update_pool_of_occupied_positions()
        self.determine_if_overshot_destination()
        if self.overshot_destination:
            #print(f"{self.vehicle_type} {self.vehicle_id} has overshot a passenger destination")
            return 0

        road_length = self.road_designation.length
        vehicle_rear = self.rear_bumper_position
        look_ahead_distance = self.speed + self.length - 1 #With t = 1

        #Create a binary array for destination stop positions
        destination_occupancy = np.zeros(road_length)
        
        # for destination in passenger_destinations:
        #     pass
            # print(f"A passenger destination is {destination.position}")
        for destination_stop in self.destination_stops:
            destination_occupancy[destination_stop.position] = 1 # Mark stops
            # print(f"{self.vehicle_type} {self.vehicle_id}: {destination_stop}'s position is {destination_stop.position}.")
        
        #Roll the array so the rear bumper is at index 0
        rolled_destinations = np.roll(destination_occupancy, -(vehicle_rear))
        # print(f"{self.vehicle_type} {self.vehicle_id} sees the destination occupancy {rolled_destinations}")
        # print(f"{self.vehicle_type} {self.vehicle_id} sees rolled destination: {rolled_destinations}")
        #Find the first nonzero index (or the nearest stop)
        search_range = rolled_destinations[1:look_ahead_distance+1]
        if np.any(search_range > 0):  # If there's at least one nonzero value
            # print("there's at least one nonzero value")
            nearest_index = np.argmax(search_range > 0)  # First nonzero index
        else:
            # print("No valid destination found")
            nearest_index = np.inf  # No valid destination found

        return max(0, nearest_index-1) if nearest_index != np.inf else np.inf


    def decelerate(self):
        """Decelerate to prevent collisions, load passengers, or unload passengers"""
        nearest_destination_distance = self.calculate_nearest_destination_distance() #if overshot, automatically 0. If not, calculate based on distance from front bumper
        # print(f" {self.vehicle_type} {self.vehicle_id} is {nearest_destination_distance} cells away from the nearest destination.")
        nearest_pedestrian_distance = self.pedestrian_headway() #if adjacent to vehicle 0, if not, calculate based on distance from front bumper
        # print(f" {self.vehicle_type} {self.vehicle_id} is {nearest_pedestrian_distance} cells away from the nearest pedestrian.")
        nearest_vehicle_distance = self.gap_distance(self.current_row) #gap distance in own lane
        # print(f" {self.vehicle_type} {self.vehicle_id} is {nearest_vehicle_distance} cells away from the nearest vehicle.")
        
        if self.vehicle_type == "jeep":
        #determine minimum distance to decelerate
            if self.capacity > len(self.passengers_within_vehicle):
                least_distance_to_decelerate = min(nearest_destination_distance, nearest_pedestrian_distance, nearest_vehicle_distance) 
            else: #if jeep is full, it won't stop for passengers
                least_distance_to_decelerate = min(nearest_destination_distance, nearest_vehicle_distance)

            target_speed = least_distance_to_decelerate

            deceleration = self.speed - target_speed
            # print(f" {self.vehicle_type} {self.vehicle_id} needs to decelerate by {deceleration} to {reason}. Its current speed is {self.speed} and target speed is {target_speed}")
            #Put an algorithm here that details the reason for stopping and the 
            if deceleration > 0: #skip deceleration if not needed
                # print(f"{self.vehicle_type} {self.vehicle_id} needs to decelerate by {deceleration}")
                #Decelerate safely (if decelerating for passengers, later, we will still check for collisions)
                if deceleration > self.safe_deceleration:
                    new_speed = max(0, self.speed - self.safe_deceleration)
                else:
                    new_speed = max(0, target_speed) #actually, the max() function is not necessary, I just have trust issues
                    # print(f" {self.vehicle_type} {self.vehicle_id} needs to decelerate to {new_speed}.")
                
                self.speed = max(0, min(new_speed, nearest_vehicle_distance)) # Ensure new_speed does not exceed nearest vehicle gap
                # print(f" {self.vehicle_type} {self.vehicle_id} decelerated to {self.speed}.")
        else:
            if self.speed > nearest_vehicle_distance:
                self.speed = nearest_vehicle_distance
                # print(f" {self.vehicle_type} {self.vehicle_id} decelerated to {self.speed}.")
        return

    def release_passenger(self, passenger, current_time):
        """
        Releases the passenger from the vehicle at their destination.
        Removes the passenger from the vehicle's list, updates the passenger's state, 
        and records metrics if needed.
        """
        self.passengers_within_vehicle.remove(passenger)
        self.occupied_seats = len(self.passengers_within_vehicle)
        passenger.alight_vehicle(self, current_time)
        # print(f"Passenger {passenger.passenger_id} alighted the vehicle.")
        return


    def matching_stops_on_sidewalk(self):
        """Check if any occupied position has a matching alighting stop in passenger destinations."""        
        
        self.matching_stop_found = False  
        # print(f"Matching_stops_on_sidewalk: {self.vehicle_type} {self.vehicle_id}'s adjacent stops are {self.stop_list_adjacent}")
        
        for stop in self.stop_list_adjacent:  # Iterate over adjacent stops\
            if stop:
                stop_list = self.sidewalk.stops[stop.position]  # This is a list of Stop objects
                stop_concerned = stop_list[0] if stop_list else None  # Get the first Stop if available

                if stop_concerned and stop.unloading_dictionary:  # Check if stop exists and has passengers
                    for passenger_id in stop.unloading_dictionary.keys():
                        if passenger_id in self.passengers_on_board:  # Match with passengers inside vehicle
                            self.matching_stop_found = True
                            # print(f"{self.vehicle_type} {self.vehicle_id} found a matching stop at {stop.position} for passenger {passenger_id}")
                            return  # Exit early if match found

        return  # No match found


    # def matching_stops_on_sidewalk(self): #Commented out: March 14, 2025
    #     """Check if any occupied position has a matching alighting stop in passenger destinations."""        
    #     # Start with False, then update to True if any match is found
    #     self.matching_stop_found = False  
    #     print(f"Matching_stops_on_sidewalk_method: {self.vehicle_type} {self.vehicle_id}'s adjacent stops are {self.stop_list_adjacent}")
    #     if any([stop in self.destination_stops for stop in self.stop_list_adjacent]): #This assumes that the stop to stop distannce is 1(Hardcoded)
    #         self.matching_stop_found = True
    #         print(f"{self.vehicle_type} {self.vehicle_id} found a matching stop adjacent")
    #     return

    def update_pool_of_occupied_positions(self):
        """This method updates the positions current occupied by the vehicle"""
        road_length = self.road_designation.length
        end_position = self.rear_bumper_position + self.length
        
        if end_position < road_length:
            self.pool_of_occupied_positions = np.arange(self.rear_bumper_position, end_position, 1)
        else:
            # Wrap around the periodic boundary
            part1 = np.arange(self.rear_bumper_position, road_length, 1)
            part2 = np.arange(0, end_position % road_length, 1)
            self.pool_of_occupied_positions = np.concatenate((part1, part2))
        return


    def unload_passengers(self, current_time):
        """Unload passengers only if their stop matches one of the occupied positions of the vehicle."""
        for passenger in self.passengers_within_vehicle:
            # passenger.determine_if_overshot_destination(self)
            # print(f"Passenger {passenger.passenger_id}'s edge crossings is {passenger.edge_crossings}.")
            if passenger.edge_crossings == 1 or passenger.about_to_cross_edge:
                # print(f"Calling unload passenger {passenger.passenger_id} method. Overshot destination?? --- {passenger.overshot_destination}")
                if passenger.overshot_destination:
                    self.release_passenger(passenger, current_time)             
                    self.passengers_served += 1
                    # Track unloading from the far lane
                    if self.current_row == 2:
                        self.far_lane_unloadings += 1
                    if self.passengers_served > 0:
                        return 
                for stop in self.stop_list_adjacent:
                    if stop:
                        # print(f"The unloading list of {stop} is {stop.unloading_list}")
                    #self.update_pool_of_occupied_positions()
                    #(f"Passenger {passenger.passenger_id} is checking the stop {stop.position} and its unloading list {stop.unloading_list}")
                        if passenger in stop.unloading_list and passenger.let_me_out: #Anticipates that chance of evenly-spaced stops
                            # print(f"Passenger {passenger.passenger_id}'s destination is adjacent to the {self.vehicle_type} {self.vehicle_id} and the passenger is in the unloading list.")
                            self.release_passenger(passenger, current_time)             
                            self.passengers_served += 1
                            # Track unloading from the far lane
                            if self.current_row == 2:
                                self.far_lane_unloadings += 1
                            if self.passengers_served > 0:
                                return    
 
        return

    def unloading(self, current_time): #Deceleration and lane changing of vehicle was already handled
        """This method handles unloading of passengers, assuming lane changing and deceleration for them have been implemented previously"""
        if self.vehicle_type == "jeep":
            # print(f"{self.vehicle_type} {self.vehicle_id}: Unload Passengers? --- {self.will_unload_passengers()}.")
            
            if (self.will_unload_passengers() or self.overshot_destination) and self.speed == 0:
                # print(f"{self.vehicle_type} {self.vehicle_id} stopped and will unload passengers.")
                self.matching_stops_on_sidewalk()
                if self.matching_stop_found or self.overshot_destination:
                    # print(f"{self.vehicle_type} {self.vehicle_id} should now be at stop because the destination is either adjacent to the vehicle or overshot by it.")
                    if self.current_row == 0: #The deceleration method stops the vehicle to v = 0 if needed
                        self.unload_passengers(current_time)               
                    elif self.current_row == 2:
                        # print(f"{self.vehicle_type} {self.vehicle_id} has tried lane changing {self.lane_change_trials_for_passengers}")
                        if self.lane_change_trials_for_passengers >= 4: #Unloading from the far lane
                            self.unload_passengers(current_time)
                        else:
                            pass
                    if not self.will_unload_passengers():
                        self.lane_change_trials_for_passengers = 0 
        return


    def get_adjacent_sidewalk_cell(self, road_cell):
        """This method obtains the sidewalk cell adjacent to a given road cell position"""
        sidewalk_cell = self.sidewalk.occupancy[road_cell]
        # print(f"{self.vehicle_type} {self.vehicle_id} is trying to access passengers at sidewalk position {road_cell}")
        return sidewalk_cell

    def load_passengers(self, sidewalk_cell, passenger_list, current_time):
        loaded = 0
        self.occupied_seats = len(self.passengers_within_vehicle)
        self.unoccupied_seats = self.capacity - self.occupied_seats

        while self.unoccupied_seats > 0 and len(passenger_list) > 0:
            #print(f"{self.vehicle_type} {self.vehicle_id} is trying to load passengers")
            passenger1 = passenger_list.pop(0) #First-come, first-served
            passenger1.board_vehicle(self, current_time)
            self.passengers_within_vehicle.append(passenger1)
            self.occupied_seats += 1
            loaded += 1
            self.unoccupied_seats = self.capacity - self.occupied_seats
            self.passengers_served += 1
            self.update_pool_of_occupied_positions()
            self.last_loading_position = self.pool_of_occupied_positions
            if self.current_row == 2:
                self.far_lane_loadings += 1
            if self.passengers_served >= 1:
                break
        return loaded

    def loading(self, current_time):
        """This method supervises boarding of passengers, assuming the vehicle have already decelerrated/ changed lanes for them"""
        # print(f"{self.vehicle_type} {self.vehicle_id} is calling loading method")
        if self.passengers_served >=1:
            return

        if self.vehicle_type == "jeep" and self.occupied_seats < self.capacity:
            if self.detect_passengers_adjacent_and_ahead():
                # print(f"{self.vehicle_type} {self.vehicle_id} detected passengers")
                start_index = self.rear_bumper_position
                end_index = self.rear_bumper_position + self.length
                index = start_index
                road_length = self.road_designation.length
                # Handle periodic boundary conditions
                #road_positions = [(i % road_length) for i in range(start_index, end_index)]

                # Freeze sidewalk cells during loading
                if self.speed == 0:
                    
                    pass
                    #self.sidewalk.freeze_cells_for_loading(road_positions)

                # print(f"{self.vehicle_type} {self.vehicle_id} detected passengers starting from {start_index} to {end_index}.")
                loaded_passengers = 0
                
                while index < end_index:
                    #print(f"{self.vehicle_type} {self.vehicle_id} is currently checking at {index}.")
                    road_cell = index % road_length
                    sidewalk_cell = self.get_adjacent_sidewalk_cell(road_cell)
                    #passenger_list = self.sidewalk.stops[road_cell][0].loading_list
                    if self.sidewalk.stops[road_cell]:  # Ensure the list is not empty
                        passenger_list = self.sidewalk.stops[road_cell][0].loading_list
                    else:
                        passenger_list = []  # No passengers if no stop exists


                    if sidewalk_cell == 0 or len(passenger_list) == 0:
                        index += 1
                        # print(f"{self.vehicle_type} {self.vehicle_id} detected no passengers, we shift to position {index}.")
                        continue

                    if self.current_row == 0:
                        # print(f"{self.vehicle_type} {self.vehicle_id}is at the nearer lane.")
                        if self.speed == 0:
                            # print(f" {self.vehicle_type} {self.vehicle_id} stopped to load passengers.")
                            loaded_passengers += self.load_passengers(sidewalk_cell, passenger_list, current_time)
                            self.occupied_seats = len(self.passengers_within_vehicle)
                            if self.occupied_seats >= self.capacity:
                                break
                    elif self.current_row == 2:
                        if self.lane_change_trials_for_passengers >= 4:
                            if self.speed == 0:
                                # print(f" {self.vehicle_type} {self.vehicle_id} stopped at the far lane to load passengers.")
                                loaded_passengers += self.load_passengers(sidewalk_cell, passenger_list, current_time)
                                #self.lane_change_trials_for_passengers = 0
                                self.occupied_seats = len(self.passengers_within_vehicle)
                                if self.occupied_seats >= self.capacity:
                                    break
                    # Break if at least one passenger was loaded
                    if loaded_passengers > 0 or self.occupied_seats >= self.capacity:
                        #self.lane_change_trials_for_passengers = 0
                        break
                    index += 1
                # Unfreeze sidewalk cells once loading is complete
                # print(f"Unfreezing check for {self.vehicle_type} {self.vehicle_id}")
                # if len(self.last_loading_position)>0 and (all(self.sidewalk.occupancy[position] == 0 for position in self.last_loading_position) or self.capacity == len(self.passengers_within_vehicle)):
                #     print(f"{self.vehicle_type} {self.vehicle_id} last loading position is {self.last_loading_position}.")
                #     print(f"Sidewalk occupancy at those positions: {[self.sidewalk.occupancy[pos] for pos in self.last_loading_position]}")
                #     rolled_sidewalk_occupancy = np.roll(self.sidewalk.occupancy, -self.last_loading_position[0])
                #     print(f"Vehicle speed: {self.speed}, Occupied seats: {len(self.passengers_within_vehicle)}/{self.capacity}")
                #     if self.speed > 0 or (np.sum(rolled_sidewalk_occupancy[0:self.length]==0) or self.capacity == len(self.passengers_within_vehicle)):
                #         self.sidewalk.unfreeze_cells(self.last_loading_position)
                #print(f"Loaded {loaded_passengers} passengers. Current passengers: {len(self.passengers_within_vehicle)} ")
        return

    def random_slowdown(self):
        """Mimics random slowdown, randomly decreases vehicle's speed based on braking probability """
        # print(f"{self.vehicle_type} {self.vehicle_id} is calling random slowdown method")
        if np.random.rand() < self.braking_prob and self.speed > 0:
            self.speed -= 1
        return

    def determine_cross_edge(self):
        #Did the vehicle just crossed the edge? (After crossing)
        if self.previous_rear_bumper_position > self.rear_bumper_position:
            self.did_cross_edge = True
            #print(f"{self.vehicle_type} {self.vehicle_id} has crossed edge.")
        else:
            self.did_cross_edge = False

    def determine_if_about_to_cross_edge(self):
        #Is the vehicle about to cross the edge?
        if ((self.front_bumper_position+5)%self.road_designation.length) < self.front_bumper_position:
            self.about_to_cross_edge = True
        else:
            self.about_to_cross_edge = False

    def move(self):
        """Implements longitudinal translation of the vehicle"""
        self.previous_stop_list_ahead = self.stop_list_ahead
        self.previous_stop_list_adjacent = self.stop_list_adjacent
        self.previous_front_bumper_position = self.front_bumper_position
        new_position = (self.rear_bumper_position + self.speed) % self.road_designation.length
        self.previous_rear_bumper_position = self.rear_bumper_position #store the previous rear_bumper_position before updating
        self.rear_bumper_position = new_position #This will be the "current" rear_bumper_position
        self.front_bumper_position = new_position + self.length - 1
        self.next_rear_bumper_position = new_position + self.speed
        self.next_front_bumper_position = self.next_rear_bumper_position + self.length - 1
        #print(f"Vehicle {self.vehicle_id}'s previous position is {self.previous_rear_bumper_position}, right now its current position is {self.rear_bumper_position}. Based on its speed, it aims to move to {self.next_rear_bumper_position}.")
        self.determine_cross_edge()
        # self.determine_if_about_to_cross_edge()
        self.update_pool_of_occupied_positions()
        self.passengers_served = 0