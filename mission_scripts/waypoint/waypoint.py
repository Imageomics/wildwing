# This script reads in a csv file containing GPS coordinates and altitudes for waypoints and sends the drone to each waypoint in sequence.

import csv
import sys


def get_waypoints(csv_file):
    """
    Read in the csv file containing waypoints and return a list of waypoints
    """
    waypoints = []
    with open(csv_file, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            waypoints.append([float(row[0]), float(row[1]), float(row[2])])
    return waypoints

def main():
    waypoints_file = sys.argv[1]
    waypoints = get_waypoints(waypoints_file)
    return waypoints
    
if __name__ == "__main__":
    main()