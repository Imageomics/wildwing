import sys
import time
import queue
import os
import datetime
import csv
import importlib.util
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

IP_RC = '???'


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


class DroneController:
    def __init__(self, output_directory, action_script_path, duration=200):
        self.output_directory = output_directory
        self.action_script_path = action_script_path
        self.duration = duration
        self.csv_file_path = os.path.join(
            output_directory, 'telemetry_log.csv')
        # TO DO: add option to specify different model, based on action script
        self.model = YOLO('yolov5su')
        self.drone = None
        self.camera = None
        self.tracker = None
        self.action_module = None

    def setup(self):
        self._ensure_output_directory()
        self._create_csv_file()
        self._load_action_script()
        self._connect_drone()
        self._create_tracker()

    def _ensure_output_directory(self):
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

    def _create_csv_file(self):
        if not os.path.exists(self.csv_file_path):
            with open(self.csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "x", "y", "z",
                                "move_x", "move_y", "move_z", "frame"])

    def _load_action_script(self):
        spec = importlib.util.spec_from_file_location(
            "action_module", self.action_script_path)
        self.action_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.action_module)
        if not hasattr(self.action_module, 'get_next_action'):
            raise AttributeError(
                "The action script must contain a 'get_next_action' function.")

    def _connect_drone(self):
        self.drone = DJIInterface(MODE='drone', IP_RC=IP_RC)
        self.camera = DJICamera(IP_RC=IP_RC)
        takeoff(self.drone)

    def _create_tracker(self):
        self.tracker = Tracker(self.drone, self.camera, self.model, self.output_directory,
                               self.csv_file_path, self.action_module.get_next_action)

    def run_mission(self):
        self._start_recording()
        self._start_streaming()
        time.sleep(self.duration)
        self._stop_mission()

    def _start_recording(self):
        self.camera.start_recording()

    def _start_streaming(self):
        self.camera.setup_stream(live_callback=self.tracker.track)
        self.camera.start_stream()

    def _stop_mission(self):
        self.camera.stop_recording()
        self.camera.stop_stream()
        landing(self.drone)


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


class WaypointController:
    def __init__(self, output_directory, action_script_path, duration=200):
        self.output_directory = output_directory
        self.action_script_path = action_script_path
        self.duration = duration
        self.csv_file_path = os.path.join(
            output_directory, 'telemetry_log.csv')
        self.drone = None
        self.action_module = None
        self.controller = None

    def setup(self):
        self._ensure_output_directory()
        self._create_csv_file()
        self._load_action_script()
        self._connect_drone()

    def _ensure_output_directory(self):
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

    def _create_csv_file(self):
        if not os.path.exists(self.csv_file_path):
            with open(self.csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "x", "y", "z",
                                "move_x", "move_y", "move_z", "waypoint"])

    def _load_action_script(self):
        spec = importlib.util.spec_from_file_location(
            "action_module", self.action_script_path)
        self.action_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.action_module)
        if not hasattr(self.action_module, 'get_waypoints'):
            raise AttributeError(
                "The action script must contain a 'get_waypoints' function.")

    def _connect_drone(self):
        self.drone = DJIInterface(MODE='drone', IP_RC=IP_RC)
        takeoff(self.drone)
        self.controller = DJIController(interface=self.drone, wpList=[])

    def run_mission(self):
        waypoints = self.action_module.get_waypoints()
        for i, waypoint in enumerate(waypoints):
            lat, long, alt = waypoint
            self._move_to(lat, long, alt)
            self._save_telemetry(lat, long, alt, i+1)
        self._stop_mission()

    def _move_to(self, lat, long, alt, orientation="NONE", heading=0):        
        wp = {'head': heading,
            'lat': lat,
            'lon': long,
            'alt': alt,
            'gimbalPitch': -1,
            'zoomRatio':-1}
        # TODO: fix gimbalPitch & zoomRatio
        self.controller.gotoWP(wp)

    def _save_telemetry(self, lat, long, alt, waypoint):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.csv_file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, lat, long, alt, 0, 0, 0, waypoint])

    def _stop_mission(self):
        landing(self.drone)


def main():
    if len(sys.argv) < 4:
        print("Usage: python djiController.py <output_directory> <mission_type> <action_script_path>")
        sys.exit(1)

    output_directory = sys.argv[1]
    mission_type = sys.argv[2]
    autonomous_mission_type = sys.argv[3]
    # TO DO: add option to specify different model, based on action script
    cv_model = sys.argv[4]
    waypoint_file = sys.argv[5]

    # TEST THIS
    if mission_type.lower() == "autonomous":
        if autonomous_mission_type == "":
            print("Please specify an autonomous mission type.")
            sys.exit(1)
        elif autonomous_mission_type.lower() == "track":
            action_script_path = "/mission_scripts/autonomous/herd_tracker.py"
        elif autonomous_mission_type.lower() == "depth":
            action_script_path = "/mission_scripts/autonomous/depth_est.py"
        controller = DroneController(output_directory, action_script_path)

    elif mission_type.lower() == "waypoint":
        action_script_path = "/mission_scripts/waypoint/waypoints.py"
        controller = WaypointController(
            output_directory, action_script_path, waypoint_file)

    else:
        print("Invalid mission type. Choose either 'autonomous' or 'waypoint'.")
        sys.exit(1)

    controller.setup()
    controller.run_mission()


if __name__ == "__main__":
    main()
