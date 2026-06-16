import sqlite3

from fat_loss_agent.repositories.db import init_db


def test_init_db_creates_expected_tables(tmp_path):
    db_path = tmp_path / "app.db"
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

    table_names = {row[0] for row in rows}
    assert {
        "agent_traces",
        "chat_messages",
        "meal_items",
        "meal_logs",
        "profiles",
    }.issubset(table_names)
