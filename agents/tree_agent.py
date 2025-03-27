# Model design
import agentpy as ap

class Tree(ap.Agent):
    def setup(self):
        self.condition = 0  # 0 = Alive, 1 = Burning, 2 = Burned
        self.growth_rate = self.p.get('tree_growth_rate', 0.01)
        self.burn_time = self.p.get('tree_burn_time', 8)

    def spreadFire(self):
        if self.condition == 1:
            neighbors = self.model.grid.neighbors(self)
            for neighbor in neighbors:
                if isinstance(neighbor, Tree) and neighbor.condition == 0:
                    if self.model.random.random() < self.p.get('probSpread', 0.2):
                        neighbor.condition = 1
                        neighbor.burn_time = self.p.get('tree_burn_time', 8)

    def burnOut(self):
        if self.condition == 1:
            self.burn_time -= 1
            if self.burn_time <= 0:
                self.condition = 2