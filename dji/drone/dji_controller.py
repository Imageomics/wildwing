from dji.drone.dji_camera import DJICamera
from dji.drone.dji_piloting import DJIPiloting
from dji.drone.dji_drone import DJIDrone


class DJIController:
    """A class to control DJI drones"""

    def __init__(self, drone_ip: str):
        self.drone = DJIDrone(drone_ip)
        self.camera = DJICamera(drone_ip)
        self.piloting = DJIPiloting(self)

    def connect(self):
        """Check connection to DJI drone"""
        self.drone.connect()

    def disconnect(self):
        """Disconnect from DJI drone"""
        self.drone.connect()

    def get_drone_coordinates(self):
        """Return drone's current gps coordinates"""
        telemetry = self.drone.request_telem()['location']
        coordinates = [telemetry['latitude'], telemetry['longitude'],
                       telemetry['altitude']]
        return coordinates


# TODO: make dji controller like anafi software pilot controller
