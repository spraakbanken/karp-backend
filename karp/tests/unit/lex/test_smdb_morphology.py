import pytest

from karp.foundation import value_objects
from karp.lex.domain.entities import Morphology, SmdbMorphology, Resource

from .factories import random_resource, SmdbMorphologyFactory

import csv


@pytest.fixture
def smdb_morphology() -> SmdbMorphology:
    return SmdbMorphologyFactory()

def pad(s,n) :
    return s + ''.join([' ' for i in range(n-len(s))])

def test_smdb_morphology(smdb_morphology: SmdbMorphology):
    
    resource = random_resource()
  #  entry = {"baseform": "gata", "paradigm": "11", "pos": "?"}

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
  #  inflection_table = smdb_morphology.get_inflection_table(
  #      identifier=entry["paradigm"], lemma=entry["baseform"]
  #  )
    # TODO what form shall the inflection_table have: maybe list[dict[str, Any]]?
    # assert inflection_table == 
    # [
    #    {"form": "gata", "tagg": "NCUSNI"},
    #    {"form": "gatas", "tagg": "NCUSGI"},
    #]
    # assert inflection_table == {
    #     "NCUSNI": {
    #         "form": "gata",
    #     },
    #     "NCUSGI": {
    #         "form": "gatas",
    #     },
    # }
  #  assert inflection_table == {
  ##      "NCUSNI": "gata",
  #      "NCUSGI": "gatas"
  
    
    with open('./fullform_utf8_202204271524.csv', newline='') as csvfile:
           
            db_table,connection = smdb_morphology.load_db('mysql://root@localhost/morphology')
            fieldnames = ["f_nr","sortform","avstform","grundform","l_nr","bklass","tagg","typ","s_nr","src","nummer","ordklass"]
            reader = csv.DictReader(csvfile)
            for row in reader:
            #    print(row)
                inflection_table = smdb_morphology.get_inflection_table(
                    db_table,
                    connection,
                    identifier=row["bklass"], lemma=row["grundform"])
                if row["tagg"] not in inflection_table :
                    print(pad("Tag " + str(row["tagg"]), 10) +  pad(" is not present in inflection table: " + str(inflection_table),60) + " for inflection class " + str(row["bklass"]) + " " + str(row["grundform"]))
                else : 
                    try:  assert(inflection_table[row["tagg"]] == row["sortform"])
                    except AssertionError: print(pad("inflected form: " + str(inflection_table[row["tagg"]]),30), 
                                                 pad("correct form: " + str(row["sortform"]),30),
                                                 "inflection class: " + str(row["bklass"]), 
                                                 "tag: " + str(row["tagg"]),
                                                 "lemma: " + str(row["grundform"]))
  
if __name__ == '__main__':
    test_smdb_morphology(SmdbMorphologyFactory())  
