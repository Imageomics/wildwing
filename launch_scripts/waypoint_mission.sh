#!/bin/bash

# usage: ./waypoint_mission.sh <number_of_drones> <drone_model> <waypoint_file> 

number_of_drones = $1
drone_model = $2
waypoint_file = $3

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
    python3 parrot/waypoint_missions/controller.py "$output_dir" > "logs/output_$timestamp.log" 2>&1
    
elif [ "$drone_model" == "dji" ]; then
   python3 dji/waypoint_missions/controller.py "$output_dir" > "logs/output_$timestamp.log" 2>&1
else
    echo "Invalid drone model"
fi
