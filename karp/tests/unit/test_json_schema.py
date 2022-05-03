from karp.lex.domain.value_objects.entry_schema import EntrySchema
import pytest

from karp.utility.json_schema import create_entry_json_schema

CONFIG_PLACES = """{
  "resource_id": "places",
  "resource_name": "Platser i Sverige",
  "fields": {
    "name": {
      "type": "string",
      "required": True
    },
    "municipality": {
      "collection": True,
      "type": "number",
      "required": True
    },
    "population": {
      "type": "number"
    },
    "area": {
      "type": "number"
    },
    "density": {
      "type": "number"
    },
    "code": {
      "type": "number",
      "required": True
    }
  },
  "sort": "name",
  "id": "code"
}"""


@pytest.fixture()
def problem_config() -> dict:
    return {
        "resource_id": "konstruktikon",
        "resource_name": "Konstruktikon",
        "fields": {
            "cat": {"type": "string"},
            "illustration": {"type": "string"},
            "cee": {"type": "string", "collection": True},
            "coll": {"type": "string", "collection": True},
            "createdBy": {"type": "string"},
            "definition": {"type": "string"},
            "examples": {"type": "string", "collection": True},
            "entryStatus": {"type": "string"},
            "intConstElem": {
                "type": "object",
                "fields": {
                    "role": {"type": "string"},
                    "name": {"type": "string"},
                    "cat": {"type": "string"},
                    "lu": {"type": "string"},
                    "gfunc": {"type": "string"},
                    "msd": {"type": "string"},
                    "aux": {"type": "string"},
                },
                "collection": True,
            },
            "extConstElem": {
                "type": "object",
                "fields": {
                    "role": {"type": "string"},
                    "name": {"type": "string"},
                    "cat": {"type": "string"},
                    "lu": {"type": "string"},
                    "gfunc": {"type": "string"},
                    "msd": {"type": "string"},
                    "aux": {"type": "string"},
                },
                "collection": True,
            },
            "inheritance": {"type": "string", "collection": True},
            "type": {"type": "string", "collection": True},
            "structure": {"type": "string", "collection": True},
            "constructionID": {"type": "string", "required": True},
            "BCxnID": {"type": "string"},
            "evokes": {"type": "string", "collection": True},
            "comment": {"type": "string"},
            "reference": {"type": "string"},
            "internal_comment": {"type": "string"},
        },
        "sort": "constructionID",
        "protected": {"read": False},
        "id": "constructionID",
    }


def test_error(problem_config: dict):
    json_schema = create_entry_json_schema(problem_config["fields"])
    _entry_schema = EntrySchema(json_schema)


def test_create_json_schema(json_schema_config):
    json_schema = create_entry_json_schema(json_schema_config["fields"])
    assert json_schema["type"] == "object"


