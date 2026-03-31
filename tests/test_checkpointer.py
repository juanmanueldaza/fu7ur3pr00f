"""Tests for checkpointer thread visibility."""

import sqlite3

from fu7ur3pr00f.memory.checkpointer import list_threads


class TestListThreads:
    def test_filters_internal_blackboard_threads(self, tmp_path):
        db_path = tmp_path / "memory.db"
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE checkpoints (thread_id TEXT)")
            cursor.execute("CREATE TABLE writes (thread_id TEXT)")
            cursor.execute(
                "INSERT INTO checkpoints(thread_id) VALUES (?), (?), (?)",
                ("main", "bb_internal123", "career"),
            )
            conn.commit()
        finally:
            conn.close()

        from unittest.mock import patch

        with patch(
            "fu7ur3pr00f.memory.checkpointer.get_data_dir", return_value=tmp_path
        ):
            assert list_threads() == ["career", "main"]
