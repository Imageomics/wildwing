#!/bin/bash

# usage: ./run_mission.sh <number_of_drones> <drone_models> <mission_type> 
#                           <autonomous_mission_type> <cv_model> <waypoint_file>

# number_of_drones = $1
number_of_drones=1 # For now, we will only use one drone
drone_models=$2
mission_type=$3
autonomous_mission_type=$4
cv_model=$5
waypoint_file=$6

# Initialize Conda for the shell
source ~/miniconda3/etc/profile.d/conda.sh

# Activate the Conda environment
conda activate wildwing

# Generate a timestamp
timestamp=$(date +"%Y%m%d_%H%M%S")

# Create file to save tracking results
output_dir="missions/mission_record_$timestamp"

# Create the output directory if it does not exist
mkdir -p "$output_dir"

# Run the Python script and save the output to a log file
if [ "$drone_models" = "parrot" ]; then
    python3 parrot/parrotController.py "$output_dir" > "logs/output_$timestamp.log" "$mission_type" "$autonomous_mission_type" "$cv_model" "$waypoint_file" 2>&1
elif [ "$drone_models" = "dji" ]; then
    # TO DO
    # python3 dji/djiController.py "$output_dir" > "logs/output_$timestamp.log" 2>&1
    echo "DJI controller script not implemented yet"
else
    echo "Invalid drone model"
fi