def test_create_complex_json_schema():
    config = {
        "fields": {
            "id": {"type": "string", "required": True},
            "s_nr": {"type": "integer"},
            "ortografi": {"type": "string", "required": True},
            "ordklass": {"type": "string", "required": True},
            "böjningsklass": {"type": "string", "required": True},
            "artikelkommentar": {"type": "string"},
            "ursprung": {"type": "string", "collection": True},
            "SOLemman": {
                "type": "object",
                "collection": True,
                "fields": {
                    "l_nr": {"type": "integer", "required": True},
                    "s_nr": {"type": "integer", "required": True},
                    "lm_sabob": {"type": "integer", "required": True},
                    "ortografi": {"type": "string", "required": True},
                    "lemmatyp": {"type": "string"},
                    "lemmaundertyp": {"type": "string"},
                    "stam": {"type": "string"},
                    "böjning": {"type": "string"},
                    "ordbildning": {"type": "string"},
                    "analys": {"type": "string"},
                    "sorteringsform": {"type": "string"},
                    "kommentar": {"type": "string"},
                    "tagg": {"type": "string"},
                    "ursprung": {"type": "string"},
                    "betydelser": {
                        "type": "object",
                        "collection": True,
                        "required": True,
                        "fields": {
                            "x_nr": {"type": "integer", "required": True},
                            "status": {"type": "string"},
                            "etymologier": {
                                "type": "object",
                                "collection": True,
                                "fields": {
                                    "förstaBelägg": {"type": "string"},
                                    "källa": {"type": "string"},
                                    "beskrivning": {"type": "string"},
                                    "status": {"type": "integer"},
                                    "kommentar": {"type": "string"},
                                },
                            },
                            "kc_nr": {"type": "integer", "required": True},
                            "huvudkommentar": {"type": "string"},
                            "formellKommmentar": {"type": "string"},
                            "formellKommmentarExempel": {"type": "string"},
                            "formellKommmentarTillägg": {"type": "string"},
                            "definition": {"type": "string"},
                            "definitionstillägg": {"type": "string"},
                            "slutkommentar": {"type": "string"},
                            "ämnesområden": {
                                "type": "object",
                                "collection": True,
                                "fields": {
                                    "ämne": {"type": "string"},
                                    "specifikt": {"type": "string"},
                                },
                            },
                            "hänvisningar": {
                                "type": "object",
                                "collection": True,
                                "fields": {
                                    "kc_nr": {"type": "integer"},
                                    "l_nr": {"type": "integer"},
                                    "typ": {"type": "string"},
                                    "hänvisning": {"type": "string"},
                                    "kommentar": {"type": "string"},
                                    "status": {"type": "integer"},
                                    "visas": {"type": "boolean"},
                                },
                            },
                            "morfex": {
                                "type": "object",
                                "collection": True,
                                "fields": {
                                    "ortografi": {"type": "string"},
                                    "hänvisning": {"type": "string"},
                                    "kommentar": {"type": "string"},
                                    "visas": {"type": "boolean"},
                                },
                            },
                            "syntex": {
                                "type": "object",
                                "collection": True,
                                "fields": {
                                    "typ": {"type": "string"},
                                    "text": {"type": "string"},
                                    "kommentar": {"type": "string"},
                                    "visas": {"type": "boolean"},
                                },
                            },
                            "valenser": {
                                "type": "object",
                                "collection": True,
                                "fields": {
                                    "vl_nr": {"type": "integer"},
                                    "typ": {"type": "string"},
                                    "prevalens": {"type": "string"},
                                    "beskrivning": {"type": "string"},
                                    "kommentar": {"type": "string"},
                                    "status": {"type": "integer"},
                                    "visas": {"type": "boolean"},
                                },
                            },
                            "underbetydelser": {
                                "type": "object",
                                "collection": True,
                                "fields": {
                                    "kc_nr": {"type": "integer", "required": True},
                                    "huvudkommentar": {"type": "string"},
                                    "typ": {"type": "string"},
                                    "formellKommmentar": {"type": "string"},
                                    "formellKommmentarvar": {"type": "string"},
                                    "formellKommmentarandra": {"type": "string"},
                                    "defintion": {"type": "string"},
                                    "definitionstillägg": {"type": "string"},
                                    "slutkommentar": {"type": "string"},
                                    "ämnesområden": {
                                        "type": "object",
                                        "collection": True,
                                        "fields": {
                                            "ämne": {"type": "string"},
                                            "specifikt": {"type": "string"},
                                        },
                                    },
                                    "hänvisningar": {
                                        "type": "object",
                                        "collection": True,
                                        "fields": {
                                            "kc_nr": {"type": "integer"},
                                            "l_nr": {"type": "integer"},
                                            "typ": {"type": "string"},
                                            "hänvisning": {"type": "string"},
                                            "kommentar": {"type": "string"},
                                            "status": {"type": "integer"},
                                            "visas": {"type": "boolean"},
                                        },
                                    },
                                    "morfex": {
                                        "type": "object",
                                        "collection": True,
                                        "fields": {
                                            "ortografi": {"type": "string"},
                                            "hänvisning": {"type": "string"},
                                            "kommentar": {"type": "string"},
                                            "visas": {"type": "boolean"},
                                        },
                                    },
                                    "syntex": {
                                        "type": "object",
                                        "collection": True,
                                        "fields": {
                                            "typ": {"type": "string"},
                                            "text": {"type": "string"},
                                            "kommentar": {"type": "string"},
                                            "visas": {"type": "boolean"},
                                        },
                                    },
                                    "valenser": {
                                        "type": "object",
                                        "collection": True,
                                        "fields": {
                                            "vl_nr": {"type": "integer"},
                                            "typ": {"type": "string"},
                                            "prevalens": {"type": "string"},
                                            "beskrivning": {"type": "string"},
                                            "kommentar": {"type": "string"},
                                            "status": {"type": "integer"},
                                            "visas": {"type": "boolean"},
                                        },
                                    },
                                },
                            },
                            "idiom": {
                                "type": "object",
                                "collection": True,
                                "fields": {
                                    "i_nr": {"type": "integer"},
                                    "hänvisning": {"type": "integer"},
                                    "idiom": {"type": "string"},
                                    "formellKommmentar": {"type": "string"},
                                    "alternativinledare": {"type": "string"},
                                    "alternativform": {"type": "string"},
                                    "status": {"type": "integer"},
                                    "idiombetydelser": {
                                        "type": "object",
                                        "collection": True,
                                        "fields": {
                                            "ix_nr": {"type": "integer"},
                                            "definitionsinledare": {"type": "string"},
                                            "huvudkommentar": {"type": "string"},
                                            "definition": {"type": "string"},
                                            "definitionstillägg": {"type": "string"},
                                            "exempel": {"type": "string"},
                                            "status": {"type": "integer"},
                                            "visas": {"type": "boolean"},
                                        },
                                    },
                                    "visas": {"type": "boolean"},
                                },
                            },
                        },
                    },
                    "sentenserOchStilrutor": {
                        "type": "object",
                        "collection": True,
                        "fields": {
                            "typ": {"type": "string"},
                            "text": {"type": "string"},
                            "origid": {"type": "integer"},
                            "origOrd": {"type": "string"},
                            "visas": {"type": "boolean"},
                        },
                    },
                    "uttal": {
                        "type": "object",
                        "collection": True,
                        "fields": {
                            "visas": {"type": "boolean"},
                            "typ": {"type": "string"},
                            "lemmaMedTryckangivelse": {"type": "string"},
                            "fonetikparentes": {"type": "string"},
                            "fonetikkommentar": {"type": "string"},
                            "filenamInlästUttal": {"type": "string"},
                        },
                    },
                    "lemma_referenser": {
                        "type": "object",
                        "collection": True,
                        "fields": {
                            "l_nr": {"type": "integer", "required": True},
                            "lm_sabob": {"type": "integer", "required": True},
                            "ortografi": {"type": "string", "required": True},
                            "lemmatyp": {"type": "string"},
                            "lemmaundertyp": {"type": "string"},
                            "stam": {"type": "string"},
                            "böjning": {"type": "string"},
                            "ordbildning": {"type": "string"},
                            "analys": {"type": "string"},
                            "sorteringsform": {"type": "string"},
                            "kommentar": {"type": "string"},
                            "tagg": {"type": "string"},
                            "ursprung": {"type": "string"},
                        },
                    },
                },
            },
            "SAOLLemman": {
                "type": "object",
                "collection": True,
                "fields": {
                    "lemmaId": {"type": "string"},
                    "ortografi": {"type": "string", "required": True},
                    "homografNr": {
                        "type": "object",
                        "fields": {
                            "nummer": {"type": "string"},
                            "version": {"type": "string"},
                        },
                    },
                    "fonetik": {
                        "type": "object",
                        "collection": True,
                        "fields": {
                            "form": {"type": "string"},
                            "kommentar": {"type": "string"},
                        },
                    },
                    "saolKlass": {"type": "string"},
                    "analys": {"type": "string"},
                    "böjning": {"type": "string"},
                    "alt": {
                        "type": "object",
                        "collection": True,
                        "fields": {
                            "grundform": {"type": "string"},
                            "homografNr": {
                                "type": "object",
                                "fields": {
                                    "nummer": {"type": "string"},
                                    "version": {"type": "string"},
                                },
                            },
                            "analys": {"type": "string"},
                            "typ": {"type": "string"},
                        },
                    },
                    "fack": {"type": "string", "collection": True},
                    "kommentarTillOrdklassSAOL11": {"type": "string"},
                    "saol_status": {"type": "integer"},
                    "ursprung": {"type": "string"},
                    "betydelser": {
                        "type": "object",
                        "collection": True,
                        "fields": {
                            "id": {"type": "string"},
                            "ordningSAOL14": {"type": "string"},
                            "definition": {"type": "string"},
                            "exempel": {
                                "type": "object",
                                "collection": True,
                                "fields": {
                                    "text": {"type": "string"},
                                    "parafras": {"type": "string"},
                                },
                            },
                            "huvudkommentar": {"type": "string"},
                            "formellKommentar": {"type": "string", "collection": True},
                        },
                    },
                    "relation": {
                        "type": "object",
                        "collection": True,
                        "fields": {
                            "typ": {"type": "string"},
                            "till_id": {"type": "string"},
                        },
                    },
                    "kommentar": {"type": "string"},
                    "ptv": {"type": "string"},
                    "smdb_n": {"type": "string"},
                    "hänvisningar": {
                        "type": "object",
                        "collection": True,
                        "fields": {
                            "typ": {"type": "string"},
                            "till_id": {"type": "string"},
                        },
                    },
                },
            },
        }
    }
    _json_schema = create_entry_json_schema(config["fields"])


class TestCreateJsonSchema:
    @pytest.mark.parametrize("field_type", ["long_string"])
    def test_create_with_type(self, field_type: str):
        resource_config = {"field_name": {"type": field_type}}
        json_schema = create_entry_json_schema(resource_config)
        _entry_schema = EntrySchema(json_schema)
