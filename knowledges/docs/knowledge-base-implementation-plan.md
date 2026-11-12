# 知识库加载与命令渲染服务 · 实施计划

> 状态：计划阶段（未落地代码）
> 适用范围：NetDevTool 配置翻译功能
> 方案基调：规范实体（`entities/`）+ 厂商实现（`vendors/{vendor}/{device_type}/`）+ `common` 回退

---

## 一、总体架构

```
HTTP/Celery
   ↓
translation_service（编排：状态流转、结果落库）
   ↓
knowledge_service（对外单一入口：translate_text）
   ↓
app/translate_rule/
   ├── models.py     YAML 契约的 Pydantic 模型
   ├── loader.py     扫描目录、解析、校验、构建索引
   ├── registry.py   索引缓存 + 路径解析 + common 回退
   ├── parser.py     模板→正则、视图状态机、源命令解析
   └── renderer.py   目标命令渲染、视图切换、tone/warning 产出
```

职责边界：

| 层 | 职责 | 不做 |
|---|---|---|
| `repositories` | 查 `devices` 表拿 `vendor_en / device_type` | 不读文件 |
| `translate_rule/*` | 读 YAML、匹配、渲染 | 不碰数据库 |
| `knowledge_service` | 组合设备档案 + 知识库，产出翻译结果 | 不写任务状态 |
| `translation_service` | 状态流转、结果 JSON 落库 | 不做语法解析 |

---

## 二、YAML 契约扩展

### 1. 规范实体 `entities/{entity_id}.yaml`

保留现有字段，新增可选字段：

```yaml
id: port_access_vlan
domain: vlan
description: "..."
view_path: ["system-view", "interface {intf}"]
parameters:
  intf:
    type: string
    required: true
    pattern: '\S+'          # 新增：自定义正则，缺省按 type 推导
  vlan_id:
    type: int
    range: [1, 4094]
    required: true
semantic_notes: [...]
```

### 2. 厂商实现 `vendors/{vendor}/{device_type}/{entity_id}.yaml`

已补 `device_type`，建议再扩展：

```yaml
entity_id: port_access_vlan
vendor: huawei
device_type: switch
product: CE6857-48S6CQ
os: V200R023C00
applies_to:
  products: ["CE6857-48S6CQ", "S5731-H48T4XC"]   # 可选，缺省按 product 精确匹配
supported: true
confidence: high
pre_commands: [...]
command: "..."
view: interface
verified: true
warnings: [...]
sources: [...]
```

校验规则（`models.py`）：

- `entity_id` 必须存在于 `entities/`，否则该文件加载失败并记录
- 同一 `(vendor, device_type, entity_id)` 重复定义 → 加载失败
- `device_type` 必须与所在目录名一致，否则告警
- `supported: false` 时 `command` 可为空，但必须带 `unsupported_reason`

---

## 三、加载与索引（`loader.py` + `registry.py`）

**加载流程**

1. 读取 `settings.KNOWLEDGE_BASE_DIR`（新增配置，默认项目根 `knowledges`）
2. 先加载 `entities/*.yaml`，建立 `entity_id → EntitySpec`
3. 再扫描 `vendors/{vendor}/{device_type}/*.yaml` 与 `vendors/{vendor}/common/*.yaml`
4. Pydantic 校验 + 交叉校验，构建三级索引：

```
(vendor, device_type, entity_id) → Implementation
(vendor, "common", entity_id)    → Implementation
```

**缓存策略**

- 进程内单例 `Registry`，加载一次常驻
- 开发开关 `KNOWLEDGE_RELOAD_ON_CHANGE`：按文件 `mtime` 懒刷新，默认关闭
- FastAPI 用 `lifespan` 预热；Celery Worker 在 import 时加载
- 加载统计打日志：实体数、实现数、跳过文件及原因

**路径解析优先级**（`registry.resolve(vendor_en, device_type, entity_id)`）

1. `{vendor}/{device_type}/{entity_id}.yaml`
2. `{vendor}/common/{entity_id}.yaml`
3. 返回 `None` → 该实体目标侧不支持

**关键细节**

- `vendor_en` 一律 `lower()`，因为库里的值是 `Huawei / H3C`
- 目录不存在不报错，视为该组合无实现

---

## 四、设备档案解析（不改接口）

推荐**查 `devices` 表**，而不是给 `POST /translations` 加 `device_type`：

