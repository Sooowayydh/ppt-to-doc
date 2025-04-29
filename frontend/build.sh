#!/bin/bash

# Ensure Python is available
python --version

# Install pip if not available
python -m ensurepip --upgrade

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Make the script executable
chmod +x build.sh 