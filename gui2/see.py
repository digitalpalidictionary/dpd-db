from tools.see_manager import SeeManager


class SeeFileManager(SeeManager):
    """GUI wrapper for SeeManager.

    Extends SeeManager with GUI-compatible interface, following the
    VariantReadingFileManager / SpellingMistakesFileManager pattern.
    """

    def get_see_entries(self) -> dict[str, str]:
        """Return a copy of the see dictionary."""
        return self.get_see_dict()
