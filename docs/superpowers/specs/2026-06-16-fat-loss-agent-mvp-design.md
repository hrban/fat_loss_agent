# 个人减脂 Agent MVP 设计

日期：2026-06-16

## 背景

这个项目从空仓库开始。第一目标不是做一个复杂平台，而是先做出一个自己每天真的愿意打开使用的个人减脂 Agent。

MVP 采用轻量 Python 单体架构：

- Streamlit：本地 Web UI
- SQLite：本地数据持久化
- 手写 Agent Orchestrator：显式编排意图、上下文、工具和回复
- Qwen API：第一版默认 LLM Provider
- Python services + repositories：清晰分层，但不引入微服务或 LangGraph

第一版最核心的可用链路是饮食记录：

```text
输入吃了什么 -> 估算营养 -> 手动修正 -> 确认保存 -> 查看今日剩余额度
```

## 产品范围

### MVP 包含什么

第一版只做两个用户可见页面。

#### 我的档案

档案页用于创建和更新默认本地用户的减脂基础信息。第一版是单用户应用，但所有业务数据都保留 `user_id` 字段，方便后续演进为多用户。

第一版默认用户是：

```text
local_user
```

档案字段包括：

- 昵称
- 性别
- 年龄
- 身高，单位 cm
- 当前体重，单位 kg
- 目标体重，单位 kg
- 活动水平
- 减脂速度：保守、标准、激进
- 饮食偏好或忌口，可选

保存档案后，系统计算并保存：

- 估算基础代谢 BMR
- 每日热量目标
- 每日蛋白质目标
- 简短目标说明

第一版的计算逻辑要可解释、偏保守，不追求医学级精确。

#### 饮食记录

饮食记录页是第一版主体验。

用户输入自然语言餐食描述，例如：

```text
午饭吃了两个鸡蛋、一碗米饭、一份牛肉
```

Agent 返回一张“待确认餐食卡片”。卡片展示：

- 餐次
- 标题
- 食物明细
- 份量假设
- 估算热量
- 估算蛋白质
- 估算碳水
- 估算脂肪
- 置信度
- 备注

用户可以在保存前手动修正这些值。只有用户确认后的餐食才写入 SQLite。

页面还展示今日摘要：

- 今日热量目标、已摄入热量、剩余热量
- 今日蛋白质目标、已摄入蛋白质、还差多少蛋白质
- 今日已记录餐食列表
- 一句针对当天剩余额度的实用建议

### MVP 明确不做什么

第一版不做：

- 登录注册
- 多用户 UI
- 食物照片识别
- RAG 知识库
- 周复盘
- FastAPI
- LangGraph
- Docker
- 定时任务
- 复杂权限
- 训练计划生成

这些都是后续扩展点。第一阶段先把饮食记录链路跑稳。

## 推荐架构

采用“轻量分层 Python 单体”的方案。

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

### 模块职责

#### `app.py`

启动 Streamlit 应用，配置页面导航，初始化数据库，并完成基础依赖组装。

#### `pages/`

只负责 Streamlit UI。页面不直接执行 SQL，也不直接调用 Qwen。

#### `agent/orchestrator.py`

负责第一版 Agent 主流程。Orchestrator 要保持小而显式。

处理文本餐食记录时，它做这些事：

1. 接收 `user_id` 和用户输入。
2. 读取用户档案上下文。
3. 读取今日当前营养摘要。
4. 调用 nutrition service 估算餐食。
5. 返回 pending meal 给页面展示。
6. 记录 trace。

Orchestrator 不直接写 SQL。确认保存由 `meal_service` 完成。

#### `llm/`

封装 LLM Provider 的差异。

MVP 默认 Provider 是 Qwen。业务层只依赖一个很薄的 LLM 接口，不依赖 Qwen 的请求细节。后续如果要接 DeepSeek，只需要增加实现同一接口的 `deepseek_client.py`。

#### `services/`

负责业务行为：

- `profile_service`：创建、读取、更新默认用户档案。
- `goal_service`：根据档案计算热量和蛋白质目标。
- `nutrition_service`：调用 Qwen，把自然语言餐食转换成结构化营养估算 JSON。
- `meal_service`：保存已确认餐食、读取餐食、计算餐食汇总。
- `summary_service`：计算今日看板数据和实用建议。
- `trace_service`：持久化 Agent 输入、工具调用、模型元信息、错误和最终状态。

#### `repositories/`

只负责 SQLite CRUD，不放业务判断。

## 数据流

### 文本饮食记录链路

```text
Streamlit 文本输入
  -> orchestrator.handle_meal_text(user_id, text)
  -> profile_service.get_profile(user_id)
  -> meal_service.get_today_summary(user_id)
  -> nutrition_service.estimate_meal_from_text(text, profile, today_summary)
  -> qwen_client.generate_json(...)
  -> nutrition_service 校验结构化 JSON
  -> orchestrator 返回 pending_meal
  -> 用户手动修正
  -> meal_service.save_meal_log(user_id, confirmed_meal)
  -> summary_service.get_today_dashboard(user_id)
  -> trace_service 写入数据库 trace 和 JSONL trace
```

### 设计规则

- UI 不直接调用 LLM。
- Agent 不直接写 SQL。
- LLM 不决定是否保存数据。
- Qwen 输出必须先解析并通过 schema 校验。
- 保存前必须经过用户确认。
- Trace logging 是 MVP 的一部分，不是后续增强项。

