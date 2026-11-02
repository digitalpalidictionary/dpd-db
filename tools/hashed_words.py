"""A large set of words kept as sorted 64-bit hashes, for membership tests only."""

from array import array
from bisect import bisect_left
from collections.abc import Iterable

_MASK = 0xFFFFFFFFFFFFFFFF


class HashedWords:
    """Holds 8 bytes per word where a Python set holds a string object per word
    (about 50 bytes plus the characters). A wrong "yes" needs a 64-bit hash
    collision. `hash(str)` is salted per process, so never save the hashes."""

    def __init__(self, words: Iterable[str] = ()) -> None:
        hashes = array("Q", (hash(word) & _MASK for word in words))
        unique = array("Q")
        last: int | None = None
        for value in sorted(hashes):
            if value != last:
                unique.append(value)
                last = value
        self._hashes = unique

    def __contains__(self, word: object) -> bool:
        if not isinstance(word, str):
            return False
        key = hash(word) & _MASK
        index = bisect_left(self._hashes, key)
        return index < len(self._hashes) and self._hashes[index] == key

    def __len__(self) -> int:
        return len(self._hashes)
