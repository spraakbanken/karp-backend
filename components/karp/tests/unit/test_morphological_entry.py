import pytest
from paradigmextract import morphparser

from karp.lex.domain.entities.entry import Entry

# from karp.lex.domain.entities.morphological_entry import (MorphologicalEntry,
#                                                     create_morphological_entry)

pytestmark = pytest.mark.skip()


def test_morph_entry_has_entry_id():
    morph_entry = create_morphological_entry(
        "pn_test", pos="pn", form_msds=[], var_insts=[], resource_id="m"
    )

    assert isinstance(morph_entry, Entry)
    assert isinstance(morph_entry, MorphologicalEntry)
    assert morph_entry.entry_id == "pn_test"


def test_morph_entry_has_function_get_inflection_table():
    morph_entry = create_morphological_entry(
        "pn_test", pos="pn", form_msds=[], var_insts=[], resource_id="m"
    )

    assert getattr(morph_entry, "get_inflection_table")


def test_morph_entry_inflect_av_1_blå():
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
        resource_id="m",
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


def test_morph_entry_inflect_av_1_höger():
    morph_entry = create_morphological_entry(
        "av_1_höger", pos="av", form_msds=[], var_insts=[], resource_id="m"
    )

    inflection_table = morph_entry.get_inflection_table("höger")

    pass


def test_morph_entry_inflect_nn_0n_ansvar():
    morph_entry = create_morphological_entry(
        "nn_0n_ansvar",
        pos="nn",
        form_msds=[
            ("1", "sg indef nom"),
            ("1+s", "sg indef gen"),
            ("1+et", "sg def nom"),
            ("1+ets", "sg def gen"),
        ],
        var_insts=[[("1", "ansvar")]],
        resource_id="m",
    )

    inflection_table = morph_entry.get_inflection_table("apa")

    assert inflection_table == [
        ("sg indef nom", "apa"),
        ("sg indef gen", "apas"),
        ("sg def nom", "apaet"),
        ("sg def gen", "apaets"),
    ]


def test_morph_entry_inflect_nn_3u_son():
    morph_entry = create_morphological_entry(
        "nn_3u_son",
        pos="nn",
        form_msds=[
            ("1+o+2", "sg indef nom"),
            ("1+o+2+s", "sg indef gen"),
            ("1+o+2+en", "sg def nom"),
            ("1+o+2+ens", "sg def gen"),
            ("1+ö+2+er", "pl indef nom"),
            ("1+ö+2+ers", "pl indef gen"),
            ("1+ö+2+erna", "pl def nom"),
            ("1+ö+2+ernas", "pl def gen"),
        ],
        var_insts=[[("1", "s"), ("2", "n")]],
        resource_id="m",
    )

    inflection_table = morph_entry.get_inflection_table("styrelseledamot")

    assert inflection_table == [
        ("sg indef nom", "styrelseledamot"),
        ("sg indef gen", "styrelseledamots"),
        ("sg def nom", "styrelseledamoten"),
        ("sg def gen", "styrelseledamotens"),
        ("pl indef nom", "styrelseledamöter"),
        ("pl indef gen", "styrelseledamöters"),
        ("pl def nom", "styrelseledamöterna"),
        ("pl def gen", "styrelseledamöternas"),
    ]


@pytest.mark.xfail(reason="can't match")
def test_morph_entry_inflect_nn_2u_bövel():
    morph_entry = create_morphological_entry(
        "nn_2u_bövel",
        pos="nn",
        form_msds=[("1+e+2", "sg indef nom")],
        var_insts=[[("1", "böv"), ("2", "l")]],
        resource_id="m",
    )
    inflection_table = morph_entry.get_inflection_table("sommar")

    assert inflection_table == [("sg indef nom", "sommar")]


def test_morph_entry_inflect_nn_0n_syre():
    morph_entry = create_morphological_entry(
        "nn_0n_syre",
        pos="nn",
        form_msds=[
            ("1", "sg indef nom"),
            ("1+s", "sg indef gen"),
            ("1+t", "sg def nom"),
            ("1+ts", "sg def gen"),
        ],
        var_insts=[[("1", "syre")]],
        resource_id="m",
    )

    inflection_table = morph_entry.get_inflection_table("vete")

    assert inflection_table == [
        ("sg indef nom", "vete"),
        ("sg indef gen", "vetes"),
        ("sg def nom", "vetet"),
        ("sg def gen", "vetets"),
    ]


