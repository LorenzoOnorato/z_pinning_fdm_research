import math
from slicer_post_processor.gcode_modifier import parse_gcode_lines
import math


def _apply_transformation(pin_positions, translation_xy, rotation_angle, cross_section_x_dim, cross_section_y_dim):
    """
    Apply translation and rotation transformations to the pin positions, considering the center of the specimen.

    Args:
        pin_positions (list): List of tuples representing the original pin positions (X, Y).
        translation_xy (tuple): XY translation values as (x_translation, y_translation).
        rotation_angle (float): Rotation angle in degrees.
        cross_section_x_dim (float): Dimension of the cross-section oriented in the x direction after rotation.

    Returns:
        list: Transformed pin positions.
    """
    x_translation, y_translation = translation_xy
    angle_rad = math.radians(rotation_angle)
    cos_theta = math.cos(angle_rad)
    sin_theta = math.sin(angle_rad)

    # Adjust the x_translation by half of the cross-section dimension in the x direction
    x_translation -= (cross_section_x_dim / 2) * cos_theta - (cross_section_y_dim / 2) * sin_theta
    y_translation -= (cross_section_x_dim / 2) * sin_theta + (cross_section_y_dim / 2) * cos_theta

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
                 pinning_extrusion_speed, diving_mode, spiral_mode, nozzle_outer_diameter,
                 rib_inside_protrusion, rib_clearance, nozzle_sinking, nozzle_sinking_speed, nozzle_sinking_wait_time,
                 nozzle_sinking_1st_layer, nozzle_extrude_sunk, wipe_enabled, wipe_speed, variable_extrusion_enabled,
                 extrusion_skew_percentage, heated_pin=False, stagger_params=None, pin_rivet_parameters=None):

        # FROM pin_cross_section_definition.py
        self.pin_positions = pin_data["pins_relative_xy"]

        # FROM pin_cross_section_definition.py (itself from dashboard.py)
        self.largest_side = pin_data["largest_side"]
        self.smallest_side = pin_data["smallest_side"]
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
        self.rib_clearance = rib_clearance
        self.wipe_speed = wipe_speed

        self.diving_mode = diving_mode
        self.heated_pin = heated_pin
        self.spiral_mode = spiral_mode
        self.nozzle_outer_diameter = nozzle_outer_diameter
        self.rib_inside_protrusion = rib_inside_protrusion
        self.nozzle_sinking = nozzle_sinking
        self.nozzle_sinking_speed = nozzle_sinking_speed
        self.nozzle_sinking_wait_time = nozzle_sinking_wait_time
        self.wipe_enabled = wipe_enabled
        self.nozzle_sinking_1st_layer = nozzle_sinking_1st_layer
        self.variable_extrusion_enabled = variable_extrusion_enabled
        self.extrusion_skew_percentage = extrusion_skew_percentage
        self.nozzle_extrude_sunk = nozzle_extrude_sunk
        self.stagger_params = stagger_params
        self.pin_rivet_parameters = pin_rivet_parameters

        # calculated
        self.total_layers = int(self.specimen_height_mm / self.layer_height)
        if self.pin_height_mm > 0 and self.layer_height > 0:
            self.pin_height_layers = int(self.pin_height_mm / self.layer_height)
        else:
            self.pin_height_layers = 0  # Handle the case where pin height or layer height is invalid

        self.pins_absolute_xy_per_part = {
            part['name']: _apply_transformation(self.pin_positions, part['xy'], part['rotation'], self.largest_side,
                                                self.smallest_side)
            for part in self.parts_dict}

        self.pins_absolute_xy = None

    def _generate_staggered_pinning_schedule(self):
        """"
        Generate a staggered pinning schedule based on the pin height and the number of layers in the specimen.

        Returns:
            dict: Staggered pinning schedule with layer numbers as keys and pin actions as values.

        """
        staggered_schedule = {}  # Output schedule
        pin_height_layers = self.pin_height_layers  # Number of layers each pin spans
        num_pins = len(self.pin_positions)  # Total number of pins

        # Initialize staggering parameters
        start_layer_offset = self.stagger_params.get("start_layer_offset",
                                                pin_height_layers // num_pins) if self.stagger_params else (
                    pin_height_layers // num_pins)
        fixed_start_layers = self.stagger_params.get("fixed_start_layers", None) if self.stagger_params else None

        # Iterate through pins
        for pin_idx in range(len(self.pin_positions)):
            # Determine the start layer
            if fixed_start_layers:
                start_layer = fixed_start_layers[pin_idx % len(fixed_start_layers)]
            else:
                start_layer = pin_idx * start_layer_offset + 1

            # Iterate through the layers for this pin
            for layer in range(start_layer, self.total_layers + pin_height_layers, pin_height_layers):

                if layer == start_layer:
                    pin_height = start_layer
                elif layer >= self.total_layers:
                    pin_height = pin_height_layers - (layer - self.total_layers)
                    layer = self.total_layers
                else:
                    pin_height = pin_height_layers

                # Add to the schedule
                if layer not in staggered_schedule:
                    staggered_schedule[layer] = []
                staggered_schedule[layer].append({
                    "pin_index": pin_idx,
                    "height_layers": pin_height
                })

        return staggered_schedule

    def compose_layer_gcode(self):

        # Generate the staggered pinning schedule
        staggered_schedule = self._generate_staggered_pinning_schedule()
        gcode_lines_per_layer = {}

        for layer in range(1, self.total_layers + 1):
            if layer not in staggered_schedule:
                continue
        # for layer, pin_actions in staggered_schedule.items():
            gcode_lines = []
            gcode_lines.append(f";--- PINNING LAYER {layer} (Z = {layer * self.layer_height}) ---")
            gcode_lines.append(f"M83 ; relative extrusion mode")
            gcode_lines.append(f"G1 F1500 E{self.retraction_length:.3f} ; de-retract filament")
            gcode_lines.append("")

            if self.heated_pin is not False:
                gcode_lines.extend([
                    f";- HEATING NOZZLE -",
                    f"M104 S{self.heated_pin} ; set pin temperature",
                    f"M109 S{self.heated_pin} ; wait for it",
                    ""
                ])

            # Process pinning actions for this layer for each part
            for part_name, part_pins_absolute_xy in self.pins_absolute_xy_per_part.items():
                gcode_lines.append(f";- PINNING PART {part_name} -")
                for pin in staggered_schedule[layer]:
                    x, y = part_pins_absolute_xy[pin["pin_index"]]
                    gcode_lines.extend(self._generate_pin_gcode(x, y, layer, pin["pin_index"], pin["height_layers"]))

            if self.heated_pin is not False:
                gcode_lines.extend([
                    f";- COOLING NOZZLE -",
                    f"M104 S{315} ; back to printing temperature",
                    f"M109 S{315} ; wait for it",
                    ""
                ])

            gcode_lines.append(f"G1 F1500 E-{self.retraction_length:.3f} ; retract filament")
            gcode_lines.append(f"M82 ; absolute extrusion mode")
            gcode_lines.append(f";--- END OF PINNING LAYER {layer} ---")
            gcode_lines.append("")

            # Store the generated G-code for this layer
            gcode_lines_per_layer[layer] = parse_gcode_lines(gcode_lines, self.layer_height)

        # Prepare constants for debugging or reference
        constants = {
            "pin_positions": self.pin_positions,
            "staggered_schedule": staggered_schedule,
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
            "diving_mode": self.diving_mode,
            "heated_pin": self.heated_pin,
            "spiral_mode": self.spiral_mode,
            "nozzle_outer_diameter": self.nozzle_outer_diameter,
            "rib_inside_protrusion": self.rib_inside_protrusion,
            "rib_clearance": self.rib_clearance,
            "nozzle_sinking": self.nozzle_sinking,
            "nozzle_sinking_speed": self.nozzle_sinking_speed,
            "nozzle_sinking_wait_time": self.nozzle_sinking_wait_time,
            "nozzle_sinking_1st_layer": self.nozzle_sinking_1st_layer,
            "wipe_enabled": self.wipe_enabled,
            "wipe_speed": self.wipe_speed,
            "variable_extrusion_enabled": self.variable_extrusion_enabled,
            "extrusion_skew_percentage": self.extrusion_skew_percentage
        }

        print("Pinning G-code composition for multiple parts: completed successfully.")

        return gcode_lines_per_layer, constants

    def _generate_pin_gcode(self, x, y, layer, idx, current_pin_height):

        # Relevant for diving_mode
        gcode_commands_per_layer = 1

        pin_layer_z = self.layer_height * layer
        z = pin_layer_z
        current_pin_height *= self.layer_height
        if self.pin_rivet_parameters:
            tot_E_pin = self._rivet_like_pin_extrusion_length(current_pin_height)
        else:
            tot_E_pin = self._calculate_extrusion_length(self.pin_dimension, current_pin_height)

        gcode_lines = []
        gcode_lines.append(f"; Pin {idx + 1} (X{x:.3f} Y{y:.3f} Z{z:.3f})")
        gcode_lines.append(f"M117 Pin {idx + 1} at layer {layer}")
        gcode_lines.append(f"G1 F1500 E{-self.retraction_length:.6f} ; retract filament before lifting")
        gcode_lines.append(f"G1 Z{pin_layer_z + self.z_hop_length:.3f} F{self.z_lift_speed} ; LIFT Z")
        gcode_lines.append(f"G1 X{x:.3f} Y{y:.3f} F{self.xy_travel_speed} ; MOVE TO XY")
        gcode_lines.append(f"G1 F1500 E{self.retraction_length:.6f} ; de-retract filament before pinning")
        gcode_lines.append(f"G1 Z{pin_layer_z:.3f} F{self.xy_travel_speed} ; DROP Z to the height of the layer")

        if self.diving_mode:
            z -= current_pin_height
            gcode_lines.append(
                f"G1 Z{z:.3f} F{self.z_drop_speed} ; DROP Z to the bottom of the pin")

        if self.nozzle_sinking and (z > self.nozzle_sinking or self.nozzle_sinking_1st_layer):
            gcode_lines.append(f"G1 Z{z - self.nozzle_sinking:.3f} F{self.nozzle_sinking_speed} ; SINKING NOZZLE")
            gcode_lines.append(f"G4 P{self.nozzle_sinking_wait_time * 1000} ; WAIT")
            if not self.nozzle_extrude_sunk:
                gcode_lines.append(f"G1 Z{z:.3f} F{self.nozzle_sinking_speed} ; LIFTING NOZZLE")

        gcode_lines.append(f"; EXTRUDING PIN")

        if self.diving_mode:
            E_layers = int(current_pin_height / self.layer_height)
            gcode_command_extrusion_length = tot_E_pin / E_layers / gcode_commands_per_layer
            step_height = self.layer_height / gcode_commands_per_layer
            spiral_radius = (self.pin_dimension / 2) - (
                    self.nozzle_outer_diameter / 2) - self.rib_inside_protrusion - self.rib_clearance

            if self.spiral_mode and spiral_radius >= 0.2:
                angle_step = 360 / gcode_commands_per_layer
            elif not self.spiral_mode:
                angle_step = 0
                spiral_radius = 0
            else:
                raise ValueError(
                    f"The available distance between nozzle and part is too small to have spiral pinning. \n"
                    f"The spiral radius would be {spiral_radius:.2f} mm.")

            for step in range(1, int(current_pin_height / step_height) + 1):
                current_z = z + step * step_height
                current_x = x + spiral_radius * math.cos(math.radians(step * angle_step))
                current_y = y + spiral_radius * math.sin(math.radians(step * angle_step))
                adjusted_feedrate = self.pinning_extrusion_speed
                if self.variable_extrusion_enabled and (E_layers - gcode_commands_per_layer) != 0:
                    skew_factor = (self.extrusion_skew_percentage / 100.0) * (
                            1 - 2 * (step - 1) / (E_layers * gcode_commands_per_layer - 1))
                    gcode_command_extrusion_length = tot_E_pin / (E_layers * gcode_commands_per_layer)
                    gcode_command_extrusion_length *= (1 + skew_factor)
                    distance_total = math.sqrt((current_x - x) ** 2 + (current_y - y) ** 2 + (
                            current_z - z - step * step_height) ** 2 + gcode_command_extrusion_length ** 2)
                    adjusted_feedrate = self.pinning_extrusion_speed * (distance_total / gcode_command_extrusion_length)

                gcode_lines.append(
                    f"G1 X{current_x:.2f} Y{current_y:.2f} Z{current_z:.2f} E{gcode_command_extrusion_length:.4f} "
                    f"F{adjusted_feedrate:.2f} ; extruding")
        else:
            gcode_lines.append(f"G1 E{tot_E_pin:.4f} F{self.pinning_extrusion_speed}  ; extruding")

        if self.nozzle_extrude_sunk:
            gcode_lines.append(f"G1 Z{pin_layer_z:.3f} F{self.nozzle_sinking_speed} ; LIFTING NOZZLE from sunk")

        gcode_lines.append(f"G4 P{1 * 1000} ; WAIT")

        if self.wipe_enabled:
            gcode_lines.append(f"; WIPING")
            gcode_lines.extend(self._generate_wipe_gcode(x, y, (self.pin_dimension / 2 - 0.1), 5,
                                                         12, self.wipe_speed))

            gcode_lines.extend(self._generate_wipe_gcode(x, y, (self.pin_dimension / 2 + 1), 7,
                                                         12, self.wipe_speed, reverse=True,
                                                         stop_radius=(self.pin_dimension / 2 - 0.1)))
        gcode_lines.extend([
            f"; End pin {idx + 1} at layer {layer}",
            ""
        ])

        return gcode_lines

    def _calculate_extrusion_length(self, pin_dimension, pin_height):
        """
        Calculate the extrusion length based on the pin volume and filament cross-section.

        Returns:
            float: The calculated extrusion length.
        """
        if self.pin_shape == "circular":
            # Pin volume (cylinder): π * r^2 * h
            pin_radius = pin_dimension / 2
            pin_volume = math.pi * (pin_radius ** 2) * pin_height
        elif self.pin_shape == "square":
            # Pin volume (prism with square cross-section): side^2 * height
            pin_volume = (pin_dimension ** 2) * pin_height
        else:
            raise ValueError(f"Unknown pin shape: {self.pin_shape}")

        # Filament cross-sectional area: π * (filament_radius)^2
        filament_radius = self.FILAMENT_DIAMETER / 2
        filament_cross_section = math.pi * (filament_radius ** 2)

        # Extrusion length = pin volume / filament cross-sectional area, adjusted by the flow ratio
        extrusion_length = (pin_volume / filament_cross_section) * self.flow_ratio

        return extrusion_length

    def _generate_wipe_gcode(self, x, y, spiral_radius, num_turns, points_per_turn, travel_speed, reverse=None,
                             stop_radius=None):

        wipe_gcode = []
        total_points = num_turns * points_per_turn  # Total number of points to generate

        for i in range(total_points):
            if reverse:
                i = total_points - i - 1
            angle = i * (360 / points_per_turn)  # Angle for each point
            current_radius = spiral_radius * (i / total_points)  # Incrementally increase the radius
            if stop_radius and current_radius < stop_radius:
                break
            x_offset = x + current_radius * math.cos(math.radians(angle))
            y_offset = y + current_radius * math.sin(math.radians(angle))
            wipe_gcode.append(
                f"G1 X{x_offset:.3f} Y{y_offset:.3f} F{travel_speed} ; spiral wipe"
            )

        # Add an extra full circle at the end
        for i in range(points_per_turn):
            angle = i * (360 / points_per_turn)  # Angle for each point
            x_offset = x + spiral_radius * math.cos(math.radians(angle))
            y_offset = y + spiral_radius * math.sin(math.radians(angle))
            wipe_gcode.append(
                f"G1 X{x_offset:.3f} Y{y_offset:.3f} F{travel_speed} ; extra full circle"
            )

        return wipe_gcode

    def _rivet_like_pin_extrusion_length(self, pin_height):
        smaller_radius = self.pin_rivet_parameters["cylinder_radius"]
        larger_radius = self.pin_rivet_parameters["cone_radius"]
        cylinder_height = self.pin_rivet_parameters["cylinder_height"] * 2
        cone_height = self.pin_rivet_parameters["cone_height"]
        pin_height = round(pin_height, 5)

        # Calculate the volume of one truncated cone
        cone_volume = self._calculate_truncated_cone_volume(smaller_radius, larger_radius, cone_height)

        if pin_height <= cone_height:
            # Only the conical part
            adjusted_cone_volume = self._calculate_truncated_cone_volume(smaller_radius,
                                                                         smaller_radius + (
                                                                                     larger_radius - smaller_radius) * (
                                                                                     pin_height / cone_height),
                                                                         pin_height)
            pin_volume = adjusted_cone_volume
        elif (cone_height + cylinder_height) >= pin_height > cone_height:
            # One full cone and part of the cylinder
            adjusted_cylinder_volume = math.pi * (smaller_radius ** 2) * (pin_height - cone_height)
            pin_volume = cone_volume + adjusted_cylinder_volume
        elif (cone_height + cylinder_height) < pin_height <= (2 * cone_height + cylinder_height):
            # One full cone, full cylinder, and part of the second cone
            adjusted_cone_height = pin_height - (cone_height + cylinder_height)
            adjusted_cone_volume = self._calculate_truncated_cone_volume(smaller_radius,
                                                                         smaller_radius + (
                                                                                     larger_radius - smaller_radius) * (
                                                                                     (pin_height - (cone_height + cylinder_height))
                                                                                     / cone_height), adjusted_cone_height)
            cylinder_volume = math.pi * (smaller_radius ** 2) * cylinder_height
            pin_volume = cone_volume + cylinder_volume + adjusted_cone_volume
        else:
            print(f"Pin height {pin_height}")

        # Filament cross-sectional area: π * (filament_radius)^2
        filament_radius = self.FILAMENT_DIAMETER / 2
        filament_cross_section = math.pi * (filament_radius ** 2)

        # Extrusion length = pin volume / filament cross-sectional area, adjusted by the flow ratio
        extrusion_length = (pin_volume / filament_cross_section) * self.flow_ratio

        return extrusion_length

    def _calculate_truncated_cone_volume(self, smaller_radius, larger_radius, height):
        return (1 / 3) * math.pi * height * (smaller_radius ** 2 + smaller_radius * larger_radius + larger_radius ** 2)