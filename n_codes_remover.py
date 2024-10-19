def remove_line_numbers_and_replace_text(input_file, output_file):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    # Process each line to remove the N+number prefix and replace text if needed
    cleaned_lines = []
    for i, line in enumerate(lines):
        # Replace "Nematx" with "Super" in the first line
        if i == 0:
            line = line.replace("Nematx", "Super")

        # Split by space and check if the first part is a line number
        parts = line.strip().split(' ', 1)
        if len(parts) > 1 and parts[0].startswith('N') and parts[0][1:].isdigit():
            # Remove the line number part and keep the rest
            cleaned_lines.append(parts[1] + '\n')
        else:
            # If no line number, keep the line as it is
            cleaned_lines.append(line)

    # Write the cleaned lines to the output file
    with open(output_file, 'w') as file:
        file.writelines(cleaned_lines)
        print("Completed cleaning and updating the G-code file")

# Example usage
gcode_filename = 'thumbnail_test'
input_gcode_path = 'D:/TUDelft/Thesis/mechanical parts development/nematx_slicer_projects/' + gcode_filename + '.gcode'
output_gcode_path = 'D:/TUDelft/Thesis/mechanical parts development/nematx_slicer_projects/' + gcode_filename + '_cleaned.gcode'
remove_line_numbers_and_replace_text(input_gcode_path, output_gcode_path)
