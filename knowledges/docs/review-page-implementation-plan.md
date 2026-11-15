# 命令审核页面实现方案（V1）

## 1. 背景与定位

审核页已由旧版「LLM 候选命令」模型重构为基于「规范实体 + 厂商实现」的规则翻译结果，前端实现已完成，当前处于 mock 数据阶段（现状见第 3 节）。

页面定位：**面向"能不能下发"的处置工作台**。审核对象是已完成的翻译任务结果，而非知识库候选命令；处置结果保存在后端 `review_decisions` 表，形成「翻译 → 聚合审核 → 检查点 → 导出」闭环。与配置翻译页之间只保留**单向数据影响**：审核页的处置结果会影响审计面板的未审核项，审计面板不影响审核页（见 3.4）。

- 审计面板（翻译页内）：随结果即时展示告警，回答"这次翻译有哪些问题"
- 命令审核页面：跨任务组织待审条目，回答"这些命令能不能下发、如何处置"

## 2. 审核范围与类别

数据均来自各翻译任务的结果（`TranslationResult`），审核页按**全部任务聚合**取数，不局限于单次翻译。

审核条目**按问题类别（告警码）组织与处理，不设档位与优先级分层**；同类条目可批量处置，不同类别按下列规则处理。

### 不纳入审核的类别

| 类别 | 处理方式 | 原因 |
|---|---|---|
| `intf_unmapped`、`intf_translated`（接口名映射） | 不进入审核池，仅在翻译页审计面板展示 | 接口编号高度依赖实际组网，用户通常自行改写接口号，逐条审核价值低、噪音大 |
| `invalid_param`（参数校验失败） | 不进入审核池，仅在翻译页审计面板临时处理 | 属翻译过程内的即时修正，用户在翻译页对照源配置改掉即可，无需进入跨任务审核列表 |

### 审核类别与处理规则

| 类别（告警码） | 含义 | 触发来源 | 处理方式 |
|---|---|---|---|
| `unknown_command` | 未识别命令，原样保留 | error 告警 | 修改后采纳（人工改写） |
| `unsupported_entity` | 目标设备不支持该实体 | error 告警 | 人工改写替代命令，或拒绝该条 |
| `unverified_impl` | 知识库标记未验证的厂商实现 | warn 告警 | 核对目标厂商命令手册后采纳或拒绝 |
| `low_confidence` | 置信度 medium/low，作者标注的不确定项 | warn 告警 | 重点核对后采纳或拒绝 |

列表默认排序：error 类在前，其次 warn 类；同类内按源行号升序，`unknown_command`、`unsupported_entity` 在 error 类内优先。

## 3. 实现边界

审核页前端已完成定型，后续实现只沉淀数据与后端能力，不再改动页面结构、交互与视觉。

### 3.1 数据范围

- **不绑定单次翻译**：不按单个 `requestId` 取数，而是聚合全部翻译任务的待审条目，形成跨任务统一的待审池；条目所属任务仅作为溯源信息保留
- **不做页面间跳转**：不在翻译页新增「进入审核」入口，也不做审核页 → 翻译页的行定位；两侧各自独立打开
- **数据来源**：翻译成功时由后端把带告警的结果行物化到 `review_items` 表（同一命令按 `(user_id, item_key)` 覆盖为最近一次），审核页按服务端分页读取，不再解析完整 `result_json`

### 3.2 与审计面板的关系（单向）

| 方向 | 规则 |
|---|---|
| 审计面板 → 审核页 | **不影响**。审计面板内的处置（含 `invalid_param` 就地修正、检查点生成）不新增、不删除，也不改变审核页条目的待审状态与数量 |
| 审核页 → 审计面板 | **影响未审核项**。审核页处置结果按稳定命令标识写入后端 `review_decisions` 表，审计面板后续接入后可将对应行从「待处理」统计中剔除，并在行上标注「已审核（采纳 / 修改后采纳 / 拒绝）」 |

