import pytest

from karp.foundation.errors import ConsistencyError
from karp.foundation.entity import (
    TimestampedEntity,
    TimestampedVersionedEntity,
    VersionedEntity,
)


class TestVersionedEntity:
    def test_discard_w_wrong_version_raises_consistency_error(self):
        entity = VersionedEntity("id_v1", 1)

        with pytest.raises(ConsistencyError):
            entity.discard(version=2)

    def test_updated_w_wrong_version_raises_consistency_error(self):
        entity = VersionedEntity("id_v1", 1)

        with pytest.raises(ConsistencyError):
            entity.update(version=2)


    def test_update_increments_version(self):
        entity = VersionedEntity("id_v1", 1)

        entity.update(version=1)

        assert entity.version == 2


class TestTimestampedEntity:
    def test_discard_w_wrong_last_modified_raises_consistency_error(self):
        entity = TimestampedEntity("id_v1", 1)
        with pytest.raises(ConsistencyError):
            entity.discard(
                last_modified=2,
                user="Test",
            )

    def test_update_w_wrong_last_modified_raises_consistency_error(self):
        entity = TimestampedEntity("id_v1", 1)

        with pytest.raises(ConsistencyError):
            entity.update(
                last_modified=2,
                user='Test',
            )

    def test_update_updates_last_modified_and_last_modified_by(self):
        entity = TimestampedEntity("id_v1")

        previous_last_modified = entity.last_modified
        previous_last_modified_by = entity.last_modified_by
        entity.update(
            last_modified=entity.last_modified,
            user="Test",
        )

        assert entity.last_modified > previous_last_modified
        assert entity.last_modified_by != previous_last_modified_by


class TestTimestampedVersionedEntity:
    def test_right_instances(self):
        entity = TimestampedVersionedEntity("id1", version=1)

        assert isinstance(entity, TimestampedVersionedEntity)
        assert isinstance(entity, VersionedEntity)
        assert isinstance(entity, TimestampedEntity)

    def test_discard_discards(self):
        entity = TimestampedVersionedEntity("id1", version=1)

        previous_last_modified = entity.last_modified
        previous_last_modified_by = entity.last_modified_by
        previous_version = entity.version

        entity.discard(
            version=entity.version,
            last_modified=entity.last_modified,
            user="Test",
        )

        assert entity.discarded
        assert entity.last_modified > previous_last_modified
        assert entity.last_modified_by != previous_last_modified_by
        assert entity.version == (previous_version + 1)


    def test_discard_w_wrong_version_raises_consistency_error(self):
        entity = TimestampedVersionedEntity("id_v1", version=1)

        with pytest.raises(ConsistencyError):
            entity.discard(
                version=2,
                last_modified=entity.last_modified,
                user='user@example.com'
            )

    def test_discard_w_wrong_last_modified_raises_consistency_error(self):
        entity = TimestampedVersionedEntity("id_v1", version=1)

        with pytest.raises(ConsistencyError):
            entity.discard(
                version=1,
                last_modified=2,
                user="Test"
            )

    def test_update_w_wrong_version_raises_consistency_error(self):
        entity = TimestampedVersionedEntity("id_v1", version=1)

        with pytest.raises(ConsistencyError):
            entity.update(
                version=2,
                last_modified=entity.last_modified,
                user='User',
            )

    def test_update_w_wrong_last_modified_raises_consistency_error(self):
        entity = TimestampedVersionedEntity("id_v1", version=1)

        with pytest.raises(ConsistencyError):
            entity.update(
                version=1,
                last_modified=2,
                user="Test"
        )

    def test_update_updates(self):
        entity = TimestampedVersionedEntity("id_v1", version=1)

        previous_last_modified = entity.last_modified
        previous_last_modified_by = entity.last_modified_by
        previous_version = entity.version

        entity.update(
            version=entity.version,
            last_modified=entity.last_modified,
            user="Test",
        )

        assert entity.last_modified > previous_last_modified
        assert entity.last_modified_by != previous_last_modified_by
        assert entity.last_modified_by == "Test"
        assert entity.version == (previous_version + 1)

