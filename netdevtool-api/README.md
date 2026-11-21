# NetDevTool Backend

网络运维智能助手后端：FastAPI + MySQL + Qdrant + Celery，提供设备手册问答、故障排查、知识库索引与配置翻译能力。

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 智能问答 | 意图识别（命令检索 / 故障排查 / 知识提问 / 超范围）→ 知识库混合检索 → 大模型生成；证据不足时可调用只读工具补查，故障排查采用「先工具调查、后结构化输出」；支持追问澄清、引用来源、点赞/点踩反馈 |
| 知识库管理 | 文档上传、删除、重试索引、元数据维护；按标题硬边界切块（父子块），dense + sparse 混合检索、RRF 融合与重排 |
| 知识缺口补齐 | 记录检索缺口，基于缺口生成 AI 候选答案，支持采纳 / 撤销 / 拒绝，采纳后写入补充知识库 |
| 配置翻译 | 基于 `translate_rule` 规则引擎的异步翻译任务（Celery），支持规则加载、解析、渲染与候选校验 |
| 审核工作台 | 待审核条目分页、审核历史、处置记录（采纳 / 修改后采纳 / 跳过）与撤销 |
| 设备与手册 | 设备列表查询、按厂商/型号打开外部链接或本地手册文件 |
| 认证 | 用户名密码 + bcrypt 校验，签发 12 小时令牌（进程内存保存，重启后失效） |
| 用量与可观测 | `ai_runs` 记录 LLM/向量/重排的 token、耗时、失败分类；Celery beat 每日清理超期记录 |
| 接口契约 | FastAPI 自动生成 OpenAPI（`/docs`、`/openapi.json`），可导出为仓库内 `openapi.json` |

## 技术栈

- **Web**：FastAPI 0.115+、Uvicorn、Pydantic v2、python-multipart
- **数据**：MySQL 8 + SQLAlchemy 2.0（`Mapped` / `mapped_column`）+ PyMySQL
- **向量检索**：Qdrant（本地嵌入式或服务端）、dense + sparse 混合召回、Rerank 模型（OpenAI 兼容 `/rerank`）
- **大模型**：LangChain Core + `langchain-openai`（兼容 OpenAI / DeepSeek / 百炼 / Moonshot / vLLM / Ollama）
- **异步任务**：Celery 5.3.6 + Redis（仅作 broker，任务状态存 MySQL）
- **文档解析**：pypdf、PyMuPDF4LLM、openpyxl
- **认证与测试**：bcrypt、pytest、httpx

## 分层架构

```
请求
 │
 ├─ api/            HTTP 语义：路由、参数校验、鉴权依赖、异常到状态码映射
 ├─ services/       业务编排：问答、索引、翻译、审核、计量等用例
 ├─ repositories/   数据访问：数据库读写的统一入口
 ├─ models/         SQLAlchemy ORM 模型（表结构定义）
 │
 ├─ rag/            检索与生成：切块、向量化、混合检索、意图识别、提示词、重排
 ├─ llm/            模型调用：错误分类/重试、结构化输出链、只读工具调用
 │  └─ tools/       工具协议、执行器与问答工具实现
 ├─ tasks/          Celery 任务：文档索引、配置翻译、定时清理
 └─ translate_rule/ 配置翻译规则引擎：规则加载、解析、渲染、候选校验
```

约定：

- 配置集中在 `app/config.py`（`pydantic-settings`），业务代码不直接读环境变量。
- 数据库会话由 `app/database.py` 提供；业务读写经 `repositories`，路由层负责参数校验与 DTO 转换。
- 跨层异常在 service 定义（如 `ChatSessionNotFound`、`ChatModelUnavailable`），由 API 层映射为 404 / 409 / 503 等状态码。
- 统一错误响应结构为 `{ code, message, detail }`（见 `app/main.py`）。

## 项目目录

