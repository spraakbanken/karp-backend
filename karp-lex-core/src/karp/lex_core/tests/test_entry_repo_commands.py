from karp.lex_core.commands import CreateEntryRepository


class TestCreateEntryRepository:
    def test_from_dict_works(self) -> None:
        cmd = CreateEntryRepository.from_dict(
            {
                "resource_id": "abc",
                "resource_name": "Abc",
            },
            # entry_repo_id="01GSAHD0K063FBMFE19BFDM4E9",
            user="user1",
        )
        assert cmd.cmdtype == "create_entry_repository"
