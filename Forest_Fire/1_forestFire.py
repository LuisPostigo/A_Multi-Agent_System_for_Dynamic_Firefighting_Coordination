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
    # This class represents an individual tree in the forest.
    def setup(self):
        # Initial condition of the tree: 0 - Alive, 1 - Burning, 2 - Burned
        self.condition = 0

    def start_fire(self):
        # Sets tree condition to 'Burning'.
        self.condition = 1

    def spread_fire(self, forest):
        # Method to spread fire to neighboring trees.
        if self.condition == 1:  # Checks if the tree is burning
            neighbors = forest.neighbors(self)  # Gets neighboring trees
            alive_neighbors = [neighbor for neighbor in neighbors if neighbor.condition == 0]  # Filter alive trees
            for neighbor in alive_neighbors:
                neighbor.start_fire()  # Starts fire on each alive neighboring tree
            self.condition = 2  # Once fire is spread, set tree condition to 'Burned'

class ForestModel(ap.Model):
    # This class models the forest containing trees.
    def setup(self):
        # Setup the forest model with a given tree density and size.
        n_trees = int(self.p['Tree density'] * (self.p.size**2))  # Calculate the number of trees based on density
        self.trees = ap.AgentList(self, n_trees, Tree)  # Create a list of Tree agents

        self.forest = ap.Grid(self, [self.p.size]*2, track_empty=True)  # Create a grid to place trees
        self.forest.add_agents(self.trees, random=True)  # Add trees to the grid at random positions

        for tree in self.trees:
            if self.forest.positions[tree][1] == 0:  # Check if a tree is on the left edge
                tree.start_fire()  # Start fire on left edge trees

    def step(self):
        # Define the steps of the simulation, where trees spread fire.
        burning_trees = [tree for tree in self.trees if tree.condition == 1]  # List burning trees
        for tree in burning_trees:
            tree.spread_fire(self.forest)  # Spread fire from each burning tree
        if not burning_trees:  # If no trees are burning, stop the simulation
            self.stop()

    def end(self):
        # Define what happens at the end of the simulation.
        burned_trees = [tree for tree in self.trees if tree.condition == 2]  # List all burned trees
        # Calculate and report the percentage of burned trees.
        self.report('burned_trees', len(burned_trees) / len(self.trees) * 100)

def animation_plot(model, ax):
    # Function to plot the forest state for animation.
    attr_grid = model.forest.attr_grid('condition')  # Get a grid of tree conditions
    color_dict = {0: '#7FC97F', 1: '#d62c2c', 2: '#e5e5e5', None: '#d5e5d5'}  # Color map for tree conditions
    ap.gridplot(attr_grid, ax=ax, color_dict=color_dict, convert=True)  # Create a plot
    ax.set_title(f"Simulation of a forest fire\nTime-step: {model.t}")  # Set title with time-step

# Animate a single run
parameters = {'Tree density': 0.6, 'size': 50, 'steps': 100}
model = ForestModel(parameters)
fig, ax = plt.subplots()
animation = ap.animate(model, fig, ax, animation_plot)
IPython.display.display(IPython.display.HTML(animation.to_jshtml(fps=5)))

# Run experiments over a range of densities
densities = np.linspace(0.1, 1.0, 10)
results = []
for density in densities:
    model = ForestModel({'Tree density': density, 'size': 50, 'steps': 100})
    output = model.run()
    results.append(output.reporters['burned_trees'])

# Plot results
plt.figure(figsize=(8, 6))
plt.plot(densities, results, marker='o')
plt.title("Percentage of Burned Trees vs. Forest Density")
plt.xlabel("Forest Density")
plt.ylabel("Percentage of Burned Trees (%)")
plt.grid(True)
plt.show()
