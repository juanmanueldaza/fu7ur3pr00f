"""Fixtures for blackboard pattern tests."""

import pytest

from fu7ur3pr00f.agents.blackboard.blackboard import make_initial_blackboard


@pytest.fixture
def empty_blackboard():
    """Blackboard with empty query and profile for test setup."""
    return make_initial_blackboard("test", {})
