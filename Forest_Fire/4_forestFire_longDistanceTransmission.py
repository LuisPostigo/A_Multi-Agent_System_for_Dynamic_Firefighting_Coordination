import agentpy as ap
import numpy as np
import matplotlib.pyplot as plt
import random
import IPython.display

class Tree(ap.Agent):
    """
    Represents a tree in a forest simulation that can be in different states of burning.
    """
    def setup(self):
        self.condition = 0  # Initial condition: 0 - Alive, 1 - Burning, 2 - Burned

    def start_fire(self):
        """
        Set the tree to be burning.
        """
        self.condition = 1

    def spread_fire(self, forest, probability_of_spread, wind_south, wind_west, big_jump):
        """
        Spread fire to neighboring trees and potentially make a long jump influenced by the wind.

        Args:
        - forest (ap.Grid): The grid where the forest is simulated.
        - probability_of_spread (float): Probability of fire spreading to adjacent trees.
        - wind_south (float): Southward wind effect on fire spread.
        - wind_west (float): Westward wind effect on fire spread.
        - big_jump (bool): If True, allows the fire to jump a greater distance occasionally.
        """
        if self.condition == 1:
            neighbors = forest.neighbors(self)
            current_pos = forest.positions[self]
            for neighbor in neighbors:
                neighbor_pos = forest.positions[neighbor]
                dx = neighbor_pos[0] - current_pos[0]
                dy = neighbor_pos[1] - current_pos[1]
                spread_chance = probability_of_spread

                # Adjust probability for wind direction
                if dx != 0:
                    spread_chance *= (1 + (wind_west * dx) / 10)
                if dy != 0:
                    spread_chance *= (1 + (wind_south * dy) / 10)

                if neighbor.condition == 0 and np.random.rand() < spread_chance:
                    neighbor.start_fire()

            # Implement long-distance jump of fire
            if big_jump and random.random() < 0.1:
                jump_distance = 5
                jump_x = int(current_pos[0] + jump_distance * np.sign(wind_west))
                jump_y = int(current_pos[1] + jump_distance * np.sign(wind_south))

                # Check if the jump is within grid boundaries
                if 0 <= jump_x < forest.width and 0 <= jump_y < forest.height:
                    target_cell = forest[jump_x, jump_y]
                    if target_cell and target_cell.condition == 0:
                        target_cell.start_fire()

            self.condition = 2  # Change condition to burned

class ForestModel(ap.Model):
    """
    A model to simulate the spread of fire in a forest with varying tree density and wind effects.
    """
    def setup(self):
        n_trees = int(self.p['Tree density'] * (self.p.size**2))
        self.trees = ap.AgentList(self, n_trees, Tree)
        self.forest = ap.Grid(self, [self.p.size]*2, track_empty=True)
        self.forest.add_agents(self.trees, random=True)

        # Start fire on the first row
        for tree in self.trees:
            if self.forest.positions[tree][1] == 0:
                tree.start_fire()

    def step(self):
        """
        Execute a single step of the model, spreading the fire among trees.
        """
        burning_trees = [tree for tree in self.trees if tree.condition == 1]
        for tree in burning_trees:
            tree.spread_fire(self.forest, self.p['probability_of_spread'], self.p['wind_south'], self.p['wind_west'], self.p['big_jump'])
        if not burning_trees:
            self.stop()

    def end(self):
        """
        Calculate the percentage of trees burned at the end of the simulation.
        """
        burned_trees = [tree for tree in self.trees if tree.condition == 2]
        self.report('burned_trees', len(burned_trees) / len(self.trees) * 100)

def animation_plot(model, ax):
    """
    Custom plot function for animating the forest fire model.
    
    Args:
    - model (ap.Model): The model to be visualized.
    - ax (matplotlib.axes.Axes): The axes object to draw the animation.
    """
    attr_grid = model.forest.attr_grid('condition')
    color_dict = {0: '#7FC97F', 1: '#d62c2c', 2: '#e5e5e5', None: '#d5e5d5'}
    ap.gridplot(attr_grid, ax=ax, color_dict=color_dict, convert=True)
    ax.set_title(f"Simulation of a forest fire\nTime-step: {model.t}")

# Parameters for the model
parameters = {
    'Tree density': 0.6,
    'size': 50,
    'steps': 100,
    'probability_of_spread': 0.3,
    'wind_south': 1,
    'wind_west': 1,
    'big_jump': True
}

# Setting up the animation
model = ForestModel(parameters)
fig, ax = plt.subplots()
animation = ap.animate(model, fig, ax, animation_plot)
IPython.display.HTML(animation.to_jshtml(fps=5))