- 数据载体：后端 `review_items`（物化条目，唯一键 `(user_id, item_key)`）与 `review_decisions`（处置，唯一键 `(user_id, item_key)`）；`item_key = SHA1(源厂商, 源型号, 目的厂商, 目的型号, 归一化源命令)`，由后端统一生成，跨翻译任务共享同一处置结果
- 读写接口：`GET /api/v1/review/items` 服务端分页（`page` / `page_size` / `status` / `target_vendor` / `target_model` / `code`），返回条目、`decision`、全局统计与筛选项；`GET /api/v1/review/decisions` 返回当前用户全部处置快照（供生成检查点）；`POST /api/v1/review/decisions` 记录处置（采纳 / 修改后采纳 / 拒绝）；`DELETE /api/v1/review/decisions/{item_key}` 撤销处置
- 生效时机：审核页每次处置直接写库；前端不再使用 localStorage 保存审核状态
- 统计口径：顶部「待审核 / 已处置」按后端返回的 `decision` 统计；审计面板联动尚未接入
- 冲突处理：同一行两侧都有处理记录时，以 `updated_at` 较晚者为准；`source === 'audit'` 的记录不参与审核页的待审判定
- 检查点：审核页生成的检查点只是 reviews 的快照，不反向驱动审计面板状态

### 3.3 暂不实现

- **「审核记录」**：不做任务列表与任务切换，入口保留占位
- **「查看源手册」**：不做厂商手册跳转，入口保留占位

## 4. 未识别命令 LLM 兜底与补充知识库

本节是审核页 `unknown_command` 类别的处理增强，属于独立增量阶段。**本节只做后端与知识库能力，不改动第 3 节的实现边界**，页面接入方式另行规划。

### 4.1 定位与边界

- `knowledges/entities` + `knowledges/vendors` 是人工维护的**权威核心层**
- 新增 `knowledges/supplements` 作为**低置信度兜底层**，不写入 `entities/`
- 两层在运行时共用同一套解析与渲染引擎，补充库只负责兜底

五条硬边界：

1. 永不自动写入，必须由人工确认
2. 永不覆盖核心实体：实体优先、补充库兜底
3. 永远 `verified: false`，命中结果 tone 为 `warn` 并附 `supplement_applied` 告警
4. **不调用 LLM 判断源厂商是否支持该命令**——命令出现在用户配置中即为最强证据
5. 页面已定型（第 3 节），本期只做接口与知识库，不涉及页面结构改动

### 4.2 总体链路

```text
翻译任务完成
  └─ 解析未命中行 → 归一化为模板 → upsert knowledge_gaps（按出现次数聚合）
        └─ 人工触发 AI 解析（触发入口另行规划，本期不改页面）
              └─ 按需组装结构化上下文 → LLM 返回候选 JSON
                    └─ 自动校验（模板回放 / 参数 / 渲染 / 视图）
                          ├─ 通过 → 返回候选，供人工确认
                          └─ 不通过 → 返回失败原因，不提供入库入口
                                └─ 人工确认 → 写入 supplements/{slug}.yaml + 知识库热重载
                                      └─ 后续翻译：实体未命中 → 补充库匹配 → warn 输出
```

### 4.3 补充知识库存储

```text
knowledges/supplements/{source_vendor}/{source_device_type}/{slug}.yaml
```

```yaml
id: ext_stp_edged_port
source:
  vendor: huawei
  device_type: switch
  product: S5735
  os: V200R019
  view_path: ["system-view", "interface {intf}"]
  command: "stp edged-port enable"
  parameters:
    intf: { type: string, required: true }
target:
  vendor: h3c
  device_type: switch
  product: S5560
  os: V7
  view_path: ["system-view", "interface {intf}"]
  command: "stp edged-port"
  pre_commands: []
  negative_command: null
origin: llm
confidence: low
verified: false
accepted_by: zxf
accepted_at: "2026-11-15T10:00:00Z"
uses: 0
sources: []
cases:
  - source: "stp edged-port enable"
    target: "stp edged-port"
```

要点：

- 条目必须**参数化**（命令中变量抽象为 `{name}`），否则只能匹配字面行，无法复用
- 必须记录**两侧视图路径**，否则缩进、quit 收尾、视图栈会错位
- 必须带 `product / os` 作用域，避免跨型号误用
- `sources` 暂留空数组：无可核实文档时不得展示为引用

