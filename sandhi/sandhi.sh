# open terminal
# ssh root@ipaddress
# apt-get install unzip
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update 
sudo apt install python3.11
sudo apt upgrade

apt install python3-pip
pip install gdown
apt install zip

unzip sandhi.zip
rm sandhi.zip
pip install poetry
poetry install
# poetry shell
export PYTHONPATH=$PYTHONPATH:sandhi/tools
nohup poetry run python3.11 sandhi/splitter.py &
cat nohup.out
# zip -j -r do_output.zip sandhi/output/