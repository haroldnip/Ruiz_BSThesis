from road import Road
from vehicle_sim import IntraRoadSimulator
from sidewalk import Sidewalk #Passenger
from passenger_sim import Passenger_Simulator
from main_sim import IntegratedSimulator
import os
import pandas as pd

allowed_rows_input = [
    (0, {"truck", "jeep"}), # Row 0 allowed for lane changing
    (1, {"truck", "jeep"}),  
    (2, {"truck", "jeep"})  # Row 2 allowed for lane changing
]
jeepney_allowed_rows = [0, 2] #allowed rows for initialization
truck_allowed_rows = [0, 2]  #allowed rows for initialization
safe_stopping_speed = 2
safe_deceleration = 2

case = "A"

# Create the sidewalk and road designations (for both pedestrian and vehicle simulators)
sidewalk = Sidewalk(length=100, width=1, max_passengers_per_cell=5)
road_designation = Road(length=100, width=4,speed_limit=5, allowed_rows = allowed_rows_input)
print(f"The allowed rows for each vehicle are {road_designation.allowed_rows}")
# Initialize the vehicle simulator (intra-road simulator) with required parameters
vehicle_simulator = IntraRoadSimulator(road=road_designation)

# Initialize the pedestrian simulator
pedestrian_simulator = Passenger_Simulator(
    sidewalk = sidewalk,
    passenger_arrival_rate = 1,  # Arrival rate of passengers per timestep
    road_designation=road_designation,
    max_passengers_per_cell=5,
    vehicle_simulator=vehicle_simulator  # Pass the vehicle simulator to handle interactions
)

# Now, initialize the integrated simulator with both simulators
integrated_simulator = IntegratedSimulator(
    vehicle_simulator=vehicle_simulator,
    pedestrian_simulator=pedestrian_simulator)



#------------------------------RUN THE SIMULATION OVER 50 TRIALS----------------------------------------------------------------------------
import os

# Define the base directory (one level above the notebook folder)
base_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))  # Moves one directory up

# Define folder names outside the notebook folder, including the new "SidewalkPatio_temporal" folder
folders = [
    "VehicleData_test",
    "TimestepSummary_test",
    "PassengerData_test",
    "Spatio-Temporal_test",
    "SidewalkPatio_temporal"  # New folder added
]

# Create a dictionary of folder paths
folder_paths = {folder: os.path.join(base_dir, folder) for folder in folders}

# Ensure directories exist
for path in folder_paths.values():
    os.makedirs(path, exist_ok=True)

# Number of trials
num_trials = 1
density = 0.4
truck_fraction = 0.2

# Loop over trials
for trial in range(1, num_trials + 1):
    # Generate dummy DataFrames (replace with actual simulation data)
    timestep_summary, passenger_data, vehicle_data, spatio_temporal, sidewalk_patio_temporal = integrated_simulator.run_simulation(
        6000, 1, 0.1, 1000, density, truck_fraction, 1, safe_stopping_speed,
        safe_deceleration, jeepney_allowed_rows, truck_allowed_rows, visualize=False
    )

    # File paths (outside the notebook folder)
    vehicle_file = os.path.join(folder_paths["VehicleData_test"], f"Trial_{trial}Mar14(density={density}, truck_fraction={truck_fraction}).csv")
    timestep_file = os.path.join(folder_paths["TimestepSummary_test"], f"Trial_{trial}Mar14(density={density}, truck_fraction={truck_fraction}).csv")
    passenger_file = os.path.join(folder_paths["PassengerData_test"], f"Trial_{trial}Mar14(density={density}, truck_fraction={truck_fraction}).csv")
    spatio_temporal_file = os.path.join(folder_paths["Spatio-Temporal_test"], f"Trial_{trial}Mar14(density={density}, truck_fraction={truck_fraction}).csv")
    sidewalk_patio_file = os.path.join(folder_paths["SidewalkPatio_temporal"], f"Trial_{trial}Mar14(density={density}, truck_fraction={truck_fraction}).csv")

    # Save CSV files
    vehicle_data.to_csv(vehicle_file, index=False)
    timestep_summary.to_csv(timestep_file, index=False)
    passenger_data.to_csv(passenger_file, index=False)
    spatio_temporal.to_csv(spatio_temporal_file, index=False)
    sidewalk_patio_temporal.to_csv(sidewalk_patio_file, index=False)  # New file save

    print(f"Saved Trial {trial} data.")

print("All trials completed successfully.")