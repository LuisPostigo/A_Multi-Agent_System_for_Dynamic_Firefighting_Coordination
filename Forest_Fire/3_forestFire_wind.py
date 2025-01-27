# Model design
import agentpy as ap

# Visualization
import numpy as np
import matplotlib.pyplot as plt

class Tree(ap.Agent):
    """
    Represents a tree in a forest model simulation that can have different fire conditions.
    """
    def setup(self):
        self.condition = 0  # Tree conditions: 0 - Alive, 1 - Burning, 2 - Burned

    def start_fire(self):
        """
        Sets the tree on fire, changing its condition to burning.
        """
        self.condition = 1

    def spread_fire(self, forest, probability_of_spread, wind_south, wind_west):
        """
        Spreads fire to neighboring trees, influenced by wind direction and speed.

        Args:
        - forest (ap.Grid): The forest grid in which this tree exists.
        - probability_of_spread (float): Base probability of the fire spreading to adjacent trees.
        - wind_south (float): Wind influence factor for north-south direction.
        - wind_west (float): Wind influence factor for east-west direction.
        """
        if self.condition == 1:
            neighbors = forest.neighbors(self)
            current_pos = forest.positions[self]
            for neighbor in neighbors:
                neighbor_pos = forest.positions[neighbor]
                dx = neighbor_pos[0] - current_pos[0]
                dy = neighbor_pos[1] - current_pos[1]
                spread_chance = probability_of_spread

                # Adjust spreading chance based on wind direction
                if dx != 0:
                    spread_chance *= (1 + (wind_west * dx) / 10)
                if dy != 0:
                    spread_chance *= (1 + (wind_south * dy) / 10)

                if neighbor.condition == 0 and np.random.rand() < spread_chance:
                    neighbor.start_fire()
            self.condition = 2

class ForestModel(ap.Model):
    """
    A model simulating the spread of fire in a forest, taking into account wind effects and tree density.
    """
    def setup(self):
        """
        Sets up the forest model by initializing trees and setting some on fire initially.
        """
        n_trees = int(self.p['Tree density'] * (self.p.size**2))
        self.trees = ap.AgentList(self, n_trees, Tree)
        self.forest = ap.Grid(self, [self.p.size]*2, track_empty=True)
        self.forest.add_agents(self.trees, random=True)

        # Start fire on all trees in the first column of the grid
        for tree in self.trees:
            if self.forest.positions[tree][1] == 0:
                tree.start_fire()

    def step(self):
        """
        Executes one step of the model, where each burning tree attempts to spread fire.
        Stops the model if no trees are currently burning.
        """
        burning_trees = [tree for tree in self.trees if tree.condition == 1]
        for tree in burning_trees:
            tree.spread_fire(self.forest, self.p['probability_of_spread'], self.p['wind_south'], self.p['wind_west'])
        if not burning_trees:
            self.stop()

    def end(self):
        """
        At the end of the simulation, calculates the percentage of burned trees.
        """
        burned_trees = [tree for tree in self.trees if tree.condition == 2]
        self.report('burned_trees', len(burned_trees) / len(self.trees) * 100)

# Set up experiment parameters
wind_speeds = np.linspace(-1, 1, 5)  # From -1 (wind from east/north) to 1 (wind from west/south)
densities = np.linspace(0.2, 0.8, 5)
results = np.zeros((len(wind_speeds), len(densities)))

for i, wind_speed in enumerate(wind_speeds):
    for j, density in enumerate(densities):
        model = ForestModel({
            'Tree density': density,
            'size': 50,
            'steps': 100,
            'probability_of_spread': 0.5,
            'wind_south': wind_speed,
            'wind_west': wind_speed
        })
        output = model.run()
        results[i, j] = output.reporters['burned_trees']

# 3D Visualization of results
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
X, Y = np.meshgrid(densities, wind_speeds)
ax.plot_surface(X, Y, results, cmap='viridis')

ax.set_xlabel('Forest Density')
ax.set_ylabel('Wind Speed')
ax.set_zlabel('Percentage of Burned Trees (%)')
ax.set_title('Impact of Wind Speed and Density on Fire Spread')
plt.show()
