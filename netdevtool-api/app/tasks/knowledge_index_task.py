"""知识库文档索引 Celery 任务。"""

from app.services.knowledge_document_service import run_index_task
from app.tasks.celery_app import celery_app


@celery_app.task(name="knowledge.index_document")
def index_knowledge_document(doc_id: int) -> None:
    run_index_task(doc_id)
