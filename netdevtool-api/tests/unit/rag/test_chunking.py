"""文档切块：长度与重叠约束、父子上下文和 Q&A 结构识别。"""

import pytest

from app.rag.chunking import chunk_text
from app.rag.schema import ChunkingConfig, NeedManualError


def test_general_chunks_respect_max_length_and_carry_overlap() -> None:
    config = ChunkingConfig(
        general_delimiter="\\n\\n",
        general_max_length=20,
        general_overlap=5,
    )

    chunks = chunk_text("甲" * 25 + "\n\n" + "乙" * 10, config)

    assert len(chunks) == 3
    assert all(len(item.text) <= 20 for item in chunks)
    assert chunks[-1].text.startswith("甲" * 5)
    assert chunks[-1].text.endswith("乙" * 10)
    assert [item.index for item in chunks] == [0, 1, 2]


def test_parent_child_chunks_share_parent_text_and_heading_context() -> None:
    config = ChunkingConfig(
        mode="parent-child",
        parent_max_length=200,
        child_delimiter="\\n",
        child_max_length=40,
        heading_split_levels="1,2",
    )
    text = (
        "# 安装\n\n"
        "## 接口配置\n\n"
        "interface GigabitEthernet0/0/1\n"
        "description uplink"
    )

    chunks = chunk_text(text, config)

    assert [item.text for item in chunks] == [
        "## 接口配置\ninterface GigabitEthernet0/0/1",
        "description uplink",
    ]
    assert all(item.kind == "child" for item in chunks)
    assert {item.parent_index for item in chunks} == {0}
    assert len({item.parent_text for item in chunks}) == 1
    assert chunks[0].parent_text.startswith("安装\n\n## 接口配置")


def test_qa_chunks_extract_question_blocks_and_ignore_preface() -> None:
    config = ChunkingConfig(mode="qa", general_max_length=200)

    chunks = chunk_text(
        "说明：以下为客户常见问题。\nQ: 如何查看接口状态？\nA: 使用 display interface。\n\n"
        "问题：如何保存配置？\n答案：使用 save。",
        config,
    )

    assert len(chunks) == 2
    assert chunks[0].text == "Q: 如何查看接口状态？\nA: 使用 display interface。"
    assert chunks[1].text == "问题：如何保存配置？\n答案：使用 save。"
    assert "说明" not in "\n".join(item.text for item in chunks)


def test_qa_mode_requires_recognizable_structure() -> None:
    with pytest.raises(NeedManualError, match="未识别到 Q&A 结构"):
        chunk_text("这只是普通说明文字，没有问答标记。", ChunkingConfig(mode="qa"))
