open terminal
ssh root@ipaddress
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update 
sudo apt install python3.11
sudo apt upgrade

apt install python3-pip
pip install gdown
apt install zip
apt-get install unzip

gdown 1j62n1EBn1K_EbjaJEoOghmX4eVC75pVS
https://drive.google.com/file/d/1j62n1EBn1K_EbjaJEoOghmX4eVC75pVS/view?usp=share_link
unzip sandhi.zip
rm sandhi.zip
mkdir sandhi/output
pip install poetry
poetry install
poetry shell
export PYTHONPATH=$PYTHONPATH:sandhi/tools
nohup python3.11 sandhi/splitter.py &
# .... wait ....
tail -n 10 nohup.out
# nohup python3.11 sandhi/postprocess.py &
zip -r do_output.zip sandhi/output/
# in local terminal
scp root@ipaddress:/root/dpd/do_output.zip do_output.zip

# ps aux | grep python
# tail -f /proc/3245/fd/1
