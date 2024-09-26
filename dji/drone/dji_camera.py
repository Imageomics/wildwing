from dji.drone.dji_camera_media import DJICameraMedia
from dji.drone.dji_camera_controls import DJICameraControls
from dji.drone.dji_drone import DJIDrone


class DJICamera:
    def __init__(self, drone_ip: str, drone_object: DJIDrone):
        self.media = DJICameraMedia(drone_ip)
        self.controls = DJICameraControls(drone_object)
