import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.celery_app import celery_app
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@celery_app.task(name="app.tasks.ml_batch.compute_ideal_embeddings", max_retries=2, queue="ml_batch")
def compute_ideal_embeddings(question_id: str):

    logger.info(f"Computing embeddings for question {question_id}")
    return {"status": "success"}

@celery_app.task(name="app.tasks.ml_batch.compute_company_benchmarks", queue="ml_batch")
def compute_company_benchmarks():

    logger.info("📊 Computing company benchmarks")
    return {"status": "completed"}

@celery_app.task(name="app.tasks.ml_batch.evaluate_model_drift", queue="ml_batch")
def evaluate_model_drift():

    logger.info("🔍 Evaluating model drift")
    return {"status": "completed"}

@celery_app.task(name="app.tasks.ml_batch.retrain_deberta_if_needed", queue="ml_batch")
def retrain_deberta_if_needed():

    logger.info("🔄 Checking if DeBERTa retrain needed")
    return {"status": "checked"}