# -*- coding: utf-8 -*-
"""Tests for the compact word set used for a contributor's inflection lists."""

import random

from tools.hashed_words import HashedWords


def test_members_are_found_and_others_are_not():
    words = HashedWords(["kata", "katā", "dhammaṃ", "gata"])
    assert "kata" in words
    assert "dhammaṃ" in words
    assert "kataa" not in words
    assert "" not in words


def test_empty_string_is_a_member_when_given():
    # today's inflection set keeps "" (inflections_list_all yields it)
    assert "" in HashedWords(["kata", ""])


def test_duplicates_count_once():
    assert len(HashedWords(["kata", "kata", "gata"])) == 2


def test_empty_input():
    words = HashedWords([])
    assert len(words) == 0
    assert "kata" not in words


def test_non_string_is_never_a_member():
    words = HashedWords(["1"])
    assert 1 not in words
    assert None not in words


def test_answers_like_a_set_on_a_large_random_sample():
    rng = random.Random(0)
    alphabet = "abcdefghiklmnoprstuvyāīūṃṭḍṇḷñṅ"

    def word() -> str:
        return "".join(rng.choice(alphabet) for _ in range(rng.randint(2, 12)))

    members = {word() for _ in range(50_000)}
    others = {word() for _ in range(50_000)} - members
    compact = HashedWords(members)
    assert all(w in compact for w in members)
    assert not any(w in compact for w in others)
