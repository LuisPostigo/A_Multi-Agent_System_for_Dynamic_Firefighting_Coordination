import agentpy as ap
import numpy as np

from agents.tree_agent import Tree

class Firefighter(ap.Agent):
    def setup(self):
        self.position_logs = []
        self.active_timesteps = 0
        self.grid = self.model.grid
        self.random = self.model.random
        self.water_supply = self.p.max_water
        self.speed = self.p.base_speed
        self.sensor_range = self.p.sensor_range
        self.extinguishing_time = 0
        self.base_station = None
        self.debug = getattr(self.p, "debug_mode", True)

    def on_add(self):
        self.base_station = self.grid.positions[self]

    def move_towards_fire(self, target_pos):
        my_pos = np.array(self.grid.positions[self])
        direction = np.array(target_pos) - my_pos
        new_pos = my_pos + np.sign(direction) * self.speed
        new_pos = (int(new_pos[0]), int(new_pos[1]))
        if (0 <= new_pos[0] < self.p.size) and (0 <= new_pos[1] < self.p.size):
            if not self.grid.agents[new_pos]:
                self.grid.move_to(self, new_pos)

    def extinguish_fire(self, tree):
        if self.water_supply > 0 and self.extinguishing_time == 0:
            self.extinguishing_time = self.p.extinguish_time
        if self.extinguishing_time > 0:
            self.extinguishing_time -= 1
            if self.extinguishing_time == 0:
                tree.condition = 2
                self.water_supply -= 1
                self.model.water_splashes.append((self.grid.positions[tree], self.model.t))
                if self.debug:
                    self.model.firefighter_debug_logs.append({
                        "firefighter_id": self.firefighter_id,
                        "fire_x": self.grid.positions[tree][0],
                        "fire_y": self.grid.positions[tree][1],
                        "time": self.model.t
                    })

    def refill_water(self):
        if self.grid.positions[self] == self.base_station:
            self.water_supply = self.p.max_water

    def step(self):
        my_pos = np.array(self.grid.positions[self])

        self.model.position_logs.append({
            "time": self.model.t,
            "agent_id": self.firefighter_id,
            "type": "firefighter",
            "x": int(my_pos[0]),
            "y": int(my_pos[1])
        })

        if self.water_supply == 0:
            self.refill_water()
            return

        assigned_contracts = [
            c for c in self.model.fire_contracts
            if self.firefighter_id in c.get("assigned", []) and c["status"] == "assigned"
        ]

        if not assigned_contracts:
            for contract in self.model.fire_contracts:
                if contract["status"] == "open":
                    if any(b["firefighter_id"] == self.firefighter_id for b in contract["bids"]):
                        continue
                    dist = np.linalg.norm(my_pos - np.array(contract["location"]))
                    bid_value = dist / (self.water_supply + 1e-5)
                    contract["bids"].append({
                        "firefighter_id": self.firefighter_id,
                        "bid": bid_value,
                        "distance": dist,
                        "water": self.water_supply,
                        "time": self.model.t
                    })
                    self.model.contract_logs.append({
                        "event": "bid",
                        "task_id": contract["task_id"],
                        "firefighter_id": self.firefighter_id,
                        "bid": bid_value,
                        "distance": dist,
                        "water": self.water_supply,
                        "time": self.model.t
                    })

        if assigned_contracts:
            contract = assigned_contracts[0]
            cluster = contract.get("cluster", [contract["location"]])
            burning_cluster = [
                t for t in self.model.trees
                if self.grid.positions[t] in cluster and t.condition == 1
            ]
            if burning_cluster:
                closest = min(burning_cluster, key=lambda t: np.linalg.norm(my_pos - np.array(self.grid.positions[t])))
                target_pos = self.grid.positions[closest]
                if np.linalg.norm(my_pos - target_pos) > self.sensor_range:
                    self.move_towards_fire(target_pos)
                else:
                    self.extinguish_fire(closest)
            else:
                contract["status"] = "complete"
                self.model.contract_logs.append({
                    "event": "complete",
                    "task_id": contract["task_id"],
                    "firefighter_id": self.firefighter_id,
                    "location": contract["location"],
                    "time": self.model.t
                })

        local_fires = [
            tree for tree in self.model.trees
            if isinstance(tree, Tree) and tree.condition == 1 and
            np.linalg.norm(np.array(self.grid.positions[tree]) - my_pos) <= self.sensor_range
        ]

        if self.debug and local_fires:
            fire_positions = [self.grid.positions[tree] for tree in local_fires]
            self.model.firefighter_debug_logs.append({
                "firefighter_id": self.firefighter_id,
                "detected_fires": fire_positions,
                "time": self.model.t
            })

        if local_fires:
            self.active_timesteps += 1
            closest = min(local_fires, key=lambda t: np.linalg.norm(np.array(self.grid.positions[t]) - my_pos))
            target_pos = self.grid.positions[closest]
            self.move_towards_fire(target_pos)
            if np.linalg.norm(np.array(target_pos) - my_pos) <= self.sensor_range:
                self.extinguish_fire(closest)
            return

        rand_pos = (self.random.randint(0, self.p.size), self.random.randint(0, self.p.size))
        self.move_towards_fire(rand_pos)