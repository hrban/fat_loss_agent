# Meal Photo Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Qwen-backed single-photo meal recognition path that produces an editable pending meal and saves confirmed photo meal metadata to SQLite.

**Architecture:** Keep the existing monolith. Add a focused `PhotoService`, a focused `VisionNutritionService`, a multimodal method on `QwenClient`, and two migration-safe `meal_logs` columns. The UI uploads one image, stores it locally, asks the orchestrator for a `PendingMealEstimate`, then reuses the current manual correction and save flow.

**Tech Stack:** Python 3.11+, Streamlit, SQLite, Pydantic, OpenAI-compatible Qwen API, pytest.

---

### Task 1: SQLite Photo Metadata

**Files:**
- Modify: `fat_loss_agent/repositories/db.py`
- Modify: `fat_loss_agent/repositories/meal_repo.py`
- Modify: `fat_loss_agent/services/meal_service.py`
- Test: `tests/test_db.py`
- Test: `tests/test_meal_service.py`

- [ ] **Step 1: Write failing DB and meal service tests**

Add assertions that `meal_logs` has `input_type` and `photo_path`, and that saving a photo meal persists both fields.

```python
def test_init_db_adds_meal_photo_metadata_columns(tmp_path):
    db_path = tmp_path / "app.db"
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(meal_logs)").fetchall()}

    assert {"input_type", "photo_path"}.issubset(columns)
```

```python
def test_save_photo_meal_persists_photo_metadata(tmp_path):
    db_path = tmp_path / "app.db"
    init_db(db_path)
    service = MealService(MealRepository(db_path))
    meal = build_test_meal()

    service.save_meal_log("local_user", "照片记录：午饭", meal, input_type="photo", photo_path="/tmp/lunch.jpg")
    summary = service.get_today_summary("local_user")

    assert summary["meals"][0]["input_type"] == "photo"
    assert summary["meals"][0]["photo_path"] == "/tmp/lunch.jpg"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_db.py::test_init_db_adds_meal_photo_metadata_columns tests/test_meal_service.py::test_save_photo_meal_persists_photo_metadata -v`

Expected: FAIL because the columns and keyword arguments do not exist yet.

- [ ] **Step 3: Implement minimal DB and repository support**

Add `input_type` and `photo_path` to the table DDL, add migration helper logic after `CREATE TABLE`, and extend `MealRepository.save_meal()` plus `MealService.save_meal_log()` with optional keyword arguments defaulting to text behavior.

- [ ] **Step 4: Run the focused tests**

Run: `.venv/bin/pytest tests/test_db.py tests/test_meal_service.py -v`

Expected: PASS.

### Task 2: Photo Storage

**Files:**
- Create: `fat_loss_agent/services/photo_service.py`
- Test: `tests/test_photo_service.py`

- [ ] **Step 1: Write failing photo service test**

```python
def test_save_upload_stores_image_with_safe_name(tmp_path):
    service = PhotoService(tmp_path / "photos")

    saved_path = service.save_upload(
        user_id="local_user",
        original_filename="午饭.JPG",
        content=b"fake-image-bytes",
    )

    assert saved_path.exists()
    assert saved_path.suffix == ".jpg"
    assert saved_path.parent == tmp_path / "photos"
    assert saved_path.read_bytes() == b"fake-image-bytes"
    assert "local_user" in saved_path.name
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_photo_service.py -v`

Expected: FAIL because `PhotoService` does not exist.

- [ ] **Step 3: Implement minimal photo saving**

Create `PhotoService` with allowed suffixes `.jpg`, `.jpeg`, `.png`, `.webp`; normalize `.jpeg` to `.jpg`; use UTC timestamp and a content hash prefix in the filename; create the destination directory.

- [ ] **Step 4: Run photo service test**

Run: `.venv/bin/pytest tests/test_photo_service.py -v`

Expected: PASS.

### Task 3: Vision Nutrition Estimation

**Files:**
- Modify: `fat_loss_agent/llm/base.py`
- Modify: `fat_loss_agent/llm/qwen_client.py`
- Modify: `fat_loss_agent/agent/prompts.py`
- Create: `fat_loss_agent/services/vision_nutrition_service.py`
- Test: `tests/test_vision_nutrition_service.py`

