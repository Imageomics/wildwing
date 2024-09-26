from dji.drone.dji_drone import DJIDrone

class DJICameraControls:
    def __init__(self, drone_object: DJIDrone):
        self.drone = drone_object

    def reset_zoom(self):
        pass

    def reset_orientation(self):
        pass

    def set_zoom(self, target, control_mode="level"):
        pass

    def set_orientation(self, yaw, pitch, roll, reference=1, wait=False):
        pass

    def wait_until_orientation(self, yaw, pitch, roll, timeout=5):
        pass