@pytest.mark.skip(reason="How shall it be used.")
def test_morph_entry_inflect_ab():
    morph_entry = create_morphological_entry(
        "ab_1_illa", pos="ab", form_msds=[("")], var_insts=[], resource_id="m"
    )

    inflection_table = morph_entry.get_inflection_table("")


def test_morph_entry_inflect_vb_2a_känna():
    morph_entry = create_morphological_entry(
        "vb_2a_känna",
        pos="vb",
        form_msds=[
            ("1+ner", "pres ind aktiv"),
            ("1+nes", "pres ind s-form"),
            ("1+ns", "pres ind s-form"),
            ("1+de", "pret ind aktiv"),
            ("1+des", "pret ind s-form"),
            ("1+n", "imper"),
            ("1+na", "inf aktiv"),
            ("1+nas", "inf s-form"),
            ("1+t", "sup aktiv"),
            ("1+ts", "sup s-form"),
        ],
        var_insts=[[("1", "kän")]],
        resource_id="m",
    )

    inflection_table = morph_entry.get_inflection_table("bränna")

    assert inflection_table == [
        ("pres ind aktiv", "bränner"),
        ("pres ind s-form", "brännes"),
        ("pres ind s-form", "bränns"),
        ("pret ind aktiv", "brände"),
        ("pret ind s-form", "brändes"),
        ("imper", "bränn"),
        ("inf aktiv", "bränna"),
        ("inf s-form", "brännas"),
        ("sup aktiv", "bränt"),
        ("sup s-form", "bränts"),
    ]


def test_morph_entry_inflect_vb_1a_laga():
    morph_entry = create_morphological_entry(
        "vb_1a_laga",
        pos="vb",
        form_msds=[
            ("1+r", "pres ind aktiv"),
            ("1+s", "pres ind s-form"),
            ("1+de", "pret ind aktiv"),
            ("1+des", "pret ind s-form"),
            ("1", "imper"),
            ("1", "inf aktiv"),
            ("1+s", "inf s-form"),
            ("1+t", "sup aktiv"),
            ("1+ts", "sup s-form"),
        ],
        var_insts=[[("1", "laga")]],
        resource_id="m",
    )

    inflection_table = morph_entry.get_inflection_table("jobba")

    assert inflection_table == [
        ("pres ind aktiv", "jobbar"),
        ("pres ind s-form", "jobbas"),
        ("pret ind aktiv", "jobbade"),
        ("pret ind s-form", "jobbades"),
        ("imper", "jobba"),
        ("inf aktiv", "jobba"),
        ("inf s-form", "jobbas"),
        ("sup aktiv", "jobbat"),
        ("sup s-form", "jobbats"),
    ]


def test_morph_entry_vb_1s_andas():
    morph_entry = create_morphological_entry(
        "vb_1s_andas",
        pos="vb",
        form_msds=[
            ("1+2", "pres ind s-form"),
            ("1+de+2", "pret ind s-form"),
            ("1+2", "imper"),
            ("1+2", "inf s-form"),
            ("1+t+2", "sup s-form"),
        ],
        var_insts=[[("1", "anda"), ("2", "s")]],
        resource_id="m"
        # var_insts=[[("1", "anda"), ("2", "s")]],
    )

    assert morph_entry.tags == ("inf aktiv", "inf s-form")

    inflection_table = morph_entry.get_inflection_table("fightas")

    variables = morphparser.eval_baseform(
        morph_entry.paradigm, "fightas", morph_entry.tags
    )

    assert variables == ["fighta", "s"]
    assert inflection_table == [
        ("pres ind s-form", "fightas"),
        ("pret ind s-form", "fightades"),
        ("imper", "fightas"),
        ("inf s-form", "fightas"),
        ("sup s-form", "fightats"),
    ]
