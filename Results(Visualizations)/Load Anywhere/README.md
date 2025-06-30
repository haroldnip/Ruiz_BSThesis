# Traffic Simulation Visualizations and Analysis

This directory contains visualizations and analysis outputs from traffic simulations focused on **passenger travel times** and **truck speeds**. Simulations are parameterized by:

- **Truck Fraction**
- **Vehicle Density**
- **Passenger Arrival Rates**

Each subfolder corresponds to a specific aspect of the analysis for different public transport lane implementation cases.

---

## 1. Convergence of Simulations

This folder contains time series plots of **vehicle spatial mean speeds** and shows how the **variance across trials** decreases as the number of trials increases. This is used to verify simulation convergence.

- **Notebook**: `Convergence_Plots_Generators.ipynb`
- **Output**: Folders named using the parameter values in the format:  
  `plots_by_case_K<kappa>_R<rate>_D<density>`,  
  e.g., `plots_by_case_K0.6_R0.1_D0.2`.

---

## 2. Determine Actual Densities

Due to vehicle heterogeneity (e.g., differences in vehicle sizes), the **actual density** on the road may exceed the **target density** during initialization. For example, a target of `D = 0.68` might result in an actual value of `D = 0.75`.

- This folder includes a notebook that:
  - Computes the **actual densities** achieved during initialization.
  - Outputs the actual values to be used when **reporting results**.
- **Note**: Target density values are used in filenames and folder labels for consistency.

---

## 3. Fundamental Diagrams of Traffic Flow

This folder contains tools and output for generating fundamental diagrams showing the relationship between **flow**, **density**, and **speed**.

- **Notebook**: `Fundamental_Diagram_Generator.ipynb`
- **Output Folder**: `Flow Summary at T = 9999`

These diagrams summarize system behavior at the final timestep.

---

## 4. Relative Travel Delay

This folder provides visualizations comparing **average passenger travel times** under various public transport lane implementations relative to a baseline (e.g., fully mixed traffic).

- Helps identify whether dedicated lanes or policies lead to improvements or delays in passenger travel.

---

## 5. Spatial Mean Speed of Trucks

Contains plots of **spatial mean speeds** for trucks, calculated across space at each timestep.

- Useful for analyzing how lane configurations affect **truck mobility and traffic fluidity**.

---

## 6. Temporal Mean Speed of Trucks

This folder shows **temporal mean speeds** of trucks, averaged over time.

- Offers insight into time-based performance metrics, such as how long a truck takes to complete a full loop of the road.

---

## 7. Waiting Times

Includes plots and statistics on **passenger waiting times** before boarding a vehicle.

- Displays both **distribution** and **summary statistics**.
- Useful for evaluating **service accessibility and passenger experience**.

---

## Notes

- File and folder names use **target parameters** for clarity and reproducibility.
- For reporting and interpretation, use the **actual values** derived from the provided notebooks.
