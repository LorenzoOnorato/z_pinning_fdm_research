from pathlib import Path
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
        pin_dimension=2.75,
        pin_shape="circular",  # either square or circular
        num_pins_largest_side=1,
        num_pins_smallest_side=1,
        pin_height_input=5,
        pin_height_input_type="layers",  # either 'layers' or 'mm'

        # printing parameters
        layer_height=0.1,
        least_edge_margin=0.5,  # proportional to nozzle diameter and number of perimeters
        infill_percentage=15.0
    )

    # Step 2: Define pins in the cross-section and visualize
    pin_cross_section_data = pin_def.define_pins_relative_xy()
    # pin_def.visualize_pin_layout()

    # Step 3: Setting parts number and position
    parts_on_build_plate = [
        {
            'name': 'test_1',
            'xy': (85.0, 30.0),
            'rotation': 0.0
        },
        # {
        #     'name': 'part_2',
        #     'xy': (92.05, 37.05),
        #     'rotation': 90.0
        # },
        # {
        #     'name': 'part_3',
        #     'xy': (85.0, 44.1),
        #     'rotation': 0.0
        # },
        # {
        #     'name': 'part_4',
        #     'xy': (77.95, 37.05),
        #     'rotation': 90.0
        # }
    ]

    # Step 4: Set printing parameters, import cross-section and parts position
    snippet_composer = GCodeCommandsComposer(
        pin_cross_section_data,
        parts_on_build_plate,

        # PRINTING GENERAL PARAMETERS
        specimen_height_mm=10.0,
        flow_ratio=1.00,
        z_lift_speed=25.0 * 60,  # mm/min
        xy_travel_speed=150.0 * 60,  # mm/min
        z_hop_length=0.2,  # mm
        retraction_length=0.5,  # mm
        z_drop_speed=10.0 * 60,  # mm/min
        pinning_extrusion_speed=2.5 * 60,  # mm/min
        wipe_speed=30.0 * 60,  # mm/min

        # PINNING ROUTINE PARAMETERS
        heated_pin=False,  # number or False. Normal printing is hardcoded to 315
        diving_mode=True,  # True or False
        spiral_mode=True,  # only active for diving nozzle
        nozzle_outer_diameter=1.45,  # mm (for spiraling mode)
        rib_inside_protrusion=0.00,  # mm (for diving nozzle)
        rib_clearance=0.00,  # mm (for diving nozzle)
        nozzle_sinking=0.00,  # mm
        nozzle_sinking_speed=10.0 * 60,  # mm/min
        nozzle_sinking_wait_time=2,  # seconds
        nozzle_sinking_1st_layer=False,  # mm
        nozzle_extrude_sunk=True,  # True or False
        wipe_enabled=True,  # Enable wipe after pinning  # True or False
        variable_extrusion_enabled=True,  # True or False
        extrusion_skew_percentage=50,  # percentage
    )

    gcode_lines, constants = snippet_composer.compose_layer_gcode()

    # Step 5: Process all G-code files in the 'gcodes' directory
    script_dir = Path(__file__).parent
    gcode_dir = script_dir / "gcodes"

    for gcode_file in gcode_dir.glob("*.gcode"):
        gcode_modifier = GCodeModifier(gcode_file.stem)
        gcode_modifier.read_gcode_file()
        gcode_modifier.insert_pin_gcode(gcode_lines, constants, start_layer=0)


if __name__ == "__main__":
    main()
