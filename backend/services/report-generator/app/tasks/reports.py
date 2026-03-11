import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
from app.celery_app import celery_app
from celery import Task
from celery.utils.log import get_task_logger
import json
import hashlib
from datetime import datetime
from uuid import UUID
logger = get_task_logger(__name__)
DATABASE_URL = 'postgresql://synthhire:localdev123@postgres:5432/synthhire'

class IdempotentTask(Task):
    abstract = True

    def before_start(self, task_id, args, kwargs):
        import redis
        r = redis.from_url('redis://redis:6379/2')
        lock_key = f'task_lock:{self.name}:{hashlib.md5(json.dumps(args).encode()).hexdigest()}'
        if r.get(lock_key):
            logger.info(f'Task {task_id} already completed — skipping (idempotent)')
            raise self.retry(countdown=0, max_retries=0)
        r.setex(lock_key, 3600, 'running')

    def on_success(self, retval, task_id, args, kwargs):
        import redis
        r = redis.from_url('redis://redis:6379/2')
        lock_key = f'task_lock:{self.name}:{hashlib.md5(json.dumps(args).encode()).hexdigest()}'
        r.setex(lock_key, 3600, 'completed')

@celery_app.task(name='app.tasks.reports.generate_debrief_report', base=IdempotentTask, bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=600, retry_jitter=True, queue='reports')
def generate_debrief_report(self, session_id: str):
    logger.info(f'📝 Generating report for session {session_id}')
    from sqlalchemy.orm import Session
    from app.main import get_db, SessionLocal
    from shared.models.tables import InterviewSession, AssessmentReport, User
    from app.main import generate_coaching_narrative, identify_strengths, identify_improvement_areas, generate_action_items, calculate_readiness_score
    from jinja2 import Environment, FileSystemLoader
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    import os
    import io
    db: Session = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.id == UUID(session_id)).first()
        if not session or not session.dimension_scores:
            logger.error(f'Session {session_id} not found or incomplete')
            return {'status': 'failed', 'reason': 'incomplete_session'}
        user = db.query(User).filter(User.id == session.user_id).first()
        user_name = user.full_name if user else 'Candidate'
        report = db.query(AssessmentReport).filter(AssessmentReport.session_id == session.id).first()
        dimension_scores = session.dimension_scores
        narrative = report.coaching_narrative if report else 'Details pending...'
        strengths = report.strengths if report and report.strengths else identify_strengths(dimension_scores)
        improvements = report.improvement_areas if report and report.improvement_areas else identify_improvement_areas(dimension_scores)
        actions = report.action_items if report and report.action_items else generate_action_items(session.session_type, improvements)
        env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), '../templates')))
        template = env.get_template('report_template.html')
        html_content = template.render(user_name=user_name, target_role=session.target_role or 'Software Engineer', date=datetime.now().strftime('%B %d, %Y'), overall_score=round(session.overall_score or 0), coaching_narrative=narrative, dimension_scores=dimension_scores, strengths=strengths, improvement_areas=improvements, action_items=actions, session_id=str(session.id))
        pdf_dir = os.path.join(os.path.dirname(__file__), '../static/reports')
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_filename = f'report_{session_id}.pdf'
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph(f'Interview Assessment: {user_name}', styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Role:</b> {session.target_role or 'N/A'}", styles['Normal']))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Paragraph(f'<b>Overall Score:</b> {round(session.overall_score or 0)}%', styles['Normal']))
        story.append(Spacer(1, 24))
        story.append(Paragraph("<b>Coach's Feedback</b>", styles['Heading2']))
        story.append(Paragraph(narrative, styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph('<b>Dimension Scores</b>', styles['Heading2']))
        data = [['Dimension', 'Score']]
        for dim, score in dimension_scores.items():
            data.append([dim.replace('_', ' ').title(), f'{int(score * 100)}%'])
        t = Table(data, colWidths=[4 * inch, 2 * inch])
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, 0), 12), ('BACKGROUND', (0, 1), (-1, -1), colors.beige), ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        story.append(t)
        story.append(Spacer(1, 24))
        story.append(Paragraph('<b>Key Strengths</b>', styles['Heading3']))
        for s in strengths:
            story.append(Paragraph(f'• {s}', styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph('<b>Areas for Improvement</b>', styles['Heading3']))
        for i in improvements:
            story.append(Paragraph(f'• {i}', styles['Normal']))
        doc.build(story)
        pdf_url = f'/static/reports/{pdf_filename}'
        if report:
            report.report_html = html_content
            report.report_pdf_url = pdf_url
            report.generation_status = 'completed'
        else:
            pass
        db.commit()
        logger.info(f'✅ Report generated: {pdf_path}')
        return {'session_id': session_id, 'status': 'completed', 'pdf_url': pdf_url}
    except Exception as e:
        logger.error(f'❌ Report generation failed: {e}')
        return {'status': 'failed', 'error': str(e)}
    finally:
        db.close()