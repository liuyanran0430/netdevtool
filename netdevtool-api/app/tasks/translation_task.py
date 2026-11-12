"""配置翻译 Celery 任务。"""

from app.services.translation_service import run_translation_task
from app.tasks.celery_app import celery_app


@celery_app.task(name="translations.translate_configuration")
def translate_configuration(request_id: str) -> None:
    run_translation_task(request_id)
