# -*- coding: utf-8 -*-
"""Tests for the VariantManager class."""

import pytest

from tools.variants_manager import VariantManager


def test_variant_manager_loads_variants():
    """Test that variant_readings.tsv is loaded correctly."""
    vm = VariantManager()
    variants = vm.get_all()
    assert "celaṇḍupekena" in variants
    assert variants["pāṇamatimāpayato"] == "pāṇamatipātayato"


def test_variant_manager_get_variants_returns_copy():
    """Test that get_variants returns a copy, not the original dict."""
    vm = VariantManager()
    variants1 = vm.get_variants()
    variants2 = vm.get_variants()
    assert variants1 is not variants2
    assert variants1 == variants2


def test_variant_manager_get_all():
    """Test that get_all returns the full variants dictionary."""
    vm = VariantManager()
    all_variants = vm.get_all()
    assert isinstance(all_variants, dict)
    assert len(all_variants) > 0


def test_variant_manager_reverse_lookup():
    """Test reverse lookup by main form."""
    vm = VariantManager()
    main_form = "celapaṭikaṃ"
    all_variants = vm.get_all()
    for variant, main in all_variants.items():
        if main == main_form:
            assert variant == "celapattikaṃ"
            break
    else:
        pytest.fail(f"Main form '{main_form}' not found in variants")


def test_variant_manager_get_main():
    """Test forward lookup: find main by variant."""
    vm = VariantManager()
    main = vm.get_main("pāṇamatimāpayato")
    assert main == "pāṇamatipātayato"


def test_variant_manager_get_main_not_found():
    """Test forward lookup returns None for unknown variant."""
    vm = VariantManager()
    main = vm.get_main("nonexistent_variant_xyz")
    assert main is None


def test_variant_manager_get_variant():
    """Test reverse lookup: find variant by main form."""
    vm = VariantManager()
    variants = vm.get_variant("celapaṭikaṃ")
    assert "celapattikaṃ" in variants


def test_variant_manager_get_variant_not_found():
    """Test reverse lookup returns empty list for unknown main form."""
    vm = VariantManager()
    variants = vm.get_variant("nonexistent_main_xyz")
    assert variants == []


def test_manual_variant_lookup_in_webapp():
    """Test manual variant is found when DB variant is missing."""
    from exporter.webapp.toolkit import get_variant_manager

    vm = get_variant_manager()
    main = vm.get_main("pāṇamatimāpayato")
    assert main == "pāṇamatipātayato"


def test_manual_variant_lookup_not_found():
    """Test manual variant returns None for unknown term."""
    from exporter.webapp.toolkit import get_variant_manager

    vm = get_variant_manager()
    main = vm.get_main("nonexistent_word_xyz")
    assert main is None
