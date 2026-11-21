"""问答只读工具：手册二次检索与设备档案查询。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.llm.tools.base import ToolResult, ToolSpec
from app.models import ChatQuestionMode
from app.rag.qa_retriever import retrieve_for_qa
from app.services.device_service import list_devices

TOOL_EVIDENCE_MAX_CHARS = 1000
MAX_DEVICE_RESULTS = 5


class SearchManualArgs(BaseModel):
    """手册二次检索参数。"""

    query: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="改写后的检索查询，使用手册中的专业术语，不要重复相同查询",
    )
    mode: Literal["command", "knowledge"] | None = Field(
        default=None, description="检索类型，留空沿用当前问答类型"
    )


class DeviceInfoArgs(BaseModel):
    """设备档案查询参数。"""

    vendor: str | None = Field(
        default=None, max_length=64, description="厂商，留空使用当前会话厂商"
    )
    model: str | None = Field(
        default=None, max_length=128, description="型号关键词，模糊匹配"
    )


class SearchFaultArgs(BaseModel):
    """故障手册二次检索参数。"""

    query: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="改写后的故障现象或关键词，使用手册术语，不要重复相同查询",
    )


def _device_info_result(
    db: Session, vendor: str | None, args: DeviceInfoArgs
) -> ToolResult:
    target_vendor = (args.vendor or vendor or "").strip()
    keyword = (args.model or "").strip().lower()
    # 会话厂商是英文 key（zte），设备表 vendor 列是中文名，两者都要匹配
    devices = [
        item
        for item in list_devices(db, vendor=None, device_type=None)
        if not target_vendor
        or item.vendor == target_vendor
        or (item.vendor_en or "").strip().lower() == target_vendor.lower()
        or item.vendor.lower() == target_vendor.lower()
    ]
    if keyword:
        devices = [item for item in devices if keyword in item.model.lower()]
    if not devices:
        return ToolResult("设备档案中未找到匹配的厂商或型号。")
    lines: list[str] = []
    for item in devices[:MAX_DEVICE_RESULTS]:
        manual = "有" if (item.manual_path or "").strip() else "无"
        lines.append(
            f"- {item.vendor} / {item.model}"
            f"（{item.device_type.value}，手册：{manual}）"
        )
    return ToolResult("设备档案查询结果：\n" + "\n".join(lines))


def _evidence_key(item: Any) -> tuple[Any, Any]:
    return (getattr(item, "doc_id", None), getattr(item, "point_id", None))


def _render_supplement(evidences: list[Any]) -> str:
    """补充证据独立编号，避免与主提示词里的 [证据N] 冲突。"""
    blocks: list[str] = []
    for index, item in enumerate(evidences, start=1):
        text = str(getattr(item, "text", "") or "")[:TOOL_EVIDENCE_MAX_CHARS]
        file_name = str(getattr(item, "file_name", "") or "未知文档")
        score = float(getattr(item, "score", 0.0) or 0.0)
        blocks.append(f"[补充{index}] {file_name}（相关度 {score:.2f}）\n{text}")
    return "\n\n".join(blocks)


def build_qa_tools(
    db: Session,
    *,
    vendor: str | None,
    default_mode: str,
    trace_id: str,
    existing: list[Any],
) -> list[ToolSpec]:
    """构造问答工具；handler 固定当前会话厂商，并跨轮去重已用证据。"""
    seen = {_evidence_key(item) for item in existing}

    def search_manual(args: SearchManualArgs) -> ToolResult:
        mode = args.mode or default_mode
        if mode not in {
            ChatQuestionMode.command.value,
            ChatQuestionMode.knowledge.value,
        }:
            mode = ChatQuestionMode.command.value
        result = retrieve_for_qa(
            db,
            query=args.query,
            mode=mode,
            vendor=vendor,
            trace_id=f"{trace_id}:tool",
        )
        new_items = [
            item for item in result.evidences if _evidence_key(item) not in seen
        ]
        for item in new_items:
            seen.add(_evidence_key(item))
        if not new_items:
            return ToolResult(
                "二次检索未命中新的手册内容。",
                meta={"top_score": result.top_score},
            )
        return ToolResult(
            content="二次检索补充证据：\n\n" + _render_supplement(new_items),
            evidences=new_items,
            meta={"top_score": result.top_score},
        )

    def get_device_info(args: DeviceInfoArgs) -> ToolResult:
        return _device_info_result(db, vendor, args)

    return [
        ToolSpec(
            name="search_manual",
            description=(
                "在当前厂商的设备手册知识库中按关键词重新检索（只读）。"
                "仅在现有证据不足、或需要换用手册术语重新检索时调用；"
                "query 应使用手册中的专业术语，不要重复相同查询。"
            ),
            args_model=SearchManualArgs,
            handler=search_manual,
            max_chars=1500,
        ),
        ToolSpec(
            name="get_device_info",
            description=(
                "查询设备档案中的厂商、型号、设备类型与是否有手册（只读）。"
                "用于确认型号或判断是否需要补充信息，不返回手册正文。"
            ),
            args_model=DeviceInfoArgs,
            handler=get_device_info,
            max_chars=800,
        ),
    ]


def build_fault_tools(
    db: Session,
    *,
    vendor: str | None,
    trace_id: str,
    existing: list[Any],
) -> list[ToolSpec]:
    """故障调查阶段的工具：只查故障手册与设备档案。"""
    seen = {_evidence_key(item) for item in existing}

    def search_fault_cases(args: SearchFaultArgs) -> ToolResult:
        result = retrieve_for_qa(
            db,
            query=args.query,
            mode=ChatQuestionMode.troubleshoot.value,
            vendor=vendor,
            trace_id=f"{trace_id}:fault-tool",
        )
        new_items = [
            item for item in result.evidences if _evidence_key(item) not in seen
        ]
        for item in new_items:
            seen.add(_evidence_key(item))
        if not new_items:
            return ToolResult(
                "故障手册中未检索到新的匹配内容。",
                meta={"top_score": result.top_score},
            )
        return ToolResult(
            content="故障手册补充证据：\n\n" + _render_supplement(new_items),
            evidences=new_items,
            meta={"top_score": result.top_score},
        )

    def get_device_info(args: DeviceInfoArgs) -> ToolResult:
        return _device_info_result(db, vendor, args)

    return [
        ToolSpec(
            name="search_fault_cases",
            description=(
                "在故障手册知识库中按现象或关键词重新检索（只读）。"
                "现有证据不足时调用；query 使用故障现象的专业描述，不要重复相同查询。"
            ),
            args_model=SearchFaultArgs,
            handler=search_fault_cases,
            max_chars=1500,
        ),
        ToolSpec(
            name="get_device_info",
            description=(
                "查询设备档案中的厂商、型号、设备类型与是否有手册（只读）。"
                "用于补全故障设备的型号与手册情况，不返回手册正文。"
            ),
            args_model=DeviceInfoArgs,
            handler=get_device_info,
            max_chars=800,
        ),
    ]