- [ ] **Step 1: Write failing vision service tests**

Test that `VisionNutritionService.estimate_meal_from_photo()` calls `generate_json_with_image()` with the photo path and validates the JSON into `PendingMealEstimate`. Add a second test that invalid schema raises `ValueError`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_vision_nutrition_service.py -v`

Expected: FAIL because the service and protocol method do not exist.

- [ ] **Step 3: Implement minimal vision service and multimodal client method**

Add `generate_json_with_image()` to the LLM protocol and `QwenClient`. Encode the image file as a base64 data URL and send it with the text prompt in OpenAI-compatible `image_url` content format.

- [ ] **Step 4: Run vision tests**

Run: `.venv/bin/pytest tests/test_vision_nutrition_service.py -v`

Expected: PASS.

### Task 4: Orchestrator Photo Path

**Files:**
- Modify: `fat_loss_agent/agent/orchestrator.py`
- Test: `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing orchestrator test**

Add a fake nutrition service method `estimate_meal_from_photo()` and assert that `handle_meal_photo("local_user", "/tmp/lunch.jpg", "少油")` returns a meal and records intent `meal_photo_log`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_orchestrator.py::test_orchestrator_handles_photo_meal_and_records_trace -v`

Expected: FAIL because `handle_meal_photo()` does not exist.

- [ ] **Step 3: Implement orchestrator method**

Mirror the text method, but pass `photo_path` and `note` to `VisionNutritionService`, use intent `meal_photo_log`, and include the vision tool name in trace tool calls.

- [ ] **Step 4: Run orchestrator tests**

Run: `.venv/bin/pytest tests/test_orchestrator.py -v`

Expected: PASS.

### Task 5: Streamlit Upload Flow

**Files:**
- Modify: `fat_loss_agent/config.py`
- Modify: `fat_loss_agent/pages/meal_chat_page.py`

- [ ] **Step 1: Extend config**

Add `photo_dir: Path` and `qwen_vision_model: str` to `AppConfig`. Default `PHOTO_DIR` to `fat_loss_agent/data/photos`; default `QWEN_VISION_MODEL` to `QWEN_MODEL`.

- [ ] **Step 2: Wire services**

Instantiate one text `QwenClient` for `NutritionService` and one vision `QwenClient` for `VisionNutritionService`. Pass both services into `AgentOrchestrator`.

- [ ] **Step 3: Add UI controls**

Add `st.file_uploader("上传餐食照片", type=["jpg", "jpeg", "png", "webp"])`, an optional note input, and a button that saves the upload through `PhotoService` then calls `handle_meal_photo()`.

- [ ] **Step 4: Reuse pending meal confirmation**

Store `pending_input_type` and `pending_photo_path` in `st.session_state`. On save, call:

```python
meal_service.save_meal_log(
    user_id,
    st.session_state.get("pending_raw_text", ""),
    edited,
    input_type=st.session_state.get("pending_input_type", "text"),
    photo_path=st.session_state.get("pending_photo_path", ""),
)
```

### Task 6: Verification

**Files:**
- All changed files

- [ ] **Step 1: Run full tests**

Run: `.venv/bin/pytest -v`

Expected: all tests pass.

- [ ] **Step 2: Start Streamlit**

Run from the worktree root: `.venv/bin/streamlit run fat_loss_agent/app.py --server.port 8501`

Expected: server listens on `http://localhost:8501/`.

- [ ] **Step 3: Browser smoke check**

Open `http://localhost:8501/`, confirm the 饮食记录 page renders, shows text input, photo upload, optional note, and today's dashboard without layout errors.

- [ ] **Step 4: Commit implementation**

Stage only source, tests, and docs. Do not stage `.env.example` or generated SQLite files.

```bash
git add docs/superpowers/specs/2026-06-16-meal-photo-input-design.md docs/superpowers/plans/2026-06-16-meal-photo-input.md fat_loss_agent tests
git commit -m "feat: add meal photo recognition flow"
```
