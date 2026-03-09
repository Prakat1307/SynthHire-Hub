from sqlalchemy.orm import Session
from ..shared.models import Company, InterviewTemplate, Question
from ..shared.database import SessionLocal
import json

def seed_companies(db: Session):
    companies_data = [
        {
            "name": "Google",
            "slug": "google",
            "description": "Search engine giant and technology leader",
            "difficulty_level": "hard",
            "typical_rounds": ["phone_screen", "coding", "coding", "system_design", "behavioral", "googleyness"],
            "interview_style": {
                "coding": "Emphasis on optimal solutions, discuss multiple approaches",
                "system_design": "Expect back-of-envelope calculations",
                "behavioral": "Values data-driven decision making"
            }
        },
        {
            "name": "Meta",
            "slug": "meta",
            "description": "Social media and technology company",
            "difficulty_level": "hard",
            "typical_rounds": ["phone_screen", "coding", "coding", "system_design", "behavioral"],
            "interview_style": {
                "coding": "Focus on communication and problem-solving process",
                "system_design": "Scale-focused designs",
                "behavioral": "Value impact and leadership"
            }
        },
        {
            "name": "Amazon",
            "slug": "amazon",
            "description": "E-commerce and cloud computing leader",
            "difficulty_level": "moderate",
            "typical_rounds": ["phone_screen", "coding", "system_design", "behavioral", "bar_raiser"],
            "interview_style": {
                "coding": "Leadership principles evaluation throughout",
                "system_design": "Cost-efficiency and operational excellence",
                "behavioral": "STAR method strictly followed"
            }
        },
        {
            "name": "Generic Startup",
            "slug": "startup",
            "description": "Fast-paced startup environment",
            "difficulty_level": "moderate",
            "typical_rounds": ["phone_screen", "technical", "culture_fit"],
            "interview_style": {
                "coding": "Practical problem-solving",
                "behavioral": "Culture fit and adaptability"
            }
        }
    ]
    
    for company_data in companies_data:
        existing = db.query(Company).filter(Company.slug == company_data["slug"]).first()
        if not existing:
            company = Company(**company_data)
            db.add(company)
    
    db.commit()

def seed_templates(db: Session):
    google = db.query(Company).filter(Company.slug == "google").first()
    meta = db.query(Company).filter(Company.slug == "meta").first()
    
    if google:
        templates = [
            {
                "company_id": google.id,
                "role": "Software Engineer II",
                "round_type": "coding",
                "experience_level": "mid",
                "persona_type": "tough_lead",
                "system_prompt": "Google technical interview...",
                "persona_vector": {
                    "warmth": 0.2,
                    "hint_frequency": 0.1,
                    "probe_depth": 0.95,
                    "ambiguity_level": 0.4,
                    "pace_pressure": 0.8,
                    "encouragement": 0.1,
                    "interruption": 0.6
                },
                "difficulty_range": {"min": 6, "max": 9},
                "duration_minutes": 45
            },
            {
                "company_id": google.id,
                "role": "Software Engineer II",
                "round_type": "system_design",
                "experience_level": "mid",
                "persona_type": "collaborative_peer",
                "system_prompt": "Google system design interview...",
                "persona_vector": {
                    "warmth": 0.8,
                    "hint_frequency": 0.5,
                    "probe_depth": 0.6,
                    "ambiguity_level": 0.3,
                    "pace_pressure": 0.4,
                    "encouragement": 0.7,
                    "interruption": 0.2
                },
                "difficulty_range": {"min": 7, "max": 10},
                "duration_minutes": 60
            }
        ]
        
        for template_data in templates:
            existing = db.query(InterviewTemplate).filter(
                InterviewTemplate.company_id == template_data["company_id"],
                InterviewTemplate.role == template_data["role"],
                InterviewTemplate.round_type == template_data["round_type"]
            ).first()
            
            if not existing:
                template = InterviewTemplate(**template_data)
                db.add(template)
    
    db.commit()

def seed_questions(db: Session):
    google = db.query(Company).filter(Company.slug == "google").first()
    
    if google:
        questions = [
            {
                "company_id": google.id,
                "question_text": "Given an array of integers, return indices of two numbers that add up to a target.",
                "question_type": "coding",
                "difficulty": 5,
                "topics": ["arrays", "hash_tables"],
                "starter_code": {
                    "python": "def two_sum(nums, target):\n    pass",
                    "javascript": "function twoSum(nums, target) {\n    \n}"
                },
                "test_cases": [
                    {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
                    {"input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]}
                ],
                "expected_complexity": {"time": "O(n)", "space": "O(n)"},
                "source": "leetcode"
            },
            {
                "company_id": google.id,
                "question_text": "Design a URL shortening service like bit.ly",
                "question_type": "system_design",
                "difficulty": 8,
                "topics": ["distributed_systems", "databases", "scalability"],
                "design_requirements": {
                    "functional": ["Shorten URLs", "Redirect to original", "Custom aliases"],
                    "non_functional": ["High availability", "Low latency", "Handle 100M URLs/day"]
                },
                "key_discussion_points": [
                    "Encoding algorithm",
                    "Database choice",
                    "Caching strategy",
                    "Rate limiting",
                    "Analytics"
                ],
                "source": "system_design_primer"
            }
        ]
        
        for q_data in questions:
            existing = db.query(Question).filter(
                Question.company_id == q_data["company_id"],
                Question.question_text == q_data["question_text"]
            ).first()
            
            if not existing:
                question = Question(**q_data)
                db.add(question)
    
    db.commit()

def run_seed():
    db = SessionLocal()
    try:
        print("Seeding companies...")
        seed_companies(db)
        print("Seeding templates...")
        seed_templates(db)
        print("Seeding questions...")
        seed_questions(db)
        print("Seed completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
