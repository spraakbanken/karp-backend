from karp.lex_core.dtos import EntryDtoDict


def test_can_create_entry_dto():
    entry_dto = EntryDtoDict(entry={"field": "value"})

    assert entry_dto.last_modified is None
    assert entry_dto.last_modified_by is None


def test_can_create_entry_dto_with_last_modified_by():
    entry_dto = EntryDtoDict(
        entry={"field": "value"}, lastModifiedBy="username@example.com"
    )

    assert entry_dto.last_modified is None
    assert entry_dto.last_modified_by == "username@example.com"


def test_example_snake_case():
    data = {
        "entity_id": "01GMMWP3ECHP7JEB9NVGRTZ7M6",
        "resource": "fulaord",
        "version": 1,
        "entry": {
            "baseform": "1- on -1",
            "id": "1-_on_-1..1",
            "wordforms": ["one to one", "one 2 one"],
            "text": "<p>även <em>one to one, one 2 one</em> (sl) flitigt använda i herrtidningarnas sexannonser och vid telefonsex. Enl Olle Waller (Fråga Olle) är det troligen tal om ”traditionella önskningar om ett parsamlag”.</p>",
        },
        "last_modified": 1671443451.340828,
        "last_modified_by": "local admin",
    }
    entry_dto = EntryDtoDict(**data)

    assert entry_dto.entity_id == data["entity_id"]
    assert entry_dto.resource == data["resource"]
    assert entry_dto.version == data["version"]
    assert entry_dto.last_modified.timestamp() == data["last_modified"]
    assert entry_dto.last_modified_by == data["last_modified_by"]

    serialized_entry = entry_dto.serialize()

    assert serialized_entry["entityId"] == data["entity_id"]
