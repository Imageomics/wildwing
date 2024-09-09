#!/bin/bash

# usage: ./launch.sh <drone_model> <mission_type>
# example: ./launch.sh parrot waypoint missions/waypoints.txt
#          ./launch.sh dji autonomous herd_track yolov5s

drone_model=$1
mission_type=$2
waypoint_file=$3
auto_mission_type=$3
model=$4

# Initialize Conda for the shell
source ~/miniconda3/etc/profile.d/conda.sh

# Activate the Conda environment
conda activate wildwing

# Generate a timestamp
timestamp=$(date +"%Y%m%d_%H%M%S")

# Create file to save tracking results
output_dir="missions/misson_record_$timestamp"

# Create the output directory if it does not exist
mkdir -p "$output_dir"

# Run the Python script and save the output to a log file
if [ "$drone_model" == "parrot" ]; then
    if [ "$mission_type" == "autonomous" ]; then
        python3 parrot/autonomous_missions/controller.py "$output_dir" > "logs/output_$timestamp.log" 2>&1
    elif [ "$mission_type" == "waypoint" ]; then
        # use the waypoint file
        # to do
        # python3 parrot/waypoint_missions/controller.py "$output_dir" > "logs/output_$timestamp.log" 2>&1
    else
        echo "Invalid mission type"
    fi
elif [ "$drone_model" == "dji" ]; then
    if [ "$mission_type" == "autonomous" ]; then
        # to do
    elif [ "$mission_type" == "waypoint" ]; then
        # to do
    else
        echo "Invalid mission type"
    fi
else
    echo "Invalid drone model"
fi
