import os

from bs4 import BeautifulSoup
from aksharamukha import transliterate
from rich import print

from helpers import get_paths


def main():

    print("[bright_yellow]convert cst4 xml to txt")
    pth = get_paths()

    for filename in sorted(os.listdir(pth.cst_xml_dir)):
        print(f"    {filename}")

        try:
            if ".xml" in filename:
                with open(
                        pth.cst_xml_dir.joinpath(filename), 'r',
                        encoding="UTF-16") as f:

                    contents = f.read()
                    soup = BeautifulSoup(contents, 'xml')
                    text_tags = soup.find_all('text')

                    text_extract = ""

                    for text_tag in text_tags:
                        text_extract += text_tag.get_text() + "\n"

                    text_translit = transliterate.process(
                        "autodetect", "IASTPali", text_extract)

                    with open(
                            pth.cst_txt_dir.joinpath(filename).joinpath(".txt"),
                            "w") as f:
                        f.write(text_translit)

            else:
                print("[red]not .xml file: skipped")

        except Exception:
            print(f"[bright_red]ERROR: {filename} failed!")


if __name__ == "__main__":
    main()
