from typing import Type

import pytest
from karp.lex_core.commands import (
    AddEntry,
    CreateEntryRepository,
    CreateResource,
    DeleteEntry,
    DeleteEntryRepository,
    DeleteResource,
    EntryCommand,
    EntryRepoCommand,
    LexCommand,
    PublishResource,
    ResourceCommand,
    SetEntryRepoId,
    UpdateEntry,
    UpdateResource,
)


@pytest.mark.parametrize(
    "data, expected_cls",
    [
        (
            {
                "resourceId": "abc",
                "cmdtype": "add_entry",
                "entry": {},
                "user": "user1",
                "message": "add",
            },
            AddEntry,
        ),
        (
            {
                "entityId": "01GSAHD0K063FBMFE19BFDM4E9",
                "version": 4,
                "resourceId": "abc",
                "cmdtype": "delete_entry",
                "user": "user1",
                "message": "add",
            },
            DeleteEntry,
        ),
        (
            {
                "entityId": "01GSAHD0K063FBMFE19BFDM4E9",
                "version": 4,
                "resourceId": "abc",
                "cmdtype": "update_entry",
                "entry": {},
                "user": "user1",
                "message": "add",
            },
            UpdateEntry,
        ),
    ],
)
def test_entry_command(data: dict, expected_cls: Type) -> None:
    lex_cmd = LexCommand(command=data)

    assert isinstance(lex_cmd.command, expected_cls)
    assert isinstance(EntryCommand(command=data).command, expected_cls)


@pytest.mark.parametrize(
    "data, expected_cls",
    [
        (
            {
                "name": "abc",
                "repositoryType": "default",
                "cmdtype": "create_entry_repository",
                "config": {},
                "user": "user1",
                "message": "add",
            },
            CreateEntryRepository,
        ),
        (
            {
                "entityId": "01GSAHD0K063FBMFE19BFDM4E9",
                "version": 4,
                "cmdtype": "delete_entry_repository",
                "user": "user1",
                "message": "add",
            },
            DeleteEntryRepository,
        ),
    ],
)
def test_entry_repo_command(data: dict, expected_cls: Type) -> None:
    lex_cmd = LexCommand(command=data)

    assert isinstance(lex_cmd.command, expected_cls)
    assert isinstance(EntryRepoCommand(command=data).command, expected_cls)


@pytest.mark.parametrize(
    "data, expected_cls",
    [
        (
            {
                "resourceId": "abc",
                "cmdtype": "create_resource",
                "config": {},
                "entryRepoId": "01GSAHD0K063FBMFE19BFDM4E9",
                "name": "ABC",
                "user": "user1",
                "message": "add",
            },
            CreateResource,
        ),
        (
            {
                "entityId": "01GSAHD0K063FBMFE19BFDM4E9",
                "version": 4,
                # "resourceId": "abc",
                "cmdtype": "delete_resource",
                "user": "user1",
                "message": "add",
            },
            DeleteResource,
        ),
        (
            {
                # "entityId": "01GSAHD0K063FBMFE19BFDM4E9",
                "version": 4,
                "resourceId": "abc",
                "name": "abc",
                "cmdtype": "update_resource",
                "config": {},
                "user": "user1",
                "message": "add",
            },
            UpdateResource,
        ),
        (
            {
                "entityId": "01GSAHD0K063FBMFE19BFDM4E9",
                "version": 4,
                # "resourceId": "abc",
                "cmdtype": "publish_resource",
                "user": "user1",
                "message": "add",
            },
            PublishResource,
        ),
        (
            {
                "entryRepoId": "01GSAHD0K063FBMFE19BFDM4E9",
                "version": 4,
                "resourceId": "abc",
                "cmdtype": "set_entry_repo_id",
                "user": "user1",
                "message": "add",
            },
            SetEntryRepoId,
        ),
    ],
)
def test_resource_command(data: dict, expected_cls: Type) -> None:
    lex_cmd = LexCommand(command=data)

    assert isinstance(lex_cmd.command, expected_cls)
    assert isinstance(ResourceCommand(command=data).command, expected_cls)
