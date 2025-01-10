from pathlib import Path
from slicer_post_processor.pin_cross_section_definition import PinDefinition
from slicer_post_processor.gcode_snippets import GCodeCommandsComposer
from slicer_post_processor.gcode_modifier import GCodeModifier

# PINNING CONFIGURATION
infill_percentage = 24
pin_diameter = 2
num_pins_largest_side = 3
num_pins_smallest_side = 1
pin_height_layers = 8

# PINNING ROUTINE PARAMETERS
diving_mode = True  # True or False

pinning_extrusion_speed = 30 * 60  # mm/min
flow_ratio = 0.75

nozzle_extrude_sunk = True  # (for diving sinking nozzle)
nozzle_sinking = 0.2  # mm (for diving nozzle
nozzle_sinking_1st_layer = False  # mm (for diving sinking nozzle)
nozzle_sinking_speed = 5.0 * 60  # mm/min (for diving sinking nozzle
nozzle_sinking_wait_time = 3  # seconds (for diving sinking nozzle)
stagger_params = {"start_layer_offset": 3,  # Offset to apply between successive pins
                  "fixed_start_layers": [8, 5, 3],  # Specific starting layers for pins
                }
pin_rivet_parameters = {"cone_radius": 0.7,  # mm
                        "cone_height": 0.4,  # mm
                        "cylinder_radius": 1,  # mm
                        "cylinder_height": 0.0  # mm/min
                        }
# pin_rivet_parameters = None

variable_extrusion_enabled = True  # True or False
extrusion_skew_percentage = 50  # percentage 50 is 50% >100 is necessary




wipe_enabled = True  # Enable wipe after pinning  # True or False

# Not used (only for diving nozzle)
spiral_mode = False  # only active for diving nozzle, True or False
rib_inside_protrusion = 0.00  # mm (for diving nozzle)
rib_clearance = 0.00  # mm (for diving nozzle)


# CONSTANT PINNING PARAMETERS
nozzle_outer_diameter = 1.45

# SPECIMEN GEOMETRY
specimen_height_mm = 10.0  # mm

def main():
    # Step 1: set pins parameters
    pin_def = PinDefinition(
        # cross-section parameters
        largest_side=10,
        smallest_side=4,

        # pin dimensions and layout parameters
        pin_dimension=pin_diameter,
        pin_shape='circular',  # either square or circular
        num_pins_largest_side=num_pins_largest_side,
        num_pins_smallest_side=num_pins_smallest_side,
        pin_height_input=pin_height_layers,
        pin_height_input_type="layers",  # either 'layers' or 'mm'

        # printing parameters
        layer_height=0.1,
        least_edge_margin=0.5,  # proportional to nozzle diameter and number of perimeters
        infill_percentage=infill_percentage
    )

    # Step 2: Define pins in the cross-section and visualize
    pin_cross_section_data = pin_def.define_pins_relative_xy()
    # pin_def.visualize_pin_layout()

    # Step 3: Setting parts number and position
    parts_on_build_plate = [
        # {
        #     'name': 'part_1',
        #     'xy': (85.0, 30.0),
        #     'rotation': 0.0
        # },
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
        # },
        {
            'name': 'part_ll1',
            'xy': (55.0, 30.0),
            'rotation': 0.0
        },
        {
            'name': 'part_ll2',
            'xy': (67.15, 42.15),
            'rotation': 90.0
        },
        {
            'name': 'part_ll3',
            'xy': (55.0, 54.35),
            'rotation': 0.0
        },
        {
            'name': 'part_ll4',
            'xy': (48.85, 42.15),
            'rotation': 90.0
        },
        # {
        #     'name': 'part_l1',
        #     'xy': (45.0, 30.0),
        #     'rotation': 0.0
        # },
        # {
        #     'name': 'part_l2',
        #     'xy': (52.05, 37.05),
        #     'rotation': 90.0
        # },
        # {
        #     'name': 'part_l3',
        #     'xy': (45.0, 44.1),
        #     'rotation': 0.0
        # },
        # {
        #     'name': 'part_l4',
        #     'xy': (37.95, 37.05),
        #     'rotation': 90.0
        # },
        # {
        #     'name': 'part_r1',
        #     'xy': (105.0, 30.0),
        #     'rotation': 0.0
        # },
        # {
        #     'name': 'part_r2',
        #     'xy': (112.05, 37.05),
        #     'rotation': 90.0
        # },
        # {
        #     'name': 'part_r3',
        #     'xy': (105.0, 44.1),
        #     'rotation': 0.0
        # },
        # {
        #     'name': 'part_r4',
        #     'xy': (97.95, 37.05),
        #     'rotation': 90.0
        # },

    ]

    # Step 4: Set printing parameters, import cross-section and parts position
    snippet_composer = GCodeCommandsComposer(
        pin_cross_section_data,
        parts_on_build_plate,

        # PRINTING GENERAL PARAMETERS
        specimen_height_mm=specimen_height_mm,
        flow_ratio=flow_ratio,
        pinning_extrusion_speed=pinning_extrusion_speed,  # mm/min
        z_lift_speed=25.0 * 60,  # mm/min
        xy_travel_speed=150.0 * 60,  # mm/min
        z_hop_length=0.2,  # mm
        retraction_length=0.5,  # mm
        z_drop_speed=10.0 * 60,  # mm/min
        wipe_speed=30.0 * 60,  # mm/min

        # PINNING ROUTINE PARAMETERS
        diving_mode=diving_mode,  # True or False
        spiral_mode=spiral_mode,  # only active for diving nozzle
        nozzle_outer_diameter=nozzle_outer_diameter,  # mm (for spiraling mode)
        rib_inside_protrusion=rib_inside_protrusion,  # mm (for diving nozzle)
        rib_clearance=rib_clearance,  # mm (for diving nozzle)
        nozzle_sinking=nozzle_sinking,  # mm
        nozzle_sinking_speed=nozzle_sinking_speed,  # mm/min
        nozzle_sinking_wait_time=nozzle_sinking_wait_time,  # seconds
        nozzle_sinking_1st_layer=nozzle_sinking_1st_layer,  # mm
        nozzle_extrude_sunk=nozzle_extrude_sunk,  # True or False
        wipe_enabled=wipe_enabled,  # Enable wipe after pinning  # True or False
        variable_extrusion_enabled=variable_extrusion_enabled,  # True or False
        extrusion_skew_percentage=extrusion_skew_percentage,  # percentage
        stagger_params=stagger_params,
        pin_rivet_parameters=pin_rivet_parameters
    )

    gcode_lines, constants = snippet_composer.compose_layer_gcode()

    # Step 5: Process all G-code files in the 'gcodes' directory
    current_file_name = Path(__file__).stem
    script_dir = Path(__file__).parent
    gcode_dir = script_dir.parent / "gcodes"

    for gcode_file in gcode_dir.glob(f"*{current_file_name}*.gcode"):
        gcode_modifier = GCodeModifier(gcode_file.stem)
        gcode_modifier.read_gcode_file()
        gcode_modifier.insert_pin_gcode(gcode_lines, constants, start_layer=0)


if __name__ == "__main__":
    main()
