#!/usr/bin/env bash

# unpack and copy downloaded dpd on the server

cp -f ~/Downloads/dpd-mdict.mdx ~/filesrv1/share1/Sharing\ between\ users/1\ For\ Everyone/Software/MDict/DPD/dpd-mdict.mdx

cp -f ~/Downloads/dpd-grammar-mdict.mdx ~/filesrv1/share1/Sharing\ between\ users/1\ For\ Everyone/Software/MDict/DPD/dpd-grammar-mdict.mdx

cp -f ~/Downloads/dpd-deconstructor-mdict.mdx ~/filesrv1/share1/Sharing\ between\ users/1\ For\ Everyone/Software/MDict/DPD/dpd-deconstructor-mdict.mdx

echo -e "\033[1;32m DPD MDic moved to the server \033[0m"

cp -f ~/Downloads/dpd-kindle.mobi ~/filesrv1/share1/Sharing\ between\ users/1\ For\ Everyone/Software/dpd-kindle.mobi

echo -e "\033[1;32m DPD Kindle moved to the server \033[0m"

poetry run python "unzip-dpd-downloaded.py"




