from time import sleep
import threading
import signal
from math import cos, sin, radians
from dji.drone.dji_drone import DJIDrone
from dji.drone.dji_constants import (
    TAKEOFF_HEIGHT, GROUND_HEIGHT, DESCENT_TIME
)


class DJIPiloting:
    def __init__(self, drone_object: DJIDrone):
        self.drone = drone_object
        self.action_queue = []
        self.threads = {}

    def go_to_wp(self, thread, wp):
        """Start a thread telling the drone to go to a waypoint"""
        self.threads[thread] = threading.Thread(
            target=self.drone.go_to_wp, args=wp)
        self.threads[thread].start()

    def _takeoff(self):
        wp = self.drone.current_wp()
        # Alternative: set altitude to a constant value
        # instead of adjusting current altitude
        wp["alt"] += TAKEOFF_HEIGHT
        self.go_to_wp('takeoff', wp)

    def _land(self):
        wp = self.drone.current_wp()
        descent_speed = wp["alt"] / DESCENT_TIME
        while wp["alt"] > GROUND_HEIGHT:
            wp["alt"] = max(GROUND_HEIGHT, wp["alt"] - descent_speed)
            self.go_to_wp('land', wp)
            sleep(1)

    def takeoff(self, queue=False):
        """Takeoff {TAKEOFF_HEIGHT} meters"""
        if not queue:
            print("------ TAKEOFF ------")
            self._takeoff()
        else:
            self.add_action(self.takeoff)

    def land(self, queue=False):
        if not queue:
            print("------ LAND ------")
            self._land()
        else:
            self.add_action(self.land)

    def wait_until_state(self, state_type, state, timeout=None):
        # TODO: implement this with dji state equivalent
        pass

    def move_by(self, x, y, z, angle, wait=False, queue=False):
        wp = self.drone.current_wp()
        if x != 0 or y != 0 or z != 0:
            heading = wp["head"]
            theta_x = (-heading + 90) % 360
            theta_y = (-heading + 180) % 360
            move_lat = x * sin(radians(theta_x)) + y * cos(radians(theta_y))
            mov_lon = x * cos(radians(theta_x)) + y * sin(radians(theta_y))
            wp["lat"] += move_lat
            wp["lon"] += mov_lon
            wp["alt"] += z
        elif angle != 0:
            wp["head"] += angle

        if not queue:
            self.go_to_wp("move_by", wp)
            if wait:
                try:
                    self.threads["move_to"].join()
                except Exception:
                    pass
            print("------ MOVEBY ------")
            print(f"------ x : {x} ------")
            print(f"------ Y : {y} ------")
            print(f"------ Z : {z} ------")
            print(f"------ ANGLE : {angle} ------")
        else:
            self.add_action([self.go_to_wp, "move_by", wp])
            if wait:
                self.wait_until_state("move_by", "hovering")

    def move_to(self, lat, lon, alt, orientation_mode="NONE", heading=0, wait=False, queue=False):
        # TODO: find dji equivalent to orientation mode
        wp = self.drone.current_wp()
        wp["lat"] = lat
        wp["lon"] = lon
        wp["alt"] = alt
        wp["head"] = heading

        if not queue:
            self.go_to_wp("move_to", wp)
            if wait:
                try:
                    self.threads["move_to"].join()
                except Exception:
                    pass
            print("------ MOVETO ------")
            print(f"------ LAT : {lat} ------")
            print(f"------ LON : {lon} ------")
            print(f"------ ALT : {alt} ------")
            print(f"------ HEADING : {heading} ------")
        else:
            self.add_action([self.go_to_wp, "move_to", wp])
            if wait:
                self.wait_until_state("move_to", "hovering")

    def cancel_move_by(self):
        self.threads["move_by"].send_signal(signal.SIGINT)

    def cancel_move_to(self):
        self.threads["move_to"].send_signal(signal.SIGINT)

    def add_action(self, action):
        """Add action to queue"""
        self.action_queue.append(action)

    def remove_action(self, index):
        """Remove action at index from queue"""
        return self.action_queue.pop(index)

    def clear_actions(self):
        """Clear action queue"""
        del self.action_queue
        self.action_queue = []

    def execute_actions(self, num=-1):
        """Execute {num} queued actions"""
        if num < 0:
            num = len(self.action_queue)

        for _ in range(num):
            action = self.action_queue.pop(0)
            if callable(action):
                action()
            else:
                function = action[0]
                params = action[1:]
                function(*params)
