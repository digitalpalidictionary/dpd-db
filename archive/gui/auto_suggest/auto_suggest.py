import csv
import io
from json import dumps
import json
import re
import time
from pathlib import Path

from google import genai
from rich import print

from db.db_helpers import get_column_names, get_db_session
from db.models import DpdHeadword
from tools.configger import config_read
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class AutoSuggestData:
    def __init__(self, id: int):
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.id = id
        self.headword: list[DpdHeadword] = (
            self.db_session.query(DpdHeadword).filter(DpdHeadword.id == id).all()
        )
        self.type: str | None = self.get_type()
        self.completed: list[DpdHeadword] | None = self.get_complete_data()

    def get_type(self):
        if self.headword:
            headword = self.headword[0]
            if headword.root_key:
                return "root"
            elif re.findall(r"\bcomp\b", headword.grammar):
                return "compound"
            elif headword.family_word:
                return "word"
        return None

    def get_complete_data(self):
        if self.headword and self.type == "root":
            return (
                self.db_session.query(DpdHeadword)
                .filter(DpdHeadword.root_key == self.headword[0].root_key)
                .filter(DpdHeadword.meaning_1 != "")
                .all()
            )


class AutoSuggestController:
    columns_excluded = [
        "lemma_2",  # its already complete
        "non_root_in_comps",  # useless field which should get deleted
        "source_1",  # don't need examples
        "sutta_1",
        "example_1",
        "source_2",
        "sutta_2",
        "example_2",
        "commentary",
        "notes",
        "cognate",
        "link",
        "origin",
        "stem",
        "pattern",
        "created_at",
        "updated_at",
        "inflections",
        "inflections_api_ca_eva_iti",
        "inflections_sinhala",
        "inflections_devanagari",
        "inflections_thai",
        "inflections_html",
        "freq_data",
        "freq_html",
        "ebt_count",
    ]

    def __init__(self, id) -> None:
        self.data = AutoSuggestData(id)
        self.prompt = self.make_prompt()
        self.api_key = config_read("apis", "gemini")
        self.client = genai.Client(api_key=self.api_key)
        # self.model = "gemini-2.0-flash"
        self.model = "gemini-2.5-pro-exp-03-25"
        self.response = self.client.models.generate_content(
            model=self.model,
            contents=self.prompt,
        )
        print(self.response.text)

    def make_tsv(self, data: list[DpdHeadword]) -> str:
        columns_yes = [
            column
            for column in get_column_names(DpdHeadword)
            if column not in self.columns_excluded
        ]
        output = io.StringIO()
        writer = csv.DictWriter(
            output, fieldnames=columns_yes, delimiter="\t", quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        for headword in data:
            writer.writerow(
                {column: getattr(headword, column) for column in columns_yes}
            )
        return output.getvalue()

    def make_prompt(self):
        return f"""
You are an expert in Pāḷi grammar.

Here is a TSV table of Pāḷi grammatical data that has COMPLETE_DATA. Please study it

{self.make_tsv(self.data.completed)}

and here is a a TSV table of a word with INCOMPLETE_DATA. 

{self.make_tsv(self.data.headword)}

Using your most careful analysis of the COMPLETE_DATA, please fill in the necessary fields in the INCOMPLETE_DATA. 

Return that as a pure JSON. I repeat only JSON, nothing else. No markup, just JSON. Really.

Make a new column at the end of the JSON called "comments". 

Any comments you want to make about your choices can be included in that. Use plain text in that field, not markdown.


"""

    def cleanup_response(self):
        if self.response and self.response.text:
            match = re.search(r"```json\n(.*?)\n```", self.response.text, re.DOTALL)

            if match:
                json_string = match.group(1).strip()
                try:
                    data = json.loads(json_string)
                    print("Successfully parsed JSON:")
                    # Pretty print the result
                    print(json.dumps(data, indent=4, ensure_ascii=False))
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    print("Extracted string part:")
                    print(json_string)
            else:
                print("Could not find JSON block within ```json ... ``` fences.")


def main():
    pr.tic()
    pr.title("Auto-complete")
    AutoSuggestController(9142)
    # save_path = Path("temp/autocomplete_after.tsv")
    # save_path.write_text(str(response.text))
    pr.yes("ok")
    pr.toc()


if __name__ == "__main__":
    main()
