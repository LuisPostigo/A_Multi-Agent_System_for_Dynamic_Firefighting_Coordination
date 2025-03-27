import agentpy as ap

from agents.tree_agent import Tree
from agents.fireFighter_agent import Firefighter
from agents.drone_agent import Drone

class ForestModel(ap.Model):
    def setup(self):
        self.position_logs = []
        self.contract_logs = []
        self.fire_contracts = []
        self.drone_debug_logs = []
        self.firefighter_debug_logs = []
        self.water_splashes = []
        self.fire_reports = []

        n_trees = int(self.p['Tree density'] * (self.p.size ** 2))
        self.grid = ap.Grid(self, [self.p.size, self.p.size], track_empty=True)
        self.trees = ap.AgentList(self, n_trees, Tree)
        self.grid.add_agents(self.trees, random=True, empty=True)

        center_x, center_y = self.p.size // 2, self.p.size // 2
        fire_size = 5
        for dx in range(-fire_size // 2, fire_size // 2 + 1):
            for dy in range(-fire_size // 2, fire_size // 2 + 1):
                x, y = center_x + dx, center_y + dy
                if 0 <= x < self.p.size and 0 <= y < self.p.size:
                    tree = self.grid.agents[x, y].to_list()
                    if tree:
                        tree[0].condition = 1

        n_firefighters = self.p.num_firefighters
        self.firefighters = ap.AgentList(self, n_firefighters, Firefighter)
        self.grid.add_agents(self.firefighters, random=True, empty=True)
        for i, firefighter in enumerate(self.firefighters):
            firefighter.firefighter_id = f"F{i}"

        n_drones = self.p.num_drones
        self.drones = ap.AgentList(self, n_drones, Drone)
        self.grid.add_agents(self.drones, random=True, empty=True)
        self.drone_targets = {0: None, 1: None, 2: None, 3: None}

        mid = self.p.size // 2
        for i, drone in enumerate(self.drones):
            drone.drone_id = f"D{i}"
            drone.quadrant = i % 4
            if drone.quadrant == 0:
                drone.row_min, drone.row_max = 0, mid - 1
                drone.col_min, drone.col_max = 0, mid - 1
            elif drone.quadrant == 1:
                drone.row_min, drone.row_max = 0, mid - 1
                drone.col_min, drone.col_max = mid, self.p.size - 1
            elif drone.quadrant == 2:
                drone.row_min, drone.row_max = mid, self.p.size - 1
                drone.col_min, drone.col_max = 0, mid - 1
            elif drone.quadrant == 3:
                drone.row_min, drone.row_max = mid, self.p.size - 1
                drone.col_min, drone.col_max = mid, self.p.size - 1

    def step(self):
        burning_trees = self.trees.select(self.trees.condition == 1)
        for tree in burning_trees:
            tree.spreadFire()
            tree.burnOut()

        self.firefighters.step()
        self.drones.step()

        if self.t >= self.p.steps:
            self.stop()

    def end(self):
        burned_trees = len(self.trees.select(self.trees.condition == 2))
        self.report('Percentage of burned trees', burned_trees / len(self.trees))
        self.report('Density', self.p['Tree density'])