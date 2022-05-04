import pytest

from karp.foundation import value_objects
from karp.lex.domain.entities import Morphology, SmdbMorphology, Resource

from .factories import random_resource, SmdbMorphologyFactory


@pytest.fixture
def smdb_morphology() -> SmdbMorphology:
    return SmdbMorphologyFactory()


def test_smdb_morphology(smdb_morphology: SmdbMorphology):
    resource = random_resource()
    entry = {"baseform": "gata", "paradigm": "11a", "pos": "?"}

    assert isinstance(smdb_morphology, Morphology)
    assert isinstance(smdb_morphology, Resource)
    # morphology = Morphology.create_resource(
    #     resource_type='SaldoMorphology',
    #     resource_config={},
    #     # entity_id=value_objects.make_unique_id(),
    # )
    # morphological_entry = {"entry_id": "pm_plg_alperna"}

    # needed_field_names = morphology.inflection_fields()

    # needed_fields = {
    #     needed_field_name: resource.get_field(needed_field_name, entry)
    #     for needed_field_name in needed_field_names
    # }
    inflection_table = smdb_morphology.get_inflection_table(
        identifer=entry["paradigm"], lemma=entry["baseform"]
    )
    # TODO what form shall the inflection_table have: maybe list[dict[str, Any]]?
    assert inflection_table == [
        {"form": "gata", "tagg": "NCUSNI"},
        {"form": "gatas", "tagg": "NCUSGI"},
    ]
    # assert inflection_table == {
    #     "NCUSNI": {
    #         "form": "gata",
    #     },
    #     "NCUSGI": {
    #         "form": "gatas",
    #     },
    # }
    # assert inflection_table == {
    #     "NCUSNI": "gata",
    #     "NCUSGI": "gatas",
    # }