### 4.4 数据库表

| 表 | 关键字段 | 用途 |
|---|---|---|
| `knowledge_gaps` | vendor, device_type, product, os, target_vendor, target_device_type, view, command_template, raw_sample, occurrences, kind, status, request_ids, created_at, updated_at | 知识质量问题聚合，按频次排序；目标侧问题按目标厂商与设备类型区分 |
| `supplement_candidates` | gap_id, llm_model, prompt_version, request_json, response_json, validation_json, status, reviewer_id | LLM 调用与校验留痕，可审计可回放 |
| `llm_runs` | request_id（本次调用 UUID，唯一）, model, method, biz_type, biz_id, prompt_tokens, completion_tokens, total_tokens, latency_ms, status, error_message, created_at | 每次大模型调用留痕，用于计费与成本核算；`biz_type` + `biz_id` 多态关联业务对象（如 `knowledge_gap` + 缺口主键） |

`kind` 取值：`unknown_source`（源侧未识别）/ `missing_target_impl`（目标侧无实现）。按项目分层：模型定义在 `app/models.py`，读写走 `app/repositories/`，编排在 `app/services/`。

### 4.5 后端改造点

| 位置 | 改造 |
|---|---|
| `app/llm/client.py` | OpenAI 兼容客户端，已就绪（依赖 `httpx`，需加入运行时依赖）；每次成功 HTTP 调用通过 `usage_sink` 回传 token 消耗 |
| `app/services/llm_billing.py` | 计费包装：`chat_json_billed()` 汇总 token 与耗时写入 `llm_runs`，落库失败只记日志不影响主流程 |
| `app/repositories/llm_run_repository.py` | `llm_runs` 表读写入口 |
| `app/translate_rule/loader.py` | 扫描 supplements，合成 1 个 EntitySpec + 源/目标 2 个 Implementation，标记 `origin: supplement` |
| `app/translate_rule/parser.py` | matcher 排序键改为 `(origin == 'supplement', -literal_length, 参数个数)`，实体永远优先 |
| `app/translate_rule/renderer.py` | 命中 supplement 时 tone 置 `warn`，追加 `supplement_applied` 告警 |
| `app/services/translation_service.py` | 翻译成功后采集两类缺口：源侧未识别命令（`unknown_source`）、目标侧实现问题（`missing_target_impl`，来自 `unsupported_entity` / `unverified_impl` / `low_confidence` 告警），归一化后 upsert `knowledge_gaps` |
| `app/api/` | 新增候选生成、补充库增删查、缺口统计接口，全部做归属校验 |
| 知识库热重载 | Celery Worker 任务启动前比对知识库目录 mtime，变化则重建 registry（避免写文件后 Worker 仍用旧缓存） |

合成实现必须走现有 `EntitySpec` / `Implementation` 模型，**不新增旁路数据结构**，这样 parser、renderer、否定前缀、视图栈、去重逻辑全部零改动复用。

### 4.6 Prompt 设计（不接 RAG、不注入 few-shot）

输入只包含结构化上下文，不检索文档、不拼接示例：

```text
源：厂商 / 设备类型 / 型号 / 版本 / 视图 / 归一化命令模板
目标：厂商 / 设备类型 / 型号 / 版本
```

输出为严格 JSON：

```json
{
  "status": "found | unknown",
  "source_template": "含 {name} 占位符的源命令模板",
  "parameters": {"name": {"type": "string|int", "required": true}},
  "target_command": "目标厂商命令，占位符与 parameters 同名",
  "target_view_path": ["system-view", "interface {intf}"],
  "pre_commands": [],
  "negative_command": null,
  "reasoning": "判断依据",
  "sources": [],
  "confidence": "low"
}
```

硬性规则：无法确定必须返回 `unknown`；不得臆造命令关键字；`source_template` 必须能还原原始命令；`target_command` 只能使用已声明占位符。

#### 决策依据：不注入 few-shot

