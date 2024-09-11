import sys
import time
import queue
import os
import datetime
import csv
from ultralytics import YOLO
import navigation
from dji.djiInterface import DJIInterface, DJIController
from dji.djiCamera import DJICamera

# To run, first fly the drone an area with direct sight of the zebras using the FreeFlight6 app
# Then run the program

# User-defined mission parameters
# 5 minutes is 300 seconds
DURATION = 200  # duration in seconds

# drone adjustment parameter
S = 0.3


# Runs what to do on every yuv_frame of the stream, modify it as needed
class Tracker:
    def __init__(self, drone: DJIInterface, camera: DJICamera, model, csv_file_path, output_directory):
        self.drone = drone
        self.media = camera
        self.model = model
        self.csv_file_path = csv_file_path
        self.output_directory = output_directory

    def track(self):
        while self.media.running:
            try:
                cv2frame = self.media.frame_queue.get(timeout=0.1)
                self.media.frame_counter += 1

                # note: adjust this number to change how often the drone moves
                # (every 20 frames in this case)
                if (self.media.frame_counter % 40) == 0:
                    x_direction, y_direction, z_direction = navigation.get_next_action(
                        cv2frame, self.model,
                        self.output_directory,
                        self.media.frame_counter)  # KEY LINE

                    # save telemetry
                    # test!
                    telemetry = self.drone.requestTelem()['location']

                    # Convert time.time() to datetime object
                    timestamp = datetime.datetime.fromtimestamp(
                        time.time()).strftime('%Y-%m-%d %H:%M:%S')

                    # Append telemetry data to CSV file
                    with open(self.csv_file_path, mode='a', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        writer.writerow([timestamp, telemetry['latitude'], telemetry[''],
                                         telemetry['altitude'], x_direction, y_direction,
                                         z_direction, self.media.frame_counter])

                    move_by(self.drone, z_direction, x_direction, y_direction)

            except queue.Empty:
                continue


def takeoff(dji_drone: DJIInterface):
    start = time.time()
    while time.time() - start < 5:
        dji_drone.requestSendStick(0, S, 0, 0)
    dji_drone.requestSendStick(0, 0, 0, 0)


def move_by(dji_drone: DJIInterface, z_direction, x_direction, y_direction):
    z_abs = abs(z_direction)
    x_abs = abs(x_direction)
    y_abs = abs(y_direction)
    max_abs = max([z_abs, x_abs, y_abs])

    if max_abs > S:
        scale = max_abs / S
        z_direction *= scale
        x_direction *= scale
        y_direction *= scale

    dji_drone.requestSendStick(0, z_direction, x_direction, y_direction)


def landing(dji_drone: DJIInterface):
    controller = DJIController(interface=dji_drone, wpList=[])
    telemetry = dji_drone.requestTelem()
    wp = {'head': telemetry['heading'],
          'lat': telemetry['location']['latitude'],
          'lon': telemetry['location']['longitude'],
          'alt': 0}
    controller.gotoWP(wp)


def main():
    # Retrieve the filename from command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python controller.py <output_directory>")
        sys.exit(1)

    output_directory = sys.argv[1]

    # Define CSV file path to store telemetry data
    # Define the CSV file path
    csv_file_path = os.path.join(output_directory, 'telemetry_log.csv')

    # Ensure the CSV file has a header row
    if not os.path.exists(csv_file_path):
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "x", "y", "z", "move_x",
                            "move_y", "move_z", "frame"])

    # Setup a dji drone
    dji_drone = DJIInterface(MODE='drone', IP_RC='???')
    dji_camera = DJICamera(IP_RC='???')
    model = YOLO('yolov5su')

    # Take off
    takeoff(dji_drone)

    # Create a tracker object
    tracker = Tracker(dji_drone, dji_camera, model,
                      csv_file_path, output_directory)

    # Set up recording
    dji_camera.setup_recording()
    dji_camera.start_recording()

    # Start the stream
    dji_camera.setup_stream(live_callback=tracker.track)
    dji_camera.start_stream()

    # Set track duration in seconds
    time.sleep(DURATION)

    # Stop recording
    dji_camera.start_recording()
    dji_camera.download_last_media()

    # Land the drone
    landing(dji_drone)


if __name__ == '__main__':
    main()
