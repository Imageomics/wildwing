## IMPORTS
import requests
import ast
import pymap3d
import math
from time import sleep
import cv2
import threading
import sys
import os 
import subprocess
import numpy as np
import pandas as pd


RESSOURCES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Ressources")
IMAGE_BUFFER = os.path.join(RESSOURCES_PATH, "buffer.jpg")

# Aircraft state endpoints suffixes
# GETTER
EP_BASE = "/"
EP_SPEED = "/aircraft/speed"
EP_HEADING = "/aircraft/heading"
EP_ATTITUDE = "/aircraft/attitude"
EP_LOCATION = "/aircraft/location"
EP_GIMBAL_ATTITUDE = "/aircraft/gimbalAttitude"
EP_ALL_STATES = "/aircraft/allStates"

# SETTER
EP_STICK = "/send/stick" # expects a sting formated as: "<leftX>,<leftY>,<rightX>,<rightY>"
EP_ZOOM = "/send/camera/zoom"
EP_GIMBAL_SET_PITCH = "/send/gimbal/pitch"

class DJIInterface:
    def __init__(self, MODE, IP_RC = "", LOG_PATH = ""):
        self.MODE = MODE

        if MODE == "webcam":
            pass
        elif MODE == "drone":
            if IP_RC == "":
                raise ValueError("IP_RC must be given to DJIInterface constructor with MODE drone")
            self.IP_RC = IP_RC
            self.baseTelemUrl = f"http://{self.IP_RC}:8080"
            self.videoSource = f"rtsp://aaa:aaa@{self.IP_RC}:8554/streaming/live/1"
        elif MODE == "replay":
            if LOG_PATH == "":
                raise ValueError("LOG_PATH must be given to DJIInterface constructor with MODE replay")
            self.LOG_PATH = LOG_PATH
            self.LOG_NAME = os.path.basename(self.LOG_PATH)
            print(f"LOG PATH: {self.LOG_PATH}")
            print(f"LOG NAME: {self.LOG_NAME}")
            self.videoSource = os.path.join(self.LOG_PATH, f"{self.LOG_NAME}.avi")
            self.telemSource = os.path.join(self.LOG_PATH, f"{self.LOG_NAME}.csv")
            self.telemLog = pd.read_csv(self.telemSource)
            self.telemIter = self.telemLog.iterrows()
            self.telem = self.getNullTelem()
        else:
            raise ValueError(f"Unkown MODE: {self.MODE}")

    def getVideoSource(self):
        return self.videoSource

    def requestGet(self, endPoint, verbose=False):
        response = requests.get(self.baseTelemUrl + endPoint)
        if verbose:
            print("EP : " + endPoint + "\t" + str(response.content, encoding="utf-8"))
        return response

    def requestAllStates(self, verbose=False):
        response = self.requestGet(EP_ALL_STATES, verbose)
        states = ast.literal_eval(response.content.decode('utf-8')) # TODO: probably very unsafe!!!
        return states

    def requestTelem(self, advance = False):
        if self.MODE == "webcam":
            return {'speed': {'x': 0, 'y': 0, 'z': 0}, 'heading': -90, 'attitude': {'pitch': 4.2, 'roll': -0.30000000000000004, 'yaw': -90}, 'location': {'latitude': 0.025641348125899938, 'longitude': 36.90376260204561, 'altitude': 20}, 'gimbalAttitude': {'pitch': -10, 'roll': 0, 'yaw': -20}, 'zoomFl': 168, 'hybridFl': 1680, 'opticalFl': 1680, 'zoomRatio': 7.0}
            # return {'speed': {'x': 0, 'y': 0, 'z': 0}, 'heading': -130.6, 'attitude': {'pitch': 4.2, 'roll': -0.30000000000000004, 'yaw': -130.6}, 'location': {'latitude': 51.4233478, 'longitude': -2.6716311, 'altitude': 20}, 'gimbalAttitude': {'pitch': -10, 'roll': 0, 'yaw': -90}, 'zoomFl': 168, 'hybridFl': 1680, 'opticalFl': 1680, 'zoomRatio': 7.0}
        elif self.MODE == "drone":
            return self.requestAllStates()
        elif self.MODE == "replay":
            if advance:
                data = next(self.telemIter)[1]
                self.telem = {'speed': {'x': data["states_speed_x"], 'y': data["states_speed_y"], 'z': data["states_speed_z"]}, 'heading': data["states_heading"], 'attitude': {'pitch': data["states_attitude_pitch"], 'roll': data["states_attitude_roll"], 'yaw': data["states_attitude_yaw"]}, 'location': {'latitude': data["states_location_latitude"], 'longitude': data["states_location_longitude"], 'altitude': data["states_location_altitude"]}, 'gimbalAttitude': {'pitch': data["states_gimbalAttitude_pitch"], 'roll': data["states_gimbalAttitude_roll"], 'yaw': data["states_gimbalAttitude_yaw"]}, 'zoomFl': data["states_zoomFl"], 'hybridFl': data["states_hybridFl"], 'opticalFl': data["states_opticalFl"], 'zoomRatio': data["states_zoomRatio"]}
            return self.telem

    def getNullTelem(self):
        return {'speed': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'heading': 0.0, 'attitude': {'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0}, 'location': {'latitude': 0.0, 'longitude': 0.0, 'altitude': 0.0}, 'gimbalAttitude': {'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0}, 'zoomFl': 0.0, 'hybridFl': 0.0, 'opticalFl': 0.0, 'zoomRatio': 0.0}
            
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

    def watchDogTest(self):
        self.requestGet(EP_BASE, True)
        self.requestSendStick(leftX=1)


