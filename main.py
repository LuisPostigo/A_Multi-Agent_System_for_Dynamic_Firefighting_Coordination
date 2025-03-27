import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from agents.tree_agent import Tree

import agentpy as ap
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import IPython

from ForestModel import ForestModel

def animation_plot(model, ax):
    attr_grid = np.full((model.p.size, model.p.size), np.nan)
    for tree in model.trees:
        pos = model.grid.positions[tree]
        attr_grid[pos] = tree.condition

    color_dict = {
        0: '#7FC97F',
        1: '#d62c2c',
        2: '#e5e5e5',
        None: '#d5e5d5'
    }
    ap.gridplot(attr_grid, ax=ax, color_dict=color_dict, convert=True)

    for pos, timestamp in model.water_splashes:
        if model.t - timestamp < 5:
            ax.scatter(pos[1], pos[0], color='white', s=20, marker='o', alpha=0.9)

    for firefighter in model.firefighters:
        pos = model.grid.positions[firefighter]
        halo = plt.Circle((pos[1], pos[0]), firefighter.sensor_range, color='cyan', alpha=0.2)
        ax.add_patch(halo)
        ax.text(pos[1], pos[0], f"{firefighter.firefighter_id}", color='blue',
                fontsize=5, fontweight='bold', ha='center', va='center')

    for drone in model.drones:
        pos = model.grid.positions[drone]
        halo = plt.Circle((pos[1], pos[0]), drone.sensor_range, color='yellow', alpha=0.1)
        ax.add_patch(halo)
        ax.scatter(pos[1], pos[0], color='yellow', s=50, marker='D')
        ax.text(pos[1], pos[0], drone.drone_id, color='orange', fontsize=9,
                ha='center', va='center', fontweight='bold')

    alive_trees = len(model.trees.select(model.trees.condition == 0))
    ax.set_title(f"Forest Fire Simulation\nTime-step: {model.t}, Trees left: {alive_trees}")


parameters = {
    'Tree density': 0.75,
    'probSpread': 0.08,
    'tree_burn_time': 8,
    'tree_growth_rate': 0.01,
    'humidity': 0.3,
    'southWindSpeed': 1,
    'westWindSpeed': 1,
    'bigJump': False,
    'size': 50,
    'steps': 200,
    'seed': 0,
    'num_firefighters': 30,
    'max_water': 50,
    'sensor_range': 2,
    'base_speed': 3,
    'extinguish_time': 1,
    'num_drones': 5,
    'drone_max_water': 30,
    'drone_speed': 3,
    'drone_sensor_range': 7,
    'drone_max_battery': 80,
    'drone_battery_warning': 10,
    'drone_extinguish_time': 1,
    'drone_water_drop': 5,
    'debug_mode': True
}


log_model = ForestModel(parameters)
log_model.run()

if log_model.firefighter_debug_logs:
    ff_logs = [
        {
            "firefighter_id": log["firefighter_id"],
            "detected_fires": ";".join([f"({x},{y})" for x, y in log["detected_fires"]]),
            "time": log["time"]
        }
        for log in log_model.firefighter_debug_logs if "detected_fires" in log
    ]
    if ff_logs:
        pd.DataFrame(ff_logs).to_csv("firefighter_fire_logs.csv", index=False)
        print("✅ Firefighter perception logs exported to 'firefighter_fire_logs.csv'")
    else:
        print("⚠️ No firefighter detections to export.")

if log_model.drone_debug_logs:
    pd.DataFrame(log_model.drone_debug_logs).to_csv("drone_fire_logs.csv", index=False)
    print("✅ Drone detection logs exported to 'drone_fire_logs.csv'")
else:
    print("⚠️ No drone detections to log.")

if log_model.contract_logs:
    pd.DataFrame(log_model.contract_logs).to_csv("cnp_contract_logs.csv", index=False)
    print("✅ CNP contract logs exported to 'cnp_contract_logs.csv'")
else:
    print("⚠️ No contract log entries to export.")

if hasattr(log_model, "position_logs") and log_model.position_logs:
    pd.DataFrame(log_model.position_logs).to_csv("position_logs.csv", index=False)
    print("✅ Agent position logs exported to 'position_logs.csv'")
else:
    print("⚠️ No position logs to export.")

for f in log_model.firefighters:
    print(f"{f.firefighter_id} final position: {log_model.grid.positions[f]}")

print("🔥 Total contracts created:", len(log_model.fire_contracts))


fig, ax = plt.subplots()
visual_model = ForestModel(parameters)
animation = ap.animate(visual_model, fig, ax, animation_plot)
IPython.display.display(IPython.display.HTML(animation.to_jshtml(fps=15)))


logs = pd.DataFrame(log_model.contract_logs)

total = logs[logs["event"] == "created"]["task_id"].nunique()
completed = logs[logs["event"] == "complete"]["task_id"].nunique()
print(f"🧯 Completion Rate: {completed}/{total} ({completed/total:.2%})")

created = logs[logs["event"] == "created"]
avg_team = created["team_size"].mean()
avg_cluster = created["cluster_size"].mean()
print(f"👥 Avg. Team Size: {avg_team:.2f}, Avg. Cluster Size: {avg_cluster:.2f}")

assign = logs[logs["event"] == "assignment"]
complete = logs[logs["event"] == "complete"]
merged = pd.merge(assign, complete, on="task_id", suffixes=("_assign", "_complete"))
merged["time_to_extinguish"] = merged["time_complete"] - merged["time_assign"]
print(f"⏱️ Avg Time to Extinguish: {merged['time_to_extinguish'].mean():.2f} steps")

idle_data = [
    (ff.firefighter_id, log_model.t - ff.active_timesteps)
    for ff in log_model.firefighters
]
idle_df = pd.DataFrame(idle_data, columns=["firefighter_id", "idle_timesteps"])
print(idle_df.sort_values("idle_timesteps", ascending=False))