#!/usr/bin/env python3

import sys

from scripts.build.config_uposatha_day import uposatha_day_reset

if __name__ == "__main__":
    uposatha_day_reset(force="force" in sys.argv[1:])
