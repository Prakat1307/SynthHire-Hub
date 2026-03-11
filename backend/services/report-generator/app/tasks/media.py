import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
from app.celery_app import celery_app
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

@celery_app.task(name='app.tasks.media.process_session_recording', max_retries=3, queue='media')
def process_session_recording(session_id: str):
    logger.info(f'🎙️ Processing recording for session {session_id}')
    return {'status': 'processed'}

@celery_app.task(name='app.tasks.media.render_whiteboard_snapshots', queue='media')
def render_whiteboard_snapshots(session_id: str):
    logger.info(f'🎨 Rendering whiteboard for session {session_id}')
    return {'status': 'completed'}