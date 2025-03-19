from db.db_helpers import get_db_session
from db.models import Lookup
from tools.lookup_is_another_value import is_another_value
from tools.paths import ProjectPaths
from tools.printer import p_green, p_red, p_yes


class AddVariantsToDb:
    def __init__(self, variants_dict):
        p_green("initializing db")

        self.variants_dict = variants_dict
        self.variant_dict_keys = list(self.variants_dict.keys())

        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)

        self.lookup_table = (
            self.db_session.query(Lookup)
            .filter(Lookup.lookup_key.in_(self.variant_dict_keys))
            .all()
        )
        self.lookup_keys: list[str] = [i.lookup_key for i in self.lookup_table]

        p_yes("")

        self.delete_variants_in_db()
        self.update_variants_in_db()
        self.add_variants_to_db()
        self.db_session.close()

    def delete_variants_in_db(self):
        """Remove old variants from the lookup table."""

        p_green("removing old variants")

        db_results = self.db_session.query(Lookup).filter(Lookup.variant != "").all()

        for i in db_results:
            if is_another_value(i, "variant"):
                i.variant = ""
            else:
                self.db_session.delete(i)
        self.db_session.commit()

        p_yes("")

    def update_variants_in_db(self):
        """Update existing variants in the lookup table."""
        p_green("updating db")

        # Get keys that need updating
        update_keys = [k for k in self.variants_dict.keys() if k in self.lookup_keys]

        # Process in chunks
        chunk_size = 1000
        update_count = 0

        for i in range(0, len(update_keys), chunk_size):
            chunk_keys = update_keys[i : i + chunk_size]

            # Get and update records
            records = (
                self.db_session.query(Lookup)
                .filter(Lookup.lookup_key.in_(chunk_keys))
                .all()
            )

            for record in records:
                try:
                    record.variants_pack(self.variants_dict[record.lookup_key])
                    update_count += 1
                except Exception as e:
                    self.db_session.rollback()
                    p_red(f"Error updating {record.lookup_key}: {str(e)}")
                    continue

            try:
                self.db_session.commit()
            except Exception as e:
                self.db_session.rollback()
                p_red(f"Error committing chunk: {str(e)}")

        p_yes(update_count)

    def add_variants_to_db(self):
        """Add new variants to the table."""
        p_green("adding to db")

        add_to_db = []
        for count, (variant, data) in enumerate(self.variants_dict.items()):
            if variant not in self.lookup_keys:
                add_me = Lookup()
                add_me.lookup_key = variant
                add_me.variants_pack(data)
                add_to_db.append(add_me)
        p_yes(len(add_to_db))

        p_green("committing db")
        self.db_session.add_all(add_to_db)
        self.db_session.add_all(add_to_db)
        self.db_session.commit()
        p_yes("")
