# Flocking Birds Model using Multi-Agent Systems

import agentpy as ap
import numpy as np
import matplotlib.pyplot as plt
import IPython.display

def normalize(v):
    # Calculates the Euclidean norm of the vector v.
    norm = np.linalg.norm(v)
    # Handling division by zero.
    if norm == 0:
        return v
    # Normalizes the vector by dividing it by its norm.
    return v / norm

class Boid(ap.Agent):
    # A class representing a single boid agent.
    def setup(self):
        self.velocity = normalize(
            self.model.nprandom.random(self.p.ndim) - 0.5)

    # Setup the boid's position in the space and find its neighbors.
    def setup_pos(self, space):
        self.space = space
        self.neighbors = space.neighbors
        self.pos = space.positions[self]

    def update_velocity(self):
        # Update the boid's velocity based on four rules.
        pos = self.pos
        ndim = self.p.ndim

        # Rule 1 - Cohesion: Move towards the average position of local flockmates.
        nbs = self.neighbors(self, distance=self.p.outer_radius)
        nbs_len = len(nbs)
        nbs_pos_array = np.array(nbs.pos)
        nbs_vec_array = np.array(nbs.velocity)
        if nbs_len > 0:
            center = np.sum(nbs_pos_array, 0) / nbs_len
            v1 = (center - pos) * self.p.cohesion_strength
        else:
            v1 = np.zeros(ndim)

        # Rule 2 - Separation: Avoid crowding local flockmates.
        v2 = np.zeros(ndim)
        for nb in self.neighbors(self, distance=self.p.inner_radius):
            v2 -= nb.pos - pos
        v2 *= self.p.seperation_strength

        # Rule 3 - Alignment: Steer towards the average heading of local flockmates.
        if nbs_len > 0:
            average_v = np.sum(nbs_vec_array, 0) / nbs_len
            v3 = (average_v - self.velocity) * self.p.alignment_strength
        else:
            v3 = np.zeros(ndim)

        # Rule 4 - Borders: Avoid edges of the space.
        v4 = np.zeros(ndim)
        d = self.p.border_distance
        s = self.p.border_strength
        for i in range(ndim):
            if pos[i] < d:
                v4[i] += s
            elif pos[i] > self.space.shape[i] - d:
                v4[i] -= s

        # Combines all forces and normalizes the velocity.
        self.velocity += v1 + v2 + v3 + v4
        self.velocity = normalize(self.velocity)

    def update_position(self):
        # Moves the boid according to its updated velocity.
        self.space.move_by(self, self.velocity)

class BoidsModel(ap.Model):
    # Here we define the model for simulating the Boids (flocking behavior).
    def setup(self):
        # Creates a space with dimensions and shape based on parameters.
        self.space = ap.Space(self, shape=[self.p.size]*self.p.ndim)
        # Creates a list of agents (Boids) and add them to the space randomly.
        self.agents = ap.AgentList(self, self.p.population, Boid)
        self.space.add_agents(self.agents, random=True)
        # Initializes the position of agents in the space.
        self.agents.setup_pos(self.space)

    def step(self):
        # Updates velocity based on the flocking rules.
        self.agents.update_velocity()
        # Moves agents to their new positions based on the updated velocities.
        self.agents.update_position()

def animation_plot_single(m, ax):
    # This function plots the positions of the boids for each frame of the animation.
    ndim = m.p.ndim
    ax.set_title(f"Boids Flocking Model {ndim}D t={m.t}")
    # Extract positions from the model's space object.
    pos = m.space.positions.values()
    pos = np.array(list(pos)).T  # Transform for plotting.
    # Plot positions as scattered points.
    ax.scatter(*pos, s=1, c='black')
    # Set the limits of the plot based on the model size.
    ax.set_xlim(0, m.p.size)
    ax.set_ylim(0, m.p.size)
    # If 3D, set the z-axis limit as well.
    if ndim == 3:
        ax.set_zlim(0, m.p.size)
    ax.set_axis_off()  # Hide axis for visual clarity.

def animation_plot(m, p):
    # Determine if the plot should be 3D based on the number of dimensions.
    projection = '3d' if p['ndim'] == 3 else None
    fig = plt.figure(figsize=(7,7))
    ax = fig.add_subplot(111, projection=projection)
    # Create an animation by repeatedly plotting the model state.
    animation = ap.animate(m(p), fig, ax, animation_plot_single)
    # Convert the animation to HTML and display it inline in a Jupyter notebook.
    return IPython.display.HTML(animation.to_jshtml(fps=20))

parameters2D = {
    'size': 50,
    'seed': 123,
    'steps': 200,
    'ndim': 2,
    'population': 200,
    'inner_radius': 3,
    'outer_radius': 10,
    'border_distance': 10,
    'cohesion_strength': 0.005,
    'seperation_strength': 0.1,
    'alignment_strength': 0.3,
    'border_strength': 0.5
}

animation_plot(BoidsModel, parameters2D)
