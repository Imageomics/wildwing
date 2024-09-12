#!/bin/bash

# usage: ./launch.sh <autonomous_mission_type> <number_of_drones> <drone_model> <cv_model>

auto_mission_type = $1 # note, this is not used in script yet, default is herd-track
num_drones = $2 # note, this is not used in script yet, default is 1
drone_model = $3 # Parrot or DJI
cv_model = $4 # note, this is not used in script yet, default is yolov5s

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
    python3 parrot/autonomous_missions/controller.py "$output_dir" > "logs/output_$timestamp.log" 2>&1
elif [ "$drone_model" == "dji" ]; then
    # python3 dji/autonomous_missions/controller.py "$output_dir" > "logs/output_$timestamp.log" 2>&1 TO DO
else
    echo "Invalid drone model"
fi
