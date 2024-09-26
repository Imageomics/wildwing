from dji.drone.dji_drone import DJIDrone

class DJICameraControls:
    def __init__(self, drone_object: DJIDrone):
        self.drone = drone_object

    def reset_zoom(self):
        self.drone.set_zoom_ratio()

    def reset_orientation(self):
        self.drone.set_gimbal_pitch()

    def set_zoom(self, target, control_mode="level"):
        # TODO: use control mode
        self.drone.set_zoom_ratio(target)

    def set_orientation(self, yaw, pitch, roll, reference=1, wait=False):
        # TODO: adjust drone to allow setting of yaw & roll
        self.drone.set_gimbal_pitch(pitch)

    def wait_until_orientation(self, yaw, pitch, roll, timeout=5):
        # TODO: poll orientation until timeout
        pass
