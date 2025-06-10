import importlib
import os
import numpy as np
import multiprocessing as mp
from road import Road
from vehicle_sim import IntraRoadSimulator
from sidewalk import Sidewalk
from passenger_sim import Passenger_Simulator
from main_sim import IntegratedSimulator

# List of parameter files to process
param_files = ["paramsB"]

def run_simulation(trial_info):
    """Runs a single simulation trial and saves results to CSV."""
    (params_file, trial, density, kappa, arrival_rate, stop_to_stop_distance, 
     case, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows) = trial_info
    
    # Dynamically import the parameter file
    params = importlib.import_module(params_file)

    # Create sidewalk and road objects
    sidewalk = Sidewalk(length=240, width=1, max_passengers_per_cell=20)
    road_designation = Road(length=240, width=4, speed_limit=5, allowed_rows=params.allowed_rows_input)

    # Initialize simulators
    vehicle_simulator = IntraRoadSimulator(road=road_designation)
    pedestrian_simulator = Passenger_Simulator(
        sidewalk=sidewalk,
        passenger_arrival_rate=arrival_rate,
        road_designation=road_designation,
        max_passengers_per_cell=20,
        vehicle_simulator=vehicle_simulator
    )

    integrated_simulator = IntegratedSimulator(
        vehicle_simulator=vehicle_simulator,
        pedestrian_simulator=pedestrian_simulator
    )

    # Shared output folder for all scripts
    output_root = os.path.abspath(os.path.join(os.getcwd(), "..", "..", "Load Anywhere Output"))
    stop_folder = os.path.join(output_root, f"Case_{case}_StopToStop_{stop_to_stop_distance}")
    arrival_folder = os.path.join(stop_folder, f"Kappa_{kappa}", f"Density_{density}", f"PassengerRate_{arrival_rate}")

    # Create required subfolders
    subfolder_paths = {name: os.path.join(arrival_folder, name) for name in
                       ["TimestepSummary", "VehicleData", "PassengerData", "SpatioTemporal", "SidewalkPatioTemporal"]}
    for folder in subfolder_paths.values():
        os.makedirs(folder, exist_ok=True)

    # Run the simulation
    timestep_summary, passenger_data, vehicle_data, spatio_temporal, sidewalk_patio_temporal = integrated_simulator.run_simulation(
        10000, 7000, density, kappa, stop_to_stop_distance, safe_stopping_speed,
        safe_deceleration, jeepney_allowed_rows, truck_allowed_rows, visualize=False
    )

    # Save data to CSV
    filename = f"Trial_{trial}_D{density}_K{kappa}_R{arrival_rate}_S{stop_to_stop_distance}.csv"
    vehicle_data.to_csv(os.path.join(subfolder_paths["VehicleData"], filename), index=False)
    timestep_summary.to_csv(os.path.join(subfolder_paths["TimestepSummary"], filename), index=False)
    passenger_data.to_csv(os.path.join(subfolder_paths["PassengerData"], filename), index=False)
    spatio_temporal.to_csv(os.path.join(subfolder_paths["SpatioTemporal"], filename), index=False)
    sidewalk_patio_temporal.to_csv(os.path.join(subfolder_paths["SidewalkPatioTemporal"], filename), index=False)

def run_simulations_for_params(params_file):
    """Loads parameters from a file and runs all simulation trials."""
    params = importlib.import_module(params_file)
    
    # Extract parameters
    case = params.case
    safe_stopping_speed = params.safe_stopping_speed
    safe_deceleration = params.safe_deceleration
    jeepney_allowed_rows = params.jeepney_allowed_rows
    truck_allowed_rows = params.truck_allowed_rows

    # Simulation parameter ranges
    densities = [round(d, 2) for d in np.arange(0, 1.04, 0.04)]
    passenger_arrival_rates = [0.3, 1]  # 0.3 AND 1
    stop_to_stop_distances = [20]
    kappa_values = [0, 0.2, 0.4]
    num_trials = 50

    # Prepare list of trial arguments
    trial_args = [(params_file, trial, density, kappa, arrival_rate, stop_to_stop_distance, case, 
                   safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows)
                  for kappa in kappa_values
                  for density in densities
                  for arrival_rate in passenger_arrival_rates
                  for stop_to_stop_distance in stop_to_stop_distances
                  for trial in range(1, num_trials + 1)]

    # Run simulations in parallel
    num_cores = min(mp.cpu_count(), 30)  # This maximizes node capacity. Lower if needed.
    with mp.Pool(num_cores) as pool:
        pool.map(run_simulation, trial_args)

if __name__ == "__main__":
    mp.set_start_method("fork", force=True)  # Ensures proper multiprocessing (Linux/macOS)
    
    for params_file in param_files:
        run_simulations_for_params(params_file)
