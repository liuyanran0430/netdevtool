"""知识库文档索引 Celery 任务。"""

from app.logging_config import logging_context
from app.services.knowledge_document_service import run_index_task
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="knowledge.index_document")
def index_knowledge_document(self, doc_id: int) -> None:
    with logging_context(task_id=self.request.id):
        run_index_task(doc_id)
