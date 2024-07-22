#!/usr/bin/env python3

"""Process BJT file"""

import json
import re
from rich import print

from pathlib import Path
from tools.pali_text_files import bjt_texts

def process_single_bjt_file(
        dict: dict,
        footnote_inline:bool=False,
        show_page_numbers:bool=False,
        show_metadata:bool=True
    ) -> str:
    
    """Return Pāḷi text for a single BJT file."""
    
    main_text = []
    
    if show_metadata:
        main_text.append(f"filename: {dict['filename']}")
        main_text.append(f"bookId  : {dict['bookId']}") 

    pages = dict["pages"]
    for page in pages:
        if show_page_numbers:
            page_number = page["pageNum"]
            main_text.append(f"page {page_number}.")

        pali = page["pali"]
        entries = pali["entries"]
        footnotes = pali["footnotes"]

        for entry in entries:
            text = entry["text"]
            
            # replace ** with bold tags
            text = re.sub(
                r"""
                (\*\*)              # find **   
                (.+?)               # capture whats in-between  
                (\*\*)              # find **   
                """, 
                "<b>\\2</b>",       # replace with bold + capture
                text, 
                flags=re.VERBOSE
            )

            # put footnotes inline
            if footnote_inline:
                footnote_links = re.findall(
                    r"""\{(\d*)\}""", text)
                for fl in footnote_links:
                    num = int(fl)
                    footnote_num = footnotes[num-1]["text"]
                    text = re.sub(
                        fr"""\{{{num}\}}""",
                        fr"{{{footnote_num}}}",
                        text, flags=re.DOTALL)
            
            # TODO add {*} footnotes

            main_text.append(text)
        
        if not footnote_inline:
            if footnotes:
                main_text.append("---------")
                for footnote in footnotes:
                    text = footnote["text"]
                    main_text.append(text)
                main_text.append("---------")

    if show_metadata:
        main_text.append(f"filename: {dict['filename']}")
        main_text.append(f"bookId  : {dict['bookId']}") 

    return "\n".join(main_text)


def main():

    roman_dir = Path("resources/tipitaka.lk/public/static/text_roman")

    books = ["mn1", "mn2", "mn3"]
    for book in books:
        for file_name in bjt_texts[book]:
            file_path = roman_dir.joinpath(file_name)
            with open(file_path) as f:
                dict = json.load(f)
            text = process_single_bjt_file(dict)
            print(text)



if __name__ == "__main__":
   main()
