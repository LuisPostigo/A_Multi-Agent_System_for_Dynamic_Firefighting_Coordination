import agentpy as ap

import numpy as np
from collections import deque

from agents.tree_agent import Tree

class Drone(ap.Agent):
    def setup(self):
        self.drone_id = id(self)
        self.debug = getattr(self.p, "debug_mode", False)

        self.grid = self.model.grid
        self.random = self.model.random
        self.speed = self.p.drone_speed
        self.sensor_range = self.p.drone_sensor_range
        self.battery = self.p.drone_max_battery
        self.battery_warning = self.p.drone_battery_warning

        self.base_station = (self.p.size - 1, self.p.size - 1)

        if not hasattr(self, 'row_min'):
            self.row_min, self.row_max = 0, self.p.size - 1
            self.col_min, self.col_max = 0, self.p.size - 1

        self.target = self.random_target_in_quadrant()

    def random_target_in_quadrant(self):
        row = self.random.randint(self.row_min, self.row_max + 1)
        col = self.random.randint(self.col_min, self.col_max + 1)
        return (row, col)

    def is_at_position(self, pos, threshold=1):
        my_pos = np.array(self.grid.positions[self])
        return np.linalg.norm(my_pos - np.array(pos)) < threshold

    def move_towards(self, target_pos):
        my_pos = np.array(self.grid.positions[self])
        target = np.array(target_pos)
        direction = target - my_pos

        if np.linalg.norm(direction) <= self.speed:
            new_pos = target
        else:
            new_pos = my_pos + np.sign(direction) * self.speed

        new_pos = np.clip(new_pos, 0, self.p.size - 1)
        self.battery -= np.linalg.norm(my_pos - new_pos)
        self.grid.move_to(self, tuple(new_pos.astype(int)))

    def return_to_base(self):
        if self.is_at_position(self.base_station):
            self.grid.move_to(self, self.base_station)
            self.battery = self.p.drone_max_battery
            self.target = self.random_target_in_quadrant()
        else:
            self.move_towards(self.base_station)

    def contract_exists(self, pos):
        return any(
            c["location"] == pos and c["status"] != "complete"
            for c in self.model.fire_contracts
        )

    def cluster_fires(self, fire_positions):
        visited = set()
        clusters = []

        def neighbors(pos):
            x, y = pos
            return [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]

        for fire in fire_positions:
            if fire in visited:
                continue
            cluster = []
            queue = deque([fire])
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                cluster.append(current)
                for n in neighbors(current):
                    if n in fire_positions and n not in visited:
                        queue.append(n)
            clusters.append(cluster)
        return clusters

    def perceive_fire(self):
        fires = [
            tree for tree in self.model.trees
            if isinstance(tree, Tree) and tree.condition == 1
        ]

        visible_fires = []
        for tree in fires:
            pos = self.grid.positions[tree]
            if np.linalg.norm(np.array(pos) - np.array(self.grid.positions[self])) <= self.sensor_range:
                visible_fires.append(pos)

        if visible_fires:
            clustered = self.cluster_fires(set(visible_fires))

            for cluster in clustered:
                if all(not self.contract_exists(pos) for pos in cluster):
                    center_pos = cluster[0]
                    team_size = max(1, len(cluster) // 2)

                    contract = {
                        "task_id": f"fire_{center_pos[0]}_{center_pos[1]}_{self.model.t}",
                        "location": center_pos,
                        "cluster": cluster,
                        "type": "extinguish_fire",
                        "timestamp": self.model.t,
                        "status": "open",
                        "bids": [],
                        "assigned": [],
                        "team_size": team_size,
                        "assign_time": None,
                        "manager": self.drone_id
                    }

                    self.model.fire_contracts.append(contract)

                    self.model.contract_logs.append({
                        "event": "created",
                        "task_id": contract["task_id"],
                        "location": center_pos,
                        "cluster_size": len(cluster),
                        "team_size": team_size,
                        "drone_id": self.drone_id,
                        "time": self.model.t
                    })

            if self.debug:
                self.model.drone_debug_logs.append({
                    "drone_id": self.drone_id,
                    "detected_fires": visible_fires,
                    "time": self.model.t
                })

            self.target = visible_fires[0]
            return True

        return False

    def step(self):
        my_pos = np.array(self.grid.positions[self])
        base_pos = np.array(self.base_station)
        distance_to_base = np.linalg.norm(my_pos - base_pos)

        self.model.position_logs.append({
            "time": self.model.t,
            "agent_id": self.drone_id,
            "type": "drone",
            "x": int(my_pos[0]),
            "y": int(my_pos[1])
        })

        if self.battery <= distance_to_base + self.battery_warning:
            self.return_to_base()
            return

        for contract in self.model.fire_contracts:
            if contract["status"] == "open" and contract["manager"] == self.drone_id and contract["bids"]:
                sorted_bids = sorted(contract["bids"], key=lambda b: b["bid"])
                selected_bids = sorted_bids[:contract["team_size"]]
                contract["assigned"] = [b["firefighter_id"] for b in selected_bids]
                contract["status"] = "assigned"
                contract["assign_time"] = self.model.t

                for bid in selected_bids:
                    self.model.contract_logs.append({
                        "event": "assignment",
                        "task_id": contract["task_id"],
                        "drone_id": self.drone_id,
                        "assigned_to": bid["firefighter_id"],
                        "bid": bid["bid"],
                        "time": self.model.t
                    })

        for contract in self.model.fire_contracts:
            if (contract["status"] == "open" and
                contract["manager"] == self.drone_id and
                contract["bids"] and
                (self.model.t - contract["timestamp"] >= 1)):
                sorted_bids = sorted(contract["bids"], key=lambda b: b["bid"])
                selected = sorted_bids[:contract.get("team_size", 2)]
                contract["assigned"] = [b["firefighter_id"] for b in selected]
                contract["status"] = "assigned"
                contract["assign_time"] = self.model.t

        if self.perceive_fire():
            if not self.is_at_position(self.target):
                self.move_towards(self.target)
            return

        if self.is_at_position(self.target):
            self.target = self.random_target_in_quadrant()
        else:
            self.move_towards(self.target)