# P-CONROLLER
CTRL_THRESH_HEAD = 0.1 # degrees
CTRL_THRESH_ALT = 0.1 # meters
CTRL_THRESH_X = 0.1 # meters
CTRL_THRESH_Y = 0.1 # meters

CTRL_GAIN_HEAD = 1/200
CTRL_GAIN_ALT = 0.1
CTRL_GAIN_X = 0.03
CTRL_GAIN_Y = 0.03

class DJIController:
    def __init__(self, interface, wpList):
        self.dji = interface
        self.wpList = wpList
        self.currentWP = 0

    def goto(self, cmd):
        if cmd == "next":
            self.currentWP = (self.currentWP + 1)%len(self.wpList)
            print(f"Going to wpID : {self.currentWP}")
            self.gotoWP(self.wpList[self.currentWP])
        elif cmd.isnumeric():
            self.currentWP = int(cmd)
            self.gotoWP(self.wpList[int(cmd)])

    def gotoWP(self, wp):
        print(f"Going to wp {wp}")
        currentControl = "altitude"
        while True:
            # Get current state
            states = self.dji.requestAllStates()

            # Computer errors
            (errEast, errNorth, errUp) = pymap3d.geodetic2enu(
                wp["lat"], wp["lon"], wp["alt"],
                states["location"]["latitude"], states["location"]["longitude"], states["location"]["altitude"]
                )
            distToWp = math.hypot(errEast, errNorth)
            bearingToWp = math.atan2(errEast, errNorth)
            errX =  -distToWp*math.cos(bearingToWp + math.pi/2 - states["heading"]/180.*math.pi)
            errY =  distToWp*math.sin(bearingToWp + math.pi/2 - states["heading"]/180.*math.pi)
            errAlt = errUp
            errHead = wp["head"] - states["heading"]

            if currentControl == "altitude":
                cmdAlt = errAlt*CTRL_GAIN_ALT
                self.dji.requestSendStick(0, cmdAlt, 0, 0)
                if abs(errAlt) < CTRL_THRESH_ALT:
                    currentControl = "horizontal"

            elif currentControl == "horizontal":
                cmdBodyX = errX*CTRL_GAIN_X
                cmdBodyY = errY*CTRL_GAIN_Y
                self.dji.requestSendStick(0, 0, cmdBodyX, cmdBodyY)
                if abs(errX) < CTRL_THRESH_X and abs(errY) < CTRL_THRESH_Y:
                    currentControl = "heading"

            elif currentControl == "heading":
                cmdHead = errHead*CTRL_GAIN_HEAD
                self.dji.requestSendStick(cmdHead, 0, 0, 0)
                if abs(errHead) < CTRL_THRESH_HEAD:
                    currentControl = "camera"

            elif currentControl == "camera":
                self.dji.requestSendGimbalPitch(wp["gimbalPitch"])
                self.dji.requestSendZoomRatio(wp["zoomRatio"])
                sleep(2)
                print(f"Waypoint reached !\n\tCurrent state: {states}")
                break



class BufferLessVideoCapture:
    def __init__(self, IP_RC):
        source = f"rtsp://aaa:aaa@{IP_RC}:8554/streaming/live/1"
        ffmpeg_cmd = [
            "ffmpeg",
            "-i",  source,
            "-vf", "fps=10",
            "-update", "1",
            "-hls_flags", "temp_file",
            IMAGE_BUFFER,
            "-y"
        ]

        # Open FFmpeg process
        self.ffmpeg_process = subprocess.Popen(ffmpeg_cmd)
        sleep(2)
        
    
    # retrieve latest frame
    def read(self):
        frame = cv2.imread(IMAGE_BUFFER)
        return True, frame

    def __del__(self):
        self.ffmpeg_process.send_signal(signal.SIGINT)
        self.ffmpeg_process.wait()  


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python TestRequest.py <IP_RC>")
    else:
        dji = DJIInterface(sys.argv[1])
        dji.requestGet(EP_BASE, True)