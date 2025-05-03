import re
from sqlalchemy.orm.session import Session
from sqlalchemy import desc, func

from db.db_helpers import get_db_session
from db.models import (
    DpdHeadword,
    DpdRoot,
    FamilyCompound,
    FamilyRoot,
    FamilyWord,
    Lookup,
)
from gui2.dpd_fields_functions import clean_lemma_1
from tools.paths import ProjectPaths


class DatabaseManager:
    def __init__(self) -> None:
        self.pth: ProjectPaths = ProjectPaths()

        self.db_session: Session
        self.new_db_session()

        self.db: list[DpdHeadword]
        self.all_inflections: set[str] = set()
        self.all_inflections_missing_meaning: set[str] = set()

        self.sandhi_ok_list: set[str] = set(
            self.pth.decon_checked.read_text().splitlines()
        )  # FIXME make a file manager for this

        # for pass2 preprocessor
        self.all_inflections_missing_example: set[str] = set()
        self.all_suffixes: set[str] = set()

        # only need these later
        self.all_lemma_1: set[str] | None = None
        self.all_lemma_clean: set[str] | None = None
        self.all_pos: set[str] | None = None
        self.all_roots: set[str] | None = None
        self.all_compound_families: set[str] | None = None
        self.all_root_families: set[str] | None = None
        self.all_word_families: set[str] | None = None
        self.all_plus_cases: list[str] | None = None  # Add this line
        self.all_compound_types: list[str] | None = None  # Add this line
        self.all_family_sets: list[str] | None = None  # Add this line

        # root signs
        self.root_sign_key: str = ""
        self.root_signs: list[str] = []
        self.root_signs_index: int = 0

        # root bases
        self.root_bases_key: str = ""
        self.root_bases: list[str] = []
        self.root_base_index: int = 0

        # family_root
        self.family_root_key: str = ""
        self.family_roots: list[str] = []
        self.family_root_index: int = 0

    def new_db_session(self):
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)

    # --- INITIALIZE DB ---

    def pre_initialize_gui_data(self):
        """Fetches only the data needed for immediate GUI component initialization."""
        self.get_all_compound_types()
        self.get_all_family_sets()
        self.get_all_plus_cases()

    def initialize_db(self):
        self.get_all_lemma_1_and_lemma_clean()
        self.get_all_pos()
        self.get_all_roots()
        self.get_all_root_families()
        self.get_all_compound_families()
        self.get_all_word_families()
        # self.get_all_compound_types() # Moved to pre_initialize_gui_data

    def get_all_roots(self) -> None:
        roots = self.db_session.query(DpdRoot.root).all()
        self.all_roots = set([root[0] for root in roots])

    def get_all_lemma_1_and_lemma_clean(self):
        lemmas = self.db_session.query(DpdHeadword.lemma_1).all()
        self.all_lemma_1 = set([lemma[0] for lemma in lemmas])
        self.all_lemma_clean = set([clean_lemma_1(lemma) for lemma in self.all_lemma_1])

    def get_all_pos(self):
        first_word = self.db_session.query(DpdHeadword).first()
        if first_word:
            self.all_pos = set(first_word.pos_list)

    def get_all_root_families(self):
        root_families = self.db_session.query(FamilyRoot.root_family).all()
        self.all_root_families = set([root_family[0] for root_family in root_families])
        self.all_root_families.update("")

    def get_all_compound_families(self):
        compound_families = self.db_session.query(FamilyCompound.compound_family).all()
        self.all_compound_families = set(
            [comp_family[0] for comp_family in compound_families]
        )
        self.all_compound_families.update("")

    def get_all_word_families(self):
        word_families = self.db_session.query(FamilyWord.word_family).all()
        self.all_word_families = set([w[0] for w in word_families])

    def get_all_compound_types(self) -> None:
        """Gets all unique, non-empty compound types from the database, sorted."""
        types = (
            self.db_session.query(DpdHeadword.compound_type)
            .filter(DpdHeadword.compound_type != "")
            .distinct()
            .all()
        )
        # Extract strings, filter out None/empty if any slipped through, sort
        self.all_compound_types = sorted([t[0] for t in types if t[0]])
        # Optionally add an empty string if you want it as a selectable option
        # self.all_compound_types.insert(0, "")

    def get_all_plus_cases(self) -> None:
        """Gets all unique, non-empty plus_case values from the database, sorted."""
        cases = (
            self.db_session.query(DpdHeadword.plus_case)
            .filter(DpdHeadword.plus_case != "")
            .distinct()
            .all()
        )
        self.all_plus_cases = sorted([c[0] for c in cases if c[0]])

    def get_all_family_sets(self) -> None:
        """Gets all unique family set components from the database, sorted."""

        all_sets_raw = (
            self.db_session.query(DpdHeadword.family_set)
            .filter(DpdHeadword.family_set != "")
            .all()
        )

        unique_components = set()
        for row in all_sets_raw:
            family_set_string = row[0]
            if family_set_string:
                components = family_set_string.split(";")
                for component in components:
                    cleaned_component = component.strip()
                    if cleaned_component:
                        unique_components.add(cleaned_component)

        self.all_family_sets = sorted(list(unique_components))
        self.all_family_sets.insert(0, "")

    # --- PASS1 AUTO ---

    def make_inflections_lists(self) -> None:
        """Load data from the database."""

        self.db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()

        self.all_inflections: set[str] = set()  # reset
        [self.all_inflections.update(i.inflections_list_all) for i in self.db]

        self.all_inflections_missing_meaning: set[str] = set()  # reset
        [
            self.all_inflections_missing_meaning.update(i.inflections_list_all)
            for i in self.db
            if not i.meaning_1
        ]

    def get_related_dict_entries(self, word_in_text) -> list[str]:
        """Get all the possible lemma, pos meaning for a word."""

        related_entries_list: list[str] = []
        lookup_results: list[Lookup] = (
            self.db_session.query(Lookup)
            .filter(Lookup.lookup_key == word_in_text)
            .all()
        )
        for i in lookup_results:
            for deconstruction in i.deconstructor_unpack[:2]:  # limit results
                for word in deconstruction.split(" + "):
                    single_result = (
                        self.db_session.query(Lookup)
                        .filter(Lookup.lookup_key == word)
                        .first()
                    )
                    if single_result:
                        ids = single_result.headwords_unpack
                        for id in ids:
                            headword: DpdHeadword | None = (
                                self.db_session.query(DpdHeadword)
                                .filter(DpdHeadword.id == id)
                                .first()
                            )
                            if headword:
                                related_entry = f"lemma_1: {headword.lemma_1}, pos: {headword.pos}, grammar: {headword.grammar}, meaning_1: {headword.meaning_combo}, root_key: {headword.root_key}, root_sign: {headword.root_sign}, root_base: {headword.root_base}, family_root: {headword.family_root}, family_compound: {headword.family_compound}, construction: {headword.construction}, stem: {headword.stem}, pattern: {headword.pattern}"
                                if related_entry not in related_entries_list:
                                    related_entries_list.append(related_entry)

        return related_entries_list

    # --- PASS2 PREPROCESSOR ---

    def make_pass2_lists(self) -> None:
        """Data that pass2 preprocessor needs."""

        self.db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()

        self.all_inflections_missing_example: set[str] = set()  # reset
        [
            self.all_inflections_missing_example.update(i.inflections_list_all)
            for i in self.db
            if ((i.meaning_1 and not i.source_1) or (not i.meaning_1))
        ]

        self.all_suffixes: set[str] = set()  # reset
        [self.all_suffixes.add(i.suffix) for i in self.db if i.suffix != ""]

    def get_headwords(self, word_in_text: str) -> list[DpdHeadword]:
        """Find headwords which match the inflection."""

        result: Lookup | None = (
            self.db_session.query(Lookup)
            .filter(Lookup.lookup_key == word_in_text)
            .first()
        )

        if not result:
            return []

        else:
            ids = result.headwords_unpack
            results_list = []
            for id in ids:
                headword = (
                    self.db_session.query(DpdHeadword)
                    .filter(DpdHeadword.id == id)
                    .filter(DpdHeadword.source_1 == "")
                    .first()
                )
                if headword:
                    results_list.append(headword)

            return results_list

    def get_related_headwords(self, i: DpdHeadword) -> list[DpdHeadword]:
        """Find headwords related by root family, compound family or word family."""

        related_headwords: list[DpdHeadword] = []

        # is a root
        if i.root_key:
            related_headwords.extend(
                self.db_session.query(DpdHeadword)
                .filter(DpdHeadword.root_key == i.root_key)
                .filter(DpdHeadword.family_root == i.family_root)
                .filter(DpdHeadword.meaning_1 != "")
                .order_by(desc(DpdHeadword.example_1 != ""))
                .limit(20)
                .all()
            )

            if not related_headwords:
                # extend all words with the root_key
                if i.root_key:
                    related_headwords.extend(
                        self.db_session.query(DpdHeadword)
                        .filter(DpdHeadword.root_key == i.root_key)
                        .filter(DpdHeadword.meaning_1 != "")
                        .order_by(desc(DpdHeadword.example_1 != ""))
                        .limit(20)
                        .all()
                    )

        # is a compound
        elif re.findall(r"\bcomp\b", i.grammar):
            words_in_construction = i.construction_line1_clean.split(" + ")
            words_in_construction = [  # removes the suffixes if any
                word for word in words_in_construction if word not in self.all_suffixes
            ]
            if words_in_construction:
                words_in_construction_rx = rf"\b({'|'.join(words_in_construction)})\b"
            else:
                return []

            related_headwords.extend(
                self.db_session.query(DpdHeadword)
                .filter(DpdHeadword.grammar.regexp_match("comp"))
                .filter(
                    (DpdHeadword.construction.regexp_match(words_in_construction_rx))
                )
                .filter(DpdHeadword.meaning_1 != "")
                .order_by(desc(DpdHeadword.example_1 != ""))
                .limit(20)
                .all()
            )

            if not related_headwords:
                pass

        # is a family word
        elif i.family_word:
            related_headwords.extend(
                self.db_session.query(DpdHeadword)
                .filter(DpdHeadword.family_word == i.family_word)
                .filter(DpdHeadword.meaning_1 != "")
                .order_by(desc(DpdHeadword.example_1 != ""))
                .limit(20)
                .all()
            )

            if not related_headwords:
                pass

        return related_headwords

    # --- GENERIC DB SEARCHES ---

    def get_headword_by_id(self, id: int) -> DpdHeadword | None:
        return self.db_session.query(DpdHeadword).filter_by(id=id).first()

    def get_headword_by_lemma(self, lemma_1: str) -> DpdHeadword | None:
        return self.db_session.query(DpdHeadword).filter_by(lemma_1=lemma_1).first()

    def get_headword_by_id_or_lemma(self, user_input: str) -> DpdHeadword | None:
        """Decide where the input is an id or a lemma and query accordingly."""

        # Refresh the session to get the latest data
        self.new_db_session()

        first_character = user_input[0]

        if first_character.isalpha():
            return self.get_headword_by_lemma(user_input)
        elif first_character.isdigit():
            return self.get_headword_by_id(int(user_input))

    # --- DB FUNCTIONS ---

    def add_word_to_db(self, new_word):
        try:
            self.db_session.add(new_word)
            self.db_session.commit()
            return (True, "")

        except Exception as e:
            self.db_session.rollback()
            print(e)
            return (False, e)

    def update_word_in_db(self, word: DpdHeadword) -> tuple[bool, str]:
        try:
            existing = self.db_session.query(DpdHeadword).filter_by(id=word.id).first()
            if existing:
                # Update all fields from the edited word
                for key, value in word.__dict__.items():
                    if not key.startswith("_") and key != "id":
                        setattr(existing, key, value)
                self.db_session.commit()
                return (True, "")
            return (False, "Word not found")
        except Exception as e:
            print(e)
            return (False, str(e))

    def delete_word_in_db(self, headword: DpdHeadword) -> tuple[bool, str]:
        try:
            id = headword.id
            self.db_session.query(DpdHeadword).filter_by(id=id).delete()
            self.db_session.commit()
            return (True, "")
        except Exception as e:
            print(e)
            self.db_session.rollback()
            return (False, str(e))

    def get_next_id(self) -> int:
        last_id: int = self.db_session.query(func.max(DpdHeadword.id)).scalar() or 0
        return last_id + 1

    # --- DPD FIELDS FUNCTIONS ---

    def get_root_string(self, root_key: str) -> str:
        root = self.db_session.query(DpdRoot).filter(DpdRoot.root == root_key).first()
        if root:
            return (
                f"{root.root} {root.root_group} {root.root_sign} ({root.root_meaning})"
            )
        else:
            return "something is wrong"

    def get_root_signs(self):
        results = (
            self.db_session.query(DpdHeadword.root_sign)
            .filter(DpdHeadword.root_key == self.root_sign_key)
            .group_by(DpdHeadword.root_sign)
            .all()
        )
        self.root_signs = sorted([v[0] for v in results if v[0] != ""])

    def get_next_root_sign(self, root_key):
        if root_key != self.root_sign_key:
            self.root_sign_key = root_key
            self.root_sign_index = 0
            self.get_root_signs()
            return self.root_signs[self.root_sign_index]
        else:
            # increment by 1 and return to 0 at end of list
            self.root_sign_index = (self.root_sign_index + 1) % len(self.root_signs)
            return self.root_signs[self.root_sign_index]

    def get_root_bases(self):
        results = (
            self.db_session.query(DpdHeadword.root_base)
            .filter(DpdHeadword.root_key == self.root_bases_key)
            .group_by(DpdHeadword.root_base)
            .all()
        )
        self.root_bases = sorted([v[0] for v in results if v[0] != ""])

    def get_next_root_base(self, root_key) -> str:
        if root_key != self.root_bases_key:
            self.root_bases_key = root_key
            self.root_base_index = 0
            self.get_root_bases()
            if self.root_bases:
                return self.root_bases[self.root_base_index]
            else:
                return ""
        else:
            if self.root_bases:
                # increment by 1 and return to 0 at end of list
                self.root_base_index = (self.root_base_index + 1) % len(self.root_bases)
                return self.root_bases[self.root_base_index]
            else:
                return ""

    def get_family_roots(self):
        results = (
            self.db_session.query(DpdHeadword.family_root)
            .filter(DpdHeadword.root_key == self.family_root_key)
            .group_by(DpdHeadword.family_root)
            .all()
        )
        self.family_roots = sorted([v[0] for v in results if v[0] != ""])

    def get_next_family_root(self, root_key) -> str:
        if root_key != self.family_root_key:
            self.family_root_key = root_key
            self.family_root_index = 0
            self.get_family_roots()
            if self.family_roots:
                return self.family_roots[self.family_root_index]
            else:
                return ""
        else:
            if self.family_roots:
                # increment by 1 and return to 0 at end of list
                self.family_root_index = (self.family_root_index + 1) % len(
                    self.family_roots
                )
                return self.family_roots[self.family_root_index]
            else:
                return ""

    # --- ---


# if __name__ == "__main__":
#     db = DatabaseManager()
#     print(db.get_headword_by_id_or_lemma("karoti 1"))
