import json
import math
from time import sleep
import pymap3d
import requests

from dji.drone.dji_constants import (
    EP_BASE,
    EP_ALL_STATES,
    EP_STICK,
    EP_GIMBAL_SET_PITCH,
    EP_ZOOM
)
from dji.drone.dji_constants import (
    CTRL_GAIN_ALT,
    CTRL_THRESH_ALT,
    CTRL_GAIN_X,
    CTRL_GAIN_Y,
    CTRL_GAIN_HEAD,
    CTRL_THRESH_X,
    CTRL_THRESH_Y,
    CTRL_THRESH_HEAD
)


class DJIDrone:
    """A class to communicate with DJI drones"""

    def __init__(self, drone_ip: str):
        self.drone_url = f"http://{drone_ip}:8080"

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
        """Check connection to DJI drone"""
        self.request_get(EP_BASE, True)
        # TODO: confirm connection?

    def disconnect(self):
        """Disconnect from DJI drone"""
        # TODO

    def current_wp(self):
        """Get current waypoint"""
        wp = {}
        telem = self.request_telem()
        location = telem["location"]
        wp["lat"] = location["latitude"]
        wp["lon"] = location["longitude"]
        wp["alt"] = location["altitude"]
        wp["head"] = telem["heading"]
        wp["gimbalPitch"] = telem["gimbalAttitude"]["pitch"]
        wp["zoomRatio"] = telem["zoomRatio"]
        return wp

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
            dist_to_wp = math.hypot(err_east, err_north)
            bearing_to_wp = math.atan2(err_east, err_north)
            err_x = -dist_to_wp * \
                math.cos(bearing_to_wp + math.pi/2 -
                         states["heading"]/180.*math.pi)
            err_y = dist_to_wp * \
                math.sin(bearing_to_wp + math.pi/2 -
                         states["heading"]/180.*math.pi)
            err_alt = err_up
            err_head = wp["head"] - states["heading"]

            if current_control == "altitude":
                cmd_alt = err_alt*CTRL_GAIN_ALT
                self.send_stick(0, cmd_alt, 0, 0)
                if abs(err_alt) < CTRL_THRESH_ALT:
                    current_control = "horizontal"

            elif current_control == "horizontal":
                cmd_body_x = err_x*CTRL_GAIN_X
                cmd_body_y = err_y*CTRL_GAIN_Y
                self.send_stick(0, 0, cmd_body_x, cmd_body_y)
                if abs(err_x) < CTRL_THRESH_X and abs(err_y) < CTRL_THRESH_Y:
                    current_control = "heading"

            elif current_control == "heading":
                cmd_head = err_head*CTRL_GAIN_HEAD
                self.send_stick(cmd_head, 0, 0, 0)
                if abs(err_head) < CTRL_THRESH_HEAD:
                    current_control = "camera"

            elif current_control == "camera":
                self.set_gimbal_pitch(wp["gimbalPitch"])
                self.set_zoom_ratio(wp["zoomRatio"])
                sleep(2)
                print(f"Waypoint reached !\n\tCurrent state: {states}")
                break
