import importlib
import os
import numpy as np
import multiprocessing as mp
from road import Road
from vehicle_sim import IntraRoadSimulator
from sidewalk import Sidewalk
from passenger_sim import Passenger_Simulator
from main_sim import IntegratedSimulator


def get_per_stop_arrival_rates(road_length, base_stop_spacing, base_arrival_rate, stop_spacings, verbose=True):
    """
    Compute passenger arrival rates per stop spacing.
    All arrival rates are considered valid and returned.
    Returns a list of tuples: (stop_spacing, arrival_rate).
    """
    num_base_stops = road_length // base_stop_spacing
    total_arrival_rate = num_base_stops * base_arrival_rate
    results = []

    if verbose:
        #print(f"{'Stop Spacing':<13} | {'Num Stops':<10} | Arrival Rate per Stop")
        #print("-" * 45)
        pass

    for spacing in stop_spacings:
        num_stops = road_length // spacing
        if num_stops == 0:
            continue
        arrival_rate_per_stop = total_arrival_rate / num_stops

        if verbose:
            #print(f"{spacing:<13} | {num_stops:<10} | {arrival_rate_per_stop:.4f}")
            pass
        results.append((spacing, round(arrival_rate_per_stop, 4)))

    return results


def run_simulation(trial_info):
    """
    Run a single simulation trial and save results to CSV files.
    trial_info is a tuple of all needed parameters.
    """
    (params_file, trial, density, kappa, stop_to_stop_distance, arrival_rate,
     case, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows) = trial_info

    # Import parameters dynamically
    params = importlib.import_module(params_file)

    # Create sidewalk and road objects
    sidewalk = Sidewalk(length=240, width=1, max_passengers_per_cell=20)
    road = Road(length=240, width=4, speed_limit=5, allowed_rows=params.allowed_rows_input)

    # Initialize simulators
    vehicle_sim = IntraRoadSimulator(road=road)
    passenger_sim = Passenger_Simulator(
        sidewalk=sidewalk,
        passenger_arrival_rate=arrival_rate,
        road_designation=road,
        max_passengers_per_cell=20,
        vehicle_simulator=vehicle_sim
    )
    integrated_sim = IntegratedSimulator(vehicle_simulator=vehicle_sim, pedestrian_simulator=passenger_sim)

    # Setup output folder structure
    base_dir = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))
    stop_folder = os.path.join(
        base_dir,
        f"With_Designated_Stops_Case_{case}_StopToStop_{stop_to_stop_distance}_Evenly_Spaced_Stops"
    )
    arrival_folder = os.path.join(stop_folder, f"Kappa_{kappa}", f"Density_{density}", f"PassengerRate_{arrival_rate:.3f}")

    subfolders = [ "TimestepSummary","VehicleData","PassengerData", "SpatioTemporal", "SidewalkPatioTemporal" ]

    for folder in subfolders:
        os.makedirs(os.path.join(arrival_folder, folder), exist_ok=True)

    # Run simulation for fixed timesteps (example: 10,000 total, 7,000 burn-in)
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

def run_simulations_for_params(params_file, verbose=True):
    """
    Prepare and run simulation trials for given parameter file.
    """
    params = importlib.import_module(params_file)

    road_length = 240
    base_stop_spacing = 20

    base_arrival_rates = [0.15, 1]  # Multiple base passenger arrival rates
    spacing_values = [20, 40, 60, 80, 120]
    density_values = [0.2, 0.48, 0.64]
    kappa_values = [0, 0.2, 0.4]
    num_trials = 50

    case = params.case
    safe_stopping_speed = params.safe_stopping_speed
    safe_deceleration = params.safe_deceleration
    jeepney_allowed_rows = params.jeepney_allowed_rows
    truck_allowed_rows = params.truck_allowed_rows

    trial_args = []

    for base_arrival in base_arrival_rates:
        if verbose:
            #print(f"\nCalculating adjusted arrival rates for base arrival rate = {base_arrival}...")
            pass
        stop_arrival_table = get_per_stop_arrival_rates(
            road_length, base_stop_spacing, base_arrival, spacing_values, verbose=verbose
        )

        for density in density_values:
            for kappa in kappa_values:
                for stop_to_stop_dist, arrival_rate in stop_arrival_table:
                    for trial in range(1, num_trials + 1):
                        trial_args.append((
                            params_file, trial, density, kappa, stop_to_stop_dist, arrival_rate,
                            case, safe_stopping_speed, safe_deceleration, jeepney_allowed_rows, truck_allowed_rows
                        ))

    # Run all trials in parallel
    num_cores = min(mp.cpu_count(), 30)
    if verbose:
        #print(f"\nStarting simulations with {num_cores} parallel workers...")
        pass
    with mp.Pool(num_cores) as pool:
        pool.map(run_simulation, trial_args)
    if verbose:
        #print("All simulations completed.")
        pass


if __name__ == "__main__":
    try:
        mp.set_start_method("fork", force=True)
    except RuntimeError:
        pass

    param_files = ["paramsD"]  # Add more param files if needed
    for param_file in param_files:
        run_simulations_for_params(param_file, verbose=True)

