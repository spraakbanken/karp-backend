from typing import List, Tuple
from unittest import mock

import pytest

from karp.infrastructure.elasticsearch6.es6_search_service import (
    Es6SearchService, UnsupportedField, _create_es_mapping)


@pytest.fixture
def es_mock():
    _es_mock = mock.Mock()
    _es_mock.cat.aliases.return_value = "nordicon nordicon_2020-03-11-091836868542\nplaces places_2020-03-09-142246186985\n"
    _es_mock.indices.get_mapping.return_value = {
        "places_2020-03-09-142246186985": {
            "mappings": {
                "entry": {
                    "dynamic": "false",
                    "properties": {
                        "_entry_version": {"type": "object", "enabled": False},
                        "_last_modified": {"type": "object", "enabled": False},
                        "_last_modified_by": {"type": "object", "enabled": False},
                        "area": {"type": "long"},
                        "code": {"type": "long"},
                        "density": {"type": "long"},
                        "freetext": {"type": "text"},
                        "larger_place": {"type": "long"},
                        "municipality": {"type": "long"},
                        "name": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "population": {"type": "long"},
                        "v_larger_place": {
                            "properties": {
                                "code": {"type": "long"},
                                "name": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                            }
                        },
                        "v_municipality": {
                            "properties": {
                                "code": {"type": "long"},
                                "name": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "state": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                            }
                        },
                        "v_smaller_places": {
                            "properties": {
                                "code": {"type": "long"},
                                "name": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                            }
                        },
                    },
                }
            }
        },
        "nordicon_2020-03-11-091836868542": {
            "mappings": {
                "entry": {
                    "dynamic": "false",
                    "properties": {
                        "_entry_version": {"type": "object", "enabled": False},
                        "_last_modified": {"type": "object", "enabled": False},
                        "_last_modified_by": {"type": "object", "enabled": False},
                        "alternatives_lemma": {
                            "properties": {
                                "DGP": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "SMP": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "etymologisches_lemma": {
                                    "properties": {
                                        "etymologie_namengeschichte": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "etymologisches_lemma": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "geschlecht": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "id_etylemma": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "kommentar_etylemma": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "lemma_MGH": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "lemma_foerstemann": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "link_NeG": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "sprache": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                    }
                                },
                                "id_sublemma": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "kommentar_sprache": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "lind": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "sprache": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "sublemma": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                            }
                        },
                        "belegstelle_handschrift": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "besonderheiten_der_schreibung": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "erhaltungszustand": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "freetext": {"type": "text"},
                        "id_nameneintrag": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "kommentar_alternatives_lemma": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "kommentar_erhaltungszustand": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "kommentar_schreibtechnik": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "kommentar_schreibung": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "kommentar_tinte": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "lemma": {
                            "properties": {
                                "DGP": {
                                    "type": "text",
                                },
                                "SMP": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "etymologisches_lemma": {
                                    "properties": {
                                        "etymologie_namengeschichte": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "etymologisches_lemma": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "geschlecht": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "id_etylemma": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "kommentar_etylemma": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "lemma_MGH": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "lemma_foerstemann": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "link_NeG": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "sprache": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                    }
                                },
                                "id_sublemma": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "kommentar_sprache": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "lind": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "sprache": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "sublemma": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                            }
                        },
                        "lesung": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "linguistischer_kommentar": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "link_auf_digitalisat": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "link_id_kontext": {
                            "properties": {
                                "belegstelle": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "datierung": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "hand": {
                                    "properties": {
                                        "besonderheiten": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "hand": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "id_hand": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "kommentar_hand": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                        "schreiberidentifikation": {
                                            "type": "text",
                                            "fields": {"raw": {"type": "keyword"}},
                                        },
                                    }
                                },
                                "id_kontext": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "kommentar_datierung": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "kommentar_layout": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "layout": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "liste": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "schriftheimat": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "schrifttyp": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "seitenplanung": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "trennzeichen": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "uberschrift": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                            }
                        },
                        "listenplatz": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "originalgraphie": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "person": {
                            "properties": {
                                "alternative_bezeichnungen": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "geschlecht": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "id_person": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "standardname": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "weitere_angaben": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                                "zeitraum": {
                                    "type": "text",
                                    "fields": {"raw": {"type": "keyword"}},
                                },
                            }
                        },
                        "saldo": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "schreibtechnik": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "sicher_unsicher": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "standesbezeichnung": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "tinte": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                    },
                }
            }
        },
    }
    return _es_mock


