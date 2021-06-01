from unittest import mock
import uuid

import pytest


from karp.domain import errors, repository


def test_entry_repository_create_raises_configuration_error_on_nonexisting_type():
    with pytest.raises(errors.ConfigurationError):
        repository.EntryRepository.create("non-existing", {})
