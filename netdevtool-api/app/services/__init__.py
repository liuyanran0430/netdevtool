"""服务层：业务流程编排。

约定：
- 组合仓储、LLM、RAG、工具完成一个完整业务动作。
- 不直接拼接 SQL，不直接依赖 FastAPI 的 Request/Response。
"""
