# run deconstructor on cloud

# ctrl-shift-p ssh connect to host
# root@ipaddress
# bash sandhi.sh
apt-get install unzip
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update 
sudo apt install python3.11
sudo apt upgrade

apt install python3-pip
pip install gdown
apt install zip

unzip -o sandhi.zip
rm sandhi.zip
apt install python3-poetry
poetry install
# poetry shell
export PYTHONPATH=$PYTHONPATH:sandhi/tools
nohup poetry run python3.11 sandhi/sandhi_splitter.py &
# cat nohup.out
# zip -j -r do_output.zip sandhi/output/ && zip do_output nohup.out