## 数据库设计

个人 MVP 使用 SQLite 足够。所有业务表都带 `user_id`，即使第一版只有 `local_user`。

### `profiles`

保存用户档案和计算后的目标。

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

保存一条已确认餐食记录。

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

保存一餐里的食物明细。

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

保存聊天历史，让页面刷新后仍能恢复上下文。

```text
id
user_id
role
content
message_type
metadata_json
created_at
```

第一版允许的 `message_type`：

- `user_text`
- `assistant_text`
- `pending_meal`
- `system_event`

### `agent_traces`

在 SQLite 里保存 trace 摘要。完整原始 trace 同步写入 `traces/agent_logs.jsonl`。

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

### MVP 不持久化 `daily_summaries`

第一版不建 `daily_summaries` 表。今日摘要从已确认的 `meal_logs` 实时汇总，避免缓存一致性问题。

## Pending Meal 数据结构

Qwen 返回的数据结构应等价于：

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

Service 层负责校验解析后的对象。只有通过校验的数据才进入可编辑确认 UI。

## LLM Provider 设计

### 配置

MVP 从环境变量读取 Qwen 配置：

```text
QWEN_API_KEY
QWEN_BASE_URL
QWEN_MODEL
```

`QWEN_API_KEY` 是模型调用必需项，不能提交到仓库。`QWEN_BASE_URL` 和 `QWEN_MODEL` 可以提供本地默认值。

### LLM 接口

应用定义一个很薄的 Provider 接口：

```text
LLMClient.generate_json(
  system_prompt: str,
  user_prompt: str,
  schema_name: str
) -> LLMResult
```

`LLMResult` 包含：

```text
content_json
raw_text
provider
model
prompt_tokens
completion_tokens
latency_ms
```

### Qwen 在 MVP 中的职责

Qwen 只负责把自然语言餐食描述转换为结构化营养估算。

它不负责：

- 保存记录
- 修改档案或目标
- 计算剩余额度
- 做数据库决策

Prompt 需要明确要求：

- 只输出 JSON。
- 当输入不是食物记录时，返回 `is_food_log=false`。
- 份量模糊时，按常见中国饮食的一人份估算。
- 每个食物都给出 calories、protein、carbs、fat、confidence 和 notes。
- 对不确定估算写清楚假设。
- 不做医疗诊断。

## 错误处理

MVP 把失败当成正常情况处理。

### 缺少 API Key

如果没有配置 `QWEN_API_KEY`，应用仍然可以打开。饮食记录页提示用户：模型调用不可用，需要先配置 API key。

### 模型超时或网络失败

UI 展示可重试错误，并记录失败 trace。

### 模型返回非法 JSON

不保存数据。把原始模型输出写入 trace，并在页面提示模型输出格式异常。

### Schema 校验失败

不保存数据。页面提示模型输出不完整或不合法。

### 用户输入太模糊

允许低置信度估算进入可编辑确认 UI。备注里说明关键假设，并鼓励用户修正。

### 用户手动修改非法

阻止保存。例如热量、蛋白质、碳水、脂肪不能是负数。

### 降级策略

如果 Qwen 调用失败，MVP 不自动猜测。用户可以手动创建一条餐食记录，trace 记录模型失败原因。

## 实现顺序

1. 创建项目骨架、依赖文件、`.env.example`、数据目录和 trace 目录。
2. 实现 SQLite 初始化和建表。
3. 实现 profile / goal services 和“我的档案”页面。
4. 实现 LLM 接口和 Qwen client。
5. 实现文本餐食估算和 schema 校验。
6. 实现聊天式饮食记录页，包括 pending meal 可编辑确认。
7. 实现 orchestrator 和 trace logging。
8. 验证从建档到确认保存一餐，再到今日摘要更新的完整链路。

## 测试策略

优先测试业务逻辑和解析逻辑。Streamlit UI 在 MVP 阶段先做人工验收。

### 单元测试

覆盖：

- `goal_service`：代表性档案下的热量和蛋白质目标计算。
- `meal_service`：已确认餐食的持久化和每日汇总。
- `nutrition_service`：mock LLM JSON 的解析、缺字段处理、非法数值拒绝。
- `orchestrator`：mock 依赖后，验证一次文本输入能产生 pending meal 并记录 trace。

### 人工验收

验证：

1. 可以用 `streamlit run fat_loss_agent/app.py` 启动应用。
2. 用户可以保存档案。
3. 应用可以计算每日热量和蛋白质目标。
4. 用户可以提交文本餐食。
5. Qwen 返回结构化营养数据。
6. Pending meal 卡片可编辑。
7. 确认后可以保存餐食。
8. 今日摘要会更新已摄入和剩余额度。
9. 刷新页面后，档案、聊天历史、餐食记录仍然存在。
10. `agent_traces` 和 `traces/agent_logs.jsonl` 中能看到本次调用记录。

## MVP 完成标准

MVP 完成的标准是这条日常链路稳定可用：

```text
打开本地 Streamlit 应用
  -> 保存个人档案
  -> 输入一餐描述
  -> 收到 Qwen 估算
  -> 修正估算
  -> 保存餐食
  -> 看到今日剩余热量和蛋白质更新
```

这是第一个真正有用的版本。后续功能应该扩展这条链路，而不是推倒重来。
