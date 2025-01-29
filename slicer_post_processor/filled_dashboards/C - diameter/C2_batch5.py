from pathlib import Path
from slicer_post_processor.pin_cross_section_definition import PinDefinition
from slicer_post_processor.gcode_snippets import GCodeCommandsComposer
from slicer_post_processor.gcode_modifier import GCodeModifier

# PINNING CONFIGURATION
infill_percentage = 33
pin_diameter = 2.4
num_pins_largest_side = 3
num_pins_smallest_side = 1
pin_height_layers = 14 * 2

stagger_params = {
    # "start_layer_offset": 5 * 10,  # Offset to apply between successive pins
    "fixed_start_layers": [14 * 2, 4 * 2, 9 * 2],  # Specific starting layers for pins
}

pin_rivet_parameters = {
    "cone_radius": 1.2,  # mm
    "cone_height": 0.4,  # mm
    "cylinder_radius": 0.9,  # mm
    "cylinder_height": 0.3  # mm/min
}  # pin_rivet_parameters = None

# SPECIMENS SHIFT
x_shift = 85.5  # mm 85.5
y_shift = 0  # mm 115.5

####################################################################################################
# PINNING ROUTINE PARAMETERS
flow_ratio = 0.91794  # 0.735

# PREVIOUS PINNING PARAMETERS
pinning_extrusion_speed = 30 * 60  # mm/min
nozzle_extrude_sunk = True  # (for diving sinking nozzle)
nozzle_sinking = 0.1  # mm (for diving nozzle)
nozzle_sinking_wait_time = 0  # seconds (for diving sinking nozzle)
variable_extrusion_enabled = False  # True or False
extrusion_skew_percentage = 100  # percentage 100 is 100%, 100 is equivalent to no skew

# FURTHER PINNING ROUTINE PARAMETERS
geometrical_extrusion_enabled = True
cone_blob = False
blob_feedrate = 100 * 60
no_pin_retraction = True
pressure_E_length = 0.5  # mm Set 0 to disable
pressure_E_speed = 100 * 60
####################################################################################################

# CONSTANT PINNING PARAMETERS
nozzle_outer_diameter = 1.45
retraction_length = 0.8  # mm
layer_height = 0.05  # mm
diving_mode = True  # True or False
wipe_enabled = True  # Enable wipe after pinning  # True or False
nozzle_sinking_1st_layer = True  # mm (for diving sinking nozzle)
nozzle_sinking_speed = 30.0 * 60  # mm/min (for diving sinking nozzle)

# Not used (only for diving nozzle)
spiral_mode = False  # only active for diving nozzle, True or False
rib_inside_protrusion = 0.00  # mm (for diving nozzle)
rib_clearance = 0.00  # mm (for diving nozzle)

# SPECIMEN GEOMETRY
specimen_height_mm = 67.320  # mm


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
        layer_height=layer_height,
        least_edge_margin=0.5,  # proportional to nozzle diameter and number of perimeters
        infill_percentage=infill_percentage
    )

    # Step 2: Define pins in the cross-section and visualize
    pin_cross_section_data = pin_def.define_pins_relative_xy()
    # pin_def.visualize_pin_layout()

    # Step 3: Setting parts number and position
    parts_on_build_plate = [
        {
            'name': 'part_1',
            'xy': (32 + x_shift, 27.5 + y_shift),
            'rotation': 90.0
        },
        {
            'name': 'part_2',
            'xy': (37 + x_shift, 27.5 + y_shift),
            'rotation': 90.0
        },
        {
            'name': 'part_3',
            'xy': (42 + x_shift, 27.5 + y_shift),
            'rotation': 90.0
        },
        {
            'name': 'part_4',
            'xy': (47 + x_shift, 27.5 + y_shift),
            'rotation': 90.0
        },
        {
            'name': 'part_5',
            'xy': (52 + x_shift, 27.5 + y_shift),
            'rotation': 90.0
        },
        # {
        #     'name': 'part_ll1',
        #     'xy': (135.0, 30.0),
        #     'rotation': 0.0
        # },
        # {
        #     'name': 'part_ll2',
        #     'xy': (147.15, 42.15),
        #     'rotation': 90.0
        # },
        # {
        #     'name': 'part_ll3',
        #     'xy': (135, 54.35),
        #     'rotation': 0.0
        # },
        # {
        #     'name': 'part_ll4',
        #     'xy': (122.85, 42.15),
        #     'rotation': 90.0
        # },
        # {
        #     'name': 'part_l1',
        #     'xy': (85.0, 30.0),
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
        retraction_length=retraction_length,  # mm
        z_drop_speed=10.0 * 60,  # mm/min
        wipe_speed=60.0 * 60,  # mm/min

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
        pin_rivet_parameters=pin_rivet_parameters,

        # FURTHER PINNING ROUTINE PARAMETERS
        geometrical_extrusion_enabled=geometrical_extrusion_enabled,
        cone_blob=cone_blob,
        blob_feedrate=blob_feedrate,
        no_pin_retraction=no_pin_retraction,
        pressure_E_length=pressure_E_length,
        pressure_E_speed=pressure_E_speed
    )

    gcode_lines, constants = snippet_composer.compose_layer_gcode()

    # Step 5: Process all G-code files in the 'gcodes' directory
    current_file_name = Path(__file__).stem
    script_dir = Path(__file__).parent
    gcode_dir = script_dir.parent.parent / "gcodes"

    for gcode_file in gcode_dir.glob(f"*{current_file_name}*.gcode"):
        gcode_modifier = GCodeModifier(gcode_file.stem, constants['layer_height'])
        gcode_modifier.read_gcode_file()
        gcode_modifier.insert_pin_gcode(gcode_lines, constants, start_layer=0)


if __name__ == "__main__":
    main()
