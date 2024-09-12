import cv2
import time
import queue
import olympe
import sys
import os
import csv
import datetime
import importlib.util
from ultralytics import YOLO
from SoftwarePilot import SoftwarePilot

class DroneController:
    def __init__(self, output_directory, action_script_path, duration=200):
        self.output_directory = output_directory
        self.action_script_path = action_script_path
        self.duration = duration
        self.csv_file_path = os.path.join(output_directory, 'telemetry_log.csv')
        self.sp = SoftwarePilot()
        self.model = YOLO('yolov5su') # TO DO: add option to specify different model, based on action script
        self.drone = None
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
            with open(self.csv_file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "x", "y", "z", "move_x", "move_y", "move_z", "frame"])

    def _load_action_script(self):
        spec = importlib.util.spec_from_file_location("action_module", self.action_script_path)
        self.action_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.action_module)
        if not hasattr(self.action_module, 'get_next_action'):
            raise AttributeError("The action script must contain a 'get_next_action' function.")

    def _connect_drone(self):
        self.drone = self.sp.setup_drone("parrot_anafi", 1, "None")
        self.drone.connect()
        self.drone.piloting.takeoff()
        time.sleep(5)  # Allow drone to stabilize

    def _create_tracker(self):
        self.tracker = Tracker(self.drone, self.model, self.output_directory, self.csv_file_path, self.action_module.get_next_action)

    def run_mission(self):
        self._start_recording()
        self._start_streaming()
        self._setup_display()
        time.sleep(self.duration)
        self._stop_mission()

    def _start_recording(self):
        self.drone.camera.media.setup_recording()
        self.drone.camera.media.start_recording()
        time.sleep(5)  # Allow recording to stabilize

    def _start_streaming(self):
        self.drone.camera.media.setup_stream(yuv_frame_processing=self.tracker.track)
        self.drone.camera.media.start_stream()

    def _setup_display(self):
        cv2.namedWindow('tracking', cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow('tracking', 500, 500)
        cv2.moveWindow('tracking', 0, 0)

    def _stop_mission(self):
        self.drone.camera.media.stop_stream()
        self.drone.camera.media.stop_recording()
        self.drone.camera.media.download_last_media()
        self.drone.piloting.land()
        self.drone.disconnect()

class Tracker:
    def __init__(self, drone, model, output_directory, csv_file_path, get_next_action_func):
        self.drone = drone
        self.model = model
        self.output_directory = output_directory
        self.csv_file_path = csv_file_path
        self.media = drone.camera.media
        self.frame_interval = 40  # Adjust this to change how often the drone moves
        self.get_next_action = get_next_action_func

    def track(self):
        while self.media.running:
            try:
                yuv_frame = self.media.frame_queue.get(timeout=0.1)
                self.media.frame_counter += 1

                if (self.media.frame_counter % self.frame_interval) == 0:
                    cv2frame = self._convert_frame(yuv_frame)
                    self._process_frame(cv2frame)

                yuv_frame.unref()
            except queue.Empty:
                continue

    def _convert_frame(self, yuv_frame):
        info = yuv_frame.info()
        height, width = info["raw"]["frame"]["info"]["height"], info["raw"]["frame"]["info"]["width"]
        cv2_cvt_color_flag = {
            olympe.VDEF_I420: cv2.COLOR_YUV2BGR_I420,
            olympe.VDEF_NV12: cv2.COLOR_YUV2BGR_NV12,
        }[yuv_frame.format()]
        return cv2.cvtColor(yuv_frame.as_ndarray(), cv2_cvt_color_flag)

    def _process_frame(self, cv2frame):
        x_direction, y_direction, z_direction = self.get_next_action(cv2frame, self.model, self.output_directory, self.media.frame_counter)
        self._move_drone(x_direction, y_direction, z_direction)
        self._save_telemetry(x_direction, y_direction, z_direction)

    def _move_drone(self, x, y, z):
        self.drone.piloting.move_by(x, y, z, 0)

    def _save_telemetry(self, x_direction, y_direction, z_direction):
        telemetry = self.drone.get_drone_coordinates()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.csv_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, telemetry[0], telemetry[1], telemetry[2], 
                             x_direction, y_direction, z_direction, self.media.frame_counter])

class WaypointController:
    def __init__(self, output_directory, action_script_path, duration=200):
        self.output_directory = output_directory
        self.action_script_path = action_script_path
        self.duration = duration
        self.csv_file_path = os.path.join(output_directory, 'telemetry_log.csv')
        self.sp = SoftwarePilot()
        self.drone = None
        self.action_module = None

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
            with open(self.csv_file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "x", "y", "z", "move_x", "move_y", "move_z", "waypoint"])

    def _load_action_script(self):
        spec = importlib.util.spec_from_file_location("action_module", self.action_script_path)
        self.action_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.action_module)
        if not hasattr(self.action_module, 'get_waypoints'):
            raise AttributeError("The action script must contain a 'get_waypoints' function.")

    def _connect_drone(self):
        self.drone = self.sp.setup_drone("parrot_anafi", 1, "None")
        self.drone.connect()
        self.drone.piloting.takeoff()
        time.sleep(5)  # Allow drone to stabilize

    def run_mission(self):
        waypoints = self.action_module.get_waypoints()
        for i, waypoint in enumerate(waypoints):
            lat, long, alt = waypoint
            self._move_to(lat, long, alt)
            self._save_telemetry(lat, long, alt, i+1)
        self._stop_mission()

    def _move_to(self, lat, long, alt, orientation="NONE", heading=0):
        self.drone.piloting.move_to(lat, long, alt, orientation, heading)

    def _save_telemetry(self, lat, long, alt, waypoint):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.csv_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, lat, long, alt, 0, 0, 0, waypoint])

    def _stop_mission(self):
        self.drone.piloting.land()
        self.drone.disconnect()

def main():
    if len(sys.argv) < 4:
        print("Usage: python parrotController.py <output_directory> <mission_type> <action_script_path>")
        sys.exit(1)

    output_directory = sys.argv[1]
    mission_type = sys.argv[2]
    autonomous_mission_type = sys.argv[3]
    cv_model = sys.argv[4] # TO DO: add option to specify different model, based on action script
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
        controller = WaypointController(output_directory, action_script_path, waypoint_file)
        
    else:
        print("Invalid mission type. Choose either 'autonomous' or 'waypoint'.")
        sys.exit(1)

    controller.setup()
    controller.run_mission()

if __name__ == "__main__":
    main()