from karp.domain.models.resource import Resource
from karp.domain.models.morphology import Morphology
from .factories import random_resource


def test_morphology():
    resource = random_resource()
    entry = {"baseform": "Appalacherna", "paradigm": "pm_plg_alperna", "pos": "pm"}

    morphology = Morphology()
    # morphological_entry = {"entry_id": "pm_plg_alperna"}

    needed_field_names = morphology.inflection_fields()

    needed_fields = {
        needed_field_name: resource.get_field(needed_field_name, entry)
        for needed_field_name in needed_field_names
    }
    inflection_table = morphology.get_inflection_table(**needed_fields)
    assert inflection_table == [
        {"form": "Appalacherna", "msd": "nom"},
        {"form": "Appalachernas", "msd": "gen"},
    ]
