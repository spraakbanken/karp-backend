from karp.lex_core.commands import AddEntry, DeleteEntry, EntryCommand, UpdateEntry
from karp.lex_core.value_objects import make_unique_id


class TestDeserializeEntryCommand:
    def test_can_deserialize_add_entry(self) -> None:
        data = {
            "cmd": {
                "cmdtype": "add_entry",
                "resourceId": "resource_a",
                "entry": {"baseform": "sko"},
                "message": "add sko",
                "user": "alice@example.com",
            }
        }

        cmd = EntryCommand(**data)

        assert isinstance(cmd.cmd, AddEntry)

    def test_can_deserialize_delete_entry(self) -> None:
        data = {
            "cmd": {
                "cmdtype": "delete_entry",
                "resourceId": "resource_a",
                "id": make_unique_id(),
                "version": 1,
                "message": "add sko",
                "user": "alice@example.com",
            }
        }

        cmd = EntryCommand(**data)

        assert isinstance(cmd.cmd, DeleteEntry)

    def test_can_deserialize_update_entry(self) -> None:
        data = {
            "cmd": {
                "cmdtype": "update_entry",
                "resourceId": "resource_a",
                "id": make_unique_id(),
                "entry": {"baseform": "sko"},
                "version": 1,
                "message": "add sko",
                "user": "alice@example.com",
            }
        }

        cmd = EntryCommand(**data)

        assert isinstance(cmd.cmd, UpdateEntry)
