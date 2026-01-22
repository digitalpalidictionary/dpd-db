from db.models import DpdHeadword, DpdRoot, Lookup
from tools.date_and_time import year_month_day_dash
from tools.meaning_construction import (
    make_grammar_line,
)


class HeadwordData:
    def __init__(self, i: DpdHeadword, fc, fi, fs):
        self.meaning = i.meaning_combo_html
        self.summary = i.construction_summary
        self.complete = i.degree_of_completion_html
        self.grammar = make_grammar_line(i)
        self.i = self.convert_newlines(i)
        self.fc = fc
        self.fi = fi
        self.fs = fs
        self.su = i.su
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()

    @staticmethod
    def convert_newlines(obj):
        # Only convert specific string columns to avoid triggering lazy loads
        # of relationships and properties through dir(obj) and getattr()
        string_columns = [
            "meaning_1", "meaning_lit", "meaning_2", "construction",
            "phonetic", "compound_construction", "commentary", "notes",
            "example_1", "example_2"
        ]
        # We'll return a proxy object or just the modified SQLAlchemy object 
        # but with only specific fields changed.
        # Since the session is about to close, modifying the object is usually okay 
        # in the webapp, but the dir(obj) was the real killer.
        for attr_name in string_columns:
            attr_value = getattr(obj, attr_name, None)
            if isinstance(attr_value, str) and attr_value:
                try:
                    setattr(obj, attr_name, attr_value.replace("\n", "<br>"))
                except AttributeError:
                    continue
        return obj


class RootsData:
    def __init__(self, r, frs, roots_count_dict) -> None:
        self.r: DpdRoot = r
        self.frs = frs
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()
        self.count = roots_count_dict[self.r.root]


class DeconstructorData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.deconstructions = result.deconstructor_unpack
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()


class VariantData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.variants = result.variants_unpack
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()


class SpellingData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.spellings = result.spelling_unpack
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()


class GrammarData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        # self.grammar = result.grammar_unpack
        self.grammar = self._process_grammar(result.grammar_unpack)
    
    def _process_grammar(self, grammar_list):
        processed_list = []
        for item in grammar_list:
            headword, pos, grammar_str = item
            components = []
            
            if grammar_str.startswith("reflx"):
                parts = grammar_str.split()
                if len(parts) >= 2:
                    components.append(parts[0] + " " + parts[1])
                    components += parts[2:]
                else:
                    components.append(grammar_str)
            elif grammar_str.startswith("in comps"):
                # Handle 'in comps' specifically if needed, 
                # but based on my previous fix, we treat it as a normal component
                # and let the template handle empty cells.
                # Actually, for the webapp, let's just split it as is or keep it as one.
                # In grammar_dict.py, I used:
                # html_line += f"<td>{grammar_str}</td>"
                # html_line += "<td class='col_empty'></td>"
                # html_line += "<td class='col_empty'></td>"
                components.append(grammar_str)
            else:
                components = grammar_str.split()
            
            # Pad with empty strings to ensure 3 components
            while len(components) < 3:
                components.append("")
                
            processed_list.append((headword, pos, components))
        return processed_list


class HelpData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.help = result.help_unpack


class AbbreviationsData:
    def __init__(self, result: Lookup):
        data = result.abbrev_unpack
        self.headword = result.lookup_key
        self.meaning = data["meaning"]
        self.pali = data["pāli"]
        self.example = data["example"]
        self.explanation = data["explanation"]


class EpdData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.epd = result.epd_unpack


class ManualVariantData:
    def __init__(self, variant: str, main: str):
        self.headword = variant
        self.main = main
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()
