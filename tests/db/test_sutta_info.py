# ruff: noqa: E402

import sys
import types

sys.modules.setdefault(
    "aksharamukha",
    types.SimpleNamespace(
        transliterate=types.SimpleNamespace(process=lambda *args, **kwargs: "")
    ),
)

from db.models import SuttaInfo


def test_sutta_info_marks_sn_collection_as_samyutta() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "devatāsaṃyutta"
    su.dpd_code = "SN1"

    assert su.is_samyutta is True
    assert su.is_vagga is False


def test_sutta_info_marks_vagga_samyuttapali_as_vagga() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "sagāthāvaggasaṃyuttapāḷi"
    su.dpd_code = "SN1-11"
    su.sc_vagga = "1. Naḷavagga"

    assert su.is_samyutta is False
    assert su.is_vagga is True
