"""Tests for profile persistence and cache behavior."""

from fu7ur3pr00f.container import container
from fu7ur3pr00f.memory.profile import edit_profile
from fu7ur3pr00f.utils.services import get_profile, reload_profile


class TestProfileCache:
    def teardown_method(self) -> None:
        container.reset_services()

    def test_edit_profile_invalidates_cached_profile(
        self, monkeypatch, tmp_path
    ) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        container.reset_services()
        reload_profile()

        cached = get_profile()
        assert cached.name == ""

        updated = edit_profile(lambda profile: setattr(profile, "name", "Juan"))
        assert updated.name == "Juan"

        fresh = get_profile()
        assert fresh.name == "Juan"
