"""配置与环境变量。

所有可配置项集中在此读取，业务代码禁止直接访问 os.environ。
"""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    APP_NAME: str = "NetDevTool API"
    APP_ENV: str = "local"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # MySQL
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "netdev"

    # Redis（Celery broker；任务状态只存 MySQL）
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # 知识库目录，留空时使用项目根下的 knowledges
    KNOWLEDGE_BASE_DIR: str = ""

    # 跨域（逗号分隔）
    CORS_ORIGINS: str = "http://localhost:5175,http://127.0.0.1:5175"

    # 大模型（供 app/llm 使用）
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = ""

    @property
    def database_url(self) -> str:
        """SQLAlchemy 连接串（密码做 URL 转义）。"""
        password = quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{password}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
