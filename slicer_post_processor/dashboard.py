# dashboard.py

from pin_cross_section_definition import PinDefinition
from gcode_snippets import GCodeCommandsComposer
from gcode_modifier import GCodeModifier


def main():
    # Step 1: set pins parameters
    pin_def = PinDefinition(
        # cross-section parameters
        largest_side=10.0,
        smallest_side=4.0,

        # pin dimensions and layout parameters
        pin_dimension=0.5,
        pin_shape="square",  # either square or circular
        num_pins_largest_side=2,
        num_pins_smallest_side=1,
        pin_height_input=5,
        pin_height_input_type="layers",  # either 'layers' or 'mm'

        # printing parameters
        layer_height=0.12,
        least_edge_margin=0.5,  # proportional to nozzle diameter and number of perimeters
        infill_percentage=1.0
    )

    # Step 2: Define pins in the cross-section and visualize
    pin_cross_section_data = pin_def.define_pins_relative_xy()
    # pin_def.visualize_pin_layout()

    # Step 3: Setting parts number and position
    parts_on_build_plate = [
        {
            'name': 'part_1',
            'xy': (0.0, 0.0),
            'rotation': 0.0
        },
        {
            'name': 'part_2',
            'xy': (10.0, 10.0),
            'rotation': 0.0
        }
    ]

    # Step 4: Set printing parameters, import cross-section and parts position
    snippet_composer = GCodeCommandsComposer(
        pin_cross_section_data,

        parts_on_build_plate,

        specimen_height_mm=7.32,
        flow_ratio=1.0,

        z_lift_speed=25.0,
        xy_travel_speed=150.0,
        z_hop_length=0.2,
        retraction_length=0.1,
        z_drop_speed=10.0,
        pinning_extrusion_speed=5.0,

        diving_nozzle=True
    )

    gcode_lines, constants = snippet_composer.compose_parts_gcode()

    # Step 4: G-code modification
    gcode_modifier = GCodeModifier('tensile_dogbone_virgin')
    gcode_modifier.read_gcode_file()
    gcode_modifier.insert_pin_gcode(gcode_lines, constants, start_layer=0)


if __name__ == "__main__":
    main()
