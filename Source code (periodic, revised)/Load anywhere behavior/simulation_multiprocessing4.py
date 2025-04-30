# import importlib
# import os
# import numpy as np
# import multiprocessing as mp
# from road import Road
# from vehicle_sim import IntraRoadSimulator
# from sidewalk import Sidewalk
# from passenger_sim import Passenger_Simulator
# from main_sim import IntegratedSimulator

# # List of parameter files to process
# param_files = ["paramsD"]

# def run_simulation(trial_info):
#     """Runs a single simulation trial and saves results to CSV."""
#     params_file, trial, density, kappa, arrival_rate, case, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows = trial_info
    
#     # Dynamically import the parameter file
#     params = importlib.import_module(params_file)

#     # Create sidewalk and road objects
#     sidewalk = Sidewalk(length=240, width=1, max_passengers_per_cell=20)
#     road_designation = Road(length=240, width=4, speed_limit=5, allowed_rows=params.allowed_rows_input)

#     # Initialize simulators
#     vehicle_simulator = IntraRoadSimulator(road=road_designation)
#     pedestrian_simulator = Passenger_Simulator(
#         sidewalk=sidewalk,
#         passenger_arrival_rate=arrival_rate,
#         road_designation=road_designation,
#         max_passengers_per_cell=20,
#         vehicle_simulator=vehicle_simulator
#     )

#     integrated_simulator = IntegratedSimulator(
#         vehicle_simulator=vehicle_simulator,
#         pedestrian_simulator=pedestrian_simulator
#     )

#     # Base directory for saving results
#     base_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
#     stop_to_stop_distance = 20
#     stop_folder = os.path.join(base_dir, f"March22_Case_{case}_StopToStop_{stop_to_stop_distance}")
#     arrival_folder = os.path.join(stop_folder, f"Kappa_{kappa}", f"Density_{density}", f"PassengerRate_{arrival_rate}")

#     # Create required subfolders
#     subfolder_paths = {name: os.path.join(arrival_folder, name) for name in
#                        ["VehicleData", "TimestepSummary", "PassengerData", "SpatioTemporal", "SidewalkPatioTemporal"]}
#     for folder in subfolder_paths.values():
#         os.makedirs(folder, exist_ok=True)

#     # Run the simulation
#     timestep_summary, passenger_data, vehicle_data, spatio_temporal, sidewalk_patio_temporal = integrated_simulator.run_simulation(
#         10000, 1, 0.1, 4000, density, kappa, 20, safe_stopping_speed,
#         safe_deceleration, jeepney_allowed_rows, truck_allowed_rows, visualize=False
#     )

#     # Save data to CSV
#     filename = f"Trial_{trial}_D{density}_K{kappa}_R{arrival_rate}.csv"
#     vehicle_data.to_csv(os.path.join(subfolder_paths["VehicleData"], filename), index=False)
#     timestep_summary.to_csv(os.path.join(subfolder_paths["TimestepSummary"], filename), index=False)
#     passenger_data.to_csv(os.path.join(subfolder_paths["PassengerData"], filename), index=False)
#     spatio_temporal.to_csv(os.path.join(subfolder_paths["SpatioTemporal"], filename), index=False)
#     sidewalk_patio_temporal.to_csv(os.path.join(subfolder_paths["SidewalkPatioTemporal"], filename), index=False)

#     #print(f"✅ Completed Trial {trial} for {params_file} - Density={density}, Kappa={kappa}, ArrivalRate={arrival_rate}")

# def run_simulations_for_params(params_file):
#     """Loads parameters from a file and runs all simulation trials."""
#     #print(f"🚀 Running simulations for {params_file}...")

#     # Dynamically import parameters
#     params = importlib.import_module(params_file)
    
#     # Extract parameters
#     case = params.case
#     safe_stopping_speed = params.safe_stopping_speed
#     safe_deceleration = params.safe_deceleration
#     jeepney_allowed_rows = params.jeepney_allowed_rows
#     truck_allowed_rows = params.truck_allowed_rows

#     # Simulation parameter ranges
#     densities = [round(d, 2) for d in np.arange(0, 1.04, 0.04)]
#     passenger_arrival_rates = [1]
#     kappa_values = [0.4]
#     num_trials = 100

#     # Prepare list of trial arguments
#     trial_args = [(params_file, trial, density, kappa, arrival_rate, case, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows)
#                   for kappa in kappa_values
#                   for density in densities
#                   for arrival_rate in passenger_arrival_rates
#                   for trial in range(1, num_trials + 1)]

