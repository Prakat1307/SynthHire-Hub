import sys
import os
sys.path.append('/app')
try:
    from shared.database import engine, Base, SessionLocal
    from shared.models import User, UserProfile, Subscription, Company, InterviewTemplate
    print('Successfully imported shared modules.')
except ImportError as e:
    print(f'Import Error: {e}')
    sys.exit(1)

def init_db():
    print('Creating tables...')
    try:
        Base.metadata.create_all(bind=engine)
        print('Tables created.')
    except Exception as e:
        print(f'Error creating tables: {e}')
        return
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == 'test@synthhire.com').first()
        if not user:
            print('Creating default user...')
            user = User(email='test@synthhire.com', full_name='Test User', auth_provider='email', is_email_verified=True)
            db.add(user)
            db.commit()
            db.refresh(user)
            profile = UserProfile(user_id=user.id, target_company='Google', target_role='Senior Software Engineer', experience_level='Senior', years_of_experience=5, preferred_language='python')
            db.add(profile)
            subscription = Subscription(user_id=user.id, plan='pro', status='active')
            db.add(subscription)
            db.commit()
            print('Default user created.')
        else:
            print('Default user already exists.')
        company = db.query(Company).filter(Company.slug == 'google').first()
        if not company:
            print('Creating Google company...')
            company = Company(name='Google', slug='google', description='Search giant.', difficulty_level='hard')
            db.add(company)
            db.commit()
            db.refresh(company)
            template = InterviewTemplate(company_id=company.id, role='Senior Software Engineer', round_type='coding', persona_type='tough_lead', system_prompt='You are a tough Google tech lead...', persona_vector={'warmth': 0.2, 'toughness': 0.9})
            db.add(template)
            db.commit()
            print('Default company created.')
        else:
            print('Default company already exists.')
    except Exception as e:
        print(f'Error seeding data: {e}')
    finally:
        db.close()
if __name__ == '__main__':
    init_db()