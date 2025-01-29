import math
import matplotlib.pyplot as plt
from numpy import pi as pi

class PinDefinition:
    def __init__(self, largest_side, smallest_side, pin_dimension, pin_shape, num_pins_largest_side,
                 num_pins_smallest_side, pin_height_input, pin_height_input_type, layer_height,
                 least_edge_margin, infill_percentage):

        # cross-section parameters
        self.largest_side = largest_side
        self.smallest_side = smallest_side

        # pin dimensions and layout parameters
        self.pin_dimension = pin_dimension
        self.num_pins_largest_side = num_pins_largest_side
        self.num_pins_smallest_side = num_pins_smallest_side
        self.pin_height_input = pin_height_input
        self.pin_height_input_type = pin_height_input_type
        self.pin_shape = pin_shape

        # printing parameters
        self.layer_height = layer_height
        self.least_edge_margin = least_edge_margin
        self.infill_percentage = infill_percentage

        # outcome of the calculation
        self.pins_relative_xy = None

    def calculate_pin_height(self):
        """Calculate pin height in mm based on input type."""
        if self.pin_height_input_type == "layers":
            return self.pin_height_input * self.layer_height
        elif self.pin_height_input_type == "mm":
            return self.pin_height_input
        else:
            raise ValueError("Problem: pin_height_input_type must be either 'layers' or 'mm'.")

    def fit_in_cross_section(self):
        """Check if the pins fit within the cross-section based on layout and infill percentage."""
        total_pin_area = ((self.num_pins_largest_side * self.num_pins_smallest_side) * pi * (self.pin_dimension ** 2) / 4)
        total_area = self.largest_side * self.smallest_side

        real_infill = total_pin_area / total_area

        total_pin_length_largest_side = (self.num_pins_largest_side - 1) * (self.pin_dimension + 2 * self.layer_height)
        total_pin_length_smallest_side = (self.num_pins_smallest_side - 1) * (
                    self.pin_dimension + 2 * self.layer_height)

        actual_edge_margin_largest = (self.largest_side - total_pin_length_largest_side) / 2
        actual_edge_margin_smallest = (self.smallest_side - total_pin_length_smallest_side) / 2

        # Allow a 10% range for the infill percentage
        if abs(real_infill * 100 - self.infill_percentage) <= 1:
            if actual_edge_margin_largest >= self.least_edge_margin and actual_edge_margin_smallest >= self.least_edge_margin:
                return True
            else:
                print(f"Problem: pins do not fit within the cross-section.")
                return False
        else:
            print(f"Problem: the number of pins is does not provide appropriate infill \n"
            f" (effective infill :{total_pin_area/total_area * 100} % -  layer protrusion is not taken into account) .")
            return False

    def calculate_pin_positions(self):
        """Calculate the position of each pin center along X and Y axes."""
        total_pin_length_x = self.num_pins_largest_side * self.pin_dimension
        total_pin_length_y = self.num_pins_smallest_side * self.pin_dimension

        available_space_x = self.largest_side - total_pin_length_x
        available_space_y = self.smallest_side - total_pin_length_y

        if self.num_pins_largest_side > 1:
            spacing_x = available_space_x / (self.num_pins_largest_side + 1)
        else:
            spacing_x = available_space_x / 2

        if self.num_pins_smallest_side > 1:
            spacing_y = available_space_y / (self.num_pins_smallest_side + 1)
        else:
            spacing_y = available_space_y / 2

        pin_positions = []
        for i in range(self.num_pins_largest_side):
            for j in range(self.num_pins_smallest_side):
                x_position = spacing_x + i * (self.pin_dimension + spacing_x) + self.pin_dimension / 2
                y_position = spacing_y + j * (self.pin_dimension + spacing_y) + self.pin_dimension / 2
                pin_positions.append((round(x_position, 4), (round(y_position, 4))))

        return pin_positions

    def visualize_pin_layout(self):
        """Visualize the layout of the pins in the cross-section."""
        fig, ax = plt.subplots()
        ax.add_patch(
            plt.Rectangle((0, 0), self.largest_side, self.smallest_side, edgecolor='black', facecolor='none', lw=2))

        for (x, y) in self.pins_relative_xy:
            if self.pin_shape == "circular":
                ax.add_patch(plt.Circle((x, y), self.pin_dimension / 2, edgecolor='blue', facecolor='blue', alpha=0.5))
            else:
                ax.add_patch(plt.Rectangle((x - self.pin_dimension / 2, y - self.pin_dimension / 2),
                                           self.pin_dimension, self.pin_dimension, edgecolor='blue', facecolor='blue',
                                           alpha=0.5))

        ax.set_xlim([0, self.largest_side])
        ax.set_ylim([0, self.smallest_side])
        ax.set_aspect('equal', 'box')
        plt.xlabel('x (mm)')
        plt.ylabel('y (mm)')
        plt.title('Pin layout')
        plt.grid(False)
        plt.show()

    def define_pins_relative_xy(self):
        """
        Defines pins and visualizes the pin layout based on the stored attributes.

        Returns:
            dict: Dictionary containing pin configuration, including shape.
        """
        # Calculate pin positions
        self.pins_relative_xy = self.calculate_pin_positions()

        # Create visualization logic here based on pin_shape
        if not self.pin_shape == "circular" and not self.pin_shape == "square":
            raise ValueError(f"Unknown pin shape: {self.pin_shape}")

        # print(self.pins_relative_xy)



        # Check if the pins fit within the cross-section
        if self.fit_in_cross_section():
            print("Pin definition: completed successfully.")  # Add this line here

            return {
                "largest_side": self.largest_side,
                "smallest_side": self.smallest_side,
                "pins_relative_xy": self.pins_relative_xy,
                "pin_height_mm": self.calculate_pin_height(),
                "pin_dimension": self.pin_dimension,
                "layer_height": self.layer_height,
                "pin_shape": self.pin_shape  # Return the pin shape for further use
            }
        else:
            raise ValueError("Problem: pins do not fit within the cross-section.")