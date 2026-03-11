import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
from app.celery_app import celery_app
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

@celery_app.task(name='app.tasks.notifications.send_report_email', max_retries=3, queue='notifications')
def send_report_email(user_id: str, session_id: str):
    logger.info(f'📧 Sending report email to user {user_id} for session {session_id}')
    return {'status': 'sent', 'user_id': user_id}

@celery_app.task(name='app.tasks.notifications.send_weekly_progress_digest', queue='notifications')
def send_weekly_progress_digest(user_id: str):
    logger.info(f'📧 Sending weekly digest to user {user_id}')
    return {'status': 'sent'}

@celery_app.task(name='app.tasks.notifications.generate_weekly_digests_all_users', queue='notifications')
def generate_weekly_digests_all_users():
    logger.info('📧 Generating weekly digests for all users')
    return {'users_queued': 0}