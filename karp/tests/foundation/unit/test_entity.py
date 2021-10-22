import pytest

from karp.foundation.errors import ConsistencyError
from karp.foundation.entity import (
    TimestampedEntity,
    TimestampedVersionedEntity,
    VersionedEntity,
)


def test_versioned_entity_discard_w_wrong_version_raises_consistency_error():
    entity = VersionedEntity("id_v1", 1)

    # event = VersionedEntity.Discarded(entity_id=entity.id, entity_version=2)

    with pytest.raises(ConsistencyError):
        entity.discard(version=2)


def test_versioned_entity_stamped_w_wrong_version_raises_consistency_error():
    entity = VersionedEntity("id_v1", 1)

    event = VersionedEntity.Stamped(entity_id=entity.id, entity_version=2)

    with pytest.raises(ConsistencyError):
        event.mutate(entity)


def test_versioned_entity_stamped_increments_version():
    entity = VersionedEntity("id_v1", 1)

    event = VersionedEntity.Stamped(entity_id=entity.id, entity_version=entity.version)

    event.mutate(entity)

    assert entity.version == 2


def test_timestamped_entity_discard_w_wrong_last_modified_raises_consistency_error():
    entity = TimestampedEntity("id_v1", 1)

    event = TimestampedEntity.Discarded(
        entity_id=entity.id, entity_last_modified=2, user="Test"
    )

    with pytest.raises(ConsistencyError):
        event.mutate(entity)


def test_timestamped_entity_stamped_w_wrong_last_modified_raises_consistency_error():
    entity = TimestampedEntity("id_v1", 1)

    event = TimestampedEntity.Stamped(
        entity_id=entity.id, entity_last_modified=2, user="Test"
    )

    with pytest.raises(ConsistencyError):
        event.mutate(entity)


def test_timestamped_entity_stamped_updates_last_modified_and_last_modified_by():
    entity = TimestampedEntity("id_v1")

    event = TimestampedEntity.Stamped(
        entity_id=entity.id, entity_last_modified=entity.last_modified, user="Test"
    )

    previous_last_modified = entity.last_modified
    previous_last_modified_by = entity.last_modified_by
    event.mutate(entity)

    assert entity.last_modified > previous_last_modified
    assert entity.last_modified_by != previous_last_modified_by


def test_timestamped_versioned_entity():
    entity = TimestampedVersionedEntity("id1", version=1)

    assert isinstance(entity, TimestampedVersionedEntity)
    assert isinstance(entity, VersionedEntity)
    assert isinstance(entity, TimestampedEntity)


def test_timestamped_versioned_entity_discarded():
    entity = TimestampedVersionedEntity("id1", version=1)

    event = TimestampedVersionedEntity.Discarded(
        entity_id=entity.id,
        entity_version=entity.version,
        entity_last_modified=entity.last_modified,
        user="Test",
    )

    previous_last_modified = entity.last_modified
    previous_last_modified_by = entity.last_modified_by
    previous_version = entity.version
    event.mutate(entity)

    assert entity.discarded
    assert entity.last_modified > previous_last_modified
    assert entity.last_modified_by != previous_last_modified_by
    assert entity.version == (previous_version + 1)


def test_timestamped_versioned_entity_discarded_w_wrong_version_raises_consistency_error():
    entity = TimestampedVersionedEntity("id_v1", version=1)

    event = TimestampedVersionedEntity.Discarded(entity_id=entity.id, entity_version=2)

    with pytest.raises(ConsistencyError):
        event.mutate(entity)


def test_timestamped_versioned_entity_discarded_w_wrong_last_modified_raises_consistency_error():
    entity = TimestampedVersionedEntity("id_v1", version=1)

    event = TimestampedVersionedEntity.Discarded(
        entity_id=entity.id, entity_version=1, entity_last_modified=2, user="Test"
    )

    with pytest.raises(ConsistencyError):
        event.mutate(entity)


def test_timestamped_versioned_entity_stamped_w_wrong_version_raises_consistency_error():
    entity = TimestampedVersionedEntity("id_v1", version=1)

    event = TimestampedVersionedEntity.Stamped(entity_id=entity.id, entity_version=2)

    with pytest.raises(ConsistencyError):
        event.mutate(entity)


def test_timestamped_versioned_entity_stamped_w_wrong_last_modified_raises_consistency_error():
    entity = TimestampedVersionedEntity("id_v1", version=1)

    event = TimestampedVersionedEntity.Stamped(
        entity_id=entity.id, entity_version=1, entity_last_modified=2, user="Test"
    )

    with pytest.raises(ConsistencyError):
        event.mutate(entity)


def test_timestamped_versioned_entity_stamped_updates():
    entity = TimestampedVersionedEntity("id_v1", version=1)

    event = TimestampedVersionedEntity.Stamped(
        entity_id=entity.id,
        entity_version=entity.version,
        entity_last_modified=entity.last_modified,
        user="Test",
    )

    previous_last_modified = entity.last_modified
    previous_last_modified_by = entity.last_modified_by
    previous_version = entity.version

    event.mutate(entity)

    assert entity.last_modified > previous_last_modified
    assert entity.last_modified_by != previous_last_modified_by
    assert entity.version == (previous_version + 1)


def test_timestamped_versioned_entity_stamp_updates_last_modified_and_version():
    entity = TimestampedVersionedEntity("id_v1", version=1)

    previous_last_modified = entity.last_modified
    previous_last_modified_by = entity.last_modified_by
    previous_version = entity.version

    entity.stamp(user="Test")

    assert entity.last_modified > previous_last_modified
    assert entity.last_modified_by == "Test"
    assert entity.version == (previous_version + 1)


def test_timestamped_versioned_entity_stamp_w_increment_version_eq_false_updates_last_modified_and_not_version():
    entity = TimestampedVersionedEntity("id_v1", version=1)

    previous_last_modified = entity.last_modified
    previous_last_modified_by = entity.last_modified_by
    previous_version = entity.version

    entity.stamp(user="Test", increment_version=False)

    assert entity.last_modified > previous_last_modified
    assert entity.last_modified_by == "Test"
    assert entity.version == previous_version
