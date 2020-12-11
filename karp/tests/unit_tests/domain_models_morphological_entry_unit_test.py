from karp.domain.models.morphological_entry import (
    MorphologicalEntry,
    create_morphological_entry,
)

from karp.domain.models.entry import Entry


def test_morph_entry_has_entry_id():
    morph_entry = create_morphological_entry(
        "pn_test", pos="pn", form_msds=[], var_insts=[]
    )

    assert isinstance(morph_entry, Entry)
    assert isinstance(morph_entry, MorphologicalEntry)
    assert morph_entry.entry_id == "pn_test"


def test_morph_entry_has_function_get_inflection_table():
    morph_entry = create_morphological_entry(
        "pn_test", pos="pn", form_msds=[], var_insts=[]
    )

    assert getattr(morph_entry, "get_inflection_table")


def test_morph_entry_inflect_av():
    morph_entry = create_morphological_entry(
        "av_1_blå",
        pos="av",
        form_msds=[
            ("1", "pos indef sg u nom"),
            ("1+s", "pos indef sg u gen"),
            ("1+tt", "pos indef sg n nom"),
            ("1+tts", "pos indef sg n gen"),
            ("1+a", "pos indef pl nom"),
            ("1", "pos indef pl nom"),
            ("1+as", "pos indef pl gen"),
            ("1+s", "pos indef pl gen"),
            ("1+a", "pos def sg no_masc nom"),
            ("1", "pos def sg no_masc nom"),
            ("1+as", "pos def sg no_masc gen"),
            ("1+s", "pos def sg no_masc gen"),
            ("1+e", "pos def sg masc nom"),
            ("1+es", "pos def sg masc gen"),
            ("1+a", "pos def pl nom"),
            ("1", "pos def pl nom"),
            ("1+as", "pos def pl gen"),
            ("1+s", "pos def pl gen"),
            ("1+are", "komp nom"),
            ("1+ares", "komp gen"),
            ("1+ast", "super indef nom"),
            ("1+asts", "super indef gen"),
            ("1+aste", "super def no_masc nom"),
            ("1+astes", "super def no_masc gen"),
            ("1+aste", "super def masc nom"),
            ("1+astes", "super def masc gen"),
        ],
        var_insts=[[("1", "blå")]],
    )

    inflection_table = morph_entry.get_inflection_table("grå")

    assert inflection_table == [
        ("pos indef sg u nom", "grå"),
        ("pos indef sg u gen", "grås"),
        ("pos indef sg n nom", "grått"),
        ("pos indef sg n gen", "gråtts"),
        ("pos indef pl nom", "gråa"),
        ("pos indef pl nom", "grå"),
        ("pos indef pl gen", "gråas"),
        ("pos indef pl gen", "grås"),
        ("pos def sg no_masc nom", "gråa"),
        ("pos def sg no_masc nom", "grå"),
        ("pos def sg no_masc gen", "gråas"),
        ("pos def sg no_masc gen", "grås"),
        ("pos def sg masc nom", "gråe"),
        ("pos def sg masc gen", "gråes"),
        ("pos def pl nom", "gråa"),
        ("pos def pl nom", "grå"),
        ("pos def pl gen", "gråas"),
        ("pos def pl gen", "grås"),
        ("komp nom", "gråare"),
        ("komp gen", "gråares"),
        ("super indef nom", "gråast"),
        ("super indef gen", "gråasts"),
        ("super def no_masc nom", "gråaste"),
        ("super def no_masc gen", "gråastes"),
        ("super def masc nom", "gråaste"),
        ("super def masc gen", "gråastes"),
    ]
