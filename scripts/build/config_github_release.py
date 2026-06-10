#!/usr/bin/env python3

"""Setup config for github release."""

from rich import print

from tools.configger import config_apply_profile
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    print("[bright_yellow]github release config options")
    config_apply_profile("github_release")
    pr.toc()


if __name__ == "__main__":
    main()
