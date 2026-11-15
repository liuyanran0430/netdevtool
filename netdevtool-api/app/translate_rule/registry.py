"""知识库索引：进程内单例缓存与 `device_type → common` 回退查询。"""

import re
import threading
from functools import lru_cache
from pathlib import Path

from app.translate_rule.loader import LoadResult, load_knowledge
from app.translate_rule.models import EntitySpec, Implementation, VendorProfile

COMMON_DEVICE_TYPE = "common"
_INTERFACE_NUMBER = r"(?P<number>[0-9][0-9/.:_-]*)"


@lru_cache(maxsize=None)
def _interface_pattern(template: str) -> re.Pattern[str]:
    """把 `Vlanif{number}` 这类模板编译为宽松匹配（忽略大小写与多余空格）。"""
    prefix, _, suffix = template.partition("{number}")
    return re.compile(
        r"^\s*" + re.escape(prefix) + r"\s*" + _INTERFACE_NUMBER + re.escape(suffix) + r"\s*$",
        re.IGNORECASE,
    )


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
        """规范实体索引，解析与渲染共用。"""
        return self._result.entities

    def get_entity(self, entity_id: str) -> EntitySpec | None:
        return self._result.entities.get(entity_id)

    def interface_templates(self, vendor: str, device_type: str) -> dict[str, str]:
        """返回厂商接口命名表，未命中时回退到 `common`。"""
        vendor_key = vendor.strip().lower()
        device_key = device_type.strip().lower()
        return (
            self._result.interfaces.get((vendor_key, device_key))
            or self._result.interfaces.get((vendor_key, COMMON_DEVICE_TYPE))
            or {}
        )

    def map_interface(
        self,
        intf: str,
        *,
        source_vendor: str,
        source_device_type: str,
        target_vendor: str,
        target_device_type: str,
    ) -> tuple[str, bool]:
        """按源厂商命名识别接口类型，再用目标厂商模板重写。

        返回 `(接口名, 是否映射成功)`；无法识别或目标厂商缺少同类型时原样返回。
        """
        source = self.interface_templates(source_vendor, source_device_type)
        target = self.interface_templates(target_vendor, target_device_type)
        for type_key, template in source.items():
            matched = _interface_pattern(template).match(intf)
            if matched is None:
                continue
            target_template = target.get(type_key)
            if not target_template:
                return intf, False
            return target_template.replace("{number}", matched.group("number")), True
        return intf, False

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
_registry_signature: tuple[tuple[str, int], ...] | None = None


def _supplements_signature(base_dir: Path) -> tuple[tuple[str, int], ...]:
    """补充知识库目录签名：文件路径 + 修改时间，用于热重载判断。"""
    supplements_dir = base_dir / "supplements"
    if not supplements_dir.is_dir():
        return ()
    signature: list[tuple[str, int]] = []
    for path in supplements_dir.rglob("*.yaml"):
        try:
            signature.append((path.as_posix(), path.stat().st_mtime_ns))
        except OSError:
            continue
    return tuple(sorted(signature))


def reload_registry() -> None:
    """标记知识库失效，下次 `get_registry()` 重新加载。"""
    global _registry, _registry_signature
    with _registry_lock:
        _registry = None
        _registry_signature = None


def get_registry() -> KnowledgeRegistry:
    """获取进程内单例；补充知识库文件变化时自动重建。"""
    global _registry, _registry_signature
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = KnowledgeRegistry.load()
                _registry_signature = _supplements_signature(_registry.base_dir)
        return _registry

    current = _supplements_signature(_registry.base_dir)
    if current == _registry_signature:
        return _registry
    with _registry_lock:
        if _registry is not None:
            current = _supplements_signature(_registry.base_dir)
            if current != _registry_signature:
                _registry = KnowledgeRegistry.load(_registry.base_dir)
                _registry_signature = current
    return _registry
