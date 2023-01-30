SHELL := /bin/bash

all:
	@echo "Specify a make target."

bootstrap:
	./scripts/bootstrap_dpd_from_csv.py | tee log.txt

backup-watcher:
	./scripts/backup_watcher.sh

gui:
	./dpd/gui.py