2026-11-15 用 5 条真实未识别命令 × 3 组做过对照实验（脚本 `scripts/experiment_fewshot.py`，明细见 `netdevtool-api/experiments/`）：

| 组 | 条件 |
|---|---|
| A | 不给示例，仅结构化上下文 |
| B | 按纯字符串相似度召回 Top3 |
| C | 人工挑选同域实现作为示例 |

实验结论：

1. **命令文本几乎无差异**：5 个用例中 4 个的命令三组完全一致，第 5 个仅占位符命名不同
2. **噪声示例引入元数据缺陷**：B 组出现视图路径丢失 `{intf}` 占位符、以及给出不属于目标厂商的 `configure terminal`
3. **置信度被示例抬高而非正确性提升**：两组用例从 `medium` 升为 `high`，但命令未变
4. **零弃权**：15 次调用全部返回 `found`，即使提示词要求不确定时返回 `unknown`
5. **来源不可核实**：`sources` 出现无法验证的手册名，等同模型自述

因此 V1 **不注入 few-shot、不接文档 RAG**。若后续引入文档检索，必须先具备语料切分与检索评测基线（recall@5 ≥ 80%），再讨论接入。

### 4.7 自动校验

候选必须全部通过才进入人工审核队列：

| 校验 | 方法 | 不通过后果 |
|---|---|---|
| 结构校验 | Pydantic 模型（`Implementation` 等） | 丢弃 |
| 源模板回放 | 用 `compile_template` 编译源模板，必须完整匹配原始行 | 丢弃（参数化不忠实） |
| 参数合法性 | 占位符 ⊆ 参数表，且 `type/format/pattern` 匹配原值 | 丢弃 |
| 渲染冒烟 | 用捕获的真实参数渲染目标命令，无残留占位符 | 丢弃 |
| **目标视图占位符** | `target_view_path` 中的占位符 ⊆ 参数表 | 丢弃（实验中 B 组缺陷即由该条拦截） |
| **视图白名单** | 视图名必须符合目标厂商 `_profile.yaml` 约定 | 丢弃 |

两条约束：

- 不采用 LLM 自报的 `confidence`，改由「回放通过 + 视图合规 + 参数覆盖」计算
- `sources` 无文档支撑时标记为「模型自述，未核实」，输出中不作为引用来源

### 4.8 敏感命令过滤

含密码、密钥、团体名的命令（`password`、`cipher`、`secret`、`community`、`key` 等）**不落库、不送 LLM**，直接标记为「需人工处理」。LLM 只接收单行命令，不接收整份配置；支持 `LLM_BASE_URL` 指向内网模型以满足合规要求。

### 4.9 生命周期

| 机制 | 规则 |
|---|---|
| 遮蔽检测 | 补充条目源命令已被真实实体覆盖时标记 shadowed，不参与匹配并告警 |
| 晋升 | `uses >= 20` 或人工判断重要 → 转为正式 entity + 多厂商实现，删除补充条目 |
| 回收 | `verified: false` 且 `uses == 0` 超 90 天 → 提示清理 |
| 方向 | 补充条目有方向性，默认不自动生成反向条目 |

### 4.10 实施步骤

| 阶段 | 内容 | 验收 |
|---|---|---|
| P0 | `knowledge_gaps` 采集 + 归一化聚合 + 敏感命令过滤 | 能看到高频缺口 Top20，敏感行不入库 |
| P1 | LLM 客户端接入 + 按需候选接口（只读不落盘）+ 4.7 全部校验 | 接口对未识别行返回候选并通过全部校验，不涉及页面改动 |
| P2 | 采纳写入 supplements + 热重载 + renderer 输出 `supplement_applied` 告警 | 首条补充条目端到端生效，二次翻译命中并标记 `warn` |
| P3 | 遮蔽检测 + 晋升 + 回收 | 新增真实实体后旧条目自动失效 |

### 4.11 明确不做

- 不注入 few-shot 示例（实验证明无增益且引入元数据缺陷）
- 不接文档 RAG（待语料切分与检索评测基线具备后再议）
- 不自动写入知识库，不覆盖核心实体
- 不把整份源配置送 LLM，敏感命令不送
- 不做跨任务批量 AI 解析
- 不采用 LLM 自报置信度与不可核实的来源引用

