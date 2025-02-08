# WildWing Deployment Instructions

## General comments & suggestions
- We did not observe a difference in the drone's battery discharge rate between manual and autonomous missions.
- User may take over manual control at any time. The drone may be manually readjusted to focus on a particular sub-group of the herd if desired. After manual adjustments, the WildWing system automatically returns to autonomous control.
- We used the version of SoftwarePilot compatible with the Parrot Anafi drone. The software is available at [SoftwarePilot](https://github.com/KevynAngueira/SoftwarePilot). A version of SoftwarePilot compatible with the DJI drones are available at [SoftwarePilotDJI](https://github.com/boubinjg/SoftwarePilot/tree/master).

## Deployment Phases

The first two deployment phases are completed manually, which include locating the animals and setting up the WildWing system.

The remaining four phases are completed autonomously by the WildWing system, conducted under the supervision of a drone pilot and animal welfare expert.

The drone was flown within the pilot's visual line of sight, per U.S. Federal Aviation Authority drone regulations.

![WildWing Deployment Phases](images/deploy.png)
WildWing Deployment Phases. Steps 1 and 2 are accomplished manually. Steps 3-6 are
accomplished autonomously by the WildWing system.


### 1. Locate Animals
brew install pandoc
We worked with the experts at The Wilds to locate the animals within the conservation center.

We parked the field vehicle approximately 250 meters from the focal animals, situated in a location with an unobstructed view of the herd.

When possible, we parked the vehicle behind a pasture fence to ensure the safety of the team and the animals.

Once the vehicle was parked, we observed the animals for five minutes to ensure they did not appear disturbed by our presence and set up the WildWing system for launch.

Alternatively, in habitats where vegetation blocks ground visibility, users may manually pilot the drone to locate the animals of interest.

### 2. Set Up WildWing System

We summarize the system settings in the following table:

| Parameter | Value |
|-----------|--------|
| Mission duration | 200 sec |
| Altitude | 20 meters ± 3 meters |
| Forward searching increment | 10 m |
| Forward/back movement | 5 meters |
| Left/right movement | 5 meters |
| Up/down movement | 5 meters |
| Sampling rate | 1:40 frames |
| Computer vision model | YOLOv5su |

We used the guidelines from Kline et al. (2024) to establish the minimum altitude parameters (20 ± 3 meters).

We selected 200 seconds as the mission duration. This allowed us to collect sufficient frames for behavior analysis while ensuring the pilot could periodically complete a thorough system check. This also allowed us to complete multiple missions quickly to use the drone's battery efficiently.

Using the results from the manual flights and the wind conditions, we tuned the controller system parameters to ensure the drone's maneuvers would not stress the animals.

The drone's flight control system converts movement commands from meters into GPS coordinates and continuously makes minor adjustments to maintain its position. During our test flights, we observed that wind conditions significantly affected the drone's ability to hold its location precisely. To address this, we tuned the controller system parameters based on data from manual test flights to optimize performance while ensuring the drone's movements would not disturb the animals. Initially, we programmed the drone to move 5 meters forward when no focal animal was detected and 2 meters in any direction (left/right, forward/back, up/down) for positioning adjustments. However, increasing these distances improved efficiency under windy conditions by reducing the drone's time making position corrections. The larger movement increments helped compensate for wind-induced displacement while maintaining effective search patterns.

We used a sampling rate of 1:40 frames or once every 1.3 seconds. This sampling rate was sufficient to track the animals walking or grazing but may be adjusted to track faster-moving species and behaviors.


### 3. Launch

To launch the drone, the pilot manually positioned the drone's camera facing the herd.

We used the hood of our field truck as the launch and landing zone to protect the propellers from being damaged by tall grass in the pastures.

We flew into the wind to reduce the drone's noise propagation when possible.

Once the drone was positioned, the WildWing system automatically started the propellers and flew the drone 20 meters directly above the launch point.

### 4. Approach

After launch, the drone is programmed to move forward in preset increments until the object detector model registers the animals of interest.

For this study, we used 10 meters for the approach increments and YOLOvsu as our object detector and classifer model.

Positioning the drone facing the animals at launch ensures the animals are eventually detected, assuming there is no dramatic change in the herd's location.

### 5. Track

Once the focal species is recognized, the dynamic tracking algorithm its autonomous navigation.

First, the herd's centroid is calculated using the bounding boxes generated by the object detector.

An example of the bounding box generated by the object detector is included in the middle image of zebras.

Using the offset between the herd centroid and camera center region, the algorithm determines the appropriate action to take to keep the herd in view of the camera.

The actions include maneuvering the drone left/right, forward/back, or up/down.

These actions were executed in 5-meter increments for this study.

The mission continued for a maximum of 5 minutes.

### 6. End Mission

After 200 seconds, depending on the battery's state, the pilot may decide to continue the mission or execute return-to-home commands.