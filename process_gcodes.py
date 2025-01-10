import os

def remove_line_numbers_and_replace_text(file_path):
    temp_file_path = file_path + '.tmp'

    with open(file_path, 'r') as file, open(temp_file_path, 'w') as temp_file:
        # Process only the first line
        first_line = file.readline().replace("NematX", "Super")
        temp_file.write(first_line)

        # Copy the rest of the lines unchanged
        for line in file:
            temp_file.write(line)

    # Replace the original file with the modified file
    os.replace(temp_file_path, file_path)
    print(f"Processed and saved: {file_path}")

    # Rename the file by appending "_S" to the file name
    new_file_path = file_path.replace('.gcode', '_S.gcode')
    os.rename(file_path, new_file_path)
    print(f"Renamed file to: {new_file_path}")

def process_gcode_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.gcode') and not filename.endswith('_S.gcode'):
            file_path = os.path.join(directory, filename)
            remove_line_numbers_and_replace_text(file_path)

if __name__ == "__main__":
    gcode_directories = [
        'D:/TUDelft/Thesis/Engineering/mechanical_parts_development/3mf_projects_nematx_slicer/pinning_routine_testing/unpinned_gcodes',
        'D:/TUDelft/Thesis/Engineering/mechanical_parts_development/3mf_projects_nematx_slicer/specimens/gcodes',
        'D:/TUDelft/Thesis/Engineering/mechanical_parts_development/3mf_projects_nematx_slicer/hole_template_tuning/holes_XY_adjustments/0.2narrow'
    ]

    for gcode_directory in gcode_directories:
        process_gcode_files(gcode_directory)