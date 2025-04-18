from sqlalchemy.orm.session import Session
from sqlalchemy import func

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, FamilyCompound, FamilyRoot, Lookup
from gui2.def_dpd_fields import clean_lemma_1
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
        )

        # need this for dropdown options
        self.all_roots: set[str] = self.get_all_roots()

        # only need thse later
        self.all_lemma_1: set[str] | None = None
        self.all_lemma_clean: set[str] | None = None
        self.all_pos: set[str] | None = None
        self.all_compound_families: set[str] | None = None
        self.all_root_families: set[str] | None = None

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

    def get_all_roots(self) -> set[str]:
        roots = self.db_session.query(DpdRoot.root).all()
        return set([root[0] for root in roots])

    # initialize db

    def initialize_db(self):
        self.get_all_lemma_1_and_lemma_clean()
        self.get_all_pos()
        self.get_all_root_families()
        self.get_all_compound_families()

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

    def get_all_compound_families(self):
        compound_families = self.db_session.query(FamilyCompound.compound_family).all()
        self.all_compound_families = set(
            [comp_family[0] for comp_family in compound_families]
        )

    # --------------------------

    def make_inflections_lists(self) -> None:
        """Load data from the database."""

        self.db: list[DpdHeadword] = self.db_session.query(DpdHeadword).all()
        self.all_inflections: set[str] = set()
        [self.all_inflections.update(i.inflections_list_all) for i in self.db]

        self.all_inflections_missing_meaning: set[str] = set()
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

    def add_word_to_db(self, new_word):
        try:
            self.db_session.add(new_word)
            self.db_session.commit()
            return (True, "")

        except Exception as e:
            print(e)
            return (False, e)

    def get_next_id(self) -> int:
        last_id: int = self.db_session.query(func.max(DpdHeadword.id)).scalar() or 0
        return last_id + 1

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
