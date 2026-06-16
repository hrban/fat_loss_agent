from __future__ import annotations

import sqlite3
from pathlib import Path


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                nickname TEXT NOT NULL,
                sex TEXT NOT NULL,
                age INTEGER NOT NULL,
                height_cm REAL NOT NULL,
                current_weight_kg REAL NOT NULL,
                target_weight_kg REAL NOT NULL,
                activity_level TEXT NOT NULL,
                fat_loss_speed TEXT NOT NULL,
                diet_preferences TEXT NOT NULL DEFAULT '',
                bmr_kcal REAL NOT NULL,
                daily_calorie_target REAL NOT NULL,
                daily_protein_target_g REAL NOT NULL,
                goal_explanation TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS meal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                logged_at TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                input_type TEXT NOT NULL DEFAULT 'text',
                raw_text TEXT NOT NULL,
                photo_path TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL,
                total_calories REAL NOT NULL,
                protein_g REAL NOT NULL,
                carbs_g REAL NOT NULL,
                fat_g REAL NOT NULL,
                confidence REAL NOT NULL,
                notes TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS meal_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_log_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                amount_text TEXT NOT NULL,
                calories REAL NOT NULL,
                protein_g REAL NOT NULL,
                carbs_g REAL NOT NULL,
                fat_g REAL NOT NULL,
                confidence REAL NOT NULL,
                notes TEXT NOT NULL,
                FOREIGN KEY (meal_log_id) REFERENCES meal_logs(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                trace_id TEXT NOT NULL UNIQUE,
                user_input TEXT NOT NULL,
                intent TEXT NOT NULL,
                tool_calls_json TEXT NOT NULL,
                llm_provider TEXT NOT NULL,
                llm_model TEXT NOT NULL,
                llm_prompt_tokens INTEGER NOT NULL DEFAULT 0,
                llm_completion_tokens INTEGER NOT NULL DEFAULT 0,
                llm_latency_ms INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                error_message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )
        ensure_column(conn, "meal_logs", "input_type", "TEXT NOT NULL DEFAULT 'text'")
        ensure_column(conn, "meal_logs", "photo_path", "TEXT NOT NULL DEFAULT ''")


def ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, column_definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
