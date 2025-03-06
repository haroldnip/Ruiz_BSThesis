import numpy as np

class Passenger:
    _id_counter = 0
    def __init__(self, sidewalk_entry_time, sidewalk_designation, road_designation, sidewalk_position, distance_within_sight, destination_stop, current_time, vehicle_simulator):
        self.passenger_id = Passenger._id_counter #identifying number of each passenger
        Passenger._id_counter += 1 #increment passenger id based on order of initialization
        self.sidewalk_entry_time = sidewalk_entry_time #The time where the passenger spawned on the sidewalk
        self.sidewalk_designation = sidewalk_designation #passenger knows on which sidewalk he/she is
        self.road_designation = road_designation #passenger knows on what road he/she is
        self.sidewalk_position = sidewalk_position #position of passenger on sidewalk
        self.destination_stop = destination_stop #The position where the passenger wants to go
        self.last_sidewalk_position = None #The position where the passenger board the jeep
        self.jeep_boarding_time = None #The time wherein the passenger boarded the jeepney
        self.arrived_at_destination_time = None #The time when the passenger arrived at his/her destination
        self.on_vehicle = False #Determines whether the passenger is inside a vehicle or not
        self.switch_direction = None #which direction the nearest vehicle is
        self.riding_time = None #Riding time 
        self.waiting_time = 0 #Amount of time the passenger waited on the sidewalk before boarding a jeepney
        self.riding_status = None #chilling means the passenger is in-transit, "let me out" means the passenger wants to alight the vehicle, None means it is on the sidewalk
        self.road_position = None #position of the vehicle's rear bumper if in a vehicle
        self.vehicle_simulator = vehicle_simulator 
        self.current_time = current_time #gives passenger a consciousness of time
        self.distance_within_sight = distance_within_sight
        self.edge_crossings = 0 
        self.stops_in_view = [] #Based on speed, the stops within sight of the passenger(speed is the basis)
        self.set_of_stops_in_sight = [] #Choose from the 2 sets(either boarding or alighting)
        self.set_of_stops_positions_in_sight = []
        self.did_cross_edge = None
        self.about_to_cross_edge = None
        self.edge_crossings_at_start = 0
        self.overshoot_destination = None
        self.destination_within_view = None
        self.destination_adjacent_to_vehicle = None
        self.riding_speed = None
        #self.edge_crossings_to_see_destination = edge_crossings_to_see_destination

    def board_vehicle(self, vehicle):
        """This logic decides if the passenger boards the vehicle if all the conditions are satisifed:
        The vehicle is a jeepney, the vehicle's speed at the current timestep is zero, and the vehicle allows loading of passengers"""
        self.on_vehicle = True
        self.last_sidewalk_position = self.sidewalk_position
        self.jeep_boarding_time = self.current_time
        self.road_position = vehicle.rear_bumper_position
        self.riding_status = "chilling"
        self.sidewalk_position = None
        # print(f"Passenger {self.passenger_id} boarded {vehicle.vehicle_type} {vehicle.vehicle_id}")
        if vehicle.did_cross_edge:
            self.edge_crossings_at_start = True
            # print(f"Passenger {self.passenger_id} boarded {vehicle.vehicle_type} {vehicle.vehicle_id}, which just crossed the boundary.")
        return

    def alight_vehicle(self, vehicle):
        """This method removes the passenger from the vehicle when the destination have been reached"""
        if self.riding_status == "let me out" or self.overshoot_destination:
            self.on_vehicle = False
            self.riding_status = "off"
            self.arrived_at_destination_time = self.current_time
            self.sidewalk_position = None
            # print(f"Passenger {self.passenger_id} alighted the jeepney.")
            # print(f"Passenger {self.passenger_id} has reached his destination at {self.destination_stop}.")
            #print(f"The passengers within the vehicle are {vehicle.passengers_within_vehicle}")
        return

    def determine_edge_crossing_at_start(self, vehicle):
        """This method resets the number of edge crossings when the passenger boarded a vehicle that just crossed the edge"""
        if self.on_vehicle:
            if self.edge_crossings_at_start:
                self.edge_crossings = 0
                self.edge_crossings_at_start = False
                # print(f"Passenger {self.passenger_id} boarded on vehicle {vehicle.vehicle_id}, which just crossed the edge. We reset edge crossing of passenger to 0.")
        return

    def determine_crossing_edge_status(self, vehicle):
        if self.on_vehicle:
            if self.edge_crossings == 1:
                pass
            else:
                if vehicle.did_cross_edge:
                    self.did_cross_edge = True
                    self.edge_crossings += 1
                    self.determine_edge_crossing_at_start(vehicle)
                    # print(f"Passenger {self.passenger_id} just crossed the edge. The edge crossings = {self.edge_crossings}.")
                else:
                    self.did_cross_edge = False
                    
                if vehicle.about_to_cross_edge:
                    self.about_to_cross_edge = True
                    # print(f"Passenger {self.passenger_id} about to cross edge. The edge crossings = {self.edge_crossings}.")

        return

    def determine_the_set_of_stops(self, vehicle):
        """This method determines the set of stops that will be visible to the passenger"""
        self.stops_in_sight = []
        
        if self.on_vehicle:
            if self.edge_crossings == 0:  # When boarding the jeep, only see the boarding stops
                # self.set_of_stops_in_sight = self.sidewalk_designation.boarding_stops.copy()
                return 
            
            elif self.edge_crossings == 0 and self.about_to_cross_edge:  # See all stops before crossing
                self.set_of_stops_in_sight = self.sidewalk_designation.boarding_stops.copy() #The boarding stops serve as fillers
                self.set_of_stops_in_sight.extend(self.sidewalk_designation.alighting_stops)  #  Fix: Extend instead of append
                # print(f"Passenger {self.passenger_id} with edge crossings = {self.edge_crossings} and about to cross edge.")
                return
            elif self.edge_crossings == 1:  # After crossing, only see alighting stops
                self.set_of_stops_in_sight = self.sidewalk_designation.alighting_stops.copy()
                # print(f"Passenger {self.passenger_id} with edge crossings = {self.edge_crossings}.")
                return

    def determine_stops_in_view(self, vehicle):  
        """
        Determine which stops are in view for a passenger, considering periodic boundaries.

        Args:
            vehicle (Vehicle): The vehicle the passenger is riding.
        """
        self.stops_in_view = [] #stops within look ahead distance
        self.determine_the_set_of_stops(vehicle)  # Determine stops in sight first
        
        road_length = self.road_designation.length  # Assuming the road length is defined
        
        if self.on_vehicle and (self.edge_crossings == 1 or self.about_to_cross_edge):
            # Roll all stops relative to the rear bumper position of the vehicle
            roll_amount = -vehicle.rear_bumper_position
            rolled_vehicle_front = np.mod(vehicle.rear_bumper_position + vehicle.length + vehicle.speed + roll_amount, road_length)
            
            self.stops_in_view = [
                stop[0] for stop_list in self.set_of_stops_in_sight for stop in [stop_list]
                if 0 <= np.mod(stop[0].position + roll_amount, road_length) < rolled_vehicle_front]
            # print(f"Passenger {self.passenger_id} called determie_stops_in_view method. The set of stops in view {self.stops_in_view}")
        return

    #Commented out: March 5, 2025
    # def determine_stops_in_view(self, vehicle):  
    #     """
    #     Determine which stops are in view for a passenger.

    #     Args:
    #         vehicle (Vehicle): The vehicle the passenger is riding.
    #     """
    #     self.stops_in_view = []
    #     self.determine_the_set_of_stops(vehicle)  # Determine stops in sight first

    #     if self.on_vehicle and (self.edge_crossings == 1 or self.about_to_cross_edge):
    #         # Fix: Filter stops based on position instead of slicing
    #         self.stops_in_view = [stop[0] for stop_list in self.set_of_stops_in_sight for stop in [stop_list]
    #             if vehicle.rear_bumper_position <= stop[0].position < vehicle.rear_bumper_position + vehicle.length + vehicle.speed]
    #         #print(f"Passenger {self.passenger_id} with edge crossings = {self.edge_crossings}" )
    #         #print(f"Passenger {self.passenger_id} views the stops {self.stops_in_view}")
    #     return

    def determine_if_destination_within_view(self, vehicle): #destination should be a stop
        """This method assumes that the passenger will never overshoot the destination without first notifying the driver that it needs to come out of the vehicle
        The mechanism accures that we always say "para" bago posibleng lumagpas sa destination."""
        if self.on_vehicle:
            # print(f"Passenger {self.passenger_id}'s destination is at {self.destination_stop.position}. He is current at {vehicle.pool_of_occupied_positions} with {self.edge_crossings} edge crossings.")
            if self.destination_stop in self.stops_in_view and (self.about_to_cross_edge or self.edge_crossings == 1):
                self.destination_within_view = True
                self.riding_status = "let me out"
                # print(f"As seen by passenger {self.passenger_id}, his destination {self.destination_stop.position} is within sight. The vehicle is at {vehicle.pool_of_occupied_positions}. It's riding status is {self.riding_status}")
            #I removed the else statement so that when this mechanism is triggered, it will stay TRUE all the time
        return


    def determine_if_overshoot_destination(self, vehicle):
        """
        Checks if a passenger has overshot their destination while riding a vehicle.
        The condition is triggered if the vehicle moves past the destination stop.
        """

        if self.overshoot_destination:
            # print(f"Passenger {self.passenger_id} has already overshot their destination at {self.destination_stop.position}.")
            return

        if not self.on_vehicle or self.current_time == self.jeep_boarding_time:
            return  # Only check after boarding.

        if self.riding_status == "let me out" and (self.about_to_cross_edge or self.edge_crossings == 1):
            previous_rear = vehicle.previous_rear_bumper_position
            current_rear = vehicle.rear_bumper_position
            destination = self.destination_stop.position

            # Check if the vehicle moved past the destination, considering periodic boundaries
            if previous_rear <= destination < current_rear or (current_rear < previous_rear and (destination >= previous_rear or destination < current_rear)):
                self.overshoot_destination = True
                #print(f"Passenger {self.passenger_id} has overshot their destination at {destination}.")


    # def determine_if_overshoot_destination(self, vehicle):
    #     # The "let me out" condition is triggered only after the passenger has crossed the edge at least once.
    #     if self.overshoot_destination:
    #         print(f"Passenger {self.passenger_id} has overshot their destination at {self.destination_stop.position}.")
    #         return

    #     if self.on_vehicle and (self.about_to_cross_edge or self.edge_crossings == 1):
    #         print(f"Passenger {self.passenger_id} is determining whether he overshot the destination or not. Current time is {self.current_time} and jeep boarding time is {self.jeep_boarding_time}")
    #         if self.current_time != self.jeep_boarding_time:
    #             previous_rear = vehicle.previous_rear_bumper_position
    #             current_rear = vehicle.rear_bumper_position
    #             road_length = self.road_designation.length  # Assuming road_length is defined somewhere in the class

    #             rolled_stops_in_sight = np.roll(self.stops_in_sight, -previous_rear)
    #             stop_range_to_check = (rolled_stops_in_sight[0:current_rear])
    #             for stop_list in stop_range_to_check:
    #                 if self.destination_stop in stop_list:
    #                     self.overshoot_destination = True
    #                     break


            # # Get all stop positions in view
            # stop_positions = np.array([stop.position for sublist in self.stops_in_sight for stop in sublist])
            # print(f"As seen by Passenger {self.passenger_id}, the stop positions are {stop_positions}")
            # if stop_positions.size == 0:
            #     return  # No stops to check

            # # Roll the previous rear bumper position to zero
            # roll_amount = -previous_rear
            # #rolled_stop_positions = np.mod(stop_positions + roll_amount, road_length)
            # rolled_current_rear = np.mod(current_rear + roll_amount, road_length)
            # rolled_destination = np.mod(self.destination_stop.position + roll_amount, road_length)

            # # Check if the rolled destination is within the range [0, rolled_current_rear)
            # if self.riding_status == "let me out":
            #     if (0 <= rolled_destination < rolled_current_rear):
            #         self.overshoot_destination = True
            #         print(f"Passenger {self.passenger_id} has overshot their destination at {self.destination_stop.position}.")

            #Commented out: March 3, 2025
            # # If there are no stops in view, mark destination as overshot.
            # if not self.stops_in_view:
            #     return
            
            # # Extract stop positions from stops_in_view.
            # stop_positions = np.array([stop.position for stop in self.stops_in_view])
            
            # # Roll stop positions to align with the vehicle’s rear bumper.
            # rolled_positions = np.roll(stop_positions, -vehicle.rear_bumper_position)
            
            # # Compare the destination stop's position with the rolled positions.
            # new_stop_index = np.where(rolled_positions == self.destination_stop.position)[0]
            
            # if self.riding_status == "let me out":
            #     # If the destination stop is not found, mark as overshot.
            #     if new_stop_index.size == 0:
            #         self.overshoot_destination = True
            #         print(f"Passenger {self.passenger_id} has overshot his destination. Destination {self.destination_stop.position} not found in stops in view.")
            #     else:
            #         self.overshoot_destination = False
        return


    #Commented out: March 2, 2025
    # def determine_if_overshoot_destination(self, vehicle):
    #     #the "let me out" will not be triggered if the passenger has not yet crossed the edge once. so this is safe
    #     if self.on_vehicle and (self.about_to_cross_edge or self.edge_crossings == 1):
    #         #Extract stop positions into an array
    #         stop_positions = np.array([stop.position for stop in self.stops_in_view])

    #         # Roll stop positions to align with the vehicle’s rear bumper
    #         rolled_positions = np.roll(stop_positions, -vehicle.rear_bumper_position)

    #         # Find the new index of the passenger’s destination
    #         new_stop_index = np.where(rolled_positions == self.destination_stop)[0]

    #         if self.riding_status == "let me out" and new_stop_index[0] < 0:
    #             self.overshoot_destination = True # Do not put an else statement so that when triggered, this will stay true
    #             print(f"As seen by passenger {self.passenger_id} has overshot his destination. His destination is {self.destination_stop}")
    #     return

    #Commented out: February 28, 2025
    # def determine_if_destination_is_adjacent(self, vehicle):
    #     """This function determines if the passenger's vehicle is already in front of the destination"""
    #     road_length = self.road_designation.length
    #     vehicle.determine_if_at_the_edge(vehicle)

    #     if vehicle.about_to_cross_edge or self.edge_crossings == 1:
    #         if vehicle.at_the_edge:
    #             if self.destination_stop in self.sidewalk_designation.alighting_stops[vehicle.rear_bumper_position:road_length] or\
    #                 self.destination_stop in self.sidewalk_designation.alighting_stops[0:vehicle.front_bumper_position]:
    #                 self.destination_adjacent_to_vehicle = True
    #                 # print(f"Passenger {self.passenger_id}'s destination is adjacent to {vehicle.vehicle_type} {vehicle.vehicle_id}.")
    #             else:
    #                 self.destination_adjacent_to_vehicle = False
    #         else:
    #             if self.destination_stop in self.sidewalk_designation.alighting_stops[vehicle.rear_bumper_position:vehicle.front_bumper_position]:
    #                 self.destination_adjacent_to_vehicle = True
    #                 # print(f"Passenger {self.passenger_id}'s destination is adjacent to {vehicle.vehicle_type} {vehicle.vehicle_id}.")
    #             else:
    #                 self.destination_adjacent_to_vehicle = False
    #     return


    def determine_if_destination_is_adjacent(self, vehicle):
        """Determines if the passenger's vehicle is already in front of the destination."""
        if vehicle.about_to_cross_edge or self.edge_crossings == 1:
            # Get alighting stops and roll it to align with the vehicle’s rear position
            rolled_alighting_stops = np.roll(self.sidewalk_designation.alighting_stops, -vehicle.rear_bumper_position)

            #Determine the range where the vehicle is positioned
            vehicle_range = rolled_alighting_stops[:vehicle.length]

             # Check if the destination is within the vehicle’s range
            self.destination_adjacent_to_vehicle = self.destination_stop in vehicle_range
            if self.destination_adjacent_to_vehicle is True:
                # print(f"Passenger {self.passenger_id}'s destination is adjacent to the vehicle.")
                pass
        return self.destination_adjacent_to_vehicle

    # def update_riding_status(self, vehicle):
    #     """
    #     Updates riding status based on the vehicle's position.
    #     """
    #     # print(f"Updating Passenger {self.passenger_id}'s riding status")
    #     if self.on_vehicle:
    #         if self.riding_status == "let me out":
    #             # print(f"Passenger {self.passenger_id} wants to get out.")
    #             self.determine_crossing_edge_status(vehicle)
    #             self.determine_edge_crossing_at_start(vehicle)
    #             self.determine_stops_in_view(vehicle)
    #             self.determine_if_destination_within_view(vehicle)
    #             self.determine_if_overshoot_destination(vehicle)
    #             self.determine_if_destination_is_adjacent(vehicle)
    #             return
    #         elif self.riding_status == "chilling":
    #             # print(f"Passenger {self.passenger_id} is chilling.")
    #             self.determine_crossing_edge_status(vehicle)
    #             self.determine_edge_crossing_at_start(vehicle)
    #             self.determine_stops_in_view(vehicle)
    #             self.determine_if_destination_within_view(vehicle)
    #             self.determine_if_overshoot_destination(vehicle)
    #             self.determine_if_destination_is_adjacent(vehicle)
    #             return


    def update_riding_status(self, vehicle):
        """
        Updates riding status based on the vehicle's position.
        """
        # print(f"Updating Passenger {self.passenger_id}'s riding status")
        if self.on_vehicle and self.riding_status in {"let me out", "chilling"}:
            # print(f"Passenger {self.passenger_id} wants to get out." if self.riding_status == "let me out" else f"Passenger {self.passenger_id} is chilling.")
            self.determine_crossing_edge_status(vehicle)
            self.determine_edge_crossing_at_start(vehicle)
            self.determine_stops_in_view(vehicle)
            self.determine_if_destination_within_view(vehicle)
            self.determine_if_overshoot_destination(vehicle)
            self.determine_if_destination_is_adjacent(vehicle)


    def nearest_vehicle_distance(self, road_designation, sidewalk_position, distance_within_sight):
        """
        Determine the nearest jeepney distance on the left and right of the sidewalk position.
        Passengers will use this information to decide whether to switch cells or not.
        Passengers know what type of vehicle is on the road as they observe road occupancy.

        Args:
            road_designation: Object containing road occupancy information.
            sidewalk_position: Current position of the passenger on the sidewalk.
            distance_within_sight: Maximum distance to check for vehicles.

        Returns:
            nearest_distance (int): Nearest distance to a vehicle, either left or right.
            switch_direction (str or None): Direction to switch ("left", "right", or None if no vehicles are nearby).
        """

        if sidewalk_position is not None:
            current_position = sidewalk_position
            #print(f"Passenger {self.passenger_id} is placed at position {current_position}.")
            sidewalk_length = road_designation.length  # Use road length for toroidal boundaries
            #print(f"Passenger {self.passenger_id} is placed on sidewalk of {sidewalk_length} cells long.")
            nearest_distance_left = 0  # Initialize to a large value????
            #print(f"Passenger {self.passenger_id} default nearest vehicle distance at left is {nearest_distance_left}.")
            nearest_distance_right = 0  # Initialize to a large value???
            #print(f"Passenger {self.passenger_id} default nearest vehicle distance at right is {nearest_distance_right}.")
            switch_direction = None
            #print(f"Passenger {self.passenger_id} default switch direction is {switch_direction}.")

            # Check for vehicles on the left
            for distance in range(1, distance_within_sight + 1):
                check_left_position = (current_position - distance) % sidewalk_length
                if road_designation.occupancy[check_left_position, 0] == 1:  # Check if a jeep is present
                    nearest_distance_left = distance - 1
                    break  # Stop checking further on the left
                    #print(f"Passenger {self.passenger_id}: After checking a distance of {distance}, the nearest vehicle at left is {nearest_distance_left} cells away.")
            # Check for vehicles on the right
            for distance in range(1, distance_within_sight + 1):
                check_right_position = (current_position + distance) % sidewalk_length
                if road_designation.occupancy[check_right_position, 0] == 1:  # Check if a jeep is present
                    nearest_distance_right = distance - 1
                    break  # Stop checking further on the right
                    #print(f"Passenger {self.passenger_id}: After checking a distance of {distance}, the nearest vehicle at left is {nearest_distance_left} cells away.")

            # Determine the closer direction and set the switch direction
            if nearest_distance_left < nearest_distance_right:
                switch_direction = "left"
                nearest_distance = nearest_distance_left
            elif nearest_distance_right < nearest_distance_left:
                switch_direction = "right"
                nearest_distance = nearest_distance_right
            else: #nearest_distance_right = nearest_distance_left
                nearest_distance = min(nearest_distance_left, nearest_distance_right)
                if np.random.rand() < 0.5:
                    switch_direction = "left"
                else:
                    switch_direction = "right"
                    #switch_direction = None if nearest_distance == float('inf') else "either"
            #print(f"Passenger {self.passenger_id}: The nearest vehicle is {nearest_distance} cells away on the {switch_direction}.")
            return nearest_distance, switch_direction   
        else:
            nearest_distance = None
            switch_direction = None
            #print(f"Passenger {self.passenger_id}: Passenger is either on the vehicle or has reached destination already")
            return nearest_distance, switch_direction

    def switch_sidewalk_position(self):
        """
        Update the passenger's sidewalk position based on the nearest vehicle distance and direction.
        Args:
            road_designation: Object containing road occupancy information.
            distance_within_sight: Maximum distance to check for vehicles.
        """
        # Get the nearest vehicle distance and direction
        nearest_distance, switch_direction = self.nearest_vehicle_distance(
            road_designation = self.road_designation,
            sidewalk_position = self.sidewalk_position,
            distance_within_sight = self.distance_within_sight
        )
        #print(f"Passenger {self.passenger_id}: The nearest vehicle is {nearest_distance} cells away on the {switch_direction}.")
        # Update the passenger's position based on the direction
        if switch_direction == "left":
            target_position = (self.sidewalk_position - nearest_distance) % self.sidewalk_designation.length
            if self.sidewalk_designation.occupancy[target_position] < self.sidewalk_designation.max_passengers_per_cell:
                self.sidewalk_designation.passengers[self.sidewalk_position].remove(self)
                self.sidewalk_position = target_position
                self.sidewalk_designation.passengers[self.sidewalk_position].append(self)
                #Update the number of passengers per sidewalk cell here (February 3, 2025)
                #print(f"Passenger switched {switch_direction} to position {self.sidewalk_position}.")
        elif switch_direction == "right":
            target_position = (self.sidewalk_position + nearest_distance) % self.sidewalk_designation.length
            if self.sidewalk_designation.occupancy[target_position] < self.sidewalk_designation.max_passengers_per_cell:
                self.sidewalk_designation.passengers[self.sidewalk_position].remove(self)
                self.sidewalk_position = target_position
                self.sidewalk_designation.passengers[self.sidewalk_position].append(self)
                #print(f"Passenger switched {switch_direction} to position {self.sidewalk_position}.")
        else:
            pass
        return

    def calculate_riding_time(self):
        if self.riding_status == "off":
            # print(f"The passenger arrived at its destination at time {self.arrived_at_destination_time}. It boarded the jeepney at time {self.jeep_boarding_time}")
            self.riding_time = self.arrived_at_destination_time - self.jeep_boarding_time
            # print(f"The riding time of passenger {self.passenger_id} is {self.riding_time}.")
        elif self.riding_status == "chilling":
            # print(f"Passenger {self.passenger_id} boarded the jeep at {self.jeep_boarding_time}.")
            self.riding_time = self.current_time - self.jeep_boarding_time
            # print(f"The current riding time of passenger {self.passenger_id} is {self.riding_time}. The passenger is still in the jeep.")
        elif self.riding_status is None:
            pass
            return 
        return

    def calculate_waiting_time(self):
        if self.riding_status == "chilling" or "off":
            # print(f"The passenger arrived at the sidewalk at time {self.sidewalk_entry_time}. It boarded the jeepney at time {self.jeep_boarding_time}")
            self.waiting_time = self.jeep_boarding_time - self.sidewalk_entry_time
            # print(f"Passenger {self.passenger_id} waited for {self.waiting_time} before boarding a jeepney.")
        elif self.riding_status is None:
            # print(f"The passenger arrived at the sidewalk at time {self.sidewalk_entry_time}.The current time is {self.current_time}")
            self.waiting_time = self.current_time - self.sidewalk_entry_time
            # print(f"The current waiting time of passenger {self.passenger_id} is {self.waiting_time}.")
            return

    def calculate_riding_speed(self, total_simulation_time):
        if self.riding_status == "off":
            distance_travelled = (self.road_designation.length - self.sidewalk_position) + self.destination_stop.position #Assuming the maximum number of edge crossing is 1(farthest)
            self.riding_speed = distance_travelled/total_simulation_time
        return self.riding_speed




    