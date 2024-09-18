import requests
from dji.drone.djiConstants import EP_BASE
from dji.drone.djiCamera import DJICamera
from dji.drone.djiPiloting import DJIPiloting


class DJIController:
    """A class to control DJI drones."""

    def __init__(self, drone_ip: str):
        self.drone_url = f"http://{drone_ip}:8080"
        self.camera = DJICamera(drone_ip)
        self.piloting = DJIPiloting(self)

    def _request_get(self, endPoint, verbose=False):
        response = requests.get(f"{self.drone_url}{endPoint}")
        if verbose:
            print(f"EP : {endPoint}\t{str(response.content, encoding='utf-8')}")
        return response

    def connect(self):
        self._request_get(EP_BASE, True)


# TODO: make dji controller like anafi software pilot controller
