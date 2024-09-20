import requests
import json
import pymap3d
import math
from time import sleep

from dji.drone.djiConstants import (
    EP_BASE,
    EP_ALL_STATES,
    EP_STICK,
    EP_GIMBAL_SET_PITCH,
    EP_ZOOM
)
from dji.drone.djiConstants import (
    CTRL_GAIN_ALT,
    CTRL_THRESH_ALT,
    CTRL_GAIN_X,
    CTRL_GAIN_Y,
    CTRL_GAIN_HEAD,
    CTRL_THRESH_X,
    CTRL_THRESH_Y,
    CTRL_THRESH_HEAD
)
from dji.drone.djiCamera import DJICamera
from dji.drone.djiPiloting import DJIPiloting


class DJIController:
    """A class to control DJI drones"""

    def __init__(self, drone_ip: str):
        self.drone_url = f"http://{drone_ip}:8080"
        self.camera = DJICamera(drone_ip)
        self.piloting = DJIPiloting(self)

    def request_get(self, end_point, verbose=False):
        """Get endpoint from DJI drone"""
        response = requests.get(f"{self.drone_url}{end_point}")
        if verbose:
            print(
                f"EP : {end_point}\t{str(response.content, encoding='utf-8')}")
        return response

    def request_all_states(self, verbose=False):
        """Request all states from DJI drone"""
        response = self.request_get(EP_ALL_STATES, verbose)
        states = json.loads(response.content.decode('utf-8'))
        return states

    def request_telem(self):
        """Request telemetry info from DJI drone"""
        return self.request_all_states()

    def request_send(self, end_point, data, verbose=False):
        """Sent data to endpoint & return response"""
        response = requests.post(f"{self.drone_url}{end_point}{str(data)}")
        if verbose:
            print(
                f"EP : {end_point}\t{str(response.content, encoding='utf-8')}")
        return response

    def send_stick(self, left_x=0, left_y=0, right_x=0, right_y=0):
        """Send stick (simulating controller) request to DJI drone"""
        # Saturate values such that they are in [-1;1]
        s = 0.3
        left_x = max(-s, min(s, left_x))
        left_y = max(-s, min(s, left_y))
        right_x = max(-s, min(s, right_x))
        right_y = max(-s, min(s, right_y))
        rep = self.request_send(
            EP_STICK, f"{left_x:.4f},{left_y:.4f},{right_x:.4f},{right_y:.4f}")
        return rep

    def set_gimbal_pitch(self, pitch=0):
        """Request DJI gimbal pitch"""
        rep = self.request_send(EP_GIMBAL_SET_PITCH, f"0,{pitch},0")
        # TODO: verify gimbal pitch?
        return rep

    def set_zoom_ratio(self, zoom_ratio=1):
        """Request DJI zoom ratio"""
        rep = self.request_send(EP_ZOOM, zoom_ratio)
        # TODO: verify zoom ratio?
        return rep

    def connect(self):
        """Check connection to drone"""
        self.request_get(EP_BASE, True)
        # TODO: confirm connection?

    def go_to_wp(self, wp):
        """Send DJI drone to waypoint"""
        print(f"Going to wp {wp}")
        current_control = "altitude"
        while True:
            # Get current state
            states = self.request_all_states()

            # Computer errors
            (err_east, err_north, err_up) = pymap3d.geodetic2enu(
                wp["lat"], wp["lon"], wp["alt"],
                states["location"]["latitude"],
                states["location"]["longitude"],
                states["location"]["altitude"]
            )
            distToWp = math.hypot(err_east, err_north)
            bearingToWp = math.atan2(err_east, err_north)
            errX = -distToWp * \
                math.cos(bearingToWp + math.pi/2 -
                         states["heading"]/180.*math.pi)
            errY = distToWp * \
                math.sin(bearingToWp + math.pi/2 -
                         states["heading"]/180.*math.pi)
            errAlt = err_up
            errHead = wp["head"] - states["heading"]

            if current_control == "altitude":
                cmdAlt = errAlt*CTRL_GAIN_ALT
                self.send_stick(0, cmdAlt, 0, 0)
                if abs(errAlt) < CTRL_THRESH_ALT:
                    current_control = "horizontal"

            elif current_control == "horizontal":
                cmdBodyX = errX*CTRL_GAIN_X
                cmdBodyY = errY*CTRL_GAIN_Y
                self.dji.requestSendStick(0, 0, cmdBodyX, cmdBodyY)
                if abs(errX) < CTRL_THRESH_X and abs(errY) < CTRL_THRESH_Y:
                    current_control = "heading"

            elif current_control == "heading":
                cmdHead = errHead*CTRL_GAIN_HEAD
                self.dji.requestSendStick(cmdHead, 0, 0, 0)
                if abs(errHead) < CTRL_THRESH_HEAD:
                    current_control = "camera"

            elif current_control == "camera":
                self.set_gimbal_pitch(wp["gimbalPitch"])
                self.set_zoom_ratio(wp["zoomRatio"])
                sleep(2)
                print(f"Waypoint reached !\n\tCurrent state: {states}")
                break


# TODO: make dji controller like anafi software pilot controller