- 新增 `DeviceRepository.get_by_vendor_and_model(vendor, model)`
- 返回 `vendor_en`、`device_type`
- 型号归一化：`CE6857-48S6CQ/V200R024C00` → `product=CE6857-48S6CQ`、`version=V200R024C00`
- 匹配顺序：`applies_to.products` 命中 → `product` 精确 → 只按 `(vendor, device_type)` 命中（confidence 降级 + warning）
- 版本号只用于置信度提示，不做硬匹配（现有数据 `V200R024C00` 与 YAML `V200R023C00` 已不一致）
- 查不到档案 → 任务 `failed`，`error="未找到设备档案"`

好处：前端下拉本来就来自 `devices` 表，无需改请求契约和类型。

---

## 五、源配置解析（`parser.py`）

这是整个方案的核心，必须按**视图状态机**做，不能逐行独立匹配。

### 1. 模板 → 正则

- 输出行首尾锚定 `^\s*...\s*$`，`re.IGNORECASE`，空白统一 `\s+`
- 参数按类型生成命名分组：
  - `int` → `(?P<name>\d+)`
  - `vlan_list` → `(?P<name>\d+(?:\s+(?:to\s+\d+|,?\s*\d+))*|\d+(?:[, ]\d+)+)`
  - `prefix / mask` → IPv4 正则
  - `string` → `(?P<name>\S+)`；位于行尾时用 `(?P<name>.+?)`
- 加载时**预编译**，按命令首个字面量关键字分桶（`port` / `ip` / `switchport`），避免全量遍历

### 2. 视图状态机

维护 `current_view` 与上下文变量（如 `intf`）：

- 用实体的 `view_path` 反推进入视图的正则，例如 `interface {intf}` → `^interface\s+(?P<intf>\S+)$`
- 处理 `quit` / `return` 的退出
- 遇到新的 `interface X` 隐式切换上下文并覆盖 `intf`
- 匹配优先级：视图切换 → `pre_commands` → `command`
- `pre_commands` 命中后标记该实体已激活；紧随的 `command` 才合成一条完整实体
- 同一行命中多个模板时按「字面量更长、参数更少」排序，冲突记 warning

### 3. 未匹配行

不丢弃，原样输出 `tone="muted"` 并附 warning，保证行号与源文件对齐。

---

## 六、命令渲染（`renderer.py`）

对每个解析出的实体，用**目标侧实现**渲染：

1. 参数校验：`required`、`type`、`range`、`pattern`；不通过则该行 `warn` + warning，不渲染
2. 目标 `supported: false` → 输出注释行 `# 目标设备不支持: {entity_id}`，`tone="warn"`
3. 计算视图路径：`entity.view_path` + 目标实现 `view`
4. 输出顺序：视图进入指令 → `pre_commands` → `command`
5. 相邻相同视图去重，避免反复 `system-view`
6. 缩进：子视图（`interface` 内）统一两空格，沿用现有页面展示风格

**接口命名（V1 明确限制）**

- `intf` 直传不翻译（华为 `10GE1/0/1` ≠ 华三 `Ten-GigabitEthernet1/0/1`）
- 输出行 `tone="warn"` + warning：`接口名未做厂商映射，请人工确认`
- V2 再新增 `entities/interface_name.yaml` 做规范化与反向渲染，解析顺序为「型号级 → device_type → common」

---

## 七、结果契约与 tone 规则

`result_json` 扩展（DB 结构不变，只扩展 JSON）：

```json
{
  "lines": [{ "no": 1, "text": "...", "tone": "success" }],
  "summary": { "total": 18, "translated": 12, "unsupported": 3, "duration_ms": 120 },
  "warnings": [{ "no": 6, "message": "接口名未做厂商映射，请人工确认" }],
  "meta": {
    "source": { "vendor": "huawei", "device_type": "switch", "product": "CE6857-48S6CQ" },
    "target": { "vendor": "h3c", "device_type": "switch", "product": "S6800-54HF" },
    "entities_used": ["port_access_vlan", "port_trunk_vlan"]
  }
}
```

tone 映射规则：

| tone | 场景 |
|---|---|
| `success` | 精确渲染成功 |
| `focus` | 关键命令（V1 可暂不用） |
| `warn` | 接口名未翻译、参数降级、`verified=false`、目标不支持 |
| `muted` | 注释、空行、未匹配原样保留 |

只有基础设施异常（设备档案缺失、知识库加载失败）才把任务置 `failed`；业务性不支持一律 `succeeded` + 行级 warning。

---

## 八、服务集成

修改 `app/services/translation_service.py`：

