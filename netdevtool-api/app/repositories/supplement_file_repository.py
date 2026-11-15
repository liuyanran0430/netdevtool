"""补充知识库文件仓储：supplements 目录下 YAML 的读写与枚举。"""

from __future__ import annotations

from pathlib import Path

import yaml

from app.translate_rule.loader import default_knowledge_dir

_SUPPLEMENT_DIR = "supplements"


class SupplementFileRepository:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        root = Path(base_dir).expanduser().resolve() if base_dir else default_knowledge_dir()
        self.base_dir = root / _SUPPLEMENT_DIR

    def write(self, vendor: str, device_type: str, slug: str, document: dict) -> Path:
        """写入补充条目，返回落盘路径。"""
        directory = self.base_dir / vendor.strip().lower() / device_type.strip().lower()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{slug}.yaml"
        text = yaml.safe_dump(document, allow_unicode=True, sort_keys=False)
        path.write_text(text, encoding="utf-8")
        return path

    def list(self) -> list[dict]:
        """枚举补充条目：返回文件信息与解析后的 YAML。"""
        if not self.base_dir.is_dir():
            return []
        items: list[dict] = []
        for path in sorted(self.base_dir.rglob("*.yaml")):
            try:
                raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001  单个文件损坏不影响列表
                continue
            if not isinstance(raw, dict):
                continue
            items.append(
                {
                    "path": path.relative_to(self.base_dir).as_posix(),
                    "raw": raw,
                }
            )
        return items

    def delete(self, supplement_id: str) -> bool:
        """按条目 id 删除文件，供人工回收。"""
        for path in self.base_dir.rglob("*.yaml"):
            try:
                raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            if isinstance(raw, dict) and str(raw.get("id")) == supplement_id:
                path.unlink()
                return True
        return False
