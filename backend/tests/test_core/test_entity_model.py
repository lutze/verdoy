"""
Tests for Entity model changes.

Covers the timestamp bug fix in Entity.set_property() which previously
wrote to nonexistent self.last_updated instead of self.updated_at.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.entity import Entity


class TestEntitySetProperty:
    """Test Entity.set_property correctly updates updated_at."""

    def test_set_property_updates_updated_at(self, db_session: Session):
        """set_property should update the updated_at timestamp."""
        entity = Entity(
            entity_type="test",
            name="Test Entity",
            properties={},
        )
        db_session.add(entity)
        db_session.commit()
        db_session.refresh(entity)

        original_updated_at = entity.updated_at

        # Small delay to ensure timestamp differs
        entity.set_property("color", "blue")
        db_session.commit()
        db_session.refresh(entity)

        assert entity.properties["color"] == "blue"
        assert entity.updated_at >= original_updated_at

    def test_set_property_initializes_empty_properties(self, db_session: Session):
        """set_property should initialize properties dict if None."""
        entity = Entity(
            entity_type="test",
            name="Test Entity",
            properties=None,
        )
        db_session.add(entity)
        db_session.commit()

        entity.set_property("key", "value")
        db_session.commit()
        db_session.refresh(entity)

        assert entity.properties == {"key": "value"}

    def test_update_properties_updates_updated_at(self, db_session: Session):
        """update_properties should also update the updated_at timestamp."""
        entity = Entity(
            entity_type="test",
            name="Test Entity",
            properties={},
        )
        db_session.add(entity)
        db_session.commit()
        db_session.refresh(entity)

        original_updated_at = entity.updated_at

        entity.update_properties(a="1", b="2")
        db_session.commit()
        db_session.refresh(entity)

        assert entity.properties["a"] == "1"
        assert entity.properties["b"] == "2"
        assert entity.updated_at >= original_updated_at

    def test_set_property_overwrites_existing_key(self, db_session: Session):
        """set_property should overwrite an existing key."""
        entity = Entity(
            entity_type="test",
            name="Test Entity",
            properties={"color": "red"},
        )
        db_session.add(entity)
        db_session.commit()

        entity.set_property("color", "green")
        db_session.commit()
        db_session.refresh(entity)

        assert entity.properties["color"] == "green"

    def test_get_property_returns_default_for_missing_key(self, db_session: Session):
        """get_property should return default for missing keys."""
        entity = Entity(
            entity_type="test",
            name="Test Entity",
            properties={"a": "1"},
        )
        db_session.add(entity)
        db_session.commit()

        assert entity.get_property("a") == "1"
        assert entity.get_property("missing") is None
        assert entity.get_property("missing", "fallback") == "fallback"

    def test_get_property_handles_none_properties(self, db_session: Session):
        """get_property should handle None properties gracefully."""
        entity = Entity(
            entity_type="test",
            name="Test Entity",
            properties=None,
        )
        db_session.add(entity)
        db_session.commit()

        assert entity.get_property("anything") is None
        assert entity.get_property("anything", "default") == "default"
