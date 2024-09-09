# This script takes a frame from a video and detects the animals in the frame.
# Based on the position of the herd in the frame, the script determines where the drone should move to keep the herd in the frame.

import math
import cv2
import sys
from ultralytics import YOLO
from PIL import Image
import pandas as pd
import time
import datetime
import json

# Generate a unique filename using the current timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
frame_counter = 0

# constants for how much to move in each direction
# NOTE these are arbitrary values and need to be adjusted based on drone speed and camera resolution
x_dist = 10 # move +/- X meters in forward/backward plane
x_dist_no_subject = 20 # move +/- X meters forward if no subject detected
y_dist = 10 # move +/- X meters in left/right plane
z_dist = 10 # move +/- X meters in up/down plane

def crop_image(image):
    """
    Crop the image to focus on the herd and improve YOLO results
    """
    im = Image.open(image)
    width, height = im.size
    crop_image = im.crop((int(width/3), int(height/4), int(width/3*2), int(height/4*3)))
    # width_third = int(width/3)
    # height_quarter = int(height/4)
    # crop_image = image[int(height_quarter):int(height_quarter*3), int(width_third):int(width_third*2)]
    return crop_image

def count_animals(results):
    """
    Count the number of animals in the frame
    """
    count = 0
    for i in results[0].boxes.cls:
        # cows: 19
        # horses: 22
        # sheep: 18
        # zebras: 17
        # dog: 16
        # person: 0
        if i == 19 or i == 22 or i == 18 or i == 17 or i==16 or i == 0: 
            count += 1
    return count

def detect_animals(frame, model):
    """
    Detect the animals in the frame
    """
    results = model(frame)
    count, results = count_animals(results), results
    return count, results 

def auto_navigation(results):
    # orig_shape outputs (height, width)
    centroid_camera = (results[0].orig_shape[1]/2, results[0].orig_shape[0]/2)
    
    #px = pd.DataFrame((results[0].boxes.boxes).numpy(), columns = ('x1', 'y1','x2', 'y2', 'confidence', 'class'))
    px = pd.DataFrame((results[0].boxes.xyxy).numpy(), columns = ('x1', 'y1','x2', 'y2'))
    # get x, y, w, h for results and convert to dataframe
    pxywh = pd.DataFrame((results[0].boxes.xywh).numpy(), columns = ('x', 'y','w', 'h'))
    px = px.join(pxywh)

    # calculate bounding box sizes in terms of pixel width and height
    bbox_sizes = []
    for b in results[0].boxes.xywh:
        bbox_sizes.append((b[2], b[3])) # get width and height of bounding box

    # get centroid of herd
    centroid_herd = (px['x'].mean(), px['y'].mean())

    image_shape_h, image_shape_w = results[0].orig_shape
    x_center_range = image_shape_w/2 - image_shape_w/8, image_shape_w/2 + image_shape_w/8
    y_center_range = image_shape_h/2 - image_shape_h/8, image_shape_h/2 + image_shape_h/8

    # calculate differencee between centroid of herd and camera
    dif_x = centroid_herd[0] - centroid_camera[0]
    dif_y = centroid_herd[1] - centroid_camera[1]

    # get the middle 75% of the image, i.e. 12.5% on each side
    left_range = results[0].orig_shape[1]/8
    right_range = results[0].orig_shape[1] - left_range
    top_range = results[0].orig_shape[0]/8
    bottom_range = results[0].orig_shape[0] - top_range

    # get range of x values for herd
    x_min_herd, x_max_herd = px['x1'].min(), px['x2'].max()
    y_min_herd, y_max_herd = px['y1'].min(), px['y2'].max()

    # Calculate next move for drone in x, y, z direction

    # navigation policy: move x, y, z, yaw until herd is in center of camera frame, keep checking every 1 sec to adjust
    # continuous adjustments allows us to avoid complex calculations and avoid overshooting
    # direction_x = "No movement in x-axis"
    # direction_y = "No movement in y-axis"
    # direction_z = "No movement in z-axis"
    direction_x = 0
    direction_y = 0
    direction_z = 0

    if (centroid_herd[0] < x_center_range[0]) | (centroid_herd[0] > x_center_range[1]):
        if dif_x > 0:
            #print("y-axis: Move right")
            direction_y = +y_dist # move right
        elif dif_x < 0:
            #print("y-axis: Move left")
            direction_y = -y_dist # move left
        else:
            #print("y-axis: No movement in y-axis")
            direction_y = 0
    else:
        #print("y-axis: No movement in y-axis")
        direction_y = 0

    # if no movement left or right, move forward or backward
    if direction_y == 0:
        # check to see if herd is in center 75% of camera frame
        if (x_min_herd >= left_range) | (x_max_herd <= right_range):
            #print("x-axis: Move forward")
            direction_x = x_dist # move forward
        elif (x_min_herd <= left_range) | (x_max_herd >= right_range):
            #print("x-axis: Move backward")
            direction_y = -x_dist # move backward
    else:
        #print("No movement in x-axis")
        direction_y = 0

    # note: y-axis in image is actually z-axis in drone; y-axis in image is inverted (0,0 is top left corner)

    if (centroid_herd[1] < y_center_range[0]) | (centroid_herd[1] > y_center_range[1]):
        if (dif_y >= 0.0) & (y_min_herd >= bottom_range):
            #print("z-axis: Move down")
            direction_z = -z_dist # move down
        elif (dif_y <= 0.0) & (y_max_herd <= bottom_range):
            #print("z-axis: Move up")
            direction_z = z_dist # move up
        else:
            #print("No movement in z-axis")
            direction_z = 0
    else:
        #print("No movement in z-axis")
        direction_z = 0

    return  direction_x, direction_y, direction_z

def get_next_action(frame, model, directory, frame_counter):
    # Get the position of the herd in the frame
    count, results = detect_animals(frame, model)

    # save the frame with bounding boxes
    results[0].save(directory + '/' + str(frame_counter) + '.jpg')

    if count == 0:
        # no animals detected, continue mission"
        print("No animals detected")
        x =  x_dist_no_subject # move forward
        y = 0 # no movement in y-axis
        z = 0 # no movement in z-axis
        return x, y, z
    else:
        # animals detected, determine where to move
        x, y, z, = auto_navigation(results)
        return x, y, z

def main(image_path, directory):
    # Get the frame from the drone video
    #image = cv2.imread(image_path)

    # crop the frame to focus on center of image
    frame = crop_image(image_path)

    # Load the YOLO model to detect animals
    model = YOLO('yolov5su')

    # Determine where the drone should move to keep the herd in the frame
    # sleep for 1 second to allow drone to move
    time.sleep(1)
    # get the next action for the drone
    actions = get_next_action(frame, model, directory)

    return print("actions: ", actions)

if __name__ == "__main__": 
    main(sys.argv[1], sys.argv[2])