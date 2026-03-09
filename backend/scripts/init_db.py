import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.shared.database import engine, Base, SessionLocal
from backend.shared.models import User, UserProfile, Subscription, Company, InterviewTemplate
from backend.shared.config import BaseServiceSettings

def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

    db = SessionLocal()
    try:
        
        user = db.query(User).filter(User.email == "test@synthhire.com").first()
        if not user:
            print("Creating default user...")
            user = User(
                email="test@synthhire.com",
                full_name="Test User",
                auth_provider="email",
                is_email_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            profile = UserProfile(
                user_id=user.id,
                target_company="Google",
                target_role="Senior Software Engineer",
                experience_level="Senior",
                years_of_experience=5,
                preferred_language="python"
            )
            db.add(profile)
            
            subscription = Subscription(
                user_id=user.id,
                plan="pro",
                status="active"
            )
            db.add(subscription)
            db.commit()
            print("Default user created.")
        
        company = db.query(Company).filter(Company.slug == "google").first()
        if not company:
            print("Creating Google company...")
            company = Company(
                name="Google",
                slug="google",
                description="Search giant.",
                difficulty_level="hard"
            )
            db.add(company)
            db.commit()
            db.refresh(company)

            template = InterviewTemplate(
                company_id=company.id,
                role="Senior Software Engineer",
                round_type="coding",
                persona_type="tough_lead",
                system_prompt="You are a tough Google tech lead...",
                persona_vector={"warmth": 0.2, "toughness": 0.9}
            )
            db.add(template)
            db.commit()
            print("Default company created.")

    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