#     # Run simulations in parallel
#     num_cores = min(mp.cpu_count(), 23)  # Use up to 24 cores
#     with mp.Pool(num_cores) as pool:
#         pool.map(run_simulation, trial_args)

#     #print(f"✅ All trials for {params_file} completed successfully.")

# if __name__ == "__main__":
#     mp.set_start_method("fork", force=True)  # Ensures proper multiprocessing (Linux/macOS)
    
#     for params_file in param_files:
#         run_simulations_for_params(params_file)

#--------------------IF CURRENT RUN WAS INTERRUPTED------------------------------------------------------------------------------------------------------------------

# import importlib
# import os
# import numpy as np
# import multiprocessing as mp
# from road import Road
# from vehicle_sim import IntraRoadSimulator
# from sidewalk import Sidewalk
# from passenger_sim import Passenger_Simulator
# from main_sim import IntegratedSimulator

# # List of parameter files to process
# param_files = ["paramsD"]

# def run_simulation(trial_info):
#     """Runs a single simulation trial and saves results to CSV only if not already completed."""
#     params_file, trial, density, kappa, arrival_rate, case, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows = trial_info
    
#     # Dynamically import the parameter file
#     params = importlib.import_module(params_file)

#     # Base directory for saving results
#     base_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
#     stop_to_stop_distance = 20
#     stop_folder = os.path.join(base_dir, f"March22_Case_{case}_StopToStop_{stop_to_stop_distance}")
#     arrival_folder = os.path.join(stop_folder, f"Kappa_{kappa}", f"Density_{density}", f"PassengerRate_{arrival_rate}")

#     # Check if the required output files already exist
#     filename = f"Trial_{trial}_D{density}_K{kappa}_R{arrival_rate}.csv"
#     subfolder_paths = {name: os.path.join(arrival_folder, name, filename) for name in
#                        ["VehicleData", "TimestepSummary", "PassengerData", "SpatioTemporal", "SidewalkPatioTemporal"]}
    
#     if all(os.path.exists(path) for path in subfolder_paths.values()):
#         print(f"Skipping already completed Trial {trial} - Density={density}, Kappa={kappa}, ArrivalRate={arrival_rate}")
#         return  # Skip this trial
    
#     # Create required subfolders
#     for folder in subfolder_paths.keys():
#         os.makedirs(os.path.dirname(subfolder_paths[folder]), exist_ok=True)

#     # Create sidewalk and road objects
#     sidewalk = Sidewalk(length=240, width=1, max_passengers_per_cell=20)
#     road_designation = Road(length=240, width=4, speed_limit=5, allowed_rows=params.allowed_rows_input)

#     # Initialize simulators
#     vehicle_simulator = IntraRoadSimulator(road=road_designation)
#     pedestrian_simulator = Passenger_Simulator(
#         sidewalk=sidewalk,
#         passenger_arrival_rate=arrival_rate,
#         road_designation=road_designation,
#         max_passengers_per_cell=20,
#         vehicle_simulator=vehicle_simulator
#     )

#     integrated_simulator = IntegratedSimulator(
#         vehicle_simulator=vehicle_simulator,
#         pedestrian_simulator=pedestrian_simulator
#     )

#     # Run the simulation
#     timestep_summary, passenger_data, vehicle_data, spatio_temporal, sidewalk_patio_temporal = integrated_simulator.run_simulation(
#         10000, 1, 0.1, 4000, density, kappa, 20, safe_stopping_speed,
#         safe_deceleration, jeepney_allowed_rows, truck_allowed_rows, visualize=False
#     )

#     # Save data to CSV
#     vehicle_data.to_csv(subfolder_paths["VehicleData"], index=False)
#     timestep_summary.to_csv(subfolder_paths["TimestepSummary"], index=False)
#     passenger_data.to_csv(subfolder_paths["PassengerData"], index=False)
#     spatio_temporal.to_csv(subfolder_paths["SpatioTemporal"], index=False)
#     sidewalk_patio_temporal.to_csv(subfolder_paths["SidewalkPatioTemporal"], index=False)

#     #print(f"✅ Completed Trial {trial} - Density={density}, Kappa={kappa}, ArrivalRate={arrival_rate}")

# def run_simulations_for_params(params_file):
#     """Loads parameters from a file and runs only missing simulation trials."""
#     print(f"🚀 Resuming simulations for {params_file}...")

#     # Dynamically import parameters
#     params = importlib.import_module(params_file)

