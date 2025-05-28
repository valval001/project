#!/bin/bash

# Update system
sudo apt update && sudo apt install -y software-properties-common

# Install Python3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Set up virtual environment
source venv/bin/activate

# Install project requirements
pip install --upgrade pip
pip install -r requirements.txt
