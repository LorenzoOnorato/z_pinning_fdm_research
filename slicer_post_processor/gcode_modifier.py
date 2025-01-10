import re
from pathlib import Path


def parse_gcode_lines(gcode_lines, layer_height):
    """
    Parses G-code lines into a structured format.
    """
    parsed_gcode = []

    gcode_pattern = re.compile(r'(?P<command>[GMT]\d+)\s*(?P<params>[XYZEFIJKR0-9.\s-]*)\s*(?P<comment>.*)?')
    # layer_pattern = re.compile(r'M117 Layer (\d+)', re.IGNORECASE)
    z_pattern = re.compile(r';Z:(-?\d+\.?\d*)')

    current_layer = None
    previous_z = 0

    for line in gcode_lines:
        # Check for layer number in the M117 Layer command
        # layer_match = layer_pattern.search(line)
        # if layer_match:
        #     current_layer = int(layer_match.group(1))

        # Check for Z-axis changes in G-code commands
        z_match = z_pattern.search(line)
        if z_match:
            previous_z = float(z_match.group(1))

        match = gcode_pattern.match(line)

        if match:
            command = match.group('command')
            params = match.group('params').strip()
            comment = match.group('comment').strip() if match.group('comment') else ''
            param_dict = {}

            if params:
                param_pairs = params.split()
                for pair in param_pairs:
                    key = pair[0]
                    value = pair[1:] if len(pair) > 1 else ''
                    param_dict[key] = value

            parsed_gcode.append({
                'command': command,
                'params': param_dict,
                'comment': comment,
                'layer': round(previous_z / layer_height, 2)
            })
        else:
            parsed_gcode.append({
                'command': None,
                'params': {},
                'comment': line.strip(),
                'layer': round(previous_z / layer_height, 2)
            })

    return parsed_gcode