def test_create_empty(es_mock):
    es_search = Es6SearchService(es_mock)

    assert "nordicon" in es_search.analyzed_fields
    assert "places" in es_search.analyzed_fields
    assert "nordicon" in es_search.sortable_fields
    assert "places" in es_search.sortable_fields
    assert "lemma.DGP" not in es_search.sortable_fields["nordicon"]
    assert "lemma.SMP" in es_search.sortable_fields["nordicon"]


def test_translate_sort_fields(es_mock):
    es_search = Es6SearchService(es_mock)

    result = es_search.translate_sort_fields(["places"], ["name"])

    expected = ["name.raw"]

    assert result == expected


def test_translate_sort_fields_raises(es_mock):
    es_search = Es6SearchService(es_mock)

    with pytest.raises(UnsupportedField):
        es_search.translate_sort_fields(["places"], ["v_larger_place"])


@pytest.mark.parametrize(
    "properties,expected_mappings,expected_non_mappings",
    [
        ({}, [], []),
        ({"a": {"type": "text"}}, [], ["a"]),
        ({"a": {"type": "long"}}, [("a", ["a"])], []),
        ({"a": {"type": "date"}}, [("a", ["a"])], []),
        ({"a": {"type": "keyword"}}, [("a", ["a"])], []),
        ({"a": {"type": "double"}}, [("a", ["a"])], []),
        ({"a": {"type": "boolean"}}, [("a", ["a"])], []),
        ({"a": {"type": "ip"}}, [("a", ["a"])], []),
        (
            {"a": {"type": "text", "fields": {"raw": {"type": "keyword"}}}},
            [("a", ["a.raw"]), ("a.raw", ["a.raw"])],
            [],
        ),
        (
            {
                "a": {
                    "properties": {
                        "code": {"type": "long"},
                        "name": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                    }
                }
            },
            [
                ("a.code", ["a.code"]),
                ("a.name", ["a.name.raw"]),
                ("a.name.raw", ["a.name.raw"]),
            ],
            ["a"],
        ),
        (
            {
                "a": {
                    "properties": {
                        "code": {"type": "long"},
                        "name": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                    }
                },
                "b": {
                    "properties": {
                        "code": {"type": "long"},
                        "name": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "description": {"type": "text"},
                    }
                },
            },
            [
                ("a.code", ["a.code"]),
                ("a.name", ["a.name.raw"]),
                ("a.name.raw", ["a.name.raw"]),
                ("b.code", ["b.code"]),
                ("b.name", ["b.name.raw"]),
                ("b.name.raw", ["b.name.raw"]),
            ],
            ["a", "b", "b.description"],
        ),
        # ({"a": {"type": "text", "fields": {"raw": {"type": "keyword"}}}}, ["a"], []),
    ],
)
def test_parse_mapping_empty(
    properties,
    expected_mappings: List[Tuple[str, List[str]]],
    expected_non_mappings: List[str],
):
    sortable_map = Es6SearchService.create_sortable_map_from_mapping(properties)

    for field, mapped_field in expected_mappings:
        assert field in sortable_map
        assert sortable_map[field] == mapped_field

    for non_field in expected_non_mappings:
        assert non_field not in sortable_map


def test_create_es_mapping_empty():
    config = {"fields": {}}
    mapping = _create_es_mapping(config)

    assert mapping == {"dynamic": False, "properties": {}}


def test_create_es_mapping_string():
    config = {"fields": {"test": {"type": "string"}}}
    mapping = _create_es_mapping(config)

    assert mapping == {
        "dynamic": False,
        "properties": {
            "test": {"fields": {"raw": {"type": "keyword"}}, "type": "text"}
        },
    }


def test_create_es_mapping_string_skip_raw():
    config = {"fields": {"test": {"type": "string", "skip_raw": True}}}
    mapping = _create_es_mapping(config)

    assert mapping == {
        "dynamic": False,
        "properties": {"test": {"type": "text"}},
    }