### 4.12 unsupported_entity 的复用

`unsupported_entity` 可以复用本章机制，且上下文比未知命令更完整，但必须先按成因拆分。

#### 4.12.1 成因拆分（前置改造）

现有判定把三种情况合并为一个告警（`renderer.py` 中 `spec is None or implementation is None or not implementation.supported`）：

| 成因 | 性质 | 是否走 AI 兜底 |
|---|---|---|
| `implementation is None` | 目标厂商缺实现，纯知识缺口 | 是 |
| `implementation.supported == False` | 知识库明确标注不支持，属人工断言 | 否（严格禁止自动覆盖） |
| `spec is None` | 实体定义缺失，属数据异常 | 否（先修数据） |

改造方式：`RenderWarning` 增加 `reason` 字段（`missing_impl` / `explicit_unsupported` / `entity_missing`），告警码仍为 `unsupported_entity`；`reason` 仅用于区分后续处置方式，页面接入另行规划。

#### 4.12.2 与未知命令方案的差异

| 维度 | `unknown_command` | `unsupported_entity`（缺实现） |
|---|---|---|
| 上下文 | 仅源命令文本，参数需模型反推 | 实体、参数、视图、源实现均已知 |
| LLM 任务 | 源模板 + 目标命令 | 仅需目标实现 |
| 源模板回放 | 必需 | 天然通过（复用实体自身 matcher） |
| 校验重点 | 源侧 + 目标侧 | 集中在目标命令、视图、参数 |
| 存储形态 | 新建合成实体 `ext_*` | 挂到既有实体，不新建实体 |

#### 4.12.3 存储形态：实现补充而非新实体

```text
knowledges/supplements/impls/{target_vendor}/{target_device_type}/{entity_id}.yaml
```

```yaml
extends: stp_edged_port
vendor: h3c
device_type: switch
product: S5560
command: "stp edged-port"
view: "interface {intf}"
pre_commands: []
negative_command: null
origin: llm
verified: false
accepted_by: zxf
accepted_at: "2026-11-15T10:00:00Z"
uses: 0
```

加载时的合并顺序：实体规范取自核心层；实现优先取核心层，缺失时再取 `supplements/impls`。这样 `entity_id`、参数与识别链路全部保持原样，只在命中时降为 `warn`，不需要为补充条目另建识别链路。

#### 4.12.4 supported: false 的处理

`supported: false` 是人工写下的断言，LLM 建议不得自动覆盖：

- 该类情况**不做 AI 兜底**，仅走人工改写或拒绝
- `supplements/impls` 不得覆盖核心层的 `supported: false`
- 确需变更时，人工直接修改核心层 YAML 并记录理由，不走补充库

#### 4.12.5 校验调整

在 4.7 的基础上：

- 源模板回放跳过（实体已识别，参数直接取自实体定义）
- 参数合法性改为「LLM 给出的目标命令占位符 ⊆ 实体参数表」
- 目标视图占位符与视图白名单校验保留
- 新增形态校验：若等价实现需要一条源命令拆成多条目标命令或跨视图分解，**直接拒绝**——现有 `Implementation` 仅支持单命令 + `pre_commands` + `sub_commands`，V1 不支持该形态

#### 4.12.6 实施步骤增量

| 阶段 | 内容 |
|---|---|
| P0 | `RenderWarning` 增加 `reason` 字段，拆分三种成因 |
| P1 | 候选接口支持 `entity_id` 模式（不生成源模板） |
| P2 | 采纳写入 `supplements/impls/`，loader 支持实现补充合并 |
| P3 | 遮蔽检测覆盖实现补充：核心层补齐实现后，补充条目自动失效 |

#### 4.12.7 明确不做

- 不用补充库覆盖 `supported: false`
- 不为已有实体新建 `ext_*` 合成实体
- 不支持一条源命令拆成多条目标命令或跨视图分解
- 实体定义缺失不提供 AI 兜底
