# A Multi-Agent System for Dynamic Firefighting Coordination

<div align="center">

![Forest Fire Simulation](assets/model_demo.png)
  
| 🧯 Completion Rate | 👥 Avg. Team Size | 🌲 Avg. Cluster Size | ⏱️ Avg Extinguish Time |
|-------------------|------------------|----------------------|------------------------|
| **89.5%**         | **1.17**         | **1.72**             | **8.23 steps**         |

| 🕰️ Most Idle Firefighter | 🚫 Collisions Detected | 🚀 Peak System Throughput |
|--------------------------|------------------------|----------------------------|
| **F2 (10 steps)**        | **2 (worst case)**     | **5 fires/timestep**       |

</div>

---

## 🌍 Overview

This simulation models a forest environment with intelligent, decentralized agents working to detect and extinguish wildfires. It includes two types of agents:

- **🚒 Firefighters:** Ground-based agents with limited range and water supply.  
- **🚁 Drones:** Aerial scouts that detect fires, cluster hotspots, and coordinate task allocation using the **Contract-Net Protocol (CNP)**.

The simulation runs on a grid-based environment using `agentpy`, and tracks dynamic interactions including perception, bidding, movement, collision, and fire suppression—all in real-time.

---

## 🧠 Architecture: Contract-Net Protocol (CNP)

Drones manage the negotiation lifecycle. Firefighters respond with context-aware bids. This results in dynamic, distributed task allocation.

### 🔁 The CNP loop:
1. **Detection:** Drones patrol and detect fire clusters via BFS.
2. **Contract Creation:** Each cluster becomes a structured JSON task with a `team_size` based on fire size.
3. **Bidding:** Firefighters evaluate contracts using a spatial utility model:  
   `bid = distance_to_fire / (water + ε)`
4. **Assignment:** The drone assigns the lowest bidders, proportional to the needed team size.
5. **Execution:** Firefighters navigate, extinguish, and mark contracts complete.

All actions are logged, time-stamped, and stored in `cnp_contract_logs.csv` for analysis.

---

## 📊 Performance Visualizations

Six performance metrics are computed per run and plotted automatically:

| Metric | Visualized As |
|--------|----------------|
| 🔥 Response Time | Histogram (fire detection ➝ assignment) |
| ⏱️ Extinguish Time | Histogram (detection ➝ fire put out) |
| 💧 Resource Use | Bar plot (team size per fire) |
| 📦 Task Allocation Efficiency | Line plot (assignments over time) |
| 🧍‍♂️ Collision Count | Line plot (collisions per timestep) |
| 📈 System Throughput | Line plot (fires completed per timestep) |

---

## ⚙️ How to Run

Follow these steps to set up and run the project on your local machine:



### 1. Clone the Repository

```bash
git clone https://github.com/LuisPostigo/A_Multi-Agent_System_for_Dynamic_Firefighting_Coordination.git
cd A_Multi-Agent_System_for_Dynamic_Firefighting_Coordination
```



### 2. Create a Virtual Environment (no conda)

```bash
python -m venv MAS_Dynamic_Firefighting_Coordination
```



### 3. Activate the Virtual Environment

- **macOS/Linux:**
  ```bash
  source MAS_Dynamic_Firefighting_Coordination/bin/activate
  ```

- **Windows (CMD):**
  ```cmd
  MAS_Dynamic_Firefighting_Coordination\Scripts\activate.bat
  ```

- **Windows (PowerShell):**
  ```powershell
  .\MAS_Dynamic_Firefighting_Coordination\Scripts\Activate.ps1
  ```



### 4. Install Dependencies

```bash
pip install -r requirements.txt
```



### 5. Run the Model

```bash
python main.py
```



### (Optional) Deactivate the Environment When Done

```bash
deactivate
```
