"""知识库索引：进程内单例缓存与 `device_type → common` 回退查询。"""

import threading
from pathlib import Path

from app.translate_rule.loader import LoadResult, load_knowledge
from app.translate_rule.models import EntitySpec, Implementation, VendorProfile

COMMON_DEVICE_TYPE = "common"


class KnowledgeRegistry:
    """实体与厂商实现的内存索引。"""

    def __init__(self, result: LoadResult) -> None:
        self._result = result
        grouped: dict[tuple[str, str], list[Implementation]] = {}
        for (vendor, device_type, _), impl in result.implementations.items():
            grouped.setdefault((vendor, device_type), []).append(impl)
        self._grouped = grouped

    @classmethod
    def load(cls, base_dir: str | Path | None = None) -> "KnowledgeRegistry":
        return cls(load_knowledge(base_dir))

    @property
    def base_dir(self) -> Path:
        return self._result.base_dir

    @property
    def entities(self) -> dict[str, EntitySpec]:
        return self._result.entities

    @property
    def implementations(self) -> dict[tuple[str, str, str], Implementation]:
        return self._result.implementations

    @property
    def profiles(self) -> dict[tuple[str, str], VendorProfile]:
        return self._result.profiles

    @property
    def skipped(self) -> list[str]:
        return list(self._result.skipped)

    @property
    def warnings(self) -> list[str]:
        return list(self._result.warnings)

    def get_entity(self, entity_id: str) -> EntitySpec | None:
        return self._result.entities.get(entity_id)

    def resolve(
        self,
        vendor: str,
        device_type: str,
        entity_id: str,
    ) -> Implementation | None:
        """按 `厂商/设备类型` 查找实现，未命中时回退到 `common`。"""
        key = (vendor.strip().lower(), device_type.strip().lower(), entity_id)
        impl = self._result.implementations.get(key)
        if impl is not None:
            return impl
        return self._result.implementations.get((key[0], COMMON_DEVICE_TYPE, entity_id))

    def implementations_for(self, vendor: str, device_type: str) -> list[Implementation]:
        """返回某厂商某设备类型下所有可用实现，专属实现覆盖 common。"""
        vendor_key = vendor.strip().lower()
        device_key = device_type.strip().lower()
        merged = {
            impl.entity_id: impl for impl in self._grouped.get((vendor_key, COMMON_DEVICE_TYPE), [])
        }
        merged.update({impl.entity_id: impl for impl in self._grouped.get((vendor_key, device_key), [])})
        return [merged[entity_id] for entity_id in sorted(merged)]

    def get_profile(self, vendor: str, device_type: str) -> VendorProfile:
        """返回厂商视图配置，缺失时使用默认值。"""
        vendor_key = vendor.strip().lower()
        device_key = device_type.strip().lower()
        profile = self._result.profiles.get((vendor_key, device_key))
        if profile is None:
            profile = self._result.profiles.get((vendor_key, COMMON_DEVICE_TYPE))
        if profile is not None:
            return profile
        return VendorProfile(vendor=vendor_key, device_type=device_key)


_registry: KnowledgeRegistry | None = None
_registry_lock = threading.Lock()


def get_registry() -> KnowledgeRegistry:
    """获取进程内单例；首次调用时加载。"""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = KnowledgeRegistry.load()
    return _registry


def reload_registry(base_dir: str | Path | None = None) -> KnowledgeRegistry:
    """强制重新加载知识库，用于开发期热更新。"""
    global _registry
    with _registry_lock:
        _registry = KnowledgeRegistry.load(base_dir)
    return _registry
