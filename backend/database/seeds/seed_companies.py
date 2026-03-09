
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from shared.database import get_session
from shared.models.tables import Company

COMPANIES = [
    {
        "name": "Google", "slug": "google", "difficulty_level": "hard",
        "glassdoor_rating": 4.5,
        "typical_rounds": ["phone_screen", "coding", "coding", "system_design", "behavioral"],
        "interview_style": {
            "coding": {
                "focus": ["algorithms", "data_structures", "optimization"],
                "style": "Emphasis on optimal solutions, discuss multiple approaches",
                "time": "45 minutes per round"
            },
            "system_design": {
                "focus": ["scalability", "distributed_systems", "data_modeling"],
                "style": "Expect back-of-envelope calculations, discuss trade-offs",
            },
            "behavioral": {
                "framework": "Googleyness + Leadership",
                "focus": ["collaboration", "ambiguity", "impact"],
            }
        }
    },
    {
        "name": "Meta", "slug": "meta", "difficulty_level": "hard",
        "glassdoor_rating": 4.3,
        "typical_rounds": ["phone_screen", "coding", "coding", "system_design", "behavioral"],
        "interview_style": {
            "coding": {
                "focus": ["graphs", "dynamic_programming", "strings"],
                "style": "Fast-paced, 2 questions in 45 minutes",
            },
            "system_design": {
                "focus": ["social_media_scale", "real_time_systems", "news_feed"],
                "style": "Product-focused design questions",
            }
        }
    },
    {
        "name": "Amazon", "slug": "amazon", "difficulty_level": "hard",
        "glassdoor_rating": 4.1,
        "typical_rounds": ["online_assessment", "phone_screen", "coding", "system_design", "behavioral", "behavioral"],
        "interview_style": {
            "behavioral": {
                "framework": "Leadership Principles (16 LPs)",
                "focus": ["customer_obsession", "ownership", "bias_for_action", "dive_deep"],
                "style": "Every round has LP questions. Use STAR method.",
            },
            "coding": {
                "focus": ["arrays", "trees", "graphs", "dynamic_programming"],
                "style": "Clean code expected, discuss complexity",
            }
        }
    },
    {
        "name": "Microsoft", "slug": "microsoft", "difficulty_level": "moderate",
        "glassdoor_rating": 4.4,
        "typical_rounds": ["phone_screen", "coding", "coding", "system_design", "behavioral"],
        "interview_style": {
            "coding": {
                "focus": ["problem_solving", "clean_code", "testing"],
                "style": "Collaborative, interviewer helps guide",
            }
        }
    },
    {
        "name": "Apple", "slug": "apple", "difficulty_level": "hard",
        "glassdoor_rating": 4.2,
        "typical_rounds": ["phone_screen", "coding", "system_design", "domain_specific", "behavioral"],
    },
    {
        "name": "Netflix", "slug": "netflix", "difficulty_level": "very_hard",
        "glassdoor_rating": 4.0,
        "typical_rounds": ["phone_screen", "technical_deep_dive", "system_design", "culture_fit"],
    },
    {
        "name": "Stripe", "slug": "stripe", "difficulty_level": "hard",
        "glassdoor_rating": 4.3,
        "typical_rounds": ["phone_screen", "coding", "system_design", "debugging", "integration"],
    },
]

async def seed_companies():

    async with get_session() as session:
        print("🏢 Seeding companies...")
        
        for company_data in COMPANIES:
            
            result = await session.execute(
                "SELECT id FROM companies WHERE slug = :slug",
                {"slug": company_data["slug"]}
            )
            existing = result.fetchone()
            
            if not existing:
                company = Company(**company_data)
                session.add(company)
                print(f"  ✅ Added: {company_data['name']}")
            else:
                print(f"  ⏩ Exists: {company_data['name']}")
        
        await session.commit()
        print("✅ Companies seeded")

if __name__ == "__main__":
    asyncio.run(seed_companies())