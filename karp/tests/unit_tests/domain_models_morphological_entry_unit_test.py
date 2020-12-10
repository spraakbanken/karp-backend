from karp.domain.models.morphological_entry import MorphologicalEntry, create_morphological_entry

from karp.domain.models.entry import Entry


def test_morph_entry_has_entry_id():
    morph_entry = create_morphological_entry("pn_test")

    assert isinstance(morph_entry, Entry)
    assert isinstance(morph_entry, MorphologicalEntry)
    assert morph_entry.entry_id == "pn_test"


def test_morph_entry_has_function_get_inflection_table():
    morph_entry = create_morphological_entry("pn_test")
    
    assert getattr(morph_entry, "get_inflection_table")


def test_morph_entry_inflect_av():
    morph_entry = create_morphological_entry("av_1_blå")

    inflection_table = morph_entry.get_inflection_table("grå")

    assert inflection_table == [("pos indef sg u nom", "grå")]