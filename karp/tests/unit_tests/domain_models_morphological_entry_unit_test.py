from karp.domain.models.morphological_entry import MorphologicalEntry, create_morphological_entry

from karp.domain.models.entry import Entry


def test_morph_entry_has_entry_id():
    morph_entry = create_morphological_entry("pn_test")

    assert isinstance(morph_entry, Entry)
    assert isinstance(morph_entry, MorphologicalEntry)
    assert morph_entry.entry_id == "pn_test"