```
netdevtool-api/
├─ app/
│  ├─ main.py                 # 应用装配、CORS、全局异常处理
│  ├─ config.py               # 配置项与 .env 读取
│  ├─ database.py             # 引擎、会话、Base
│  ├─ schemas.py              # 接口出入参 DTO
│  ├─ api/                    # 路由层
│  │  ├─ router.py            # 路由聚合
│  │  ├─ deps.py              # 当前用户依赖
│  │  ├─ health.py  auth.py  devices.py  translations.py
│  │  └─ knowledge.py  review.py  chat.py
│  ├─ services/               # 业务服务
│  ├─ repositories/           # 数据访问
│  ├─ models/                 # ORM 模型（device / knowledge / chat / gap / review / translation / ai_run / user）
│  ├─ rag/                    # 切块、向量化、检索、意图、提示词、重排
│  ├─ llm/                    # 模型调用
│  │  ├─ client.py            # 调用、错误分类/重试、chat_with_tools
│  │  ├─ chain.py             # 结构化输出链
│  │  └─ tools/               # 工具协议、执行器、问答只读工具
│  ├─ tasks/                  # celery_app、文档索引、翻译、维护任务
│  └─ translate_rule/         # 配置翻译规则引擎
├─ script/export_openapi.py   # 导出 OpenAPI 契约
├─ tests/                     # pytest 用例
├─ requirements.txt
├─ requirements-dev.txt
├─ .env.example
├─ openapi.json
└─ README.md
```

## 快速启动

### 1. 环境准备

- Python 3.11+（当前开发使用 3.13）
- MySQL 8（数据库默认 `netdev`，字符集 `utf8mb4`）
- Redis（Celery broker，默认 `redis://127.0.0.1:6379/0`）
- Qdrant：可启动本地服务（默认 `http://127.0.0.1:6333`），`QDRANT_URL` 留空时使用嵌入式本地存储

> 表结构以 `app/models` 为准，仓库当前未内置 Alembic 迁移；首次部署需先在 MySQL 创建 `netdev` 库并建表。

### 2. 安装依赖

```powershell
cd netdevtool-api
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
# 需要跑测试时
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

### 3. 配置环境变量

```powershell
Copy-Item .env.example .env
```

至少确认：

- `MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DB`
- `REDIS_URL`
- `QDRANT_URL`（留空用嵌入模式）
- `LLM_BASE_URL / LLM_API_KEY / LLM_MODEL`（模型调用必需，否则问答返回 503）
- `CHAT_QA_MODEL / CHAT_INTENT_MODEL`（可选，留空沿用 `LLM_MODEL`）
- `LLM_QA_BUDGET_SECONDS`（问答整体时间预算，默认 60）
- `CORS_ORIGINS`（与前端端口一致）

### 4. 启动服务

```powershell
# 后端
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8083

# Celery worker（Windows 必须 --pool=solo）
.venv\Scripts\python.exe -m celery -A app.tasks.celery_app worker --loglevel=info --pool=solo

# Celery beat（定时任务）
.venv\Scripts\python.exe -m celery -A app.tasks.celery_app beat --loglevel=info
```

也可以使用仓库根目录的一键脚本：

```powershell
scripts\start-all.bat   # MySQL / Redis / Qdrant / 后端 / Celery / 前端
scripts\stop-all.bat    # 停止以上进程
```

### 5. 验证

```powershell
# 健康检查
curl.exe http://127.0.0.1:8083/api/v1/health

# 接口文档
# http://127.0.0.1:8083/docs
```

```powershell
# 运行测试
.venv\Scripts\python.exe -m pytest -q

