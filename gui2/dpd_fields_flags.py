from dataclasses import dataclass, field, fields


@dataclass
class Flags:
    """Holds boolean flags for GUI field automation logic."""

    construction_done: bool = field(default=False)
    stem_pattern_done: bool = field(default=False)
    derived_from_done: bool = field(default=False)
    family_compound_done: bool = field(default=False)
    loaded_from_db: bool = field(default=False)
    sanskrit_done: bool = field(default=False)
    synonyms_done: bool = field(default=False)
    family_word_done: bool = field(default=False)
    correction: bool = field(default=False)
    addition: bool = field(default=False)

    def reset(self):
        """Reset all flags to their default values."""

        for f in fields(self):
            setattr(self, f.name, f.default)
