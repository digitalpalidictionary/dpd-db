#!/bin/bash

# run deconstructor on cloud

# ctrl-shift-p ssh connect to host
# root@ipaddress
# bash sandhi.sh

# Update and upgrade the system
sudo apt-get update && sudo apt-get upgrade -y --no-install-recommends

# Install prerequisites
sudo apt-get install -y unzip

# Add deadsnakes PPA and install Python 3.11
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11

# Install pip for Python 3
sudo apt-get install -y python3-pip

# Install gdown
pip3 install gdown

# Install zip utility
sudo apt-get install -y zip

# Unzip the file and clean up
unzip -o sandhi.zip && rm sandhi.zip

# Install Poetry using the official installer
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Update and upgrade the system
sudo apt-get update && sudo apt-get upgrade -y --no-install-recommends

# Install prerequisites
sudo apt-get install -y unzip

# Add deadsnakes PPA and install Python 3.11
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11

# Install pip for Python 3
sudo apt-get install -y python3-pip

# Install gdown
pip3 install gdown

# Install zip utility
sudo apt-get install -y zip

# Unzip the file and clean up
unzip -o sandhi.zip && rm sandhi.zip

# Install Poetry using the official installer
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/root/.local/bin:$PATH"
alias python=python3.11
source ~/.bashrc
poetry self update

# Install project dependencies
poetry install

# Add the Pythonpath
export PYTHONPATH=$PYTHONPATH:db/deconstructor/tools

# Run
nohup poetry run python3.11 db/deconstructor/sandhi_splitter.py &

# View Progress
# cat nohup.out

# Zip output
# zip -j -r output_do.zip db/deconstructor/output/ && zip output_do nohup.out
