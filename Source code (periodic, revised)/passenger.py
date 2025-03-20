import numpy as np

class Passenger:
    _id_counter = 0
    def __init__(self, sidewalk_entry_time, sidewalk, road_designation, sidewalk_position, destination_stop, vehicle_simulator, passenger_simulator):
        self.passenger_id = Passenger._id_counter #identifying number of each passenger
        Passenger._id_counter += 1 #increment passenger id based on order of initialization
        self.sidewalk_entry_time = sidewalk_entry_time #The time where the passenger spawned on the sidewalk
        self.sidewalk = sidewalk #passenger knows on which sidewalk he/she is
        self.road_designation = road_designation #passenger knows on what road he/she is
        self.sidewalk_position = sidewalk_position #position of passenger on sidewalk
        self.destination_stop = destination_stop #The position where the passenger wants to go
        self.last_sidewalk_position = None #The position where the passenger board the jeep
        self.jeep_boarding_time = None #The time wherein the passenger boarded the jeepney
        self.arrived_at_destination_time = None #The time when the passenger arrived at his/her destination
        self.on_vehicle = False #Determines whether the passenger is inside a vehicle or not
        self.riding_time = None #Riding time 
        self.waiting_time = 0 #Amount of time the passenger waited on the sidewalk before boarding a jeepney
        self.vehicle_simulator = vehicle_simulator 
        self.edge_crossings = 0  #Can I just make these as lists instead of attributes?
        self.edge_crossings_at_start = None
        self.riding_speed = None
        self.passenger_simulator = passenger_simulator
        self.just_boarded = None
        self.just_boarded_once = None
        self.overshot_destination = None
        self.informed_the_driver = False
        self.about_to_cross_edge = None
        self.data = {"id": self.passenger_id, "destination":self.destination_stop}
        self.let_me_out = None

    def board_vehicle(self, vehicle, current_time):
        """This logic decides if the passenger boards the vehicle if all the conditions are satisifed:
        The vehicle is a jeepney, the vehicle's speed at the current timestep is zero, and the vehicle allows loading of passengers"""
        self.on_vehicle = True
        self.last_sidewalk_position = self.sidewalk_position
        self.jeep_boarding_time = current_time
        self.riding_status = "chilling"
        self.sidewalk_position = None
        stop = self.sidewalk.stops[self.destination_stop.position][0]
        stop.unloading_dictionary[self.passenger_id] = self.data
        stop.unloading_list.append(self)
        vehicle.passengers_on_board[self.passenger_id] = self.data
        # print(f"Passenger {self.passenger_id} is in the stop : {self.sidewalk.stops[self.destination_stop.position]}")
        # print(f"Passenger {self.passenger_id} boarded {vehicle.vehicle_type} {vehicle.vehicle_id} from loading list {self.sidewalk.stops[self.destination_stop.position][0].loading_list}. ")
        # print(f"Passenger {self.passenger_id} is in {vehicle.vehicle_type} {vehicle.vehicle_id}, and in the unloading list {self.sidewalk.stops[self.destination_stop.position][0].unloading_list}. ")
        #self.sidewalk.stops[self.destination_stop.position][0].loading_list.remove(self) - not needed since pop automatically removes the passenger from the loading list
        self.passenger_simulator.waiting_passengers.remove(self)
        self.passenger_simulator.in_transit_passengers.append(self)
        #print(f"Passenger {self.passenger_id} boarded {vehicle.vehicle_type} {vehicle.vehicle_id}")
        self.just_boarded = True
        vehicle.determine_cross_edge()
        if vehicle.did_cross_edge:
            self.edge_crossings_at_start = True
            # print(f"Passenger {self.passenger_id} boarded {vehicle.vehicle_type} {vehicle.vehicle_id}, which just crossed the boundary. So, we reset edge crossings.")
        return

    def alight_vehicle(self, vehicle, current_time):
        """This method removes the passenger from the vehicle when the destination have been reached"""
        self.on_vehicle = False
        self.riding_status = "off"
        self.arrived_at_destination_time = current_time
        self.sidewalk_position = None
        # print(f"Passenger {self.passenger_id}'s destination stop is {self.destination_stop}.")
        # print(f"The destination stops by the vehicle is {vehicle.destination_stops}.")
        # print(f"Passenger {self.passenger_id} just boarded??? --- {self.just_boarded} (Should be False)")
        vehicle.destination_stops.remove(self.destination_stop)
        stop = self.sidewalk.stops[self.destination_stop.position][0]
        stop.unloading_dictionary.pop(self.passenger_id, None)
        stop.unloading_list.remove(self)
        vehicle.passengers_on_board.pop(self.passenger_id, None)
        self.passenger_simulator.in_transit_passengers.remove(self)
        self.passenger_simulator.alighted_passengers.append(self)
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
                vehicle.determine_cross_edge()
                vehicle.determine_if_about_to_cross_edge()
                if vehicle.did_cross_edge:
                    self.edge_crossings += 1
                    self.determine_edge_crossing_at_start(vehicle)
                    # print(f"Passenger {self.passenger_id} just crossed the edge. The edge crossings = {self.edge_crossings}.")
                if vehicle.about_to_cross_edge:
                    self.about_to_cross_edge = True
                    # print(f"Passenger {self.passenger_id} about to cross edge. The edge crossings = {self.edge_crossings}.")
        return


    def determine_if_just_boarded(self, vehicle):
        if self.just_boarded_once:
            return
        # Initialize occupancy array
        # print(f"Passenger {self.passenger_id} just boarded the {vehicle.vehicle_type} {vehicle.vehicle_id}.")
        position_occupancy = np.zeros(self.road_designation.length, dtype=int)

        # Mark positions in occupancy array
        position_occupancy[self.last_sidewalk_position - vehicle.length] = 1  # Last pickup spot
        # print(f"Passenger {self.passenger_id} on {vehicle.vehicle_type} that has a last loading rear position of {self.last_sidewalk_position} and current rear bumper position of {vehicle.rear_bumper_position}")
        position_occupancy[vehicle.rear_bumper_position] = 1       # Rear bumper

        # Roll the occupancy array based on the last loading position
        rolled_occupancy = np.roll(position_occupancy, -(self.last_sidewalk_position- vehicle.length))

        # Find the index of the rear bumper in the rolled array
        rear_bumper_in_rolled =np.argmax(rolled_occupancy[1:] == 1)
        # print(f"Passenger {self.passenger_id} on {vehicle.vehicle_type} that moved {rear_bumper_in_rolled} since the last loading position")

        # Check if the vehicle moved more than 2 cells
        if (rear_bumper_in_rolled) > 5 and self.just_boarded:
            # print(f"Passenger {self.passenger_id} on {vehicle.vehicle_type} moved {rear_bumper_in_rolled} since the last loading position, just boarded status becomes False.")
            self.just_boarded = False
            self.just_boarded_once = True
        return   

    def determine_if_overshot_destination(self, vehicle):
        if self.overshot_destination or self.edge_crossings == 0:
            return
        if self.let_me_out:
            previous_rear = vehicle.previous_rear_bumper_position
            current_rear = vehicle.rear_bumper_position
            destination = self.destination_stop.position

            # Check if the vehicle moved past the destination, considering periodic boundaries
            if previous_rear <= destination < current_rear or (current_rear < previous_rear and (destination >= previous_rear or destination < current_rear)):
                self.overshot_destination = True
                # print(f"Passenger {self.passenger_id} has overshot their destination at {destination}. Edge crossings --- {self.edge_crossings}")
        return

    def determine_if_let_me_out(self, vehicle):
        """This function determines if the passenger needs to alight the vehicle already"""
        if self.let_me_out:
            # print(f"Passenger {self.passenger_id} want to get out, its destination is at {self.destination_stop.position}. Overshot destination??? -- {self.overshot_destination}")
            return
        if (self.destination_stop in vehicle.destination_stops) and (self.destination_stop in vehicle.stop_list_adjacent_and_ahead) and (self.about_to_cross_edge or self.edge_crossings == 1):
            self.let_me_out = True
            # print(f"Passenger {self.passenger_id} want to get outt, its destination is at {self.destination_stop.position}.  Overshot destination??? -- {self.overshot_destination}")
        return