"""知识缺口仓储：knowledge_gaps 表读写唯一入口。"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DeviceType, KnowledgeGap, KnowledgeGapKind


class KnowledgeGapRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, gap_id: int) -> KnowledgeGap | None:
        return self.db.get(KnowledgeGap, gap_id)

    def upsert(
        self,
        *,
        vendor: str,
        device_type: DeviceType,
        product: str,
        os: str | None,
        view: str | None,
        command_template: str,
        raw_sample: str,
        request_id: str,
        kind: KnowledgeGapKind = KnowledgeGapKind.unknown_source,
        target_vendor: str = "",
        target_device_type: str = "",
    ) -> KnowledgeGap:
        """按作用域 + 命令模板聚合：已存在则累加次数并补充任务溯源。

        `missing_target_impl` 类缺口按目标厂商与目标设备类型区分，避免同一命令
        在不同目标上的置信度问题被合并；源侧未识别时目标维度为空。
        """
        stmt = select(KnowledgeGap).where(
            KnowledgeGap.vendor == vendor,
            KnowledgeGap.device_type == device_type,
            KnowledgeGap.product == product,
            func.coalesce(KnowledgeGap.os, "") == (os or ""),
            KnowledgeGap.target_vendor == (target_vendor or ""),
            KnowledgeGap.target_device_type == (target_device_type or ""),
            KnowledgeGap.command_template == command_template,
            KnowledgeGap.kind == kind,
        )
        gap = self.db.scalars(stmt).first()
        if gap is None:
            gap = KnowledgeGap(
                vendor=vendor,
                device_type=device_type,
                product=product,
                os=os,
                target_vendor=target_vendor or "",
                target_device_type=target_device_type or "",
                view=view,
                command_template=command_template,
                raw_sample=raw_sample,
                occurrences=1,
                kind=kind,
                request_ids=[request_id],
            )
            self.db.add(gap)
        else:
            gap.occurrences += 1
            # JSON 列按整体赋值才能被 SQLAlchemy 识别为变更
            request_ids = list(gap.request_ids or [])
            if request_id not in request_ids:
                request_ids.append(request_id)
            gap.request_ids = request_ids
            gap.updated_at = datetime.now()
            if not gap.view and view:
                gap.view = view
            if gap.status == "ignored":
                gap.status = "open"
        self.db.commit()
        self.db.refresh(gap)
        return gap

    def list_by_scope(self, *, vendor: str, product: str) -> list[KnowledgeGap]:
        """按厂商与型号取全部缺口，供审核条目关联 gap_id。"""
        stmt = select(KnowledgeGap).where(
            KnowledgeGap.vendor == vendor,
            KnowledgeGap.product == product,
        )
        return list(self.db.scalars(stmt))

    def list(
        self,
        *,
        limit: int = 20,
        kind: KnowledgeGapKind | None = None,
        status: str | None = None,
        vendor: str | None = None,
    ) -> list[KnowledgeGap]:
        stmt = select(KnowledgeGap)
        if kind is not None:
            stmt = stmt.where(KnowledgeGap.kind == kind)
        if status:
            stmt = stmt.where(KnowledgeGap.status == status)
        if vendor:
            stmt = stmt.where(KnowledgeGap.vendor == vendor)
        stmt = stmt.order_by(
            KnowledgeGap.occurrences.desc(), KnowledgeGap.updated_at.desc()
        ).limit(limit)
        return list(self.db.scalars(stmt).all())

    def update(self, gap: KnowledgeGap) -> KnowledgeGap:
        self.db.commit()
        self.db.refresh(gap)
        return gap
