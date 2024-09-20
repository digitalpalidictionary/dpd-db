#!/usr/bin/env python3

"""Print the version number"""

from tools.configger import config_read

def main():
    print(config_read("version", "version"))


if __name__ == "__main__":
    main()
