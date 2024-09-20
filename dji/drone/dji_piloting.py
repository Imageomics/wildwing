from time import sleep
from dji.drone.dji_drone import DJIDrone
from dji.drone.dji_constants import (
    TAKEOFF_HEIGHT, GROUND_HEIGHT, DESCENT_TIME
)


class DJIPiloting:
    def __init__(self, drone_object: DJIDrone):
        self.drone = drone_object
        self.action_queue = []

    def _takeoff(self):
        wp = self.drone.current_wp()
        # Alternative: set altitude to a constant value
        # instead of adjusting current altitude
        wp["alt"] += TAKEOFF_HEIGHT
        self.drone.go_to_wp(wp)

    def _land(self):
        wp = self.drone.current_wp()
        descent_speed = wp["alt"] / DESCENT_TIME
        while wp["alt"] > GROUND_HEIGHT:
            wp["alt"] = max(GROUND_HEIGHT, wp["alt"] - descent_speed)
        self.drone.go_to_wp(wp)
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
        pass

    def move_by(self, x, y, z, angle, wait=False, queue=False):
        pass

    def move_to(self, lat, lon, alt, orientation_mode="NONE", heading=0, wait=False, queue=False):
        pass

    def cancel_move_by(self):
        pass

    def cancel_move_to(self):
        pass

    def add_action(self, action):
        pass

    def remove_action(self, index):
        pass

    def clear_actions(self):
        self.action_queue = []

    def execute_actions(self, num=-1):
        if num < 0:
            num = len(self.action_queue)

        for _ in range(num):
            action = self.action_queue.pop(0)
            action()