class GCodeModifier:
    def __init__(self, filename, layer_height):
        self.filename = filename
        self.gcode_lines = None
        self.parsed_gcode_lines = None
        self.modified_gcode_lines = []
        self.layer_height = layer_height

    def read_gcode_file(self):
        """
        Reads a G-code file and stores the G-code lines.
        """
        script_dir = Path(__file__).parent
        gcode_dir = script_dir / "gcodes"
        gcode_file_path = gcode_dir / f"{self.filename}.gcode"

        if not gcode_file_path.is_file():
            raise FileNotFoundError(f"G-code file not found: {gcode_file_path}")

        with open(gcode_file_path, 'r') as file:
            self.gcode_lines = [line.strip() for line in file.readlines()]

        self.parsed_gcode_lines = parse_gcode_lines(self.gcode_lines, self.layer_height)

    def insert_pin_gcode(self, pin_gcode_dict, constants, start_layer=0):
        """
        Inserts the pinning G-code into the original G-code at the specified layers.

        Args:
            pin_gcode_dict (dict): Dictionary containing G-code for each layer.
            constants (dict): Dictionary of constants like pin height, interval, etc.
            start_layer (int): Layer to start inserting pins.
        """

        # Generate the constant info as G-code comments
        constant_comments = []
        constant_comments.append({'comment': "; HEADER PINNING PARAMETERS"})
        for key, value in constants.items():
            constant_comments.append({'comment': f"; {key}: {value}"})

        parsed_gcode = self.parsed_gcode_lines
        modified_gcode = []
        header_pin_inserted = False  # Track if pinning header has been inserted
        object_printing_started = False  # Track when the object starts printing
        last_layer_pinned = False  # Track if the last layer was pinned

        for line in parsed_gcode:
            # HEADER PINNING PARAMETERS
            if not object_printing_started and "; printing object" in line.get('comment', ''):
                object_printing_started = True  # Start counting layers from this point

            # Insert constants block just before ; thumbnail begin
            if not header_pin_inserted and "; thumbnail begin" in line.get('comment', ''):
                modified_gcode.append({'comment': ""})  # Add a blank line before the constants block
                modified_gcode.extend(constant_comments)
                modified_gcode.append({'comment': ""})  # Add a blank line after the constants block
                header_pin_inserted = True  # Ensure we only insert the header once

            # ACTUAL PINNING GCODE
            if "move to next layer" in line.get('comment', ''):
                if (line['layer'] - 1) in pin_gcode_dict and line['layer'] >= start_layer:
                    modified_gcode.append({'comment': ""})  # Add a blank line
                    modified_gcode.append({'comment': ""})  # Add a blank line
                    for pin_line in pin_gcode_dict[(line['layer'] - 1)]:
                        modified_gcode.append(pin_line)  # Directly append the pin_line (which is already a dictionary)
            elif "end_gcode" in line.get('comment', '') and not last_layer_pinned:
                modified_gcode.append({'comment': ""})  # Add a blank line
                modified_gcode.append({'comment': ""})  # Add a blank line
                for pin_line in pin_gcode_dict[(line['layer'])]:
                    modified_gcode.append(pin_line)  # Directly append the pin_line (which is already a dictionary)
                last_layer_pinned = True


            modified_gcode.append(line)

        # Convert modified_gcode (list of dictionaries) to string format
        self.modified_gcode_lines = [self._convert_dict_to_gcode(gcode_dict) for gcode_dict in modified_gcode]

        self.save_gcode(constants)

    def _convert_dict_to_gcode(self, gcode_dict):
        """
        Converts a G-code dictionary back into a string format for saving.

        Args:
            gcode_dict (dict): Dictionary containing 'command', 'params', and 'comment'.

        Returns:
            str: The corresponding G-code line in string format.
        """
        gcode_line = ""

        # If there's a command, add it
        if gcode_dict.get('command'):
            gcode_line += gcode_dict['command']
            # If there are parameters, format them as 'key=value' pairs
            if gcode_dict.get('params'):
                for param, value in gcode_dict['params'].items():
                    gcode_line += f" {param}{value}"

        # If there's a comment, append it after the command/params
        if gcode_dict.get('comment'):
            if gcode_line:
                gcode_line += " "  # Add a space before the comment if there's already a command/params
            gcode_line += gcode_dict['comment']

        return gcode_line

    def save_gcode(self, constants):
        """
        Saves the modified G-code to a file.
        """
        script_dir = Path(__file__).parent
        output_dir = script_dir / "post_processed_gcodes"
        output_dir.mkdir(exist_ok=True)
        filename_suffix = ""

        filename_suffix += "_phl" + str(constants["pin_height_layers"])
        if constants["diving_mode"] is True:
            filename_suffix += "_dv"
        else:
            filename_suffix += "_top"
        if constants["heated_pin"] is not False:
            filename_suffix += f"_hp{constants['heated_pin']}"
        if constants["nozzle_sinking"] != 0:
            filename_suffix += f"_sk{constants['nozzle_sinking']}"
        if constants["nozzle_sinking"] != 0:
            filename_suffix += f"skw{constants['nozzle_sinking_wait_time']}"
        if constants["spiral_mode"]:
            filename_suffix += "_spT"
        if constants["rib_inside_protrusion"] != 0:
            filename_suffix += f"_rb{constants['rib_inside_protrusion']}"
        if constants["rib_clearance"] != 0:
            filename_suffix += f"_rbc{constants['rib_clearance']}"
        if constants["variable_extrusion_enabled"] and constants["extrusion_skew_percentage"] != 0:
            filename_suffix += f"_ve{constants['extrusion_skew_percentage']}"
        if constants["wipe_enabled"]:
            filename_suffix += "_wp"

        output_file_path = output_dir / f"{self.filename.replace('_CL', '')}{filename_suffix}.gcode"

        with open(output_file_path, 'w') as file:
            for line in self.modified_gcode_lines:
                file.write(f"{line}\n")

        print(f"Modified gcode saved to {output_file_path}")
