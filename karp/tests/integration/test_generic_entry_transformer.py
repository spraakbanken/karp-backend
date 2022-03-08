import pytest

from karp.lex import EntryDto
from karp.lex_infrastructure import GenericGetReferencedEntries, GenericEntryViews, GenericGetEntryRepositoryId
from karp.search import EntryTransformer
from karp.search_infrastructure import GenericEntryTransformer

from karp.tests.unit.lex import adapters as lex_adapters
from karp.tests.unit.search import adapters as search_adapters


@pytest.fixture
def transformer():
    index_uow = search_adapters.InMemoryIndexUnitOfWork()
    resource_uow = lex_adapters.InMemoryResourceUnitOfWork()
    resource_repo = lex_adapters.InMemoryReadResourceRepository()
    entry_repo_uow = lex_adapters.InMemoryEntryUowRepositoryUnitOfWork()
    entry_view = GenericEntryViews()
    get_referenced_entries = GenericGetReferencedEntries()
    return GenericEntryTransformer(
        index_uow=index_uow,
        resource_repo=resource_repo,
        entry_views=entry_views,
        get_referenced_entries=get_referenced_entries,
    )


@pytest.fixture
def entry():
    return EntryDto(**{
        "timestamp": 1646646987.439395,
        "entity_id": "UUID('017f63cf-0aaf-6a9c-b67d-d868b8673f1a')",
        "repo_id": "UUID('017f5537-c5da-a0ea-453b-c76d4382e116')",
        "entry_id": "oenig..adjektiv..41k",
        "body": {
            "id": "oenig..adjektiv..41k",
            "ortografi": "oenig",
            "ordklass": "adjektiv",
            "b\u00f6jningsklass": "41k",
            "status": {
                "saol_status": [],
                "status": [
                    "\u00e4ndrad",
                    "\u00e4ndrad"
                ],
                "lm_sabob": [
                    1,
                    0
                ],
                "status_sabob": [
                    "",
                    ""
                ]
            },
            "artikelkommentar": [
                "formen oenighet aktiverad f\u00f6r att inte hv fr missh\u00e4llighet ska se 9",
                "formen oenighet aktiverad f\u00f6r att inte hv fr missh\u00e4llighet ska se 9"
            ],
            "superlemma_typ": [
                "SO2009",
                "SO2009"
            ],
            "SOLemman": [
                {
                    "l_nr": 265097,
                    "s_nr": 104260,
                    "lemmaordning": 1,
                    "lemmatyp": "lemma",
                    "lemmaundertyp": "",
                    "stam": "",
                    "b\u00f6jning": "&t &a",
                    "ordbildning": "o=en\u00b7ig",
                    "analys": "o=en\u00b7ig",
                    "sorteringsform": "oenig",
                    "kommentar": "SOstatus 0",
                    "tagg": "",
                    "betydelser": [
                        {
                            "x_nr": 265098,
                            "huvudbetydelse": {
                                "kc_nr": 598504,
                                "definition": "som har annan uppfattning",
                                "huvudkommentar": "",
                                "formellKommentar": "",
                                "formellKommentarExempel": "",
                                "formellKommentarTill\u00e4gg": "",
                                "slutkommentar": "",
                                "definitionstill\u00e4gg": "\u00e4n ngn annan",
                                "\u00e4mnesomr\u00e5den": [],
                                "h\u00e4nvisningar": [],
                                "morfex": [
                                    {
                                        "ortografi": "oenighet",
                                        "h\u00e4nvisning": "",
                                        "kommentar": "",
                                        "visas": true
                                    }
                                ],
                                "syntex": [
                                    {
                                        "typ": "?",
                                        "text": "han var oenig med sin fru om vilken v\u00e4g de skulle ta",
                                        "kommentar": "",
                                        "visas": true
                                    }
                                ],
                                "valenser": [
                                    {
                                        "vl_nr": 14108,
                                        "typ": "?",
                                        "prevalens": "",
                                        "beskrivning": "& med ngn (om ngn/ngt/SATS)",
                                        "kommentar": "",
                                        "status": 0
                                    },
                                    {
                                        "vl_nr": 14109,
                                        "typ": "?",
                                        "prevalens": "",
                                        "beskrivning": "ngra \u00e4r &a (om ngn/ngt/SATS)",
                                        "kommentar": "*",
                                        "status": 0
                                    }
                                ]
                            },
                            "etymologier": [
                                {
                                    "f\u00f6rstaBel\u00e4gg": "1639",
                                    "k\u00e4lla": "",
                                    "beskrivning": "",
                                    "status": 0,
                                    "kommentar": ""
                                }
                            ],
                            "underbetydelser": [
                                {
                                    "kc_nr": 598505,
                                    "definition": "som har inb\u00f6rdes olika \u00e5sikter",
                                    "huvudkommentar": "",
                                    "formellKommentar": "",
                                    "formellKommentarExempel": "",
                                    "formellKommentarTill\u00e4gg": "",
                                    "slutkommentar": "",
                                    "\u00e4mnesomr\u00e5den": [],
                                    "h\u00e4nvisningar": [],
                                    "morfex": [],
                                    "syntex": [
                                        {
                                            "typ": "?",
                                            "text": "utredarna var oeniga om orsakerna till katastrofen",
                                            "kommentar": "",
                                            "visas": true
                                        }
                                    ],
                                    "valenser": [],
                                    "typ": "i plur. vanl. med inneb\u00f6rd av \u00f6msesidighet"
                                }
                            ],
                            "idiom": [],
                            "status": "GRANSKA"
                        }
                    ],
                    "sentenserOchStilrutor": [],
                    "uttal": [
                        {
                            "l_nr": 265097,
                            "visas": true,
                            "s_nr": 104260,
                            "typ": "",
                            "lemmaMedTryckangivelse": "o`enig",
                            "fonetikparentes": "",
                            "fonetikkommentar": "",
                            "filnamnInl\u00e4stUttal": "265097_1.mp3"
                        }
                    ]
                },
                {
                    "l_nr": 10001371,
                    "s_nr": 104260,
                    "lemmaordning": 2,
                    "lemmatyp": "bojform",
                    "lemmaundertyp": "",
                    "stam": "",
                    "b\u00f6jning": "",
                    "ordbildning": "",
                    "analys": "",
                    "sorteringsform": "oenighet",
                    "kommentar": "hv fr\u00e5n missh\u00e4llighet, f\u00e5r ej nias",
                    "tagg": "",
                    "betydelser": [
                        {
                            "x_nr": 265098,
                            "huvudbetydelse": {
                                "kc_nr": 598504,
                                "definition": "som har annan uppfattning",
                                "huvudkommentar": "",
                                "formellKommentar": "",
                                "formellKommentarExempel": "",
                                "formellKommentarTill\u00e4gg": "",
                                "slutkommentar": "",
                                "definitionstill\u00e4gg": "\u00e4n ngn annan",
                                "\u00e4mnesomr\u00e5den": [],
                                "h\u00e4nvisningar": [],
                                "morfex": [
                                    {
                                        "ortografi": "oenighet",
                                        "h\u00e4nvisning": "",
                                        "kommentar": "",
                                        "visas": true
                                    }
                                ],
                                "syntex": [
                                    {
                                        "typ": "?",
                                        "text": "han var oenig med sin fru om vilken v\u00e4g de skulle ta",
                                        "kommentar": "",
                                        "visas": true
                                    }
                                ],
                                "valenser": [
                                    {
                                        "vl_nr": 14108,
                                        "typ": "?",
                                        "prevalens": "",
                                        "beskrivning": "& med ngn (om ngn/ngt/SATS)",
                                        "kommentar": "",
                                        "status": 0
                                    },
                                    {
                                        "vl_nr": 14109,
                                        "typ": "?",
                                        "prevalens": "",
                                        "beskrivning": "ngra \u00e4r &a (om ngn/ngt/SATS)",
                                        "kommentar": "*",
                                        "status": 0
                                    }
                                ]
                            },
                            "etymologier": [
                                {
                                    "f\u00f6rstaBel\u00e4gg": "1639",
                                    "k\u00e4lla": "",
                                    "beskrivning": "",
                                    "status": 0,
                                    "kommentar": ""
                                }
                            ],
                            "underbetydelser": [
                                {
                                    "kc_nr": 598505,
                                    "definition": "som har inb\u00f6rdes olika \u00e5sikter",
                                    "huvudkommentar": "",
                                    "formellKommentar": "",
                                    "formellKommentarExempel": "",
                                    "formellKommentarTill\u00e4gg": "",
                                    "slutkommentar": "",
                                    "\u00e4mnesomr\u00e5den": [],
                                    "h\u00e4nvisningar": [],
                                    "morfex": [],
                                    "syntex": [
                                        {
                                            "typ": "?",
                                            "text": "utredarna var oeniga om orsakerna till katastrofen",
                                            "kommentar": "",
                                            "visas": true
                                        }
                                    ],
                                    "valenser": [],
                                    "typ": "i plur. vanl. med inneb\u00f6rd av \u00f6msesidighet"
                                }
                            ],
                            "idiom": [],
                            "status": "GRANSKA"
                        }
                    ],
                    "sentenserOchStilrutor": [],
                    "uttal": []
                }
            ],
            "SAOLLemman": [
                {
                    "lemmaId": "63496",
                    "fonetik": [],
                    "saolKlass": "41",
                    "analys": "o=en\u00b7ig",
                    "b\u00f6jning": "+t +a",
                    "alt": [],
                    "fack": [],
                    "kommentarTillOrdklassSAOL11": "-",
                    "saol_status": 0,
                    "antal": 1,
                    "betydelser": [],
                    "relation": [],
                    "h\u00e4nvisningar": []
                }
            ]
        },
        "message": "imported through cli",
        "user": "local admin"
    })


def test_transform(transformer: EntryTransformer, entry: EntryDto):
    resource_id = "lexlex"
    transformed_entry = transformer.transform(resource_id, entry)
