# Model design
import agentpy as ap
import sys
import io

# Visualization
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
import IPython

class Tree(ap.Agent):
    """
    A Tree class in a forest model simulation which can change states from alive, to burning, to burned.
    """

    def setup(self):
        """
        Initializes the tree's condition.
        Conditions: 0 - Alive, 1 - Burning, 2 - Burned
        """
        self.condition = 0  # Default condition is alive

    def start_fire(self):
        """
        Sets the tree's condition to burning.
        """
        self.condition = 1

    def spread_fire(self, forest, probability_of_spread):
        """
        Attempts to spread fire to neighboring trees based on a given probability.
        
        Args:
        - forest (ap.Grid): The grid representing the forest containing the tree.
        - probability_of_spread (float): The likelihood of the fire spreading to each neighbor.
        """
        if self.condition == 1:
            neighbors = forest.neighbors(self)
            for neighbor in neighbors:
                if neighbor.condition == 0 and np.random.rand() < probability_of_spread:
                    neighbor.start_fire()
            self.condition = 2  # Once the fire is spread, the tree is burned down.

class ForestModel(ap.Model):
    """
    A model simulating the spread of fire through a forest of trees.
    """

    def setup(self):
        """
        Sets up the model by initializing the grid and populating it with trees.
        Trees on the edge of the forest grid will start on fire.
        """
        n_trees = int(self.p['Tree density'] * (self.p.size**2))  # Calculate the number of trees based on the density
        self.trees = ap.AgentList(self, n_trees, Tree)  # Create a list of tree agents
        self.forest = ap.Grid(self, [self.p.size]*2, track_empty=True)  # Create a grid for the forest
        self.forest.add_agents(self.trees, random=True)  # Randomly distribute trees on the grid
        
        # Start fire on all trees in the first column of the grid
        for tree in self.trees:
            if self.forest.positions[tree][1] == 0:
                tree.start_fire()

    def step(self):
        """
        Executes one time step of the model, where each burning tree tries to spread the fire.
        The model stops if no trees are burning.
        """
        burning_trees = [tree for tree in self.trees if tree.condition == 1]
        for tree in burning_trees:
            tree.spread_fire(self.forest, self.p['probability_of_spread'])
        if not burning_trees:
            self.stop()

    def end(self):
        """
        Calculates and reports the percentage of burned trees at the end of the simulation.
        """
        burned_trees = [tree for tree in self.trees if tree.condition == 2]
        self.report('burned_trees', len(burned_trees) / len(self.trees) * 100)

# Parameters for the experiment
densities = np.linspace(0.2, 0.9, 10)  # Better resolution
prob_spreads = np.linspace(0.1, 0.9, 10)
results = np.zeros((len(densities), len(prob_spreads)))

for i, density in enumerate(densities):
    for j, prob_spread in enumerate(prob_spreads):
        model = ForestModel({'Tree density': density, 'size': 50, 'steps': 100, 'probability_of_spread': prob_spread})
        output = model.run()
        results[i, j] = output.reporters['burned_trees']

# 3D Plotting
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

X, Y = np.meshgrid(prob_spreads, densities)
ax.plot_surface(X, Y, results, cmap='viridis')

ax.set_xlabel('Probability of Spread')
ax.set_ylabel('Forest Density')
ax.set_zlabel('Percentage of Burned Trees (%)')
ax.set_title('3D Visualization of Fire Spread Dynamics')

plt.show()
