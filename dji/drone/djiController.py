import requests
from dji.drone.djiConstants import EP_BASE


class DJIController:
    """A class to control DJI drones."""

    def __init__(self, drone_ip: str):
        self.drone_url = f"http://{drone_ip}:8080"

    def _request_get(self, endPoint, verbose=False):
        response = requests.get(f"{self.drone_url}{endPoint}")
        if verbose:
            print(f"EP : {endPoint}\t{str(response.content, encoding='utf-8')}")
        return response

    def connect(self):
        self._request_get(EP_BASE, True)


# make dji controller like anafi software pilot controller
