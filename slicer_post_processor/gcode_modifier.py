import re
from pathlib import Path


def parse_gcode_lines(gcode_lines):
    """
    Parses G-code lines into a structured format.
    """
    parsed_gcode = []

    gcode_pattern = re.compile(r'(?P<command>[GMT]\d+)\s*(?P<params>[XYZEFIJKR].*)?\s*(?:;(?P<comment>.*))?')
    layer_pattern = re.compile(r'M117 Layer (\d+)', re.IGNORECASE)
    z_pattern = re.compile(r'Z(\d+\.?\d*)')

    current_layer = None
    previous_z = None

    for line in gcode_lines:
        # Check for layer number in the M117 Layer command
        layer_match = layer_pattern.search(line)
        if layer_match:
            current_layer = int(layer_match.group(1))

        # Check for Z-axis changes in G-code commands
        z_match = z_pattern.search(line)
        if z_match:
            z_value = float(z_match.group(1))
            if previous_z is not None and z_value != previous_z:
                current_layer = (current_layer or 0) + 1
            previous_z = z_value

        match = gcode_pattern.match(line)

        if match:
            command = match.group('command')
            params_str = match.group('params')
            comment = match.group('comment')

            params = {}
            if params_str:
                param_pairs = params_str.split()
                for param_pair in param_pairs:
                    key = param_pair[0]
                    value_str = param_pair[1:]
                    value_str = value_str.split(';')[0]
                    try:
                        value = float(value_str)
                    except ValueError:
                        value = value_str
                    params[key] = value

            parsed_line = {
                'command': command,
                'params': params,
                'comment': comment if comment else "",
                'layer': current_layer
            }

            parsed_gcode.append(parsed_line)
        else:
            parsed_gcode.append({
                'command': None,
                'params': {},
                'comment': line.strip(),
                'layer': current_layer,
            })

    return parsed_gcode

class GCodeModifier:
    def __init__(self, filename):
        self.filename = filename
        self.gcode_lines = None
        self.parsed_gcode_lines = None
        self.modified_gcode_lines = []

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

        self.parsed_gcode_lines = parse_gcode_lines(self.gcode_lines)

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
        current_layer = 0
        interval = constants["pin_height_layers"]
        header_pin_inserted = False  # Track if pinning header has been inserted
        object_printing_started = False  # Track when the object starts printing

        for line in parsed_gcode:
            # HEADER PINNING PARAMETERS
            if not object_printing_started and "; printing object" in line.get('comment', ''):
                object_printing_started = True  # Start counting layers from this point

            # Insert constants block just before ; EXECUTABLE_BLOCK_START
            if not header_pin_inserted and "; EXECUTABLE_BLOCK_START" in line.get('comment', ''):
                modified_gcode.append({'comment': ""})  # Add a blank line before the constants block
                modified_gcode.extend(constant_comments)
                modified_gcode.append({'comment': ""})  # Add a blank line after the constants block
                header_pin_inserted = True  # Ensure we only insert the header once

            # ACTUAL PINNING GCODE
            if ";LAYER_CHANGE" in line.get('comment', ''):
                current_layer += 1

                # Insert pinning G-code if it's the correct layer
                if current_layer >= start_layer and (current_layer - start_layer) % interval == 0:
                    if current_layer in pin_gcode_dict:
                        modified_gcode.append({'comment': ""})  # Add a blank line
                        modified_gcode.append({'comment': ""})  # Add a blank line
                        for pin_line in pin_gcode_dict[current_layer]:
                            modified_gcode.append(
                                pin_line)  # Directly append the pin_line (which is already a dictionary)

            modified_gcode.append(line)

        # Convert modified_gcode (list of dictionaries) to string format
        for gcode_dict in modified_gcode:
            gcode_string = self._convert_dict_to_gcode(gcode_dict)
            self.modified_gcode_lines.append(gcode_string)

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
        if constants["diving_nozzle"]:
            output_file_path = output_dir / f"{self.filename}_diving_nozzle_postprocessed.gcode"
        else:
            output_file_path = output_dir / f"{self.filename}_postprocessed.gcode"

        with open(output_file_path, 'w') as file:
            for line in self.modified_gcode_lines:
                file.write(f"{line}\n")

        print(f"Modified gcode saved to {output_file_path}")
