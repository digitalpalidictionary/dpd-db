#!/usr/bin/env python3

"""Save a list of raw inflections (without stems) to TSV."""

import json

from db.db_helpers import get_db_session
from db.models import InflectionTemplates
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.tsv_read_write import write_tsv_list


def main():
    tic()
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    infl_templ = db_session.query(InflectionTemplates)

    inflections_pos = []
    for i in infl_templ:
        if i.data is None:
            continue
        data = json.loads(i.data)
        for row in data:
            if row != data[0]:
                row_length = len(row)
                for x in range(1, row_length, 2):
                    for inflection in row[x]:
                        pos = row[x+1][0]
                        pattern = i.pattern
                        inflections_pos += [(inflection, pos, pattern)]

    inflections_pos = sorted(
        inflections_pos, key=lambda x: (pali_sort_key(x[0]), x[1], x[2]))

    path = pth.temp_dir.joinpath("inflections_raw.tsv")
    headers = ["inflection", "pos", "pattern"]
    write_tsv_list(str(path), headers, inflections_pos)

    toc()


if __name__ == "__main__":
    main()
