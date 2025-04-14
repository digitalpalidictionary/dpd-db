from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.paths import ProjectPaths


class DatabaseManager:
    def __init__(self) -> None:
        self.pth: ProjectPaths = ProjectPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.db: list[DpdHeadword]
        self.all_inflections: set[str] = set()
        self.all_inflections_missing_meaning: set[str] = set()
        self.sandhi_ok_list: list[str] = self.pth.decon_checked.read_text().splitlines()

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
            return True

        except Exception:
            return False
