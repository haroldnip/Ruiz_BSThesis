class Counter:
    def __init__(self):
        #self.position = position  # The position where we count vehicles
        self.total_vehicles = 0   # Total vehicles passing through the position
        self.passenger_throughput = 0
        self.total_jeeps = 0
        self.total_trucks = 0

    def count_vehicle(self, vehicle):
        # Check if the vehicle has crossed the position 99 at this timestep
        if vehicle.rear_bumper_position < vehicle.previous_rear_bumper_position:
            self.total_vehicles += 1
    
    def count_passenger(self, vehicle):
        if vehicle.rear_bumper_position < vehicle.previous_rear_bumper_position:
            self.passenger_throughput += vehicle.occupied_seats

    def count_jeeps(self, vehicle):
        if vehicle.rear_bumper_position < vehicle.previous_rear_bumper_position:
            if vehicle.vehicle_type == "jeep":
                self.total_jeeps += 1

    def count_trucks(self, vehicle):
        if vehicle.rear_bumper_position < vehicle.previous_rear_bumper_position:
            if vehicle.vehicle_type == "truck":
                self.total_trucks += 1

    def calculate_vehicle_throughput(self):
        return self.total_vehicles

    def calculate_passenger_throughput(self):
        return self.passenger_throughput

    def calculate_jeep_throughput(self):
        return self.total_jeeps

    def calculate_truck_throughput(self):
        return self.total_trucks

    def reset_counting(self):
        self.total_vehicles = 0
        self.passenger_throughput = 0
        self.total_jeeps = 0
        self.total_trucks = 0