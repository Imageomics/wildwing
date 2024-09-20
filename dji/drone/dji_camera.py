from dji.drone.dji_camera_media import DJICameraMedia


class DJICamera:
    def __init__(self, drone_ip):
        self.media = DJICameraMedia(drone_ip)
