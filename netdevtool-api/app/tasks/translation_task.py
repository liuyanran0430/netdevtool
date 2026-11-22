"""配置翻译 Celery 任务。"""

from app.logging_config import logging_context
from app.services.translation_service import run_translation_task
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="translations.translate_configuration")
def translate_configuration(self, request_id: str) -> None:
    with logging_context(task_id=self.request.id):
        run_translation_task(request_id)
