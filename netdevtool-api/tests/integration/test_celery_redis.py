"""真实 Redis 集成：验证 Celery JSON 任务投递，不启动 Worker、不执行配置。"""

import os
from uuid import uuid4

import pytest
from celery import Celery

REDIS_URL = os.getenv("NETDEVTOOL_TEST_REDIS_URL", "")
pytestmark = [
    pytest.mark.integration,
    pytest.mark.celery_redis,
    pytest.mark.skipif(
        not REDIS_URL,
        reason="设置 NETDEVTOOL_TEST_REDIS_URL 为测试 Redis 后启用",
    ),
]


def test_celery_publishes_json_task_to_isolated_queue() -> None:
    broker = Celery(
        "netdevtool-pytest",
        broker=REDIS_URL,
        task_ignore_result=True,
        task_serializer="json",
        accept_content=["json"],
    )
    queue_name = f"pytest-{uuid4().hex}"

    result = broker.send_task(
        "pytest.noop",
        args=["payload"],
        queue=queue_name,
    )

    with (
        broker.connection() as connection,
        connection.SimpleQueue(queue_name) as queue,
    ):
        message = queue.get(timeout=5)
        try:
            assert message.payload["headers"]["task"] == "pytest.noop"
            assert message.payload["headers"]["id"] == result.id
            assert message.payload["headers"]["argsrepr"] == "('payload',)"
            assert message.payload["content-type"] == "application/json"
        finally:
            message.ack()
