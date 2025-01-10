import cv2
import datetime
import os

# Define the stream URL and the directory where the video will be saved
STREAM_URL = "http://100.67.196.53/webcam/?action=stream"   # UM12
# STREAM_URL = "http://100.118.8.127/webcam/?action=stream"  # UM08
SAVE_DIR = "D:/TUDelft/Thesis/Engineering/mechanical_parts_development"  # Change this to your desired directory

# Generate a filename with a timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
video_filename = os.path.join(SAVE_DIR, f"video_{timestamp}.mp4")

# Open the video stream
cap = cv2.VideoCapture(STREAM_URL)

# Check if the stream opened successfully
if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

# Define the codec and create VideoWriter object
# Adjust `fps` and `frame_size` based on the stream's actual properties
fps = 20.0
frame_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # Codec for MP4 format
out = cv2.VideoWriter(video_filename, fourcc, fps, frame_size)

print("Recording started. Press 'q' to stop.")

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # Rotate the frame by 180 degrees
            frame = cv2.rotate(frame, cv2.ROTATE_180)

            # Write the frame to the output file
            out.write(frame)

            # Display the frame (optional)
            cv2.imshow("Recording", frame)

            # Press 'q' to stop recording
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Stopping recording...")
                break
        else:
            print("Error: Failed to retrieve frame.")
            break
except KeyboardInterrupt:
    print("Recording interrupted.")

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()
print(f"Recording saved to {video_filename}")
