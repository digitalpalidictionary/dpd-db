#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tomlkit

from rich import print

from db.models import DbInfo
from db.db_helpers import get_db_session
from tools.configger import config_update
from tools.date_and_time import year_month_day
from tools.paths import ProjectPaths
from tools.printer import printer as pr


major = 0
minor = 2


def printer(key, value):
    print(f"[green]{key:<20}[white]{value}")


def make_version():
    patch = year_month_day()

    version = f"v{major}.{minor}.{patch}"
    version_light = f"v{major}.{minor}"

    printer("version", version)
    printer("version light", version_light)

    return version, version_light


def update_project_version(pth, version_light_light):
    with open(pth.pyproject_path) as file:
        doc = file.read()
        t = tomlkit.parse(doc)
        t["project"]["version"] = version_light_light  # type: ignore

    with open(pth.pyproject_path, "w") as file:
        file.write(t.as_string())

    printer("pyproject.toml", "ok")


def update_db_version(pth, version):
    db_session = get_db_session(pth.dpd_db_path)
    db_info = db_session.query(DbInfo).filter_by(key="dpd_release_version").first()

    # update the dpd_release_version if it exists
    if db_info:
        db_info.value = version

    # add the dpd_release_version and author info if it doesn't exist
    else:
        dpd_release_version = DbInfo(key="dpd_release_version", value=version)
        db_session.add(dpd_release_version)

        author = DbInfo(key="author", value="Bodhirasa")
        db_session.add(author)

        email_address = DbInfo(key="email", value="digitalpalidictionary@gmail.com")
        db_session.add(email_address)

        website = DbInfo(key="website", value="https://www.dpdict.net/")
        db_session.add(website)

        docs = DbInfo(key="docs", value="https://digitalpalidictionary.github.io/")
        db_session.add(docs)

        github = DbInfo(
            key="github", value="https://github.com/digitalpalidictionary/dpd-db"
        )
        db_session.add(github)

        latest_release = DbInfo(
            key="latest_release",
            value="https://github.com/digitalpalidictionary/dpd-db/releases",
        )
        db_session.add(latest_release)

        license = DbInfo(key="license", value="CC BY-NC-SA 4.0")
        db_session.add(license)

        ___ = DbInfo(key="___", value="___")
        db_session.add(___)

    db_session.commit()
    printer("dpd.db", "ok")


def main():
    pr.tic()
    pr.title("updating dpd release version")
    pth = ProjectPaths()
    version, version_light = make_version()

    config_update("version", "version", version, silent=True)
    printer("config.ini", "ok")

    # update_project_version(pth, version_light)
    update_db_version(pth, version)

    pr.toc()


if __name__ == "__main__":
    main()
