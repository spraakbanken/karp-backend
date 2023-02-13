from karp.foundation import value_objects  # noqa: F401
from karp.lex.domain.entities.morphology import Morphology  # noqa: F401
from karp.lex.domain.entities.resource import Resource  # noqa: F401

from .factories import random_resource


def test_morphology():
    resource = random_resource()  # noqa: F841
    entry = {  # noqa: F841
        "baseform": "Appalacherna",
        "paradigm": "pm_plg_alperna",
        "pos": "pm",
    }  # noqa: F841

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
    # inflection_table = morphology.get_inflection_table(**needed_fields)
    # assert inflection_table == [
    #     {"form": "Appalacherna", "msd": "nom"},
    #     {"form": "Appalachernas", "msd": "gen"},
    # ]
