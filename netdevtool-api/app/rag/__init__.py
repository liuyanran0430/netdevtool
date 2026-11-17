"""RAG 能力层：切块、编码、Qdrant 读写与检索。

本包只依赖 Qdrant SDK、embedding 模型与标准库，不导入 models、repositories、database；
知识库配置通过 dataclass 传入，便于单元测试与问答侧复用。
"""
