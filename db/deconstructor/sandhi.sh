# run deconstructor on cloud

# ctrl-shift-p ssh connect to host
# root@ipaddress
# bash sandhi.sh
apt-get install -y unzip
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update 
sudo apt install -y python3.11
sudo apt upgrade -y

apt install -y python3-pip
pip install gdown
apt install -y zip

unzip -o sandhi.zip
rm sandhi.zip
apt install -y python3-poetry
poetry install
# poetry shell
export PYTHONPATH=$PYTHONPATH:db/deconstructor/tools
nohup poetry run python3.11 db/deconstructor/sandhi_splitter.py &
# cat nohup.out
# zip -j -r output_do.zip db/deconstructor/output/ && zip output_do nohup.out
