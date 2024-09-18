import requests
import json
import pymap3d
import math
from time import sleep
import os
import pandas as pd

from dji.drone.djiConstants import EP_BASE, EP_ALL_STATES
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

    def request_all_states(self, verbose=False):
        response = self._request_get(EP_ALL_STATES, verbose)
        states = json.loads(response.content.decode('utf-8'))
        return states

    def request_telem(self):
        return self.request_all_states()

    def requestSend(self, endPoint, data, verbose=False):
        response = requests.post(self.baseTelemUrl + endPoint, str(data))
        if verbose:
            print("EP : " + endPoint + "\t" + str(response.content, encoding="utf-8"))
        return response

    def requestSendStick(self, leftX = 0, leftY = 0, rightX = 0, rightY = 0):
        # Saturate values such that they are in [-1;1]
        s = 0.3
        leftX = max(-s,min(s,leftX))
        leftY = max(-s,min(s,leftY))
        rightX = max(-s,min(s,rightX))
        rightY = max(-s,min(s,rightY))
        rep = self.requestSend(EP_STICK, f"{leftX:.4f},{leftY:.4f},{rightX:.4f},{rightY:.4f}")
        return rep

    def requestSendGimbalPitch(self, pitch = 0):
        rep = self.requestSend(EP_GIMBAL_SET_PITCH, f"0,{pitch},0")
        return rep

    def requestSendZoomRatio(self, zoomRatio = 1):
        rep = self.requestSend(EP_ZOOM, zoomRatio)
        return rep

    def connect(self):
        self._request_get(EP_BASE, True)

    def go_to_WP(self, wp):
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
                self.requestSendStick(0, cmdAlt, 0, 0)
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
                self.dji.requestSendGimbalPitch(wp["gimbalPitch"])
                self.dji.requestSendZoomRatio(wp["zoomRatio"])
                sleep(2)
                print(f"Waypoint reached !\n\tCurrent state: {states}")
                break


# TODO: make dji controller like anafi software pilot controller
