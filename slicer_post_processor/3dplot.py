import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Define the limits for x, y, and z
x_limit = 10
y_limit = 10
z_limit = 1

# Create a grid for x and y
x = np.linspace(0, x_limit, 100)
y = np.linspace(0, y_limit, 100)
x_grid, y_grid = np.meshgrid(x, y)

# Define the inverted parabola on the xz plane (vertex at x=5)
z1 = 1 - ((x_grid - 7) ** 2) / 49  # Scaled to fit z_limit=1 and intersect x=0
z1[z1 < 0] = 0  # Ensure non-negative values

# Define the logarithmic function on the yz plane
z2 = 0.8 * np.sqrt(y_grid * 0.9) / np.sqrt(y_limit) * (1 - np.exp(-y_grid))  # Normalized to fit z_limit=1 with smoother derivative
# Multiply the two functions
z=(z1+z2)/2*(z1*z2)**0.5
# Create the 3D plot
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

# Plot the surface
surf = ax.plot_surface(x_grid, y_grid, z, cmap='viridis', edgecolor='k', alpha=0.8)

# Set labels and limits
ax.set_xlabel('size')
ax.set_ylabel('topology')
ax.set_zlabel('value [z=(z1+z2)/2*(z1*z2)**0.5]')
ax.set_xlim(0, x_limit)
ax.set_ylim(0, y_limit)
ax.set_zlim(0, z_limit)

# Add a color bar
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)

# Show the plot
plt.title("combined value of size and topology")
plt.show()
