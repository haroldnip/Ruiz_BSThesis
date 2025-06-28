# 🚗 Heterogeneous Vehicle Simulation

This repository contains the source code for simulating heterogeneous traffic involving **trucks** and **jeepneys**, including passenger behavior and stop configurations.

## ⚠️ Caution: High Computational Load

This simulation is **computationally expensive**. With the current parameters set in the multiprocessing scripts, it can generate output files up to **~100 GB** in size.

- Visualizations are included in the simulation outputs.
- **CSV output files are not uploaded** to this repository due to their large size.

---

## 🚦 Load-Anywhere Behavior

Each script simulates a different implementation of lane usage for public transport (PT). Run the appropriate file based on the desired lane policy:

| Script Name                        | Description                                                       |
|-----------------------------------|-------------------------------------------------------------------|
| `simulation_multiprocessing.py`   | Control setup (baseline)                                          |
| `simulation_multiprocessing2.py`  | Outer lane truck ban; both lanes open to jeepneys                 |
| `simulation_multiprocessing3.py`  | Inner lane jeepney ban; both lanes open to trucks                 |
| `simulation_multiprocessing4.py`  | Mutually exclusive lanes for trucks and jeepneys                  |

---

## 🚏 Evenly-Spaced Stops

To simulate evenly spaced stops, run the versions of the above scripts with `_evenly_spaced_stops` appended to the filenames. For example:

```bash
python simulation_multiprocessing_evenly_spaced_stops.py
