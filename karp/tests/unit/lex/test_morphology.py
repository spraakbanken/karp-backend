from karp.foundation import value_objects
from karp.lex.domain.entities.morphology import Morphology
from karp.lex.domain.entities.resource import Resource

from .factories import random_resource


def test_morphology():
    resource = random_resource()
    entry = {"baseform": "Appalacherna", "paradigm": "pm_plg_alperna", "pos": "pm"}

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
