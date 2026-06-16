# Fat Loss Agent MVP Design

Date: 2026-06-16

## Context

This project starts from an empty repository. The first goal is not to build a large platform, but to build a personal fat-loss agent that the owner can actually use every day.

The MVP uses a lightweight Python monolith:

- Streamlit for the local UI
- SQLite for local persistence
- A hand-written agent orchestrator
- Qwen API as the default LLM provider
- Explicit Python services and repositories instead of microservices or LangGraph

The first usable workflow is diet logging:

```text
Enter what I ate -> estimate nutrition -> manually correct -> save -> see today's remaining budget
```

## Product Scope

### In Scope

The MVP includes two user-facing pages.

#### Profile Page

The profile page creates and updates the default local user's fat-loss profile. The first version is single-user, but all persisted business data includes `user_id` so the project can later evolve into multi-user mode.

The default first-version user is:

```text
local_user
```

The profile captures:

- Nickname
- Sex
- Age
- Height in centimeters
- Current weight in kilograms
- Target weight in kilograms
- Activity level
- Fat-loss speed: conservative, standard, or aggressive
- Optional diet preferences or restrictions

After saving the profile, the app calculates and stores:

- Estimated BMR
- Daily calorie target
- Daily protein target
- A short goal explanation

The calculation should be explainable and conservative. It does not need to be medically precise in the MVP.

#### Diet Logging Page

The diet logging page is the main experience.

The user types a natural-language meal description, for example:

```text
午饭吃了两个鸡蛋、一碗米饭、一份牛肉
```

The agent returns a pending meal card. The card shows:

- Meal type
- Title
- Food item list
- Amount assumptions
- Estimated calories
- Estimated protein
- Estimated carbs
- Estimated fat
- Confidence
- Notes

The user can manually correct the values before saving. The app only writes confirmed meals to SQLite.

The page also shows today's summary:

- Daily calorie target, consumed calories, and remaining calories
- Daily protein target, consumed protein, and remaining protein
- Meal list for today
- A short practical suggestion for the rest of the day

### Explicitly Out of Scope

The MVP does not include:

- Login or registration
- Multi-user UI
- Food photo recognition
- RAG knowledge base
- Weekly review
- FastAPI
- LangGraph
- Docker
- Scheduled jobs
- Complex permissions
- Training plan generation

These are extension points after the diet logging workflow is stable.

## Recommended Architecture

Use the lightweight version of a layered Python monolith.

```text
fat_loss_agent/
  app.py
  pages/
    profile_page.py
    meal_chat_page.py
  agent/
    orchestrator.py
    prompts.py
    schemas.py
  llm/
    base.py
    qwen_client.py
  services/
    profile_service.py
    goal_service.py
    meal_service.py
    nutrition_service.py
    summary_service.py
    trace_service.py
  repositories/
    db.py
    profile_repo.py
    meal_repo.py
    chat_repo.py
    trace_repo.py
  data/
    app.db
  traces/
    agent_logs.jsonl
```

### Module Responsibilities

#### `app.py`

Starts the Streamlit app, configures navigation, initializes the database, and wires dependencies.

#### `pages/`

Owns Streamlit UI only. Pages do not execute SQL and do not call Qwen directly.

#### `agent/orchestrator.py`

Owns the first agent workflow. The orchestrator is intentionally small and explicit.

For a text meal log, it:

1. Receives `user_id` and user input.
2. Reads profile context.
3. Reads today's current nutrition summary.
4. Calls the nutrition service to estimate the meal.
5. Returns a pending meal object to the page.
6. Records the trace.

The orchestrator does not directly write SQL. Confirmed saving happens through `meal_service`.

#### `llm/`

Owns provider-specific LLM details.

The MVP default provider is Qwen. The business layer depends on a small LLM interface, not on Qwen-specific request code. A later DeepSeek client can implement the same interface.

#### `services/`

Owns business behavior:

- `profile_service`: create, read, and update the default user profile.
- `goal_service`: calculate calorie and protein targets from profile data.
- `nutrition_service`: ask Qwen to convert a natural-language meal into structured nutrition JSON.
- `meal_service`: save confirmed meals, read meals, and calculate meal totals.
- `summary_service`: calculate today's dashboard values and practical suggestions.
- `trace_service`: persist agent inputs, tool calls, model metadata, errors, and final status.

#### `repositories/`

Owns SQLite CRUD only. Repositories should not contain business rules.

## Data Flow

### Text Meal Logging

```text
Streamlit text input
  -> orchestrator.handle_meal_text(user_id, text)
  -> profile_service.get_profile(user_id)
  -> meal_service.get_today_summary(user_id)
  -> nutrition_service.estimate_meal_from_text(text, profile, today_summary)
  -> qwen_client.generate_json(...)
  -> nutrition_service validates structured JSON
  -> orchestrator returns pending_meal
  -> user manually corrects values
  -> meal_service.save_meal_log(user_id, confirmed_meal)
  -> summary_service.get_today_dashboard(user_id)
  -> trace_service records database trace and JSONL trace
```

### Design Rules

- The UI does not call the LLM directly.
- The agent does not write SQL directly.
- The LLM does not decide whether to save data.
- Qwen output must be parsed and schema-validated before use.
- Saving requires user confirmation.
- Trace logging is part of the MVP, not a later enhancement.

## Database Design

SQLite is enough for the personal MVP. All business tables include `user_id`, even though the first version uses only `local_user`.

### `profiles`

Stores user profile and calculated targets.

```text
id
user_id
nickname
sex
age
height_cm
current_weight_kg
target_weight_kg
activity_level
fat_loss_speed
diet_preferences
bmr_kcal
daily_calorie_target
daily_protein_target_g
goal_explanation
created_at
updated_at
```

