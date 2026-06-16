# Fat Loss Agent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于已确认的中文设计 spec，实现一个本地可用的个人减脂 Agent MVP，支持建档、文本饮食估算、手动修正保存、今日摘要和 trace 记录。

**Architecture:** 采用轻量分层 Python 单体。Streamlit 只负责 UI，services 负责业务规则，repositories 负责 SQLite，agent orchestrator 负责显式编排，llm 层通过 OpenAI 兼容接口调用 Qwen。

**Tech Stack:** Python 3.11+、Streamlit、SQLite、Pydantic、OpenAI Python SDK、python-dotenv、pytest。

---

## 文件结构

实现完成后，项目应包含：

```text
fat_loss_agent/
  __init__.py
  app.py
  config.py
  pages/
    __init__.py
    profile_page.py
    meal_chat_page.py
  agent/
    __init__.py
    orchestrator.py
    prompts.py
    schemas.py
  llm/
    __init__.py
    base.py
    qwen_client.py
  services/
    __init__.py
    profile_service.py
    goal_service.py
    meal_service.py
    nutrition_service.py
    summary_service.py
    trace_service.py
  repositories/
    __init__.py
    db.py
    profile_repo.py
    meal_repo.py
    chat_repo.py
    trace_repo.py
  data/
    .gitkeep
  traces/
    .gitkeep
tests/
  test_db.py
  test_goal_service.py
  test_profile_service.py
  test_meal_service.py
  test_schemas.py
  test_nutrition_service.py
  test_trace_service.py
  test_orchestrator.py
.env.example
.gitignore
pyproject.toml
```

职责边界：

- `pages/`：只写 Streamlit UI，不直接调 SQL 或 Qwen。
- `services/`：业务规则和用例级操作。
- `repositories/`：SQLite CRUD。
- `agent/`：Agent 编排、prompt 和结构化 schema。
- `llm/`：Provider 抽象和 Qwen 客户端。

## 外部接口约定

Qwen 通过阿里云百炼 OpenAI 兼容接口接入。默认值：

