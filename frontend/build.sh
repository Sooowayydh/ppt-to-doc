#!/bin/bash

# Ensure Python 3.9 is available
python3.9 --version

# Install pip if not available
python3.9 -m ensurepip --upgrade

# Upgrade pip
python3.9 -m pip install --upgrade pip

# Install requirements
python3.9 -m pip install -r requirements.txt

# Make the script executable
chmod +x build.sh 