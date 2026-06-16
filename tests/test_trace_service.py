import json

from fat_loss_agent.repositories.db import init_db
from fat_loss_agent.repositories.trace_repo import TraceRepository
from fat_loss_agent.services.trace_service import TraceService


def test_trace_service_writes_sqlite_and_jsonl(tmp_path):
    db_path = tmp_path / "app.db"
    log_path = tmp_path / "agent_logs.jsonl"
    init_db(db_path)
    service = TraceService(TraceRepository(db_path), log_path)

    trace_id = service.record_trace(
        user_id="local_user",
        user_input="午饭吃了鸡蛋",
        intent="meal_log",
        tool_calls=[{"name": "estimate_meal_from_text"}],
        llm_provider="qwen",
        llm_model="qwen-plus",
        llm_prompt_tokens=10,
        llm_completion_tokens=20,
        llm_latency_ms=300,
        status="success",
        error_message="",
    )

    rows = service.repo.list_recent("local_user", limit=5)
    payload = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert trace_id
    assert rows[0]["trace_id"] == trace_id
    assert payload["trace_id"] == trace_id
