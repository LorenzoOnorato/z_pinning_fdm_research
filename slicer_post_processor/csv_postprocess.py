import os
import csv

def process_csv_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            process_csv_file(file_path)

def process_csv_file(file_path):
    with open(file_path, mode='r', newline='') as file:
        reader = csv.reader(file)
        headers = next(reader)
        rows = list(reader)

    # Add new headers if they don't exist
    if len(headers) < 9:
        headers.extend(["tot_E", "tot_t", "t", "feedrate", "avg_speed", "max_speed"])
        print(f"Added new headers. Virgin file being edited.")
    else:
        print(f"Overwriting file.")

    incremental_e = 0
    time_elapsed = 0
    previous_f = 0
    previous_e = 0

    for i, row in enumerate(rows):
        z_value = float(row[0])
        e_value = float(row[1])
        f_value = float(row[2])
        incremental_e += e_value

        if i == 0:
            previous_f = 0
            z_diff = 0
        else:
            previous_z = float(rows[i-1][0])
            previous_f = float(rows[i-1][2])
            z_diff = abs(z_value - previous_z)

        e_diff = abs(e_value)

        acceleration_z = 30  # mm/s^2
        acceleration_e = 3000  # mm/s^2
        previous_speed_z = previous_f / 60  # Convert to mm/s
        current_speed_z = f_value / 60  # Convert to mm/s
        previous_speed_e = previous_f / 60  # Convert to mm/s
        current_speed_e = f_value / 60  # Convert to mm/s

        time_z = calculate_ramp_time(previous_speed_z, current_speed_z, z_diff, acceleration_z)
        time_e = calculate_ramp_time(previous_speed_e, current_speed_e, e_diff, acceleration_e)

        time_for_current_move = max(time_z, time_e)

        time_elapsed += time_for_current_move
        feedrate = e_value / time_for_current_move if time_for_current_move != 0 else 0

        avg_speed = (previous_f + f_value) / 2  # Average speed in mm/min
        max_speed = f_value  # Maximum speed at the end of the movement

        # Overwrite or add new columns
        if len(row) >= 9:
            row[3] = round(incremental_e, 4)
            row[4] = round(time_elapsed, 4)
            row[5] = round(time_for_current_move, 4)
            row[6] = round(feedrate, 4)
            row[7] = round(avg_speed, 4)
            row[8] = round(max_speed, 4)
        else:
            row.extend([round(incremental_e, 4), round(time_elapsed, 4), round(time_for_current_move, 4), round(feedrate, 4), round(avg_speed, 4), round(max_speed, 4)])

    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)

def calculate_ramp_time(v0, v1, distance, acceleration):
    if v0 == v1:
        return distance / v0
    t_accel = abs(v1 - v0) / acceleration
    d_accel = 0.5 * (v0 + v1) * t_accel
    if d_accel >= distance:
        t_accel = (2 * distance / (v0 + v1)) ** 0.5
        return t_accel
    t_cruise = (distance - d_accel) / v1
    return t_accel + t_cruise

if __name__ == "__main__":
    csv_directory = "D:\\TUDelft\\Thesis\\Engineering\\mechanical_parts_development\\FDM_Pinning\\slicer_post_processor\\csv_outputs"
    process_csv_files(csv_directory)
    print("Finished processing csv files.")