- 删除 `time.sleep(5)` 与「源文本原样回显」
- `run_translation_task` 内改为：查设备档案 → 调 `knowledge_service.translate_text` → 序列化结果
- 保留现有状态流转与取消逻辑（已通过验证，不动）
- 新增 `app/services/knowledge_service.py` 作为唯一对外入口

配置与依赖：

- `config.py` 新增 `KNOWLEDGE_BASE_DIR`、`KNOWLEDGE_RELOAD_ON_CHANGE`
- `.env.example` 同步补充
- `requirements.txt` 显式加入 `pyyaml`（当前是间接依赖）

---

## 九、前端调整

- `src/api/translations.ts`：`TranslationResult` 增加 `warnings`、`summary` 新字段、`meta`（可选，向后兼容）
- `src/pages/TranslatePage.tsx`：状态行展示「已翻译 / 不支持 / 待确认」数量；warning 行沿用 `warn` 样式
- tone 与 `CodeLine.state`（`focus | success | warn | muted`）已完全对齐，无需改动数据层

---

## 十、测试计划

**单元测试**

- `loader`：合法/非法 YAML、重复键、`device_type` 目录不一致
- `registry`：三级命中、common 回退、`vendor_en` 大小写
- `parser`：模板→正则各参数类型、视图进入/切换/退出、一行多匹配、未匹配行
- `renderer`：参数校验、`supported: false`、视图去重、tone/warning

**金样例测试**

- 固定输入片段 + 期望输出，覆盖 `huawei→h3c`、`huawei→zte`、`h3c→huawei`
- 至少包含 access VLAN、trunk VLAN、静态路由三类实体

**集成测试**

- Celery 用 `task_always_eager=True`，不依赖 Redis
- `POST → 轮询 → succeeded`，校验 `result_json` 结构

**回归**

- 现有 `pytest` 2 项必须继续通过
- 前端 `npm run lint` + `npm run build`

---

## 十一、实施顺序与验收标准

| 阶段 | 内容 | 验收标准 |
|---|---|---|
| 1 | YAML 契约模型 + 加载校验 | 启动时能打印实体/实现数量，坏文件有明确日志 |
| 2 | 索引与路径回退 | 三级命中与 common 回退单测全绿 |
| 3 | 设备档案解析 | 6 台设备均能解析出 `vendor_en / device_type` |
| 4 | 模板→正则 + 视图状态机 | 三类实体可正确识别并抽取参数 |
| 5 | 渲染器 | 三类实体可渲染出目标命令，tone/warning 正确 |
| 6 | 接入 Celery 任务 | 端到端真实翻译，替换 sleep 占位 |
| 7 | 前端结果展示 | 显示翻译数/不支持数，warning 可定位行号 |
| 8 | 金样例与集成测试 | 三组厂商组合用例通过 |
| 9 | （V2）接口名映射 | 接口名可跨厂商转换 |

---

## 十二、风险与 V1 边界

| 风险 | 说明 | 应对 |
|---|---|---|
| 接口命名差异 | 华为/华三/中兴命名体系不同 | V1 不翻译，标 `warn`；V2 引入映射实体 |
| 视图嵌套与退出 | `quit`/`return` 语义、隐式切换 | 状态机显式建模，配单测 |
| 命令顺序依赖 | 先删后加、`undo` 语义 | V1 仅做语法级翻译，不做等价性保证 |
| 型号/版本差异 | YAML `os` 与库内版本不一致 | 只做产品级匹配，版本仅影响 confidence |
| 续行与注释 | `#`、缩进、多行命令 | V1 原样保留并标 `muted` |
| 匹配歧义 | 短命令多实体命中 | 按特异性排序 + 冲突 warning |
| 性能 | 实体增加后逐行正则 | 加载期预编译 + 首关键字分桶 |

**V1 明确不做**：接口名自动转换、语义等价性校验、命令顺序重排、`undo` 反向翻译、多行命令合并。

---

## 附：当前知识库结构

```
knowledges/
  entities/
    port_access_vlan.yaml
    port_trunk_vlan.yaml
    static_route.yaml
  vendors/
    huawei/switch/{port_access_vlan,port_trunk_vlan,static_route}.yaml
    h3c/switch/{port_access_vlan,port_trunk_vlan,static_route}.yaml
    zte/switch/{port_access_vlan,port_trunk_vlan,static_route}.yaml
```

- 厂商实现文件均已含 `device_type: switch`
- `common/`、`firewall/` 目录按需再建，当前无防火墙实现内容
