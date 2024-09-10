import sys
import time
import queue
import cv2
import os
import datetime
import csv
import olympe
from ultralytics import YOLO
import navigation
from dji.djiInterface import DJIInterface

# To run, first fly the drone an area with direct sight of the zebras using the FreeFlight6 app
# Then run the program

# User-defined mission parameters
# 5 minutes is 300 seconds
DURATION = 200  # duration in seconds

# drone adjustment parameter
S = 0.3


class DJICamera:
    def __init__(self):
        self.running = False
        self.frame_counter = 0


# Runs what to do on every yuv_frame of the stream, modify it as needed
class Tracker:
    def __init__(self, drone: DJIInterface, model, csv_file_path, output_directory):
        self.drone = drone
        self.media = drone.videoSource
        self.model = model
        self.csv_file_path = csv_file_path
        self.output_directory = output_directory

    def track(self):
        while self.media.running:
            try:
                yuv_frame = self.media.frame_queue.get(timeout=0.1)
                self.media.frame_counter += 1

                # note: adjust this number to change how often the drone moves
                # (every 20 frames in this case)
                if (self.media.frame_counter % 40) == 0:
                    # convert pdraw YUV flag to OpenCV YUV flag
                    cv2_cvt_color_flag = {
                        olympe.VDEF_I420: cv2.COLOR_YUV2BGR_I420,
                        olympe.VDEF_NV12: cv2.COLOR_YUV2BGR_NV12,
                    }[yuv_frame.format()]

                    cv2frame = cv2.cvtColor(
                        yuv_frame.as_ndarray(), cv2_cvt_color_flag)

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
                        writer.writerow([timestamp, telemetry['latitude'], telemetry['longitude'],
                                         telemetry['altitude'], x_direction, y_direction,
                                         z_direction, self.media.frame_counter])

                    self.drone.requestSendStick(
                        0, z_direction, x_direction, y_direction)

            except queue.Empty:
                continue

        # You should process your frames here and release (unref) them when you're done.
        # Don't hold a reference on your frames for too long to avoid memory leaks and/or memory
        # pool exhaustion.
        yuv_frame.unref()


def takeoff(dji_drone):
    start = time.time()
    while time.time() - start < 5:
        dji_drone.requestSendStick(0, S, 0, 0)
    dji_drone.requestSendStick(0, 0, 0, 0)

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
    dji_drone = DJIInterface(MODE='drone', IP_RC='localhost')
    dji_camera = DJICamera()
    model = YOLO('yolov5su')

    # Take off
    takeoff(dji_drone)

    # Create a tracker object
    tracker = Tracker(dji_drone, model, csv_file_path, output_directory)

    # wait for drone to stabilize
    time.sleep(5)

    # set track duration in seconds
    time.sleep(DURATION)

    # Land the drone
    cmdAlt = 0
    dji_drone.requestSendStick(0, cmdAlt, 0, 0)


if __name__ == '__main__':
    main()