#     # Extract parameters
#     case = params.case
#     safe_stopping_speed = params.safe_stopping_speed
#     safe_deceleration = params.safe_deceleration
#     jeepney_allowed_rows = params.jeepney_allowed_rows
#     truck_allowed_rows = params.truck_allowed_rows

#     # Simulation parameter ranges
#     densities = [round(d, 2) for d in np.arange(0, 1.04, 0.04)]
#     passenger_arrival_rates = [1]
#     kappa_values = [0.4]
#     num_trials = 100

#     # Base directory for checking existing files
#     base_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
#     stop_to_stop_distance = 20

#     # Prepare list of only missing trials
#     trial_args = []
#     for kappa in kappa_values:
#         for density in densities:
#             for arrival_rate in passenger_arrival_rates:
#                 for trial in range(1, num_trials + 1):
#                     # Define the trial's output path
#                     stop_folder = os.path.join(base_dir, f"March22_Case_{case}_StopToStop_{stop_to_stop_distance}")
#                     arrival_folder = os.path.join(stop_folder, f"Kappa_{kappa}", f"Density_{density}", f"PassengerRate_{arrival_rate}")
#                     filename = f"Trial_{trial}_D{density}_K{kappa}_R{arrival_rate}.csv"
#                     subfolder_paths = {name: os.path.join(arrival_folder, name, filename) for name in
#                                        ["VehicleData", "TimestepSummary", "PassengerData", "SpatioTemporal", "SidewalkPatioTemporal"]}

#                     # Only add trials that are missing
#                     if not all(os.path.exists(path) for path in subfolder_paths.values()):
#                         trial_args.append((params_file, trial, density, kappa, arrival_rate, case, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows))

#     # If all trials are complete, exit early
#     if not trial_args:
#         print(f"✅ All trials for {params_file} are already complete.")
#         return

#     # Run remaining simulations in parallel
#     num_cores = min(mp.cpu_count(), 30)  # Use up to 23 cores
#     with mp.Pool(num_cores) as pool:
#         pool.map(run_simulation, trial_args)

#     #print(f"✅ Remaining trials for {params_file} completed successfully.")

# if __name__ == "__main__":
#     mp.set_start_method("fork", force=True)  # Ensures proper multiprocessing (Linux/macOS)
    
#     for params_file in param_files:
#         run_simulations_for_params(params_file)

#---------------------------------VARY STOP TO STOP DISTANCE -----------------------------------------------------------------------------
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
param_files = ["paramsD"]

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

    # Base directory for saving results
    base_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
    stop_folder = os.path.join(base_dir, f"March26(Vehicle and Timestep)_Case_{case}_StopToStop_{stop_to_stop_distance}")
    arrival_folder = os.path.join(stop_folder, f"Kappa_{kappa}", f"Density_{density}", f"PassengerRate_{arrival_rate}")

    # Create required subfolders
    subfolder_paths = {name: os.path.join(arrival_folder, name) for name in
                       ["VehicleData", "TimestepSummary", "PassengerData", "SpatioTemporal", "SidewalkPatioTemporal"]}
    for folder in subfolder_paths.values():
        os.makedirs(folder, exist_ok=True)

    # Run the simulation
    timestep_summary, passenger_data, vehicle_data, spatio_temporal, sidewalk_patio_temporal = integrated_simulator.run_simulation(
        10000, 7000, density, kappa, stop_to_stop_distance, safe_stopping_speed,
        safe_deceleration, jeepney_allowed_rows, truck_allowed_rows, visualize=False
    )

    # Save data to CSV
    filename = f"Trial_{trial}_D{density}_K{kappa}_R{arrival_rate}.csv"
    vehicle_data.to_csv(os.path.join(subfolder_paths["VehicleData"], filename), index=False)
    timestep_summary.to_csv(os.path.join(subfolder_paths["TimestepSummary"], filename), index=False)
    #passenger_data.to_csv(os.path.join(subfolder_paths["PassengerData"], filename), index=False)
    #spatio_temporal.to_csv(os.path.join(subfolder_paths["SpatioTemporal"], filename), index=False)
    #sidewalk_patio_temporal.to_csv(os.path.join(subfolder_paths["SidewalkPatioTemporal"], filename), index=False)

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
    passenger_arrival_rates = [0.3]#0.3 AND 1
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
    num_cores = min(mp.cpu_count(), 9)
    with mp.Pool(num_cores) as pool:
        pool.map(run_simulation, trial_args)

if __name__ == "__main__":
    mp.set_start_method("fork", force=True)  # Ensures proper multiprocessing (Linux/macOS)
    
    for params_file in param_files:
        run_simulations_for_params(params_file)