# 修改接口后刷新契约
.venv\Scripts\python.exe script\export_openapi.py
```

## API 路由

统一前缀 `/api/v1`。除 `/health` 与 `/auth/login` 外均需 `Authorization: Bearer <token>`。

| 模块 | 方法与路径 | 说明 |
| --- | --- | --- |
| system | `GET /health` | 健康检查 |
| auth | `POST /auth/login` | 登录并签发令牌 |
| auth | `GET /auth/me` | 当前登录用户 |
| auth | `POST /auth/logout` | 退出登录（令牌失效） |
| devices | `GET /devices` | 设备列表（按厂商/类型过滤） |
| devices | `GET /devices/manual` | 打开设备手册（外部链接或本地文件） |
| translations | `POST /translations` | 创建异步翻译任务（202） |
| translations | `GET /translations` | 最近翻译任务 |
| translations | `GET /translations/{request_id}` | 任务状态与结果 |
| translations | `GET /translations/{request_id}/source` | 源配置 |
| translations | `DELETE /translations/{request_id}` | 取消任务 |
| knowledge | `GET /knowledge/status` | 数据库 / Qdrant 连接状态 |
| knowledge | `GET /knowledge/bases` | 知识库列表 |
| knowledge | `PUT /knowledge/bases/{base_id}/config` | 更新切块与检索配置 |
| knowledge | `POST /knowledge/bases/{base_id}/documents` | 批量上传文档（逐文件返回结果） |
| knowledge | `GET /knowledge/bases/{base_id}/documents` | 文档列表（状态/类型/关键词过滤） |
| knowledge | `DELETE /knowledge/documents/{doc_id}` | 删除文档及其向量 |
| knowledge | `POST /knowledge/documents/{doc_id}/retry` | 重试索引 |
| knowledge | `PATCH /knowledge/documents/metadata` | 批量更新元数据 |
| knowledge | `PATCH /knowledge/documents/{doc_id}/metadata` | 更新单文档元数据 |
| knowledge | `GET /knowledge/gaps` | 知识缺口列表 |
| knowledge | `GET /knowledge/gaps/{gap_id}` | 缺口详情 |
| knowledge | `POST /knowledge/gaps/{gap_id}/candidates` | 生成 AI 候选（大模型） |
| knowledge | `GET /knowledge/gaps/{gap_id}/candidates` | 历史候选 |
| knowledge | `POST /knowledge/candidates/{candidate_id}/accept` | 采纳候选 |
| knowledge | `POST /knowledge/candidates/{candidate_id}/revoke` | 撤销采纳 |
| knowledge | `POST /knowledge/candidates/{candidate_id}/reject` | 拒绝候选 |
| knowledge | `GET /knowledge/supplements` | 补充知识库条目 |
| knowledge | `DELETE /knowledge/supplements/{supplement_id}` | 删除补充条目 |
| review | `GET /review/items` | 待审核条目分页 |
| review | `GET /review/history` | 审核处置历史 |
| review | `GET /review/decisions` | 处置快照 |
| review | `POST /review/decisions` | 记录处置 |
| review | `DELETE /review/decisions/{item_key}` | 撤销处置 |
| chat | `GET /chat/sessions` | 会话列表（支持关键词搜索） |
| chat | `GET /chat/sessions/{session_id}` | 会话详情与消息 |
| chat | `PATCH /chat/sessions/{session_id}` | 重命名会话 |
| chat | `DELETE /chat/sessions/{session_id}` | 软删除会话 |
| chat | `POST /chat/messages/stream` | 发送消息并 SSE 流式返回（命令/知识逐字输出） |
| chat | `PUT /chat/messages/{message_id}/feedback` | 点赞 / 点踩（踩需原因，rating=0 取消） |
| chat | `GET /chat/progress/{request_id}` | 查询处理阶段（前端轮询） |

说明：

- `POST /chat/messages/stream` 支持 `X-Chat-Request-Id` 请求头，用于关联进度轮询；返回 `text/event-stream`，事件为 `meta / stage / delta / result / citations / done / error`；命令与知识逐字推送，故障排查以 `result` 一次性下发完整 JSON。
- LLM 未配置时该接口在建立流之前返回 **503**；意图范围外、追问等通过流内事件返回。
- 完整契约以 `openapi.json` 或 `/docs` 为准。

## LLM 调用错误处理

实现位于 `app/llm/client.py` 与 `app/llm/chain.py`，所有 OpenAI 兼容异常先归类为 `LLMError(kind=...)`，再决定重试与用户提示。

### 错误分类

| kind | 触发场景 | 重试 | 处理结果 |
| --- | --- | --- | --- |
| `not_configured` | 缺少 `LLM_BASE_URL / LLM_API_KEY / LLM_MODEL` | 否 | 接口返回 **503**「AI 服务未配置」 |
| `auth` | 401 / 403（Key 失效、无权限、额度不足） | 否 | 回答标记失败，提示联系管理员 |
| `rate_limit` | 429 | 是（最多 2 次） | 退避后仍失败则提示「请求较多，请稍后再试」 |
| `timeout` | 请求超时 | 是（最多 1 次） | 超时或超出整体预算则失败 |
| `network` | 连接失败、网络中断 | 是（最多 1 次） | 提示网络异常 |
| `server` | 5xx / 502 / 503 / 504 | 是（最多 2 次） | 短线重试后失败，提示服务暂不可用 |
| `context_length` | 400/413 且命中上下文超长特征 | 否（改为裁剪上下文后重试一次） | 证据减半 + 单条 1000 字 + 历史仅最近 1 轮 |
| `bad_request` | 其他 400 / 422 | 否 | 若是 `response_format` 不兼容则去掉 JSON 模式重试一次 |
| `empty` | 返回内容为空（推理模型耗尽 token 等） | 翻倍 `max_tokens` 重试一次 | 仍为空则失败 |
| `invalid_json` | 需要 JSON 但解析失败 | 结构校验失败且疑似截断时重试一次 | 仍失败则回答标记失败；前端对非 JSON 内容按纯文本渲染 |
| `unknown` | 其他异常 | 否 | 通用失败提示 |

### 重试与预算策略

- 仅对 `rate_limit / timeout / network / server` 重试；`max_retries=0` 交给统一的 `_run_with_retry` 控制。
- 工具调用（`chat_with_tools`）复用同一套分类、重试与预算逻辑。
- 指数退避 + 抖动：限流基数 0.8s，其余 0.5s，单次退避上限 5s；优先遵循响应头 `Retry-After`。
- 问答生成设置整体预算 `LLM_QA_BUDGET_SECONDS`（默认 60s），每次调用的超时取 `min(配置超时, 剩余预算)`；预算不足时不再重试，直接失败。
- 每次模型调用（包括重试中的成功调用）都会通过 `usage_sink` 汇总 token，避免漏计费。

### 用户可见性与留痕

- 失败回答以助手消息落库：`chat_messages.status = failed`，`error_message` 形如 `auth: LLM 调用失败：...`；正文只展示可操作提示，技术细节不外露。
- 每次 LLM 业务调用（问答生成、故障排查、知识缺口候选等）通过 `app/services/ai_billing.py` 写入 `ai_runs`：
  - 成功：记录模型、token 消耗、耗时；
  - 失败：`status=failed`，`error_message` 带错误分类前缀，便于按类型统计；
  - `ai_runs` 默认保留 30 天，由 Celery beat 每日 03:30 执行 `maintenance.cleanup_ai_runs` 清理。
- 常见排查入口：`celery-worker.log`、`ai_runs` 表、`chat_messages.error_message`。

## 智能问答整体实现方案

智能问答把用户问题、会话上下文、企业知识库与大模型编排成可追溯的回答。主流程在 `app/services/chat_service.py`，检索与提示词在 `app/rag/`，模型与工具在 `app/llm/`。

### 1. 能力边界

| 能力 | 说明 |
| --- | --- |
| 意图分流 | `command` / `troubleshoot` / `knowledge` / `out_of_scope` 四类 |
| 多轮会话 | 最近 2 轮历史；会话级厂商上下文；追问补答自动合并 |
| 检索增强 | 按意图映射知识库类型，dense + sparse + RRF + rerank |
| 追问澄清 | 缺失槽位 + 低置信度时最多追问 2 轮 |
| 工具补查 | 证据不足时模型可调用只读工具，最多 2 轮；故障排查为「先工具、后结构化」两阶段 |
| 结构化输出 | 故障排查输出 JSON；命令与知识输出 Markdown |
| 可追溯 | 引用来源落库；失败留痕；token 与耗时计量 |
| 交互方式 | 命令/知识支持 SSE 流式；故障排查与澄清使用一次性事件 |

### 2. 端到端流程

```text
POST /api/v1/chat/messages/stream（SSE）
  → 会话创建/复用 + 厂商归一化 + 最近 2 轮历史
  → 用户消息落库，trace_id = 用户消息 ID
  → 意图识别（结构化 JSON）
      ├ out_of_scope → 固定拒答，不检索
      └ command / troubleshoot / knowledge
  → 按意图映射知识库类型，执行混合检索
  → 澄清判断（缺失槽位 + 置信度）
      └ 命中 → 写入追问，等待用户补充
  → 证据不足 → 只读工具补查（≤2 轮；故障排查为「调查 → 结构化生成」两阶段）
  → 生成答案（故障排查 JSON；命令/知识 Markdown）
  → 引用落库、token/耗时计量、返回 ChatSendOutcome
