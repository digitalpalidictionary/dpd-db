import pickle

from rich import print

from tools.paths import ProjectPaths
from tools.date_and_time import year_month_day


def get_daily_record(pth: ProjectPaths):
    date = year_month_day()
    if not pth.daily_record_path.exists():
        daily_record: dict = {}
        daily_record = daily_record_add_date(daily_record, date)
    else:
        daily_record = daily_record_read(pth)
        if date not in daily_record:
            daily_record = daily_record_add_date(daily_record, date)
    daily_record_save(pth, daily_record)
    return daily_record


def daily_record_read(pth) -> dict:
        with open(pth.daily_record_path, "rb") as f:
            return pickle.load(f)


def daily_record_save(pth: ProjectPaths, daily_record: dict) -> None:
        with open(pth.daily_record_path, "wb") as f:
            pickle.dump(daily_record, f)


def daily_record_add_date(daily_record: dict, date: str) -> dict:
   if date not in daily_record:
       daily_record.update({date: {"added":[], "edited":[], "deleted":[]}})
   return daily_record


def daily_record_update(window,
                        pth:ProjectPaths,
                        action: str,
                        word_id: int):

    """"Actions are "add", "edit", "delete", refresh"""

    date = year_month_day()
    daily_record = get_daily_record(pth)
    if date not in daily_record:
        daily_record = daily_record_add_date(daily_record, date)
    if action == "add":
        daily_record[date]["added"] += [word_id]
    elif action == "edit":
        daily_record[date]["edited"] += [word_id]
    elif action == "delete":
        daily_record[date]["deleted"] += [word_id]
    elif action == "refresh":
        pass
    daily_record_save(pth, daily_record)
    print(daily_record[date])

    window["daily_added"].update(len(daily_record[date]["added"]))
    window["daily_edited"].update(len(daily_record[date]["edited"]))
    window["daily_deleted"].update(len(daily_record[date]["deleted"]))
                                      