### `meal_logs`

Stores one confirmed meal.

```text
id
user_id
logged_at
meal_type
raw_text
title
total_calories
protein_g
carbs_g
fat_g
confidence
notes
created_at
updated_at
```

### `meal_items`

Stores food-level details inside a meal.

```text
id
meal_log_id
name
amount_text
calories
protein_g
carbs_g
fat_g
confidence
notes
```

### `chat_messages`

Stores chat history so the page can survive refreshes.

```text
id
user_id
role
content
message_type
metadata_json
created_at
```

Allowed first-version `message_type` values:

- `user_text`
- `assistant_text`
- `pending_meal`
- `system_event`

### `agent_traces`

Stores trace summaries in SQLite. Full raw traces are also written to `traces/agent_logs.jsonl`.

```text
id
user_id
trace_id
user_input
intent
tool_calls_json
llm_provider
llm_model
llm_prompt_tokens
llm_completion_tokens
llm_latency_ms
status
error_message
created_at
```

### Not Persisted in MVP

Do not create a `daily_summaries` table in the MVP. Today's summary should be calculated from confirmed meal logs at runtime to avoid cache consistency problems.

## Pending Meal Shape

Qwen returns a structure equivalent to:

```json
{
  "is_food_log": true,
  "meal_type": "lunch",
  "title": "鸡蛋、米饭和牛肉",
  "items": [
    {
      "name": "鸡蛋",
      "amount_text": "2个",
      "calories": 140,
      "protein_g": 12,
      "carbs_g": 1,
      "fat_g": 10,
      "confidence": 0.8,
      "notes": "按普通水煮蛋估算"
    }
  ],
  "total_calories": 650,
  "protein_g": 42,
  "carbs_g": 58,
  "fat_g": 24,
  "confidence": 0.7,
  "notes": "米饭和牛肉份量未明确，按常见一人份估算"
}
```

The service layer validates the parsed object before it reaches the editable confirmation UI.

## LLM Provider Design

### Configuration

The MVP reads Qwen configuration from environment variables:

```text
QWEN_API_KEY
QWEN_BASE_URL
QWEN_MODEL
```

`QWEN_API_KEY` is required for model calls and must not be committed. `QWEN_BASE_URL` and `QWEN_MODEL` can have local defaults.

### LLM Interface

The application defines a small provider interface:

```text
LLMClient.generate_json(
  system_prompt: str,
  user_prompt: str,
  schema_name: str
) -> LLMResult
```

`LLMResult` includes:

```text
content_json
raw_text
provider
model
prompt_tokens
completion_tokens
latency_ms
```

### Qwen's MVP Responsibility

Qwen only converts natural-language meal descriptions into structured nutrition estimates.

It does not:

- Save records
- Modify profile or goals
- Calculate remaining budget
- Make database decisions

The prompt should require:

- JSON-only output
- `is_food_log=false` when the input is not a food log
- Common one-person Chinese diet assumptions when amounts are vague
- Calories, protein, carbs, fat, confidence, and notes for each item
- Clear assumptions for uncertain estimates
- No medical diagnosis

## Error Handling

The MVP treats failures as normal cases.

### Missing API Key

If `QWEN_API_KEY` is missing, the app still opens. The diet logging page explains that model calls are unavailable until the key is configured.

### Model Timeout or Network Failure

Show a retryable error in the UI and record a failed trace.

### Invalid JSON

Do not save. Store the raw model output in the trace and show a format error.

### Schema Validation Failure

Do not save. Show a clear message that the model output was incomplete or invalid.

### Vague User Input

Allow low-confidence estimates to reach the editable confirmation UI. The notes should show the assumptions and encourage the user to correct values.

### Invalid Manual Edits

Block save when numeric fields are invalid, for example negative calories or protein.

### Fallback

If Qwen fails, the MVP does not auto-guess. The user may manually create a meal record, and the trace records the model failure.

## Implementation Order

1. Create the project skeleton, dependency files, `.env.example`, data directory, and trace directory.
2. Implement SQLite initialization and table creation.
3. Implement profile and goal services plus the profile page.
4. Implement the LLM interface and Qwen client.
5. Implement text meal estimation with schema validation.
6. Implement the chat-style diet logging page with editable pending meal confirmation.
7. Implement the orchestrator and trace logging.
8. Verify the full workflow from profile creation to confirmed meal logging and today's summary.

## Testing Strategy

Use focused tests for business logic and parsing. Streamlit can be manually verified in the MVP.

### Unit Tests

Cover:

- `goal_service`: calorie and protein target calculations for representative profiles.
- `meal_service`: confirmed meal persistence and daily aggregation.
- `nutrition_service`: parsing mock LLM JSON, handling missing fields, and rejecting invalid numeric values.
- `orchestrator`: one text input produces a pending meal and records a trace when dependencies are mocked.

### Manual Acceptance Tests

Verify:

1. The app starts with `streamlit run fat_loss_agent/app.py`.
2. The user can save a profile.
3. The app calculates calorie and protein targets.
4. The user can submit a text meal.
5. Qwen returns structured nutrition data.
6. The pending meal card is editable.
7. Confirming the card saves the meal.
8. Today's summary updates consumed and remaining nutrition.
9. Refreshing the app preserves profile, chat history, and meal logs.
10. `agent_traces` and `traces/agent_logs.jsonl` contain the call record.

## MVP Completion Standard

The MVP is complete when this daily workflow is stable:

```text
Open local Streamlit app
  -> save profile
  -> type meal description
  -> receive Qwen estimate
  -> correct estimate
  -> save meal
  -> see updated remaining calories and protein
```

This is the first useful version. Later work should extend this workflow instead of replacing it.
