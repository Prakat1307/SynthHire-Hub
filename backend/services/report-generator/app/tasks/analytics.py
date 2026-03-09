import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.celery_app import celery_app
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta

logger = get_task_logger(__name__)

@celery_app.task(name="app.tasks.analytics.update_progress_snapshot", queue="analytics")
def update_progress_snapshot(user_id: str):

    logger.info(f"📈 Updating progress for user {user_id}")
    return {"user_id": user_id}

@celery_app.task(name="app.tasks.analytics.refresh_materialized_views", queue="analytics")
def refresh_materialized_views():

    logger.info("🔄 Refreshing materialized views")
    return {"status": "refreshed"}

@celery_app.task(name="app.tasks.analytics.cleanup_stale_sessions", queue="analytics")
def cleanup_stale_sessions():

    logger.info("🧹 Cleaning stale sessions")
    return {"cleaned": 0}

@celery_app.task(name="app.tasks.analytics.aggregate_cohort_analytics", queue="analytics")
def aggregate_cohort_analytics():

    logger.info("📊 Aggregating cohort analytics")
    return {"status": "completed"}

@celery_app.task(name="app.tasks.analytics.cleanup_expired_data", queue="analytics")
def cleanup_expired_data():

    logger.info("🗑️ Cleaning expired data")
    return {"status": "completed"}

@celery_app.task(name="app.tasks.analytics.purge_old_emotional_data", queue="analytics")
def purge_old_emotional_data():

    logger.info("🗑️ Purging old emotional data")
    return {"status": "completed"}