```text
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

代码读取：

```text
QWEN_API_KEY
QWEN_BASE_URL
QWEN_MODEL
```

为兼容阿里云文档中的命名，`QwenClient` 在 `QWEN_API_KEY` 缺失时可以读取 `DASHSCOPE_API_KEY`。

---

### Task 1: 项目骨架与依赖

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `fat_loss_agent/__init__.py`
- Create: `fat_loss_agent/config.py`
- Create: package `__init__.py` files
- Create: `fat_loss_agent/data/.gitkeep`
- Create: `fat_loss_agent/traces/.gitkeep`

- [ ] **Step 1: 创建依赖配置**

Create `pyproject.toml`:

```toml
[project]
name = "fat-loss-agent"
version = "0.1.0"
description = "Personal fat-loss agent MVP"
requires-python = ">=3.11"
dependencies = [
  "openai>=1.0.0",
  "pydantic>=2.7.0",
  "python-dotenv>=1.0.1",
  "streamlit>=1.36.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0"
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: 创建环境变量样例**

Create `.env.example`:

```text
QWEN_API_KEY=
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
APP_DB_PATH=fat_loss_agent/data/app.db
TRACE_LOG_PATH=fat_loss_agent/traces/agent_logs.jsonl
```

- [ ] **Step 3: 创建 gitignore**

Create `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.streamlit/secrets.toml
fat_loss_agent/data/*.db
fat_loss_agent/data/*.db-*
fat_loss_agent/traces/*.jsonl
```

- [ ] **Step 4: 创建配置模块**

Create `fat_loss_agent/config.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_USER_ID = "local_user"


@dataclass(frozen=True)
class AppConfig:
    db_path: Path
    trace_log_path: Path
    qwen_api_key: str | None
    qwen_base_url: str
    qwen_model: str


def load_config() -> AppConfig:
    load_dotenv()
    db_path = Path(os.getenv("APP_DB_PATH", "fat_loss_agent/data/app.db"))
    trace_log_path = Path(os.getenv("TRACE_LOG_PATH", "fat_loss_agent/traces/agent_logs.jsonl"))
    qwen_api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    return AppConfig(
        db_path=db_path,
        trace_log_path=trace_log_path,
        qwen_api_key=qwen_api_key,
        qwen_base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        qwen_model=os.getenv("QWEN_MODEL", "qwen-plus"),
    )
```

- [ ] **Step 5: 创建包目录和保留文件**

Create empty `__init__.py` files:

```text
fat_loss_agent/__init__.py
fat_loss_agent/pages/__init__.py
fat_loss_agent/agent/__init__.py
fat_loss_agent/llm/__init__.py
fat_loss_agent/services/__init__.py
fat_loss_agent/repositories/__init__.py
```

Create empty keep files:

```text
fat_loss_agent/data/.gitkeep
fat_loss_agent/traces/.gitkeep
```

- [ ] **Step 6: 安装依赖并验证导入**

Run:

```bash
python -m pip install -e ".[dev]"
python - <<'PY'
from fat_loss_agent.config import load_config, DEFAULT_USER_ID
config = load_config()
assert DEFAULT_USER_ID == "local_user"
assert config.qwen_model
print("config import ok")
PY
```

Expected:

```text
config import ok
```

- [ ] **Step 7: 提交骨架**

```bash
git add pyproject.toml .env.example .gitignore fat_loss_agent
git commit -m "chore: scaffold fat loss agent project"
```

---

### Task 2: Pydantic Schema 与校验

**Files:**
- Create: `fat_loss_agent/agent/schemas.py`
- Create: `tests/test_schemas.py`

- [ ] **Step 1: 写失败测试**

Create `tests/test_schemas.py`:

```python
import pytest
from pydantic import ValidationError

from fat_loss_agent.agent.schemas import MealItemEstimate, PendingMealEstimate


def test_pending_meal_accepts_valid_qwen_shape():
    meal = PendingMealEstimate(
        is_food_log=True,
        meal_type="lunch",
        title="鸡蛋和米饭",
        items=[
            MealItemEstimate(
                name="鸡蛋",
                amount_text="2个",
                calories=140,
                protein_g=12,
                carbs_g=1,
                fat_g=10,
                confidence=0.8,
                notes="按水煮蛋估算",
            )
        ],
        total_calories=140,
        protein_g=12,
        carbs_g=1,
        fat_g=10,
        confidence=0.8,
        notes="份量明确",
    )

    assert meal.items[0].name == "鸡蛋"
    assert meal.total_calories == 140


def test_pending_meal_rejects_negative_nutrition():
    with pytest.raises(ValidationError):
        MealItemEstimate(
            name="米饭",
            amount_text="一碗",
            calories=-1,
            protein_g=4,
            carbs_g=55,
            fat_g=1,
            confidence=0.6,
            notes="非法热量",
        )


def test_pending_meal_requires_item_when_food_log():
    with pytest.raises(ValidationError):
        PendingMealEstimate(
            is_food_log=True,
            meal_type="dinner",
            title="空餐食",
            items=[],
            total_calories=0,
            protein_g=0,
            carbs_g=0,
            fat_g=0,
            confidence=0.2,
            notes="没有明细",
        )
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/test_schemas.py -v
```

Expected: FAIL because `fat_loss_agent.agent.schemas` does not exist.

- [ ] **Step 3: 实现 schema**

Create `fat_loss_agent/agent/schemas.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


MealType = Literal["breakfast", "lunch", "dinner", "snack", "unknown"]


class MealItemEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    amount_text: str = Field(min_length=1)
    calories: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    notes: str = ""


class PendingMealEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_food_log: bool
    meal_type: MealType = "unknown"
    title: str = ""
    items: list[MealItemEstimate] = Field(default_factory=list)
    total_calories: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    notes: str = ""

    @model_validator(mode="after")
    def require_items_for_food_log(self) -> "PendingMealEstimate":
        if self.is_food_log and not self.items:
            raise ValueError("food log estimates must include at least one item")
        return self
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
pytest tests/test_schemas.py -v
```

Expected: PASS.

- [ ] **Step 5: 提交 schema**

```bash
git add fat_loss_agent/agent/schemas.py tests/test_schemas.py
git commit -m "feat: add meal estimate schemas"
```

---

### Task 3: SQLite 初始化与表结构

**Files:**
- Create: `fat_loss_agent/repositories/db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: 写失败测试**

Create `tests/test_db.py`:

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/test_db.py -v
```

Expected: FAIL because `init_db` does not exist.

- [ ] **Step 3: 实现数据库初始化**

Create `fat_loss_agent/repositories/db.py`:

```python
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
                raw_text TEXT NOT NULL,
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
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
pytest tests/test_db.py -v
```

Expected: PASS.

- [ ] **Step 5: 提交数据库初始化**

```bash
git add fat_loss_agent/repositories/db.py tests/test_db.py
git commit -m "feat: initialize sqlite schema"
```

---

### Task 4: 档案与目标预算服务

**Files:**
- Create: `fat_loss_agent/repositories/profile_repo.py`
- Create: `fat_loss_agent/services/goal_service.py`
- Create: `fat_loss_agent/services/profile_service.py`
- Create: `tests/test_goal_service.py`
- Create: `tests/test_profile_service.py`

- [ ] **Step 1: 写 goal service 失败测试**

Create `tests/test_goal_service.py`:

```python
from fat_loss_agent.services.goal_service import calculate_goals


def test_calculate_goals_for_standard_male_profile():
    result = calculate_goals(
        sex="male",
        age=30,
        height_cm=175,
        current_weight_kg=80,
        target_weight_kg=72,
        activity_level="moderate",
        fat_loss_speed="standard",
    )

    assert 1600 <= result.daily_calorie_target <= 2300
    assert result.daily_protein_target_g == 128
    assert "标准" in result.goal_explanation


def test_calculate_goals_for_conservative_female_profile():
    result = calculate_goals(
        sex="female",
        age=28,
        height_cm=165,
        current_weight_kg=62,
        target_weight_kg=58,
        activity_level="light",
        fat_loss_speed="conservative",
    )

    assert result.bmr_kcal > 1200
    assert result.daily_calorie_target >= 1200
    assert result.daily_protein_target_g == 99
```

- [ ] **Step 2: 写 profile service 失败测试**

Create `tests/test_profile_service.py`:

```python
from fat_loss_agent.repositories.db import init_db
from fat_loss_agent.repositories.profile_repo import ProfileRepository
from fat_loss_agent.services.profile_service import ProfileService


def test_profile_service_upserts_and_reads_profile(tmp_path):
    db_path = tmp_path / "app.db"
    init_db(db_path)
    service = ProfileService(ProfileRepository(db_path))

    saved = service.save_profile(
        user_id="local_user",
        nickname="Yao",
        sex="male",
        age=30,
        height_cm=175,
        current_weight_kg=80,
        target_weight_kg=72,
        activity_level="moderate",
        fat_loss_speed="standard",
        diet_preferences="少油",
    )

    loaded = service.get_profile("local_user")
    assert loaded is not None
    assert loaded["nickname"] == "Yao"
    assert saved["daily_protein_target_g"] == 128
```

- [ ] **Step 3: 运行测试确认失败**

Run:

```bash
pytest tests/test_goal_service.py tests/test_profile_service.py -v
```

Expected: FAIL because service and repository modules do not exist.

- [ ] **Step 4: 实现 goal service**

Create `fat_loss_agent/services/goal_service.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GoalResult:
    bmr_kcal: int
    daily_calorie_target: int
    daily_protein_target_g: int
    goal_explanation: str


ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
}

DEFICITS = {
    "conservative": 300,
    "standard": 500,
    "aggressive": 700,
}

SPEED_LABELS = {
    "conservative": "保守",
    "standard": "标准",
    "aggressive": "激进",
}


def calculate_goals(
    *,
    sex: str,
    age: int,
    height_cm: float,
    current_weight_kg: float,
    target_weight_kg: float,
    activity_level: str,
    fat_loss_speed: str,
) -> GoalResult:
    if sex == "male":
        bmr = 10 * current_weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * current_weight_kg + 6.25 * height_cm - 5 * age - 161

    factor = ACTIVITY_FACTORS.get(activity_level, ACTIVITY_FACTORS["light"])
    deficit = DEFICITS.get(fat_loss_speed, DEFICITS["standard"])
    tdee = bmr * factor
    min_calories = 1500 if sex == "male" else 1200
    calorie_target = max(int(round(tdee - deficit)), min_calories)
    protein_target = int(round(current_weight_kg * 1.6))
    label = SPEED_LABELS.get(fat_loss_speed, SPEED_LABELS["standard"])
    explanation = (
        f"按 Mifflin-St Jeor 公式估算 BMR，活动系数 {factor}，"
        f"{label}减脂每日约 {deficit} kcal 缺口。"
    )

    return GoalResult(
        bmr_kcal=int(round(bmr)),
        daily_calorie_target=calorie_target,
        daily_protein_target_g=protein_target,
        goal_explanation=explanation,
    )
```

- [ ] **Step 5: 实现 profile repository**

Create `fat_loss_agent/repositories/profile_repo.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fat_loss_agent.repositories.db import get_connection


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProfileRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_by_user_id(self, user_id: str) -> dict[str, Any] | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def upsert(self, profile: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        existing = self.get_by_user_id(profile["user_id"])
        data = {**profile, "updated_at": now}
        if existing:
            assignments = ", ".join(f"{key} = ?" for key in data if key != "user_id")
            values = [value for key, value in data.items() if key != "user_id"]
            values.append(profile["user_id"])
            with get_connection(self.db_path) as conn:
                conn.execute(f"UPDATE profiles SET {assignments} WHERE user_id = ?", values)
            return self.get_by_user_id(profile["user_id"]) or data

        data["created_at"] = now
        columns = ", ".join(data.keys())
        bind_marks = ", ".join("?" for _ in data)
        with get_connection(self.db_path) as conn:
            conn.execute(
                f"INSERT INTO profiles ({columns}) VALUES ({bind_marks})",
                list(data.values()),
            )
        return self.get_by_user_id(profile["user_id"]) or data
```

- [ ] **Step 6: 实现 profile service**

Create `fat_loss_agent/services/profile_service.py`:

```python
from __future__ import annotations

from typing import Any

from fat_loss_agent.repositories.profile_repo import ProfileRepository
from fat_loss_agent.services.goal_service import calculate_goals


class ProfileService:
    def __init__(self, repo: ProfileRepository):
        self.repo = repo

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        return self.repo.get_by_user_id(user_id)

    def save_profile(
        self,
        *,
        user_id: str,
        nickname: str,
        sex: str,
        age: int,
        height_cm: float,
        current_weight_kg: float,
        target_weight_kg: float,
        activity_level: str,
        fat_loss_speed: str,
        diet_preferences: str,
    ) -> dict[str, Any]:
        goals = calculate_goals(
            sex=sex,
            age=age,
            height_cm=height_cm,
            current_weight_kg=current_weight_kg,
            target_weight_kg=target_weight_kg,
            activity_level=activity_level,
            fat_loss_speed=fat_loss_speed,
        )
        return self.repo.upsert(
            {
                "user_id": user_id,
                "nickname": nickname,
                "sex": sex,
                "age": age,
                "height_cm": height_cm,
                "current_weight_kg": current_weight_kg,
                "target_weight_kg": target_weight_kg,
                "activity_level": activity_level,
                "fat_loss_speed": fat_loss_speed,
                "diet_preferences": diet_preferences,
                "bmr_kcal": goals.bmr_kcal,
                "daily_calorie_target": goals.daily_calorie_target,
                "daily_protein_target_g": goals.daily_protein_target_g,
                "goal_explanation": goals.goal_explanation,
            }
        )
```

- [ ] **Step 7: 运行测试确认通过**

Run:

```bash
pytest tests/test_goal_service.py tests/test_profile_service.py -v
```

Expected: PASS.

- [ ] **Step 8: 提交档案和目标服务**

```bash
git add fat_loss_agent/repositories/profile_repo.py fat_loss_agent/services/goal_service.py fat_loss_agent/services/profile_service.py tests/test_goal_service.py tests/test_profile_service.py
git commit -m "feat: add profile and goal services"
```

---

### Task 5: 餐食持久化与今日汇总

**Files:**
- Create: `fat_loss_agent/repositories/meal_repo.py`
- Create: `fat_loss_agent/services/meal_service.py`
- Create: `fat_loss_agent/services/summary_service.py`
- Create: `tests/test_meal_service.py`

- [ ] **Step 1: 写失败测试**

Create `tests/test_meal_service.py`:

```python
from fat_loss_agent.agent.schemas import MealItemEstimate, PendingMealEstimate
from fat_loss_agent.repositories.db import init_db
from fat_loss_agent.repositories.meal_repo import MealRepository
from fat_loss_agent.services.meal_service import MealService
from fat_loss_agent.services.summary_service import SummaryService


def test_save_meal_and_get_today_summary(tmp_path):
    db_path = tmp_path / "app.db"
    init_db(db_path)
    service = MealService(MealRepository(db_path))
    meal = PendingMealEstimate(
        is_food_log=True,
        meal_type="lunch",
        title="鸡蛋米饭",
        items=[
            MealItemEstimate(
                name="鸡蛋",
                amount_text="2个",
                calories=140,
                protein_g=12,
                carbs_g=1,
                fat_g=10,
                confidence=0.8,
                notes="",
            )
        ],
        total_calories=140,
        protein_g=12,
        carbs_g=1,
        fat_g=10,
        confidence=0.8,
        notes="",
    )

    saved_id = service.save_meal_log("local_user", "午饭吃了两个鸡蛋", meal)
    summary = service.get_today_summary("local_user")

    assert saved_id > 0
    assert summary["total_calories"] == 140
    assert summary["protein_g"] == 12
    assert len(summary["meals"]) == 1


def test_summary_service_calculates_remaining_budget():
    dashboard = SummaryService.build_dashboard(
        profile={"daily_calorie_target": 1800, "daily_protein_target_g": 120},
        meal_summary={"total_calories": 650, "protein_g": 42, "carbs_g": 58, "fat_g": 24, "meals": []},
    )

    assert dashboard["remaining_calories"] == 1150
    assert dashboard["remaining_protein_g"] == 78
    assert "蛋白质" in dashboard["suggestion"]
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/test_meal_service.py -v
```

Expected: FAIL because meal repository and services do not exist.

- [ ] **Step 3: 实现 meal repository**

Create `fat_loss_agent/repositories/meal_repo.py`:

```python
from __future__ import annotations

from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

from fat_loss_agent.agent.schemas import PendingMealEstimate
from fat_loss_agent.repositories.db import get_connection


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MealRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def save_meal(self, user_id: str, raw_text: str, meal: PendingMealEstimate) -> int:
        now = utc_now_iso()
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO meal_logs (
                    user_id, logged_at, meal_type, raw_text, title,
                    total_calories, protein_g, carbs_g, fat_g,
                    confidence, notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    now,
                    meal.meal_type,
                    raw_text,
                    meal.title,
                    meal.total_calories,
                    meal.protein_g,
                    meal.carbs_g,
                    meal.fat_g,
                    meal.confidence,
                    meal.notes,
                    now,
                    now,
                ),
            )
            meal_log_id = int(cursor.lastrowid)
            for item in meal.items:
                conn.execute(
                    """
                    INSERT INTO meal_items (
                        meal_log_id, name, amount_text, calories,
                        protein_g, carbs_g, fat_g, confidence, notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        meal_log_id,
                        item.name,
                        item.amount_text,
                        item.calories,
                        item.protein_g,
                        item.carbs_g,
                        item.fat_g,
                        item.confidence,
                        item.notes,
                    ),
                )
        return meal_log_id

    def list_meals_for_day(self, user_id: str, target_date: date) -> list[dict[str, Any]]:
        start = datetime.combine(target_date, time.min, tzinfo=timezone.utc).isoformat()
        end = datetime.combine(target_date, time.max, tzinfo=timezone.utc).isoformat()
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM meal_logs
                WHERE user_id = ? AND logged_at BETWEEN ? AND ?
                ORDER BY logged_at ASC
                """,
                (user_id, start, end),
            ).fetchall()
        return [dict(row) for row in rows]
```

- [ ] **Step 4: 实现 meal service**

Create `fat_loss_agent/services/meal_service.py`:

```python
from __future__ import annotations

from datetime import date
from typing import Any

from fat_loss_agent.agent.schemas import PendingMealEstimate
from fat_loss_agent.repositories.meal_repo import MealRepository


class MealService:
    def __init__(self, repo: MealRepository):
        self.repo = repo

    def save_meal_log(self, user_id: str, raw_text: str, meal: PendingMealEstimate) -> int:
        return self.repo.save_meal(user_id=user_id, raw_text=raw_text, meal=meal)

    def get_today_summary(self, user_id: str) -> dict[str, Any]:
        meals = self.repo.list_meals_for_day(user_id, date.today())
        return {
            "total_calories": round(sum(row["total_calories"] for row in meals), 1),
            "protein_g": round(sum(row["protein_g"] for row in meals), 1),
            "carbs_g": round(sum(row["carbs_g"] for row in meals), 1),
            "fat_g": round(sum(row["fat_g"] for row in meals), 1),
            "meals": meals,
        }
```

- [ ] **Step 5: 实现 summary service**

Create `fat_loss_agent/services/summary_service.py`:

```python
from __future__ import annotations

from typing import Any


class SummaryService:
    @staticmethod
    def build_dashboard(profile: dict[str, Any] | None, meal_summary: dict[str, Any]) -> dict[str, Any]:
        calorie_target = float(profile["daily_calorie_target"]) if profile else 0
        protein_target = float(profile["daily_protein_target_g"]) if profile else 0
        consumed_calories = float(meal_summary.get("total_calories", 0))
        consumed_protein = float(meal_summary.get("protein_g", 0))
        remaining_calories = round(calorie_target - consumed_calories, 1)
        remaining_protein = round(protein_target - consumed_protein, 1)

        if not profile:
            suggestion = "先完成我的档案，系统才能计算今日剩余额度。"
        elif remaining_protein > 30:
            suggestion = "晚些时候优先补蛋白质，主食按剩余热量控制。"
        elif remaining_calories < 300:
            suggestion = "今日热量空间不多，后续选择低脂高蛋白食物。"
        else:
            suggestion = "今日还有一定空间，保持蛋白质和蔬菜优先。"

        return {
            "daily_calorie_target": calorie_target,
            "daily_protein_target_g": protein_target,
            "consumed_calories": consumed_calories,
            "consumed_protein_g": consumed_protein,
            "remaining_calories": remaining_calories,
            "remaining_protein_g": remaining_protein,
            "meals": meal_summary.get("meals", []),
            "suggestion": suggestion,
        }
```

- [ ] **Step 6: 运行测试确认通过**

Run:

```bash
pytest tests/test_meal_service.py -v
```

Expected: PASS.

- [ ] **Step 7: 提交餐食服务**

```bash
git add fat_loss_agent/repositories/meal_repo.py fat_loss_agent/services/meal_service.py fat_loss_agent/services/summary_service.py tests/test_meal_service.py
git commit -m "feat: add meal logging services"
```

---

### Task 6: Trace 与聊天记录

**Files:**
- Create: `fat_loss_agent/repositories/trace_repo.py`
- Create: `fat_loss_agent/repositories/chat_repo.py`
- Create: `fat_loss_agent/services/trace_service.py`
- Create: `tests/test_trace_service.py`

- [ ] **Step 1: 写失败测试**

Create `tests/test_trace_service.py`:

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/test_trace_service.py -v
```

Expected: FAIL because trace repository and service do not exist.

- [ ] **Step 3: 实现 trace repository**

Create `fat_loss_agent/repositories/trace_repo.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fat_loss_agent.repositories.db import get_connection


class TraceRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def insert(self, trace: dict[str, Any]) -> None:
        trace = {**trace, "created_at": datetime.now(timezone.utc).isoformat()}
        columns = ", ".join(trace.keys())
        bind_marks = ", ".join("?" for _ in trace)
        with get_connection(self.db_path) as conn:
            conn.execute(
                f"INSERT INTO agent_traces ({columns}) VALUES ({bind_marks})",
                list(trace.values()),
            )

    def list_recent(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM agent_traces
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]
```

- [ ] **Step 4: 实现 chat repository**

Create `fat_loss_agent/repositories/chat_repo.py`:

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fat_loss_agent.repositories.db import get_connection


class ChatRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def add_message(
        self,
        *,
        user_id: str,
        role: str,
        content: str,
        message_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO chat_messages (
                    user_id, role, content, message_type, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    role,
                    content,
                    message_type,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def list_recent(self, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM chat_messages
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return list(reversed([dict(row) for row in rows]))
```

- [ ] **Step 5: 实现 trace service**

Create `fat_loss_agent/services/trace_service.py`:

```python
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fat_loss_agent.repositories.trace_repo import TraceRepository


class TraceService:
    def __init__(self, repo: TraceRepository, jsonl_path: Path):
        self.repo = repo
        self.jsonl_path = jsonl_path

    def record_trace(
        self,
        *,
        user_id: str,
        user_input: str,
        intent: str,
        tool_calls: list[dict[str, Any]],
        llm_provider: str,
        llm_model: str,
        llm_prompt_tokens: int,
        llm_completion_tokens: int,
        llm_latency_ms: int,
        status: str,
        error_message: str,
    ) -> str:
        trace_id = str(uuid.uuid4())
        trace = {
            "user_id": user_id,
            "trace_id": trace_id,
            "user_input": user_input,
            "intent": intent,
            "tool_calls_json": json.dumps(tool_calls, ensure_ascii=False),
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "llm_prompt_tokens": llm_prompt_tokens,
            "llm_completion_tokens": llm_completion_tokens,
            "llm_latency_ms": llm_latency_ms,
            "status": status,
            "error_message": error_message,
        }
        self.repo.insert(trace)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(trace, ensure_ascii=False) + "\n")
        return trace_id
```

- [ ] **Step 6: 运行测试确认通过**

Run:

```bash
pytest tests/test_trace_service.py -v
```

Expected: PASS.

- [ ] **Step 7: 提交 trace 和聊天仓储**

```bash
git add fat_loss_agent/repositories/trace_repo.py fat_loss_agent/repositories/chat_repo.py fat_loss_agent/services/trace_service.py tests/test_trace_service.py
git commit -m "feat: add trace and chat persistence"
```

---

### Task 7: LLM 抽象与 Qwen Client

**Files:**
- Create: `fat_loss_agent/llm/base.py`
- Create: `fat_loss_agent/llm/qwen_client.py`

- [ ] **Step 1: 创建 LLM 抽象**

Create `fat_loss_agent/llm/base.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMResult:
    content_json: dict[str, Any]
    raw_text: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int


class LLMClient(Protocol):
    def generate_json(self, *, system_prompt: str, user_prompt: str, schema_name: str) -> LLMResult:
        raise NotImplementedError
```

- [ ] **Step 2: 创建 Qwen client**

Create `fat_loss_agent/llm/qwen_client.py`:

```python
from __future__ import annotations

import json
import time
from typing import Any

from openai import OpenAI

from fat_loss_agent.llm.base import LLMResult


class MissingQwenApiKeyError(RuntimeError):
    pass


class InvalidLLMJsonError(RuntimeError):
    def __init__(self, raw_text: str):
        super().__init__("Qwen returned invalid JSON")
        self.raw_text = raw_text


class QwenClient:
    def __init__(self, *, api_key: str | None, base_url: str, model: str):
        if not api_key:
            raise MissingQwenApiKeyError("QWEN_API_KEY or DASHSCOPE_API_KEY is required")
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate_json(self, *, system_prompt: str, user_prompt: str, schema_name: str) -> LLMResult:
        started = time.perf_counter()
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        raw_text = completion.choices[0].message.content or ""
        try:
            content_json: dict[str, Any] = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise InvalidLLMJsonError(raw_text) from exc

        usage = completion.usage
        return LLMResult(
            content_json=content_json,
            raw_text=raw_text,
            provider="qwen",
            model=self.model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            latency_ms=latency_ms,
        )
```

- [ ] **Step 3: 验证模块导入**

Run:

```bash
python - <<'PY'
from fat_loss_agent.llm.base import LLMResult
from fat_loss_agent.llm.qwen_client import MissingQwenApiKeyError, QwenClient

try:
    QwenClient(api_key=None, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", model="qwen-plus")
except MissingQwenApiKeyError:
    print("missing key handled")
else:
    raise SystemExit("missing key was not handled")
PY
```

Expected:

```text
missing key handled
```

- [ ] **Step 4: 提交 LLM client**

```bash
git add fat_loss_agent/llm/base.py fat_loss_agent/llm/qwen_client.py
git commit -m "feat: add qwen llm client"
```

---

### Task 8: Prompt 与 Nutrition Service

**Files:**
- Create: `fat_loss_agent/agent/prompts.py`
- Create: `fat_loss_agent/services/nutrition_service.py`
- Create: `tests/test_nutrition_service.py`

- [ ] **Step 1: 写失败测试**

Create `tests/test_nutrition_service.py`:

```python
import pytest

from fat_loss_agent.llm.base import LLMResult
from fat_loss_agent.services.nutrition_service import NutritionService


class FakeLLM:
    def __init__(self, payload):
        self.payload = payload

    def generate_json(self, *, system_prompt: str, user_prompt: str, schema_name: str) -> LLMResult:
        return LLMResult(
            content_json=self.payload,
            raw_text="{}",
            provider="fake",
            model="fake-model",
            prompt_tokens=1,
            completion_tokens=2,
            latency_ms=3,
        )


def test_estimate_meal_from_text_returns_valid_pending_meal():
    service = NutritionService(
        FakeLLM(
            {
                "is_food_log": True,
                "meal_type": "lunch",
                "title": "鸡蛋米饭",
                "items": [
                    {
                        "name": "鸡蛋",
                        "amount_text": "2个",
                        "calories": 140,
                        "protein_g": 12,
                        "carbs_g": 1,
                        "fat_g": 10,
                        "confidence": 0.8,
                        "notes": "",
                    }
                ],
                "total_calories": 140,
                "protein_g": 12,
                "carbs_g": 1,
                "fat_g": 10,
                "confidence": 0.8,
                "notes": "",
            }
        )
    )

    result = service.estimate_meal_from_text(
        text="午饭吃了两个鸡蛋",
        profile={"daily_calorie_target": 1800},
        today_summary={"total_calories": 0},
    )

    assert result.meal.title == "鸡蛋米饭"
    assert result.llm.provider == "fake"


def test_estimate_meal_rejects_invalid_schema():
    service = NutritionService(FakeLLM({"is_food_log": True, "items": []}))

    with pytest.raises(ValueError):
        service.estimate_meal_from_text(
            text="午饭吃了两个鸡蛋",
            profile={},
            today_summary={},
        )
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/test_nutrition_service.py -v
```

Expected: FAIL because nutrition service does not exist.

- [ ] **Step 3: 实现 prompt**

Create `fat_loss_agent/agent/prompts.py`:

```python
MEAL_ESTIMATION_SYSTEM_PROMPT = """你是一个谨慎的中文饮食记录营养估算助手。

你的任务是把用户的自然语言餐食描述转换成 JSON。
只输出 JSON，不要输出 Markdown，不要输出解释性段落。

规则：
1. 如果用户输入不是食物记录，返回 is_food_log=false。
2. 如果份量不明确，按常见中国饮食的一人份估算。
3. 每个食物都要给 calories、protein_g、carbs_g、fat_g、confidence、notes。
4. confidence 取 0 到 1，份量越不明确置信度越低。
5. notes 写清楚关键估算假设。
6. 不做医疗诊断，不给疾病治疗建议。

JSON 字段：
is_food_log, meal_type, title, items, total_calories, protein_g, carbs_g, fat_g, confidence, notes
items 字段：
name, amount_text, calories, protein_g, carbs_g, fat_g, confidence, notes
"""


def build_meal_estimation_user_prompt(text: str, profile: dict, today_summary: dict) -> str:
    return f"""用户餐食输入：
{text}

用户目标上下文：
{profile}

今日已记录摘要：
{today_summary}

请输出符合 schema 的 JSON。"""
```

- [ ] **Step 4: 实现 nutrition service**

Create `fat_loss_agent/services/nutrition_service.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from fat_loss_agent.agent.prompts import MEAL_ESTIMATION_SYSTEM_PROMPT, build_meal_estimation_user_prompt
from fat_loss_agent.agent.schemas import PendingMealEstimate
from fat_loss_agent.llm.base import LLMClient, LLMResult


@dataclass(frozen=True)
class MealEstimationResult:
    meal: PendingMealEstimate
    llm: LLMResult


class NutritionService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def estimate_meal_from_text(
        self,
        *,
        text: str,
        profile: dict[str, Any] | None,
        today_summary: dict[str, Any],
    ) -> MealEstimationResult:
        llm_result = self.llm_client.generate_json(
            system_prompt=MEAL_ESTIMATION_SYSTEM_PROMPT,
            user_prompt=build_meal_estimation_user_prompt(text, profile or {}, today_summary),
            schema_name="PendingMealEstimate",
        )
        try:
            meal = PendingMealEstimate.model_validate(llm_result.content_json)
        except ValidationError as exc:
            raise ValueError(f"invalid meal estimate schema: {exc}") from exc
        return MealEstimationResult(meal=meal, llm=llm_result)
```

- [ ] **Step 5: 运行测试确认通过**

Run:

```bash
pytest tests/test_nutrition_service.py -v
```

Expected: PASS.

- [ ] **Step 6: 提交 nutrition service**

```bash
git add fat_loss_agent/agent/prompts.py fat_loss_agent/services/nutrition_service.py tests/test_nutrition_service.py
git commit -m "feat: add nutrition estimation service"
```

---

### Task 9: Agent Orchestrator

**Files:**
- Create: `fat_loss_agent/agent/orchestrator.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: 写失败测试**

Create `tests/test_orchestrator.py`:

```python
from fat_loss_agent.agent.orchestrator import AgentOrchestrator
from fat_loss_agent.agent.schemas import MealItemEstimate, PendingMealEstimate
from fat_loss_agent.llm.base import LLMResult
from fat_loss_agent.services.nutrition_service import MealEstimationResult


class FakeProfileService:
    def get_profile(self, user_id):
        return {"daily_calorie_target": 1800, "daily_protein_target_g": 120}


class FakeMealService:
    def get_today_summary(self, user_id):
        return {"total_calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "meals": []}


class FakeNutritionService:
    def estimate_meal_from_text(self, *, text, profile, today_summary):
        return MealEstimationResult(
            meal=PendingMealEstimate(
                is_food_log=True,
                meal_type="lunch",
                title="鸡蛋",
                items=[
                    MealItemEstimate(
                        name="鸡蛋",
                        amount_text="2个",
                        calories=140,
                        protein_g=12,
                        carbs_g=1,
                        fat_g=10,
                        confidence=0.8,
                        notes="",
                    )
                ],
                total_calories=140,
                protein_g=12,
                carbs_g=1,
                fat_g=10,
                confidence=0.8,
                notes="",
            ),
            llm=LLMResult(
                content_json={},
                raw_text="{}",
                provider="fake",
                model="fake-model",
                prompt_tokens=1,
                completion_tokens=2,
                latency_ms=3,
            ),
        )


class FakeTraceService:
    def __init__(self):
        self.calls = []

    def record_trace(self, **kwargs):
        self.calls.append(kwargs)
        return "trace-1"


def test_orchestrator_returns_pending_meal_and_records_trace():
    trace_service = FakeTraceService()
    orchestrator = AgentOrchestrator(
        profile_service=FakeProfileService(),
        meal_service=FakeMealService(),
        nutrition_service=FakeNutritionService(),
        trace_service=trace_service,
    )

    result = orchestrator.handle_meal_text("local_user", "午饭吃了两个鸡蛋")

    assert result.meal.title == "鸡蛋"
    assert result.trace_id == "trace-1"
    assert trace_service.calls[0]["intent"] == "meal_log"
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/test_orchestrator.py -v
```

Expected: FAIL because orchestrator does not exist.

- [ ] **Step 3: 实现 orchestrator**

Create `fat_loss_agent/agent/orchestrator.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fat_loss_agent.agent.schemas import PendingMealEstimate


@dataclass(frozen=True)
class OrchestratorMealResult:
    meal: PendingMealEstimate
    trace_id: str


class AgentOrchestrator:
    def __init__(self, *, profile_service: Any, meal_service: Any, nutrition_service: Any, trace_service: Any):
        self.profile_service = profile_service
        self.meal_service = meal_service
        self.nutrition_service = nutrition_service
        self.trace_service = trace_service

    def handle_meal_text(self, user_id: str, text: str) -> OrchestratorMealResult:
        profile = self.profile_service.get_profile(user_id)
        today_summary = self.meal_service.get_today_summary(user_id)
        tool_calls = [
            {"name": "profile_service.get_profile"},
            {"name": "meal_service.get_today_summary"},
            {"name": "nutrition_service.estimate_meal_from_text"},
        ]
        try:
            estimation = self.nutrition_service.estimate_meal_from_text(
                text=text,
                profile=profile,
                today_summary=today_summary,
            )
            trace_id = self.trace_service.record_trace(
                user_id=user_id,
                user_input=text,
                intent="meal_log",
                tool_calls=tool_calls,
                llm_provider=estimation.llm.provider,
                llm_model=estimation.llm.model,
                llm_prompt_tokens=estimation.llm.prompt_tokens,
                llm_completion_tokens=estimation.llm.completion_tokens,
                llm_latency_ms=estimation.llm.latency_ms,
                status="success",
                error_message="",
            )
            return OrchestratorMealResult(meal=estimation.meal, trace_id=trace_id)
        except Exception as exc:
            self.trace_service.record_trace(
                user_id=user_id,
                user_input=text,
                intent="meal_log",
                tool_calls=tool_calls,
                llm_provider="unknown",
                llm_model="unknown",
                llm_prompt_tokens=0,
                llm_completion_tokens=0,
                llm_latency_ms=0,
                status="error",
                error_message=str(exc),
            )
            raise
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
pytest tests/test_orchestrator.py -v
```

Expected: PASS.

- [ ] **Step 5: 提交 orchestrator**

```bash
git add fat_loss_agent/agent/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: add meal logging orchestrator"
```

---

### Task 10: Streamlit 档案页与应用入口

**Files:**
- Create: `fat_loss_agent/app.py`
- Create: `fat_loss_agent/pages/profile_page.py`

- [ ] **Step 1: 实现应用入口和依赖组装**

Create `fat_loss_agent/app.py`:

```python
from __future__ import annotations

import streamlit as st

from fat_loss_agent.config import DEFAULT_USER_ID, load_config
from fat_loss_agent.pages.meal_chat_page import render_meal_chat_page
from fat_loss_agent.pages.profile_page import render_profile_page
from fat_loss_agent.repositories.db import init_db


def main() -> None:
    config = load_config()
    init_db(config.db_path)
    st.set_page_config(page_title="个人减脂 Agent", page_icon="🍽️", layout="wide")
    st.sidebar.title("个人减脂 Agent")
    page = st.sidebar.radio("页面", ["饮食记录", "我的档案"])
    if page == "我的档案":
        render_profile_page(config=config, user_id=DEFAULT_USER_ID)
    else:
        render_meal_chat_page(config=config, user_id=DEFAULT_USER_ID)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 实现档案页**

Create `fat_loss_agent/pages/profile_page.py`:

```python
from __future__ import annotations

import streamlit as st

from fat_loss_agent.config import AppConfig
from fat_loss_agent.repositories.profile_repo import ProfileRepository
from fat_loss_agent.services.profile_service import ProfileService


SEX_OPTIONS = {"男": "male", "女": "female"}
ACTIVITY_OPTIONS = {
    "久坐": "sedentary",
    "轻度活动": "light",
    "中等活动": "moderate",
    "高活动": "active",
}
SPEED_OPTIONS = {"保守": "conservative", "标准": "standard", "激进": "aggressive"}


def render_profile_page(*, config: AppConfig, user_id: str) -> None:
    service = ProfileService(ProfileRepository(config.db_path))
    existing = service.get_profile(user_id) or {}

    st.title("我的档案")
    with st.form("profile_form"):
        nickname = st.text_input("昵称", value=existing.get("nickname", ""))
        sex_label = st.selectbox("性别", list(SEX_OPTIONS.keys()), index=0 if existing.get("sex") != "female" else 1)
        age = st.number_input("年龄", min_value=10, max_value=100, value=int(existing.get("age", 30)))
        height_cm = st.number_input("身高 cm", min_value=100.0, max_value=230.0, value=float(existing.get("height_cm", 175.0)))
        current_weight_kg = st.number_input("当前体重 kg", min_value=30.0, max_value=250.0, value=float(existing.get("current_weight_kg", 80.0)))
        target_weight_kg = st.number_input("目标体重 kg", min_value=30.0, max_value=250.0, value=float(existing.get("target_weight_kg", 72.0)))
        activity_label = st.selectbox("活动水平", list(ACTIVITY_OPTIONS.keys()))
        speed_label = st.selectbox("减脂速度", list(SPEED_OPTIONS.keys()), index=1)
        diet_preferences = st.text_area("饮食偏好或忌口", value=existing.get("diet_preferences", ""))
        submitted = st.form_submit_button("保存档案")

    if submitted:
        saved = service.save_profile(
            user_id=user_id,
            nickname=nickname or "本地用户",
            sex=SEX_OPTIONS[sex_label],
            age=int(age),
            height_cm=float(height_cm),
            current_weight_kg=float(current_weight_kg),
            target_weight_kg=float(target_weight_kg),
            activity_level=ACTIVITY_OPTIONS[activity_label],
            fat_loss_speed=SPEED_OPTIONS[speed_label],
            diet_preferences=diet_preferences,
        )
        st.success("档案已保存")
        st.metric("每日热量目标", f"{int(saved['daily_calorie_target'])} kcal")
        st.metric("每日蛋白质目标", f"{int(saved['daily_protein_target_g'])} g")
        st.info(saved["goal_explanation"])
```

- [ ] **Step 3: 创建临时饮食页骨架以保证 app 可导入**

Create `fat_loss_agent/pages/meal_chat_page.py`:

```python
from __future__ import annotations

import streamlit as st

from fat_loss_agent.config import AppConfig


def render_meal_chat_page(*, config: AppConfig, user_id: str) -> None:
    st.title("饮食记录")
    st.info("饮食记录页面将在下一任务接入 Agent。")
```

- [ ] **Step 4: 验证 app 导入**

Run:

```bash
python - <<'PY'
from fat_loss_agent.app import main
print("app import ok")
PY
```

Expected:

```text
app import ok
```

- [ ] **Step 5: 提交档案 UI**

```bash
git add fat_loss_agent/app.py fat_loss_agent/pages/profile_page.py fat_loss_agent/pages/meal_chat_page.py
git commit -m "feat: add streamlit profile page"
```

---

### Task 11: Streamlit 饮食记录页

**Files:**
- Modify: `fat_loss_agent/pages/meal_chat_page.py`

- [ ] **Step 1: 实现依赖组装 helper**

Replace `fat_loss_agent/pages/meal_chat_page.py` with:

```python
from __future__ import annotations

import streamlit as st

from fat_loss_agent.agent.orchestrator import AgentOrchestrator
from fat_loss_agent.agent.schemas import MealItemEstimate, PendingMealEstimate
from fat_loss_agent.config import AppConfig
from fat_loss_agent.llm.qwen_client import MissingQwenApiKeyError, QwenClient
from fat_loss_agent.repositories.chat_repo import ChatRepository
from fat_loss_agent.repositories.meal_repo import MealRepository
from fat_loss_agent.repositories.profile_repo import ProfileRepository
from fat_loss_agent.repositories.trace_repo import TraceRepository
from fat_loss_agent.services.meal_service import MealService
from fat_loss_agent.services.nutrition_service import NutritionService
from fat_loss_agent.services.profile_service import ProfileService
from fat_loss_agent.services.summary_service import SummaryService
from fat_loss_agent.services.trace_service import TraceService


def build_services(config: AppConfig):
    profile_service = ProfileService(ProfileRepository(config.db_path))
    meal_service = MealService(MealRepository(config.db_path))
    trace_service = TraceService(TraceRepository(config.db_path), config.trace_log_path)
    qwen_client = QwenClient(
        api_key=config.qwen_api_key,
        base_url=config.qwen_base_url,
        model=config.qwen_model,
    )
    nutrition_service = NutritionService(qwen_client)
    orchestrator = AgentOrchestrator(
        profile_service=profile_service,
        meal_service=meal_service,
        nutrition_service=nutrition_service,
        trace_service=trace_service,
    )
    return profile_service, meal_service, orchestrator
```

- [ ] **Step 2: 实现 pending meal 编辑 UI**

Append to `fat_loss_agent/pages/meal_chat_page.py`:

```python
def edit_pending_meal(meal: PendingMealEstimate) -> PendingMealEstimate:
    st.subheader("待确认餐食")
    meal_type = st.selectbox(
        "餐次",
        ["breakfast", "lunch", "dinner", "snack", "unknown"],
        index=["breakfast", "lunch", "dinner", "snack", "unknown"].index(meal.meal_type),
    )
    title = st.text_input("标题", value=meal.title)
    total_calories = st.number_input("总热量 kcal", min_value=0.0, value=float(meal.total_calories))
    protein_g = st.number_input("蛋白质 g", min_value=0.0, value=float(meal.protein_g))
    carbs_g = st.number_input("碳水 g", min_value=0.0, value=float(meal.carbs_g))
    fat_g = st.number_input("脂肪 g", min_value=0.0, value=float(meal.fat_g))
    confidence = st.slider("整体置信度", min_value=0.0, max_value=1.0, value=float(meal.confidence))
    notes = st.text_area("备注", value=meal.notes)

    edited_items: list[MealItemEstimate] = []
    for index, item in enumerate(meal.items):
        with st.expander(f"食物 {index + 1}: {item.name}", expanded=True):
            name = st.text_input("名称", value=item.name, key=f"item_name_{index}")
            amount_text = st.text_input("份量", value=item.amount_text, key=f"item_amount_{index}")
            calories = st.number_input("热量 kcal", min_value=0.0, value=float(item.calories), key=f"item_cal_{index}")
            item_protein = st.number_input("蛋白质 g", min_value=0.0, value=float(item.protein_g), key=f"item_protein_{index}")
            item_carbs = st.number_input("碳水 g", min_value=0.0, value=float(item.carbs_g), key=f"item_carbs_{index}")
            item_fat = st.number_input("脂肪 g", min_value=0.0, value=float(item.fat_g), key=f"item_fat_{index}")
            item_confidence = st.slider("置信度", 0.0, 1.0, float(item.confidence), key=f"item_conf_{index}")
            item_notes = st.text_area("备注", value=item.notes, key=f"item_notes_{index}")
            edited_items.append(
                MealItemEstimate(
                    name=name,
                    amount_text=amount_text,
                    calories=calories,
                    protein_g=item_protein,
                    carbs_g=item_carbs,
                    fat_g=item_fat,
                    confidence=item_confidence,
                    notes=item_notes,
                )
            )

    return PendingMealEstimate(
        is_food_log=True,
        meal_type=meal_type,
        title=title,
        items=edited_items,
        total_calories=total_calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        confidence=confidence,
        notes=notes,
    )
```

- [ ] **Step 3: 实现主渲染函数**

Append to `fat_loss_agent/pages/meal_chat_page.py`:

```python
def render_dashboard(profile_service: ProfileService, meal_service: MealService, user_id: str) -> None:
    profile = profile_service.get_profile(user_id)
    meal_summary = meal_service.get_today_summary(user_id)
    dashboard = SummaryService.build_dashboard(profile, meal_summary)

    st.subheader("今日摘要")
    col1, col2 = st.columns(2)
    col1.metric("剩余热量", f"{dashboard['remaining_calories']:.0f} kcal")
    col2.metric("还差蛋白质", f"{dashboard['remaining_protein_g']:.0f} g")
    st.caption(dashboard["suggestion"])
    if dashboard["meals"]:
        st.write("今日已记录")
        for meal in dashboard["meals"]:
            st.write(f"- {meal['title']}：{meal['total_calories']:.0f} kcal，蛋白质 {meal['protein_g']:.0f} g")


def render_meal_chat_page(*, config: AppConfig, user_id: str) -> None:
    st.title("饮食记录")
    left, right = st.columns([2, 1])

    with right:
        profile_service = ProfileService(ProfileRepository(config.db_path))
        meal_service = MealService(MealRepository(config.db_path))
        render_dashboard(profile_service, meal_service, user_id)

    with left:
        text = st.chat_input("输入你吃了什么，例如：午饭吃了两个鸡蛋、一碗米饭、一份牛肉")
        if text:
            ChatRepository(config.db_path).add_message(
                user_id=user_id,
                role="user",
                content=text,
                message_type="user_text",
            )
            try:
                profile_service, meal_service, orchestrator = build_services(config)
                result = orchestrator.handle_meal_text(user_id, text)
                st.session_state["pending_meal"] = result.meal.model_dump()
                st.session_state["pending_raw_text"] = text
                st.success(f"已生成估算，trace_id={result.trace_id}")
            except MissingQwenApiKeyError:
                st.error("未配置 QWEN_API_KEY 或 DASHSCOPE_API_KEY，无法调用 Qwen。")
            except Exception as exc:
                st.error(f"估算失败：{exc}")

        pending = st.session_state.get("pending_meal")
        if pending:
            meal = PendingMealEstimate.model_validate(pending)
            edited = edit_pending_meal(meal)
            if st.button("确认保存"):
                meal_service = MealService(MealRepository(config.db_path))
                meal_service.save_meal_log(user_id, st.session_state.get("pending_raw_text", ""), edited)
                ChatRepository(config.db_path).add_message(
                    user_id=user_id,
                    role="assistant",
                    content=f"已保存：{edited.title}",
                    message_type="assistant_text",
                    metadata=edited.model_dump(),
                )
                st.session_state.pop("pending_meal", None)
                st.session_state.pop("pending_raw_text", None)
                st.success("餐食已保存")
                st.rerun()
```

- [ ] **Step 4: 验证 app 导入**

Run:

```bash
python - <<'PY'
from fat_loss_agent.pages.meal_chat_page import render_meal_chat_page
print("meal page import ok")
PY
```

Expected:

```text
meal page import ok
```

- [ ] **Step 5: 提交饮食记录 UI**

```bash
git add fat_loss_agent/pages/meal_chat_page.py
git commit -m "feat: add meal chat streamlit page"
```

---

### Task 12: 全量测试与人工验收

**Files:**
- Modify only if verification finds concrete defects.

- [ ] **Step 1: 运行全部单元测试**

Run:

```bash
pytest -v
```

Expected: all tests PASS.

- [ ] **Step 2: 验证 Streamlit 应用可启动**

Run:

```bash
streamlit run fat_loss_agent/app.py
```

Expected:

```text
Local URL: http://localhost:8501
```

- [ ] **Step 3: 手动验收无 API key 场景**

Without `QWEN_API_KEY` or `DASHSCOPE_API_KEY`:

1. Open `http://localhost:8501`.
2. Go to `我的档案`.
3. Save a profile.
4. Go to `饮食记录`.
5. Submit `午饭吃了两个鸡蛋、一碗米饭`.
6. Confirm the UI shows a missing API key message and the app does not crash.

- [ ] **Step 4: 手动验收有 API key 场景**

With a valid API key:

```bash
export QWEN_API_KEY="your-key"
streamlit run fat_loss_agent/app.py
```

Then verify:

1. `我的档案` can save profile data.
2. `饮食记录` accepts text input.
3. Qwen returns a structured pending meal.
4. Pending meal values can be edited.
5. Confirm save writes the meal.
6. Today's summary updates remaining calories and protein.
7. Refreshing the page preserves profile and meal data.
8. `fat_loss_agent/traces/agent_logs.jsonl` contains a trace line.

- [ ] **Step 5: 最终提交验收修复**

If verification required code fixes:

```bash
git add fat_loss_agent tests
git commit -m "fix: stabilize fat loss agent mvp"
```

If no fixes were required:

```bash
git status --short
```

Expected: no uncommitted changes except local `.env` or generated ignored files.

---

## Plan Self-Review

Spec coverage:

- 建档页面：Task 4 and Task 10.
- 文本饮食记录：Task 8, Task 9, and Task 11.
- Qwen 默认 Provider：Task 7 and Task 8.
- SQLite 表结构：Task 3.
- 手动修正后保存：Task 11.
- 今日摘要：Task 5 and Task 11.
- Trace 记录：Task 6 and Task 9.
- 单用户但预留 `user_id`：Task 3 through Task 6.
- 不做登录、照片、RAG、周复盘、FastAPI、LangGraph、Docker：plan does not add these features.

Placeholder scan:

- No unresolved markers or unspecified implementation steps.

Type consistency:

- `PendingMealEstimate`, `MealItemEstimate`, `LLMResult`, and `MealEstimationResult` are introduced before use.
- `MealService.save_meal_log`, `MealService.get_today_summary`, `ProfileService.get_profile`, and `TraceService.record_trace` signatures match orchestrator usage.
