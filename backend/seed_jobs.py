import asyncio
from sqlalchemy.orm import Session
from shared.models.session import SessionLocal
from shared.models.tables import JobListing, JobStatus
from uuid import uuid4
import datetime
import random

def seed_jobs():
    db = SessionLocal()
    
    if db.query(JobListing).count() > 0:
        print("Jobs already seeded.")
        return

    company_names = ["Acme Corp", "TechNova", "Stark Industries", "Wayne Enterprises", "Globex Corporation"]
    titles = ["Senior Software Engineer", "Frontend Developer", "Backend Developer", "Full Stack Engineer", "Machine Learning Intern", "Product Manager"]
    locations = ["San Francisco, CA", "New York, NY", "Austin, TX", "London, UK", "Remote"]
    
    roles = [
        {"title": "Senior Frontend Engineer", "reqs": ["React", "TypeScript", "Next.js", "5+ years experience"], "remote": True, "salary": "$140k - $180k"},
        {"title": "Backend Services Lead", "reqs": ["Python", "FastAPI", "PostgreSQL", "System Design"], "remote": False, "loc": "San Francisco, CA", "salary": "$160k - $210k"},
        {"title": "Machine Learning Engineer", "reqs": ["PyTorch", "LLMs", "Python", "Docker"], "remote": True, "salary": "$150k - $190k"},
        {"title": "Full Stack Developer", "reqs": ["React", "Node.js", "MongoDB", "AWS"], "remote": False, "loc": "Austin, TX", "salary": "$120k - $150k"},
        {"title": "React Native Developer", "reqs": ["React Native", "iOS", "Android", "Mobile UI"], "remote": True, "salary": "$110k - $140k"},
        {"title": "DevOps Engineer", "reqs": ["Kubernetes", "AWS", "CI/CD", "Terraform"], "remote": False, "loc": "New York, NY", "salary": "$130k - $170k"},
    ]

    for role in roles:
        job = JobListing(
            id=uuid4(),
            title=role["title"],
            description=f"We are looking for an experienced {role['title']} to join our fast-growing engineering team. You will be responsible for designing, building, and maintaining scalable applications. \n\nWe offer competitive compensation, comprehensive benefits, and a culture that values innovation and work-life balance.",
            requirements=role["reqs"],
            location=role.get("loc"),
            is_remote=role["remote"],
            salary_range=role["salary"],
            status=JobStatus.PUBLISHED,
            published_at=datetime.datetime.utcnow(),
            external_url=f"https://example.com/jobs/{uuid4()}" if random.random() > 0.5 else None
        )
        db.add(job)
    
    db.commit()
    print("Seed complete! Added 6 dummy job listings.")

if __name__ == "__main__":
    seed_jobs()
