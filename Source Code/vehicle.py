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
        self.allow_unloading = False #Number of passengers on board
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
        self.allow_unloading = None
        self.allow_loading = None

    def accelerate(self):
        """Increases vehicle's speed by 1 cell, up to the maximum speed"""
        if self.speed < self.max_speed:
            self.speed += 1
            # print(f"{self.vehicle_type} {self.vehicle_id} accelerated to a speed of {self.speed}")

    def gap_distance(self, vehicle_row_to_be_checked):  #This is responsible for VEHICLE gap distance
        """Debugging this - make gap distance consider toroidal boundary cond. recently introduced"""
        """vehicle row to be checked: Input is row 0, you check for lane 1(row 0 and 1). Input is row 1, you check for lane at the middle (row 1 and 2). Input is row 2, you check for lane 2(rows 2 and 3)."""
        rear_bumper_position = self.rear_bumper_position
        #print(f"{self.vehicle_type} {self.vehicle_id}'s rear bumper is at {rear_bumper_position}")
        #print(f"{self.vehicle_type} {self.vehicle_id}'s front bumper is at {self.front_bumper_position}")
        look_ahead_distance = self.speed #With t=1
        #print(f"{self.vehicle_type} {self.vehicle_id}'s maximum distance is  {look_ahead_distance}")
        road_length = self.road_designation.length
        #print(f"{self.vehicle_type} {self.vehicle_id}'s road has length of {road_length}")
        
        gap_distance = look_ahead_distance
        
        for distance in range(1, look_ahead_distance + 1):
            start_of_space_to_be_checked = (rear_bumper_position + self.length + distance - 1)  % road_length #putting the modulo operator here removes the need for separate considerations under periodic boundary conditions
            #print(f"{self.vehicle_type} {self.vehicle_id}: next rear bumper rear_bumper_position is {start_of_space_to_be_checked}")
            if np.sum(self.road_designation.occupancy[start_of_space_to_be_checked, vehicle_row_to_be_checked:vehicle_row_to_be_checked + self.width]) != 0:
                gap_distance = distance - 1 #When the vehicle is detected, that distance is already occupied, so we subtract 1 to be accurate
                #print(np.sum(self.road_designation.road_occupancy[start_of_space_to_be_checked, vehicle_row_to_be_checked:vehicle_row_to_be_checked + self.width]))
                break
        if gap_distance < 0: #For debugging
            print(f"Error, {self.vehicle_type} {self.vehicle_id} negative gap distance of {gap_distance}, at rear bumper rear_bumper_position {self.rear_bumper_position}") 
        else:
            print(f"Vehicle {self.vehicle_id}'s gap distance from the leading vehicle is {gap_distance}")

        return gap_distance # Return the  gap distance


    def check_lane_availability(self, target_row):
        """This method checks for the adjacent lane: if determines if the cells adjacent to the vehicle are empty and the cells within its look ahead distance"""
        print(f"{self.vehicle_type} {self.vehicle_id} checks the availability of lane {target_row/2}")
        look_ahead_distance = self.speed #Assuming t = 1
        rolled_occupancy = np.roll(self.road_designation.occupancy, -self.rear_bumper_position, axis = 0)
        print(f"{self.vehicle_type} {self.vehicle_id} checks the availability of lane {target_row/2}: {np.sum(rolled_occupancy[0:self.length + look_ahead_distance + 1, target_row])}")
        print(f"{self.vehicle_type} {self.vehicle_id} checks {rolled_occupancy[0: look_ahead_distance + 1, target_row].T}")
        return np.sum(rolled_occupancy[0: look_ahead_distance + 1, target_row])

    def begin_straddling(self, direction):
        """This method executes the actual action of changing lanes (in particular, this methods let the vehicle begin straddling)
            This method assumes that the occupancy on the lane of interest was already checked."""
        self.speed = self.gap_distance(self.current_row)
        
        if self.speed == 0:
            self.accelerate()
            #print(f"{self.vehicle_type} {self.vehicle_id} accelerates to possibly lane change. ")

        rolled_occupancy = np.roll(self.road_designation.occupancy, -self.front_bumper_position, axis = 0)

        if self.speed > 0 and np.all(rolled_occupancy[1:self.speed + 1, self.current_row])== 0: #Check on the current lane
            self.current_row += direction
            self.move()
            if self.current_row == 1:
                self.lane_change_trials_for_passengers = 0
                #print(f"{self.vehicle_type} {self.vehicle_id} begins straddling, it is on row {self.current_row}, positions {self.rear_bumper_position}-{self.front_bumper_position}")
        else:
            #print(f"{self.vehicle_type} {self.vehicle_id} cannot straddle. ")
        return

    def is_lane_change_allowed(self, target_row):
        "Check if the target row is restricted for the vehicle"
        for row, allowed_type in self.road_designation.allowed_rows:
            if target_row == row and self.vehicle_type not in allowed_type:
                return False
        return True

    def detect_passengers_adjacent_and_ahead(self):
        """Check if there are passengers in the next few sidewalk cells, considering periodic boundaries. 
        Will be used to know if will decelerate or lane change for LOADING of passengers"""
        if self.vehicle_type == "jeep":
            road_length = self.road_designation.length
            look_ahead_distance = self.speed #With t = 1
            future_positions = [(self.rear_bumper_position + i) % road_length for i in range(0, self.length + look_ahead_distance)] #Detect passengers that are adjacent to the vehicle and within its look ahead distance
            if any(len(self.sidewalk.passengers[position]) > 0 for position in future_positions):
                return True
                #print(f"{self.vehicle_type} {self.vehicle_id} detects passengers adjacent and ahead")
            else:
                return False
                #print(f"{self.vehicle_type} {self.vehicle_id} detects no passengers")
        else:
            return False
            #print(f"{self.vehicle_type} {self.vehicle_id} is not a passenger vehicle")

    def collect_passenger_destinations(self):
        """If the passenger's destination is within sight, this method collects passenger"""
        if self.vehicle_type == "jeep":
            passenger_destinations = {}
            print(f"The passengers within {self.vehicle_type} {self.vehicle_id} are {self.passengers_within_vehicle}")
            for passenger in self.passengers_within_vehicle:
                passenger.update_riding_status(self)
                if passenger.riding_status == "let me out":
                    print(f"One passenger in {self.vehicle_type} {self.vehicle_id} says manong para po.")
                    passenger_destinations = {passenger.destination_stop for passenger in self.passengers_within_vehicle if passenger.destination_stop is not None}
            print(f"{self.vehicle_type} {self.vehicle_id}'s passenger destinations are {passenger_destinations}")
            self.matching_stops_on_sidewalk(passenger_destinations)
            return passenger_destinations
            
        else:
            return None

    def will_unload_passengers(self):
        """Determines if any of the passenger within the vehicle wants to come out of it"""
        if self.vehicle_type == "jeep":
            passenger_destinations = self.collect_passenger_destinations()
            self.determine_if_overshot_destination()
            if passenger_destinations is not None or self.overshot_destination:
                return True
                print(f"{self.vehicle_type} {self.vehicle_id} is about to unload passengers.")
            else:
                return False
        else:
            return False

    def attempt_lane_change_for_passengers(self):
        """This method attempts to lane change for passengers. This assumed that passengers are to be unloaded or loaded, and capacity has not yet reached"""
        if self.vehicle_type != "jeep":
            pass

        if self.lane_change_trials_for_passengers >= 4 or self.current_row == 0:
            print(f"{self.vehicle_type} {self.vehicle_id} gave up changing lanes, will try to load/unload on the far lane")
            pass
        
        if self.current_row == 2:
            print(f"{self.vehicle_type} {self.vehicle_id} will try lane changing to the right lane")
            target_row = 0
            if self.is_lane_change_allowed(target_row):
                print(f"Lane change on row {target_row} is allowed. Will try doing so.")
                self.lane_change_direction = "right"
                road_portion_checked = self.check_lane_availability(1) #We check the middle lane
                print(f"{self.vehicle_type} {self.vehicle_id} checked a road portion with summed occupancy of {road_portion_checked} ")
                if road_portion_checked == 0:
                    print(f"{self.vehicle_type} {self.vehicle_id} can change lanes. It will now begin straddling.")
                    self.begin_straddling(-1)  # Initiates lane change
                    return
            if self.lane_change_trials_for_passengers < 4:
                print(f"{self.vehicle_type} {self.vehicle_id} has tried lane changing {self.lane_change_trials_for_passengers} times.")
                self.lane_change_trials_for_passengers += 1  # Stop attempting after 4 failed tries
                print(f"{self.vehicle_type} {self.vehicle_id} has tried lane changing {self.lane_change_trials_for_passengers} times (incremented).")
            elif self.lane_change_trials_for_passengers >= 4:
                print(f"{self.vehicle_type} {self.vehicle_id} has attempted lane changing 4 times.")
                return
        

    def lane_changing(self):
        """This method handles the lane changing if there are passengers to be loaded or unloaded, or just based on driver's behavior"""
        gap_distance_of_own_lane = self.gap_distance(self.current_row)
        print(f"{self.vehicle_type} {self.vehicle_id}'s gap distance from a leading vehicle on its lane is {gap_distance_of_own_lane}")
        gap_distance_of_right_lane = self.gap_distance(self.current_row - 2) if self.current_row == 2 else gap_distance_of_own_lane
        print(f"{self.vehicle_type} {self.vehicle_id}'s gap distance from a leading vehicle on the right lane is {gap_distance_of_right_lane}")
        gap_distance_of_left_lane = self.gap_distance(self.current_row + 2) if self.current_row == 0 else gap_distance_of_own_lane
        print(f"{self.vehicle_type} {self.vehicle_id}'s gap distance from a leading vehicle on the left lane is {gap_distance_of_left_lane}")
        #Put a portion that handles lane changing for passengers
        if (self.will_unload_passengers() or self.detect_passengers_adjacent_and_ahead()) and (len(self.passengers_within_vehicle) < self.capacity) and self.vehicle_type!= "truck":
            self.attempt_lane_change_for_passengers()
            print(f"{self.vehicle_type} {self.vehicle_id} attempted to lane change for passengers. It attempted {self.lane_change_trials_for_passengers} times.")  #if detected passengers, skip the remaining
        else:
            #This portion handles vehicle lane changing based on which has more available space
            if self.speed > gap_distance_of_own_lane:
                print(f"{self.vehicle_type} {self.vehicle_id} will try to lane change for more space")
                if self.current_row == 0 and gap_distance_of_left_lane > gap_distance_of_own_lane:
                    target_row = self.current_row + 2
                    if self.is_lane_change_allowed(target_row):
                        self.lane_change_direction = 'left'
                        self.speed = gap_distance_of_own_lane
                        road_portion_checked = self.check_lane_availability(target_row)
                        print(f"{self.vehicle_type} {self.vehicle_id} checked a road portion with summed occupancy of {road_portion_checked} ")
                        if road_portion_checked == 0:
                            self.begin_straddling(1)
                            print(f"{self.vehicle_type} {self.vehicle_id} is now straddling from from lane 0.")
                elif self.current_row == 2 and gap_distance_of_right_lane > gap_distance_of_own_lane:
                    target_row = self.current_row - 2
                    if self.is_lane_change_allowed(target_row):
                        self.lane_change_direction = "right"
                        self.speed = gap_distance_of_own_lane
                        road_portion_checked = self.check_lane_availability(target_row+1)
                        if road_portion_checked == 0:
                            self.begin_straddling(-1)
                            print(f"{self.vehicle_type} {self.vehicle_id} is now straddling from from lane 1.")
                else:
                    pass
            else:
                pass
        return

    def finish_lane_change(self):
        """This method handles straddling cases, completes the straddling case"""
        if self.current_row == 1:
            print(f"The lane change direction of {self.vehicle_type} {self.vehicle_id} is {self.lane_change_direction}")
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
                print(f"{self.vehicle_type} {self.vehicle_id}'s space ahead is {shifted_occupancy}, the front bumper is at {self.front_bumper_position}'")
                
                if self.speed > 0:
                    space_available = np.sum(shifted_occupancy[0:look_ahead_distance+1, self.current_row:self.current_row + self.width]) == 0
                    print(f"{self.vehicle_type} {self.vehicle_id}'s space checked is {shifted_occupancy[0:look_ahead_distance+1, self.current_row:self.current_row + self.width].T}'")
                elif self.speed == 0:
                    space_available = np.sum(shifted_occupancy[0:2, self.current_row:self.current_row + self.width])== 0 #Check at least 2 cells in front
                    print(f"{self.vehicle_type} {self.vehicle_id}'s space checked is {shifted_occupancy[0:2, self.current_row:self.current_row + self.width].T}'")
                
                if space_available:
                    print(f"{self.vehicle_type} {self.vehicle_id}'s empty space ahead is {shifted_occupancy}'")
                    if self.speed == 0:
                        self.accelerate()
                        print(f"{self.vehicle_type} {self.vehicle_id}'s speed is 0 so we accelerate to be able to lane change.'")
                    self.current_row = target_row
                    self.move()
                    self.lane_change_direction = None
                    print(f"{self.vehicle_type} {self.vehicle_id}'s lane change direction is {self.lane_change_direction}.")
                else:
                    self.decelerate()
                    print(f"{self.vehicle_type} {self.vehicle_id}'s space in front is not available'")
            else:
                print(f"{self.vehicle_type} {self.vehicle} has no target row.")
        return

    def pedestrian_headway(self):
        """This method determines the distance of the nearest pedestrian to the jeepney"""
        look_ahead_distance = self.speed #Assuming t = 1
        rear_bumper = self.rear_bumper_position
        front_bumper = self.front_bumper_position        
        #Shift the sidewalk occupancy array where the rear bumper is at index 0
        rolled_sidewalk = np.roll(self.sidewalk.occupancy[:, 0], -rear_bumper)

        #Check if any pedestrian is adjacent to the vehicle
        if np.any(rolled_sidewalk[:self.length] > 0):
            return 0 #Passenger is directly adjacent
        
        rolled_sidewalk_shifted = np.roll(self.sidewalk.occupancy[:, 0], -front_bumper) #front bumper is at index 0
        #Search for the first occupied space within the look ahead distance
        pedestrian_headway_list = np.where(rolled_sidewalk_shifted[1:look_ahead_distance + 1] > 0)[0] #1 yung index after nung front bumper(which makes sense)
        #The array above will never cross boundary conditions (this will only be calculated for jeepneys, maximum speed is 5, and jeep length is 3. The farthest it could go is until index 7. )
        return pedestrian_headway_list[0] if pedestrian_headway_list.size > 0 else look_ahead_distance

    def determine_if_overshot_destination(self):
        """This method determines whether the vehicle overshot the destination of at least one passenger"""
        passenger_overshoots = set() #empty set
        for passenger in self.passengers_within_vehicle:
            if passenger.overshoot_destination:
                passenger_overshoots.add(passenger)
        #If there is at least one overshooting passenger, set the flag to True
        self.overshot_destination = bool(passenger_overshoots)

    def calculate_nearest_destination_distance(self): #This is not final, I stopped right here (Feb. 13, 2025, 9:26 PM)
        """This method is triggered only if the destination of the passenger is within sight.
        To be used for deceleration purposes"""
        #if the vehicle overshoot a passenger's destination, the output here is automatically zero

        self.determine_if_overshot_destination()
        if self.overshot_destination:
            print(f"{self.vehicle_type} {self.vehicle_id} has overshot a passenger destination")
            return 0

        road_length = self.road_designation.length
        vehicle_rear = self.rear_bumper_position
        look_ahead_distance = self.speed #With t = 1

        #Collect passenger destinations
        passenger_destinations = self.collect_passenger_destinations()
        if not passenger_destinations:
            print(f"{self.vehicle_type} {self.vehicle_id} has no passenger to be unloaded.")
            return inf #No stops ahead

        #Create a binary array for destination stop positions
        destination_occupancy = np.zeros(road_length)
        print(f"{self.vehicle_type} {self.vehicle_id} sees the destination occupancy {destination_occupancy}")
        for destination_stop in passenger_destinations:
            destination_occupancy[destination_stop.position] = 1 # Mark stops

        #Roll the array so the rear bumper is at index 0
        rolled_destinations = np.roll(destination_occupancy, -(vehicle_rear))
        print(f"{self.vehicle_type} {self.vehicle_id} sees rolled destination: {rolled_destinations}")
        #Find the first nonzero index (or the nearest stop)
        nearest_distance = np.where(rolled_destinations[1:look_ahead_distance+1] > 0)[0]
        return max(0, nearest_distance[0] - 2) if nearest_distance.size > 0 else inf


    def decelerate(self):
        """Decelerate to prevent collisions, load passengers, or unload passengers"""
        nearest_destination_distance = self.calculate_nearest_destination_distance() #if overshot, automatically 0. If not, calculate based on distance from front bumper
        print(f" {self.vehicle_type} {self.vehicle_id} is {nearest_destination_distance} cells away from the nearest destination.")
        nearest_pedestrian_distance = self.pedestrian_headway() #if adjacent to vehicle 0, if not, calculate based on distance from front bumper
        print(f" {self.vehicle_type} {self.vehicle_id} is {nearest_pedestrian_distance} cells away from the nearest pedestrian.")
        nearest_vehicle_distance = self.gap_distance(self.current_row) #gap distance in own lane
        print(f" {self.vehicle_type} {self.vehicle_id} is {nearest_vehicle_distance} cells away from the nearest vehicle.")
        reason = None
        if self.vehicle_type == "jeep":
        #determine minimum distance to decelerate
            if self.capacity > len(self.passengers_within_vehicle):
                least_distance_to_decelerate = min(nearest_destination_distance, nearest_pedestrian_distance, nearest_vehicle_distance) 
            else: #if jeep is full, it won't stop for passengers
                least_distance_to_decelerate = min(nearest_destination_distance, nearest_vehicle_distance)

            target_speed = least_distance_to_decelerate
            # if least_distance_to_decelerate == nearest_vehicle_distance:
            #     target_speed = nearest_vehicle_distance
            #     reason = "prevent collisions"
                # print(f" {self.vehicle_type} {self.vehicle_id} needs to decelerate to {least_distance_to_decelerate} to {reason}")

                
            # else: #least_distance_to_decelerate in [nearest_pedestrian_distance, nearest_destination_distance]:
            #     target_speed = min(nearest_pedestrian_distance, nearest_destination_distance)
            #     reason = "for passengers"
                # print(f" {self.vehicle_type} {self.vehicle_id} needs to decelerate to {least_distance_to_decelerate} {reason}")

            deceleration = self.speed - target_speed
            print(f" {self.vehicle_type} {self.vehicle_id} needs to decelerate by {deceleration}.")
            #Put an algorithm here that details the reason for stopping and the 
            if deceleration > 0: #skip deceleration if not needed
                #Decelerate safely (if decelerating for passengers, later, we will still check for collisions)
                if deceleration > self.safe_deceleration:
                    new_speed = max(0, self.speed - self.safe_deceleration)
                    #if new_speed < self.safe_stopping_speed and reason == "for passengers":
                        #new_speed = self.safe_stopping_speed
                    print(f" {self.vehicle_type} {self.vehicle_id} needs to decelerate to {new_speed}.")

                else:
                    new_speed = max(0, target_speed) #actually, the max() function is not necessary, I just have trust issues
                    print(f" {self.vehicle_type} {self.vehicle_id} needs to decelerate to {new_speed}.")
                
                self.speed = max(0, min(new_speed, nearest_vehicle_distance)) # Ensure new_speed does not exceed nearest vehicle gap
                print(f" {self.vehicle_type} {self.vehicle_id} decelerated to {self.speed}.")
        else:
            if self.speed > nearest_vehicle_distance:
                self.speed = nearest_vehicle_distance
                print(f" {self.vehicle_type} {self.vehicle_id} decelerated to {self.speed}.")
        return

    def release_passenger(self, passenger):
        """
        Releases the passenger from the vehicle at their destination.
        Removes the passenger from the vehicle's list, updates the passenger's state, 
        and records metrics if needed.
        """
        self.passengers_within_vehicle.remove(passenger)
        self.occupied_seats = len(self.passengers_within_vehicle)
        passenger.alight_vehicle(self)
        return

    def matching_stops_on_sidewalk(self, passenger_destinations): #implemented inside "collect passenger destinations method"
        """Check if any occupied position has a matching alighting stop in passenger destinations."""
        #self.matching_stop_found = any(any(stop in passenger_destinations for stop in self.sidewalk.alighting_stops[position]) for position in self.pool_of_occupied_positions)
        for position in self.pool_of_occupied_positions:
            if any(stop in passenger_destinations for stop in self.sidewalk.alighting_stops[position]):
                self.matching_stop_found = True
                print(f"{self.vehicle_type} {self.vehicle_id} detected matching stops on sidewalk.")
            else:
                self.matching_stop_found = False
        return

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

    def can_stop_safely(self):
        return self.speed <= self.safe_speed_to_stop

    def unloading(self, unloaded_passengers): #Deceleration and lane changing of vehicle was already handled
        """This method handles unloading of passengers, assuming lane changing and deceleration for them have been implemented previously"""
        # print(f"{self.vehicle_type} {self.vehicle_id} is calling unloading method")
        #For debugging purposes
        # passenger_destinations = self.collect_passenger_destinations()
        # print(f"{self.vehicle_type} {self.vehicle_id}'s passenger destinations are {passenger_destinations}")
        # positions_of_destinations = []
        # for destination in passenger_destinations:
        #     destination.position.append(positions_of_destinations)
        # print(f"{self.vehicle_type} {self.vehicle_id}'s passenger destinations are {passenger_destinations}")
        # self.determine_if_overshot_destination()
        # if self.overshot_destination:
            # print(f"{self.vehicle_type} {self.vehicle_id} overshot a passenger's destination.")
        # self.matching_stops_on_sidewalk(passenger_destinations)

        #-------------------------------------------------------------------------------
        if self.vehicle_type == "jeep":
            # print(f"{self.vehicle_type} {self.vehicle_id}'s speed is {self.speed}")
            if self.will_unload_passengers() and self.speed == 0:
                # print(f"{self.vehicle_type} {self.vehicle_id} stopped to unload passengers.")
                if self.matching_stop_found or self.overshot_destination:
                    # print(f"{self.vehicle_type} {self.vehicle_id} nees to stop because the destination is either adjacent to the vehicle or overshot by it.")
                    if self.current_row == 0: #The deceleration method stops the vehicle to v = 0 if needed
                        self.lane_change_direction = None
                        for passenger in self.passengers_within_vehicle: #Try list comprehension as well
                            if passenger.riding_status == "let me out" and (passenger.destination_stop.position in self.pool_of_occupied_positions or passenger.overshoot_destination):
                                self.release_passenger(passenger)             
                                unloaded_passengers.append(passenger)
                            else:
                                pass                            
                    elif self.current_row == 2:
                        if self.lane_change_trials_for_passengers >= 4:
                            self.lane_change_direction = None
                            for passenger in self.passengers_within_vehicle:
                                if passenger.riding_status == "let me out" and (passenger.destination_stop.position in self.pool_of_occupied_positions or passenger.overshoot_destination):
                                    self.release_passenger(passenger)             
                                    unloaded_passengers.append(passenger)
                                else:
                                    pass  
                        else:
                            pass
        return

    def get_adjacent_sidewalk_cell(self, road_cell):
        """This method obtains the sidewalk cell adjacent to a given road cell position"""
        sidewalk_cell = self.sidewalk.occupancy[road_cell]
        # print(f"{self.vehicle_type} {self.vehicle_id} is trying to access passengers at sidewalk position {road_cell}")
        return sidewalk_cell

    def load_passengers(self, sidewalk_cell, passenger_list):
        loaded = 0
        self.occupied_seats = len(self.passengers_within_vehicle)
        self.unoccupied_seats = self.capacity - self.occupied_seats

        while self.unoccupied_seats > 0 and len(passenger_list) > 0:
            # print(f"{self.vehicle_type} {self.vehicle_id} is trying to load passengers")
            passenger1 = passenger_list.pop(0) #First-come, first-served
            passenger1.board_vehicle(self)
            self.passengers_within_vehicle.append(passenger1)
            self.occupied_seats += 1
            loaded += 1
            self.unoccupied_seats = self.capacity - self.occupied_seats
        return loaded

    def loading(self):
        """This method supervises boarding of passengers, assuming the vehicle have already decelerrated/ changed lanes for them"""
        # print(f"{self.vehicle_type} {self.vehicle_id} is calling loading method")
        if self.vehicle_type == "jeep" and self.occupied_seats < self.capacity:
            if self.detect_passengers_adjacent_and_ahead():
                # print(f"{self.vehicle_type} {self.vehicle_id} detected passengers")
                start_index = self.rear_bumper_position
                end_index = self.rear_bumper_position + self.length + self.speed
                index = start_index
                road_length = self.road_designation.length
                # print(f"{self.vehicle_type} {self.vehicle_id} detected passengers starting from {start_index} to {end_index}.")
                loaded_passengers = 0
                while index < end_index:
                    # print(f"{self.vehicle_type} {self.vehicle_id} is currently checking at {index}.")
                    road_cell = index % road_length
                    sidewalk_cell = self.get_adjacent_sidewalk_cell(road_cell)
                    passenger_list = self.sidewalk.passengers[road_cell]

                    if sidewalk_cell == 0 or len(passenger_list) == 0:
                        index += 1
                        # print(f"{self.vehicle_type} {self.vehicle_id} detected no passengers, we shift to position {index}.")
                        continue

                    if self.current_row == 0:
                        # print(f"{self.vehicle_type} {self.vehicle_id}is at the nearer lane.")
                        if self.speed == 0:
                            # print(f" {self.vehicle_type} {self.vehicle_id} stopped to load passengers.")
                            loaded_passengers += self.load_passengers(sidewalk_cell, passenger_list)
                    elif self.current_row == 2:
                        if self.lane_change_trials_for_passengers >= 4:
                            # print(f"{self.vehicle_type} {self.vehicle_id} will load at the far lane.")
                            if self.speed == 0:
                                # print(f" {self.vehicle_type} {self.vehicle_id} stopped to load passengers.")
                                loaded_passengers += self.load_passengers(sidewalk_cell, passenger_list)

                    index += 1
                # print(f"Loaded {loaded_passengers} passengers. Current passengers: {len(self.passengers_within_vehicle)} ")
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
        else:
            self.did_cross_edge = False

    def determine_if_about_to_cross_edge(self):
        #Is the vehicle about to cross the edge?
        if self.next_front_bumper_position < self.front_bumper_position:
            self.about_to_cross_edge = True
        else:
            self.about_to_cross_edge = False


    def determine_if_at_the_edge(self, vehicle):
        """This method determines if the vehicle is at the edge(periodic boundaries)"""
        if self.rear_bumper_position > self.front_bumper_position:
            self.at_the_edge = True
        else:
            self.at_the_edge = False
        return

    def move(self):
        """Implements longitudinal translation of the vehicle"""
        new_position = (self.rear_bumper_position + self.speed) % self.road_designation.length
        self.previous_rear_bumper_position = self.rear_bumper_position #store the previous rear_bumper_position before updating
        self.rear_bumper_position = new_position #This will be the "current" rear_bumper_position
        self.front_bumper_position = new_position + self.length - 1
        self.next_rear_bumper_position = new_position + self.speed
        self.next_front_bumper_position = self.next_rear_bumper_position + self.length - 1
        # print(f"Vehicle {self.vehicle_id}'s previous position is {self.previous_rear_bumper_position}, right now its current position is {self.rear_bumper_position}. Based on its speed, it aims to move to {self.next_rear_bumper_position}.")
        self.determine_cross_edge()
        self.determine_if_about_to_cross_edge()
        self.update_pool_of_occupied_positions()