```

三个进度阶段通过 `GET /chat/progress/{request_id}` 暴露：`intent`、`retrieval`、`generation`；流式接口在故障排查启用工具时额外推送 `stage=tool`。

### 3. 会话与上下文

- 会话级字段 `chat_sessions.vendor`；每次请求携带的厂商优先覆盖会话值，`all` 表示不限。
- `normalize_vendor` 把「华为/中兴/华三」与英文 key（`huawei/zte/h3c`）统一为 `devices.vendor_en`，兼容历史会话中保存的中文名。
- 历史只取最近 2 轮（`HISTORY_ROUNDS=2`），同时用于意图识别与生成提示词。
- 追问补答：`pending_clarify` 保存原问题与轮次；用户下一条短回答（≤60 字、不含问号）会合并为「原问题 + 补充信息：xxx」后重新走完整流程。
- 会话标题取首条问题前 30 字；空标题会话在后续提问时自动补全。

### 4. 意图识别

| mode | 判定特征 | 使用知识库类型 | 输出形态 |
| --- | --- | --- | --- |
| `command` | 命令、配置、参数 | `manual` | Markdown 四段式 |
| `troubleshoot` | 报错、现象、日志 | `troubleshooting` | 结构化 JSON |
| `knowledge` | 概念、原理、架构 | `architecture` | Markdown |
| `out_of_scope` | 与网络运维无关 | 不检索 | 固定拒答 |

- 通过 `invoke_structured` 输出 `IntentResult`（mode / missing_slots / clarify_question / reason），温度 0、512 tokens、30s 超时；模型优先级 `CHAT_INTENT_MODEL → CHAT_QA_MODEL → LLM_MODEL`。
- 识别失败不拒答：按前端已选类型兜底，`unknown` 视为 `knowledge`。
- 厂商已确定（非 `all`）时，代码会剔除「厂商/品牌/vendor」类缺失槽位，并清除提到厂商的追问，避免重复要求选择厂商。

### 5. 知识检索

- 库级类型路由：以 `knowledge_bases.kb_type`（`manual` / `architecture` / `troubleshooting`）为准，`MODE_KB_TYPES` 严格对应；按名称猜测的旧规则只作兜底。
- 每轮只检索类型匹配且已启用的知识库，并按库独立融合：
  1. dense 向量召回 + sparse 关键词召回；
  2. 按库 `hybrid_semantic_weight` 做加权 RRF；
  3. 用 `hybrid_top_k` 截取最终条数，`hybrid_score_threshold` 过滤；
  4. 配置了 rerank 时按 query 与证据重排，异常则降级为融合分数（`trace.status=rerank_degraded`）。
- 切块支持按标题级别硬边界与标题路径维护；父子块用于召回后还原上下文。
- 进入提示词的证据单条最多 1500 字（`QA_EVIDENCE_MAX_CHARS`）；引用落库保存文件名、文档、分块、相关度与片段。

### 6. 追问澄清

同时满足以下条件才追问：

- 意图返回了 `missing_slots` 和非空 `clarify_question`；
- 不是 `out_of_scope`；
- 追问轮次小于 `MAX_CLARIFY_ROUNDS`（2）；
- 无检索证据，或 `top_score < CLARIFY_CONFIDENCE`（0.70）；重排降级时仅按「无证据」判断。

澄清响应带可选 `options` 与 `allow_free_text`。只有真正缺少「厂商/品牌」时才返回设备表厂商列表；厂商已知时不再要求选择。追问消息以 `status=clarifying` 落库，前端用独立样式展示。

### 7. 工具补查

命令、知识与故障排查问题在首轮证据不足时，模型可主动调用只读工具补查。

触发条件：

- 意图为 `command`、`knowledge` 或 `troubleshoot`；
- 无证据，或 `top_score < 0.55`；
- 重排降级且已有证据时不触发。

| 工具 | 参数 | 作用 | 返回 |
| --- | --- | --- | --- |
| `search_manual` | `query`（2–200 字）、`mode`（command/knowledge，可空） | 用改写后的手册术语在当前厂商知识库二次检索 | 补充证据文本 + 引用证据 |
| `search_fault_cases` | `query`（2–200 字） | 在故障手册库中按现象二次检索（仅故障调查阶段） | 补充证据文本 + 引用证据 |
| `get_device_info` | `vendor`（可空）、`model`（可空，模糊匹配） | 查询设备档案的厂商、型号、类型、是否有手册 | 摘要，最多 5 条，不产生引用 |

故障排查走两阶段，避免 JSON 模式与工具协议冲突：

1. **调查阶段**：独立提示词 + `search_fault_cases` / `get_device_info`，最多 2 轮、每轮 2 个调用，单独限时 25s；产出一段调查小结。
2. **结构化阶段**：不绑定工具，用合并后的证据 + 小结调用 `with_structured_output`，输出 `TroubleshootAnswer`。

小结只作辅助理解，会明确标注“不是证据、不得作为 `evidence_refs` 引用”，引用仅来自检索证据。工具不支持或调查阶段无新增证据时，直接进入结构化阶段或返回固定说明。

执行约束：

- 工具通过 `ToolSpec` 白名单注册，Pydantic 校验参数；未知工具、参数非法、执行异常都转成文本回填，不打断问答。
- 最多 2 轮、每轮最多 2 个调用；超限调用也会回填 `ToolMessage`，保证消息序列合法。
- 补充证据使用 `[补充N]` 独立编号，按 `(doc_id, point_id)` 与已有证据去重后合并并写入引用。
- 端点不支持工具（400 且含 tool/function/unsupported）时抛 `ToolsUnsupported`：有证据回退普通生成，无证据返回固定说明。
- 所有轮次共享生成预算；执行日志形如 `tool=... latency=...ms evidences=...`。
- 工具本身不写 `ai_runs`，模型调用 token 仍照常计量。

### 8. 生成与输出格式

- **命令**：四段式 Markdown「配置命令 / 参数说明 / 配置示例 / 注意事项」，提示符与视图名按证据原样保留，不统一改写；前端按 Markdown 渲染并加统一外框，多行命令展示时换行转「；」，复制文本同样处理。
- **知识**：Markdown 正文；证据不足时可结合通用网络知识，但与证据冲突时以证据为准。
- **故障排查**：`TroubleshootAnswer` JSON（`hypotheses` / `steps` / `solutions` / `summary`），前端渲染为原因、诊断步骤与解决方案卡片；JSON 解析失败时按纯文本展示，不使用 Markdown。证据不足时先做工具调查（≤2 轮、单独限时 25s），调查小结仅作辅助、不进入引用；结构化阶段不绑定工具。
- 引用来源与复制/赞/踩操作条在正文之外渲染。

### 9. 引用、反馈与计量

- **引用**：`chat_message_citations` 保存 `kb_id`、`doc_id`、`file_name`、`point_id`、`score`、`snippet`，前端展示来源文件并支持定位。
- **反馈**：`chat_message_feedbacks` 的 `rating` 取 `1 / 0 / -1`，点踩必须填写原因；`(message_id, user_id)` 唯一，用户删除时级联删除。
- **计量**：`chat_messages` 记录 model、prompt/completion tokens、latency；`ai_runs` 记录每次 LLM、embedding、rerank 调用（成功与失败），默认保留 30 天。
- **关联**：`trace_id` 为本次提问的用户消息 ID，可串联引用、`ai_runs` 与日志。

### 10. 失败与降级

| 场景 | 行为 |
| --- | --- |
| LLM 未配置 | 接口返回 **503**，前端提示联系管理员 |
| 限流 / 超时 / 5xx | 分类重试后失败，返回可操作文案（详见「LLM 调用错误处理」） |
| 上下文超长 | 证据减半、单条 1000 字、历史仅保留 1 轮后重试一次 |
| 端点不支持工具 | 静默回退普通生成；无证据时返回固定说明 |
| 故障调查超时/失败 | 放弃补充，使用现有证据直接进入结构化生成 |
| 无证据且工具未返回有效内容 | 按 mode 返回固定说明；厂商已知时不再要求补充厂商 |
| 生成失败 | 失败回答落库 `status=failed`，`error_message` 带错误分类 |

### 11. 进度与前端交互

- 进度接口：占位消息仍可轮询 `GET /chat/progress/{request_id}`，与 SSE 的 `stage` 事件互为补充。
- 流式接口：`POST /chat/messages/stream` 直接推送 `stage` 事件，经 `meta` 占位后逐字下发 `delta`；`troubleshoot` 走 `result` 一次性下发完整 JSON，避免半截 JSON。
- 前端接入：使用 `fetch` + `ReadableStream` 解析 SSE，收到 `meta` 后将占位消息切换为真实消息 ID 并逐字追加；`troubleshoot` 的 `result` 仍由故障排查卡片渲染。
- 消息状态：`pending`（等待）、`streaming`（生成中）、`clarifying`（需补充信息）、`evidenced`（知识库增强）。
- 断开处理：客户端断开时保留已生成内容并标记 `failed`；流开始后不再重试，错误通过 `error` 事件返回。
- 前端会话与消息状态集中在 `useChatSession`，渲染统一走 `ChatMessageView` 与 `MarkdownContent`；命令类答案使用统一外框，故障排查使用专用卡片。

### 12. 关键参数

| 参数 | 位置 | 默认值 / 说明 |
| --- | --- | --- |
| `HISTORY_ROUNDS` | `chat_service.py` | 2 轮历史 |
| `MAX_CLARIFY_ROUNDS` | `chat_service.py` | 最多追问 2 次 |
| `CLARIFY_CONFIDENCE` | `chat_service.py` | 0.70 |
| `CLARIFY_ANSWER_MAX_LENGTH` | `chat_service.py` | 补答合并上限 60 字 |
| `TOOL_EVIDENCE_SCORE` | `chat_service.py` | 0.55，低于则启用工具 |
| `MAX_TOOL_ROUNDS` | `chat_service.py` | 2 轮 |
| `MAX_TOOL_CALLS_PER_ROUND` | `chat_service.py` | 每轮 2 个 |
| `FAULT_INVESTIGATION_SECONDS` | `chat_service.py` | 故障调查阶段单独限时 25s |
| `TOOL_EVIDENCE_SNIPPET_CHARS` | `chat_service.py` | 调查阶段单条证据 1000 字 |
| `QA_EVIDENCE_MAX_CHARS` | `app/rag/schema.py` | 单条证据 1500 字 |
| `LLM_QA_BUDGET_SECONDS` | `app/config.py` | 整个生成阶段预算 60s |
| `CONTEXT_RETRY_EVIDENCE_CHARS` | `chat_service.py` | 上下文超长时降为 1000 字 |

### 13. 代码索引

| 环节 | 文件 |
| --- | --- |
| 接口 | `app/api/chat.py` |
| 问答编排 | `app/services/chat_service.py` |
| 意图识别 | `app/rag/qa_intent.py` |
| 混合检索与重排 | `app/rag/qa_retriever.py`、`qdrant_store.py`、`embedding.py`、`rerank.py` |
| 提示词与证据渲染 | `app/rag/qa_prompts.py` |
| 切块与索引 | `app/rag/chunking.py`、`indexer.py` |
| 工具协议与实现 | `app/llm/tools/` |
| 模型调用与错误分类 | `app/llm/client.py`、`chain.py` |
| 进度与计量 | `app/services/chat_progress.py`、`ai_billing.py` |
| 前端 | `netdevtool-web/src/pages/ChatPage.tsx`、`hooks/useChatSession.ts`、`components/Markdown.tsx` |

### 14. 后续演进

- 故障排查的「先工具、后结构化」已落地，后续可评估更多只读数据源。

