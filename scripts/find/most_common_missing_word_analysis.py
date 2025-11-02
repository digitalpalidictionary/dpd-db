from rich import print

from tools.tsv_read_write import read_tsv_dict


def open_file():
    try:
        return read_tsv_dict("scripts/find/most_common_missing_words.tsv")
    except FileNotFoundError:
        return read_tsv_dict("scripts/find/most_common_missing_words_old.tsv")


def get_stats(data):
    total_dict = {}
    total_dict["word#"] = "total"
    running_total = 0
    k25000 = True
    k50000 = True
    k100000 = True
    k250000 = True
    for num, i in enumerate(data):
        running_total += int(i["count"])
        if k25000 and running_total > 25000:
            total_dict[num] = 25000
            k25000 = False
        if k50000 and running_total > 50000:
            total_dict[num] = 50000
            k50000 = False
        if k100000 and running_total > 100000:
            total_dict[num] = 100000
            k100000 = False
        if k250000 and running_total > 250000:
            total_dict[num] = 250000
            k250000 = False
    total_dict[num] = running_total

    return total_dict


def get_stats2(data):
    total_dict = {}
    running_total = 0
    for num, i in enumerate(data):
        running_total += int(i["count"])
    total = running_total

    running_total = 0

    for num, i in enumerate(data):
        running_total += int(i["count"])
        if num % 5000 == 0:
            total_dict[num] = (running_total / total) * 100

    total_dict[num] = 100.00
    return total_dict


def main():
    data = open_file()

    totals_dict = get_stats(data)
    for k, v in totals_dict.items():
        print(f"{k:>6}: {v:>6}")

    print()

    totals_dict2 = get_stats2(data)
    for k, v in totals_dict2.items():
        print(f"{k:>6}: {v:>6.2f}")


if __name__ == "__main__":
    main()
