import math
from gcode_modifier import parse_gcode_lines


def _apply_transformation(pin_positions, translation_xy, rotation_angle):
    """
    Apply translation and rotation transformations to the pin positions.

    Args:
        pin_positions (list): List of tuples representing the original pin positions (X, Y).
        translation_xy (tuple): XY translation values as (x_translation, y_translation).
        rotation_angle (float): Rotation angle in degrees.

    Returns:
        list: Transformed pin positions.
    """
    x_translation, y_translation = translation_xy
    angle_rad = math.radians(rotation_angle)
    cos_theta = math.cos(angle_rad)
    sin_theta = math.sin(angle_rad)

    transformed_positions = []
    for x, y in pin_positions:
        # Apply rotation
        x_rotated = x * cos_theta - y * sin_theta
        y_rotated = x * sin_theta + y * cos_theta

        # Apply translation
        x_transformed = x_rotated + x_translation
        y_transformed = y_rotated + y_translation

        transformed_positions.append((x_transformed, y_transformed))

    return transformed_positions


class GCodeCommandsComposer:
    FILAMENT_DIAMETER = 1.75  # Filament diameter (mm)

    def __init__(self, pin_data, parts_dict, specimen_height_mm, flow_ratio, z_lift_speed,
                 xy_travel_speed, z_hop_length, retraction_length, z_drop_speed,
                 pinning_extrusion_speed, diving_nozzle):

        # FROM pin_cross_section_definition.py
        self.pin_positions = pin_data["pins_relative_xy"]

        # FROM pin_cross_section_definition.py (itself from dashboard.py)
        self.pin_height_mm = pin_data["pin_height_mm"]
        self.pin_dimension = pin_data["pin_dimension"]
        self.layer_height = pin_data["layer_height"]
        self.pin_shape = pin_data["pin_shape"]  # "square" or "circular"

        # FROM dashboard.py
        self.parts_dict = parts_dict
        self.specimen_height_mm = specimen_height_mm
        self.flow_ratio = flow_ratio

        self.z_lift_speed = z_lift_speed
        self.xy_travel_speed = xy_travel_speed
        self.z_hop_length = z_hop_length
        self.retraction_length = retraction_length  # Amount to retract filament before moving
        self.z_drop_speed = z_drop_speed
        self.pinning_extrusion_speed = pinning_extrusion_speed

        self.diving_nozzle = diving_nozzle

        # calculated
        self.total_layers = int(self.specimen_height_mm / self.layer_height)
        if self.pin_height_mm > 0 and self.layer_height > 0:
            self.pin_height_layers = int(self.pin_height_mm / self.layer_height)
        else:
            self.pin_height_layers = 0  # Handle the case where pin height or layer height is invalid

        self.pins_absolute_xy_per_part = {
            part['name']: _apply_transformation(self.pin_positions, part['xy'], part['rotation'])
            for part in self.parts_dict }

        self.pins_absolute_xy = None

    def compose_parts_gcode(self):
        """
        Composes G-code for pinning at the specified layers based on the pin height.
        Returns:
            tuple: (gcode_lines_per_layer, constants)
        """
        if self.pin_height_layers == 0 or self.total_layers == 0:
            print("Error: Invalid pin or specimen height.")
            return {}, {}


        gcode_lines_per_layer = {}
        extrusion_length = self._calculate_extrusion_length()

        # Loop through the layers where pinning should happen, based on pin_height_layers
        for layer in range(self.pin_height_layers, self.total_layers + 1, self.pin_height_layers):
            is_last_layer = (layer + self.pin_height_layers >= self.total_layers)

            if is_last_layer:
                remaining_height = self.pin_height_mm - (self.pin_height_layers * self.layer_height)
                extrusion_length *= (remaining_height / self.layer_height)

            gcode_lines = []
            gcode_lines.extend([f"--- PINNING LAYER {layer} ---"])
            gcode_lines.extend([""])

            # Loop through each part on the build plate
            for part_name, part_pins_absolute_xy in self.pins_absolute_xy_per_part.items():
                serpentine_order = part_pins_absolute_xy if layer % 2 == 0 else part_pins_absolute_xy[::-1]

                gcode_lines.extend([f"- PINNING PART {part_name} -"])

                for pin_idx, (x, y) in enumerate(serpentine_order, start=1):
                    gcode_lines.extend(self._generate_pin_gcode(x, y, layer * self.layer_height, pin_idx,
                                                                extrusion_length, layer))

            # Parse the generated G-code and store it in the dictionary
            gcode_lines_per_layer[layer] = parse_gcode_lines(gcode_lines)

        # Prepare constants
        constants = {
            "pin_positions": self.pin_positions,
            "pin_height_mm": self.pin_height_mm,
            "pin_dimension": self.pin_dimension,
            "layer_height": self.layer_height,
            "pin_height_layers": self.pin_height_layers,
            "total_layers": self.total_layers,
            "retract_amount": self.retraction_length,
            "z_lift": self.z_hop_length,
            "xy_speed": self.xy_travel_speed,
            "z_drop_speed": self.z_drop_speed,
            "pin_speed": self.z_lift_speed,
            "parts_dict": self.parts_dict,
            "diving_nozzle": self.diving_nozzle
        }

        print("Pinning G-code composition for multiple parts: completed successfully.")

        return gcode_lines_per_layer, constants

    def _generate_pin_gcode(self, x, y, z, idx, extrusion_length, layer):
        """
        Helper function to generate G-code for a single pin at position (x, y) for a specific layer.

        Args:
            x (float): X position of the pin.
            y (float): Y position of the pin.
            z (float): Z height of the pin.
            idx (int): Index of the pin.
            extrusion_length (float): Amount of extrusion based on the pin's volume.
            layer (int): The current layer index.

        Returns:
            list: G-code lines for the given pin.
        """
        gcode_lines = [f"; Pin {idx} at layer {layer} (X{x:.2f} Y{y:.2f} Z{z:.2f})",
                       f"M117 Pin {idx} at layer {layer} ; Display message on printer screen",
                       "BLINK_LIGHT BLINK_COUNT=1 ; Call BLINK_LIGHT with custom parameters",
                       f"G1 F1500 E-{self.retraction_length:.4f} ; retract filament before extruding",
                       f"G91 ; relative",
                       f"G1 Z{self.z_hop_length:.2f} F{self.z_lift_speed} ; LIFT Z", f"G90 ; absolute",
                       f"G1 X{x:.2f} Y{y:.2f} F{self.xy_travel_speed} ; MOVE TO XY", f"G91 ; relative",
                       f"G1 Z-{self.z_hop_length:.2f} F{self.z_drop_speed} ; DROP Z to the height of the layer",
                       ]

        if self.diving_nozzle:
            gcode_lines.extend([f" - Pin Dropping - ",
                                "G90 ; absolute",
                                "M83 ; relative extrusion mode",
                                f"G1 F{self.z_drop_speed} Z{-self.pin_height_mm:.3f} ; sinking fully into hole",
                                f"G1 F{self.pinning_extrusion_speed} Z{self.pin_height_mm:.3f} "
                                f"      E{extrusion_length + self.retraction_length:.4f} ; lifting while extruding",
                                ])
        else:
            gcode_lines.extend(["G90 ; absolute",
                                "M83 ; relative extrusion mode",
                                f"G1 F{self.pinning_extrusion_speed} "
                                f"E{extrusion_length + self.retraction_length:.4f} ; extruding material after retraction",
                                ])

        gcode_lines.extend(["G90 ; absolute",
                            f"; End pin {idx} at layer {layer}",
                            ""
                            ])

        return gcode_lines

    def _calculate_extrusion_length(self):
        """
        Calculate the extrusion length based on the pin volume and filament cross-section.

        Returns:
            float: The calculated extrusion length.
        """
        if self.pin_shape == "circular":
            # Pin volume (cylinder): π * r^2 * h
            pin_radius = self.pin_dimension / 2
            pin_volume = math.pi * (pin_radius ** 2) * self.pin_height_mm
        elif self.pin_shape == "square":
            # Pin volume (prism with square cross-section): side^2 * height
            pin_volume = (self.pin_dimension ** 2) * self.pin_height_mm
        else:
            raise ValueError(f"Unknown pin shape: {self.pin_shape}")

        # Filament cross-sectional area: π * (filament_radius)^2
        filament_radius = self.FILAMENT_DIAMETER / 2
        filament_cross_section = math.pi * (filament_radius ** 2)

        # Extrusion length = pin volume / filament cross-sectional area, adjusted by the flow ratio
        extrusion_length = (pin_volume / filament_cross_section) * self.flow_ratio

        return extrusion_length