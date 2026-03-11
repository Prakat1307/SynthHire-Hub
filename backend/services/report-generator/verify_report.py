import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.tasks.reports import generate_debrief_report
from shared.models import get_engine, get_session_factory, InterviewSession, User
from app.config import settings
import uuid

def verify_report_generation():
    print('Testing Report Generation...')
    engine = get_engine(settings.database_url)
    SessionLocal = get_session_factory(engine)
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).first()
        if not session:
            print('No sessions found to generate report for.')
            return
        print(f'Generating report for session {session.id}...')
        if not session.dimension_scores:
            session.dimension_scores = {'technical_correctness': 0.8, 'communication_clarity': 0.7, 'problem_decomposition': 0.6}
            db.commit()
        result = generate_debrief_report(str(session.id))
        print('Result:', result)
        if result.get('status') == 'completed':
            print('✅ Report generated successfully!')
            print(f"URL: {result.get('pdf_url')}")
            pdf_path = os.path.join(os.path.dirname(__file__), '../app/static/reports', f'report_{session.id}.pdf')
            if os.path.exists(pdf_path):
                print(f'✅ PDF file verified at {pdf_path}')
            else:
                print(f'❌ PDF file missing at {pdf_path}')
        else:
            print('❌ Report generation failed')
    except Exception as e:
        print('Error:', e)
    finally:
        db.close()
if __name__ == '__main__':
    verify_report_generation()