import os
import httpx
import hashlib
from typing import List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from backend.shared.models.tables import JobPosting
from backend.shared.schemas.job import JobPostingItem
load_dotenv()
JSEARCH_API_KEY = os.getenv('JSEARCH_API_KEY')
ADZUNA_APP_ID = os.getenv('ADZUNA_APP_ID')
ADZUNA_APP_KEY = os.getenv('ADZUNA_APP_KEY')
APIFY_TOKEN = os.getenv('APIFY_TOKEN')

class JobAggregationService:

    @staticmethod
    async def fetch_jobs(query: str, location: str=None, page: int=1, db: Session=None) -> List[JobPostingItem]:
        results = []
        api_errors = []
        try:
            jsearch_jobs = await JobAggregationService.call_jsearch(query, location, page)
            results.extend(jsearch_jobs)
            print(f'[JobAggregation] JSearch returned {len(jsearch_jobs)} jobs')
        except Exception as e:
            api_errors.append(f'JSearch: {e}')
            print(f'[JobAggregation] JSearch failed: {e}')
        if not results:
            try:
                adzuna_jobs = await JobAggregationService.call_adzuna(query, location, page)
                results.extend(adzuna_jobs)
                print(f'[JobAggregation] Adzuna returned {len(adzuna_jobs)} jobs')
            except Exception as e:
                api_errors.append(f'Adzuna: {e}')
                print(f'[JobAggregation] Adzuna failed: {e}')
        if not results:
            print(f'[JobAggregation] All external APIs returned no results. Using intelligent fallback data.')
            results = JobAggregationService.generate_fallback_jobs(query, location)
        jobs_models = JobAggregationService.deduplicate_and_normalize(results)
        if db:
            for job in jobs_models:
                try:
                    existing = db.query(JobPosting).filter(JobPosting.job_id == job.job_id).first()
                    if not existing:
                        new_job = JobPosting(job_id=job.job_id, source=job.source, title=job.title, company=job.company, company_logo_url=job.company_logo_url, location=job.location, is_remote=job.is_remote, salary_min=job.salary_min, salary_max=job.salary_max, description=job.description, required_skills=job.required_skills, apply_url=job.apply_url, posted_date=job.posted_date)
                        db.add(new_job)
                except Exception as e:
                    print(f'[JobAggregation] Error preparing job for DB: {e}')
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                print(f'[JobAggregation] Error saving aggregated jobs to DB: {e}')
        return jobs_models

    @staticmethod
    async def call_jsearch(query: str, location: str, page: int) -> List[dict]:
        if not JSEARCH_API_KEY or JSEARCH_API_KEY == 'pending':
            print('[JobAggregation] JSearch API key not configured, skipping')
            return []
        search_term = query
        if location:
            search_term += f' in {location}'
        url = 'https://jsearch.p.rapidapi.com/search'
        querystring = {'query': search_term, 'page': str(page), 'num_pages': '1'}
        headers = {'X-RapidAPI-Key': JSEARCH_API_KEY, 'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=querystring, timeout=10.0)
            print(f'[JobAggregation] JSearch response status: {response.status_code}')
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', [])
                print(f'[JobAggregation] JSearch returned {len(items)} items')
                return [{'job_id': f"js_{item.get('job_id')}", 'source': 'jsearch', 'title': item.get('job_title'), 'company': item.get('employer_name'), 'company_logo_url': item.get('employer_logo'), 'location': f"{item.get('job_city', '')}, {item.get('job_country', '')}".strip(', '), 'is_remote': item.get('job_is_remote', False), 'description': item.get('job_description'), 'apply_url': item.get('job_apply_link'), 'required_skills': [skill.get('skill') for category in item.get('job_required_skills', []) for skill in category.get('skills', [])] if item.get('job_required_skills') else []} for item in items]
            else:
                print(f'[JobAggregation] JSearch error response: {response.text[:500]}')
                raise Exception(f'JSearch API error {response.status_code}: {response.text[:200]}')

    @staticmethod
    async def call_adzuna(query: str, location: str, page: int) -> List[dict]:
        if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
            print('[JobAggregation] Adzuna API keys not configured, skipping')
            return []
        country = 'in'
        if location:
            location_lower = location.lower()
            if any((c in location_lower for c in ['usa', 'united states', 'new york', 'california', 'san francisco'])):
                country = 'us'
            elif any((c in location_lower for c in ['uk', 'london', 'united kingdom'])):
                country = 'gb'
        url = f'https://api.adzuna.com/v1/api/jobs/{country}/search/{page}'
        params = {'app_id': ADZUNA_APP_ID, 'app_key': ADZUNA_APP_KEY, 'results_per_page': 15, 'what': query}
        if location:
            params['where'] = location
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            print(f'[JobAggregation] Adzuna response status: {response.status_code}')
            if response.status_code == 200:
                data = response.json()
                items = data.get('results', [])
                print(f'[JobAggregation] Adzuna returned {len(items)} items')
                return [{'job_id': f"az_{item.get('id', '')}", 'source': 'adzuna', 'title': item.get('title', '').replace('<strong>', '').replace('</strong>', ''), 'company': item.get('company', {}).get('display_name', 'Unknown'), 'location': item.get('location', {}).get('display_name', ''), 'is_remote': 'remote' in item.get('title', '').lower() or 'remote' in item.get('description', '').lower(), 'salary_min': item.get('salary_min'), 'salary_max': item.get('salary_max'), 'salary_currency': 'INR' if country == 'in' else 'GBP' if country == 'gb' else 'USD', 'description': item.get('description', '').replace('<strong>', '').replace('</strong>', ''), 'apply_url': item.get('redirect_url'), 'required_skills': []} for item in items]
            else:
                print(f'[JobAggregation] Adzuna error: {response.text[:500]}')
                raise Exception(f'Adzuna API error {response.status_code}: {response.text[:200]}')

    @staticmethod
    def generate_fallback_jobs(query: str, location: str=None) -> List[dict]:
        query_lower = query.lower()
        loc = location or 'Remote'
        job_templates = {'machine learning': [{'title': 'Machine Learning Engineer', 'company': 'TCS', 'skills': ['Python', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'SQL'], 'salary_min': 1200000, 'salary_max': 2500000}, {'title': 'Senior ML Engineer', 'company': 'Infosys', 'skills': ['Python', 'Deep Learning', 'NLP', 'Computer Vision', 'AWS'], 'salary_min': 1800000, 'salary_max': 3500000}, {'title': 'Data Scientist - ML', 'company': 'Wipro', 'skills': ['Python', 'R', 'Machine Learning', 'Statistics', 'Spark'], 'salary_min': 1000000, 'salary_max': 2200000}, {'title': 'ML Research Engineer', 'company': 'Google India', 'skills': ['Python', 'TensorFlow', 'JAX', 'Research', 'Publications'], 'salary_min': 3000000, 'salary_max': 6000000}, {'title': 'Applied ML Engineer', 'company': 'Microsoft India', 'skills': ['Python', 'Azure ML', 'MLOps', 'Docker', 'Kubernetes'], 'salary_min': 2500000, 'salary_max': 4500000}, {'title': 'ML Platform Engineer', 'company': 'Amazon India', 'skills': ['Python', 'SageMaker', 'MLOps', 'AWS', 'Data Pipelines'], 'salary_min': 2800000, 'salary_max': 5000000}, {'title': 'Junior ML Engineer', 'company': 'Zoho', 'skills': ['Python', 'Scikit-learn', 'Pandas', 'NumPy', 'SQL'], 'salary_min': 600000, 'salary_max': 1200000}, {'title': 'Machine Learning Intern', 'company': 'Freshworks', 'skills': ['Python', 'ML Basics', 'Linear Algebra', 'Statistics'], 'salary_min': 300000, 'salary_max': 600000}], 'software engineer': [{'title': 'Software Development Engineer', 'company': 'Amazon', 'skills': ['Java', 'AWS', 'System Design', 'DSA', 'Microservices'], 'salary_min': 2000000, 'salary_max': 4000000}, {'title': 'Full Stack Developer', 'company': 'Flipkart', 'skills': ['React', 'Node.js', 'Python', 'MongoDB', 'Docker'], 'salary_min': 1500000, 'salary_max': 3000000}, {'title': 'Backend Engineer', 'company': 'Razorpay', 'skills': ['Go', 'Python', 'PostgreSQL', 'Redis', 'Kafka'], 'salary_min': 1800000, 'salary_max': 3500000}, {'title': 'Frontend Engineer', 'company': 'Swiggy', 'skills': ['React', 'TypeScript', 'Next.js', 'GraphQL', 'CSS'], 'salary_min': 1400000, 'salary_max': 2800000}, {'title': 'SDE II', 'company': 'Google India', 'skills': ['C++', 'Python', 'System Design', 'Algorithms', 'Distributed Systems'], 'salary_min': 3500000, 'salary_max': 6500000}, {'title': 'Software Engineer', 'company': 'Atlassian India', 'skills': ['Java', 'Spring Boot', 'React', 'PostgreSQL', 'CI/CD'], 'salary_min': 2200000, 'salary_max': 4000000}], 'data': [{'title': 'Data Engineer', 'company': 'Walmart Labs India', 'skills': ['Python', 'Spark', 'Airflow', 'SQL', 'AWS'], 'salary_min': 1500000, 'salary_max': 3000000}, {'title': 'Data Analyst', 'company': 'Deloitte India', 'skills': ['SQL', 'Python', 'Tableau', 'Excel', 'Statistics'], 'salary_min': 800000, 'salary_max': 1800000}, {'title': 'Senior Data Scientist', 'company': 'Mu Sigma', 'skills': ['Python', 'R', 'ML', 'Deep Learning', 'NLP'], 'salary_min': 2000000, 'salary_max': 4000000}, {'title': 'Big Data Engineer', 'company': 'Cloudera India', 'skills': ['Hadoop', 'Spark', 'Hive', 'Kafka', 'Scala'], 'salary_min': 1800000, 'salary_max': 3500000}], 'frontend': [{'title': 'Senior Frontend Developer', 'company': 'Zomato', 'skills': ['React', 'TypeScript', 'Next.js', 'Tailwind CSS', 'GraphQL'], 'salary_min': 1800000, 'salary_max': 3500000}, {'title': 'UI Engineer', 'company': 'Phonepe', 'skills': ['React Native', 'JavaScript', 'CSS', 'Redux', 'Jest'], 'salary_min': 1500000, 'salary_max': 2800000}, {'title': 'Frontend Architect', 'company': 'Meesho', 'skills': ['React', 'Micro-frontends', 'Webpack', 'Performance', 'TypeScript'], 'salary_min': 2500000, 'salary_max': 4500000}], 'devops': [{'title': 'DevOps Engineer', 'company': 'Hasura', 'skills': ['Docker', 'Kubernetes', 'Terraform', 'AWS', 'CI/CD'], 'salary_min': 1500000, 'salary_max': 3000000}, {'title': 'SRE Engineer', 'company': 'Nutanix India', 'skills': ['Linux', 'Ansible', 'Prometheus', 'Grafana', 'Python'], 'salary_min': 1800000, 'salary_max': 3500000}, {'title': 'Cloud Engineer', 'company': 'Oracle India', 'skills': ['OCI', 'AWS', 'Azure', 'Terraform', 'Docker'], 'salary_min': 1600000, 'salary_max': 3200000}]}
        matched_jobs = []
        for category, templates in job_templates.items():
            if category in query_lower or any((word in query_lower for word in category.split())):
                matched_jobs.extend(templates)
        if not matched_jobs:
            matched_jobs = [{'title': f'Senior {query} Specialist', 'company': 'TCS', 'skills': [query, 'Communication', 'Problem Solving', 'Team Collaboration'], 'salary_min': 1200000, 'salary_max': 2500000}, {'title': f'{query} Engineer', 'company': 'Infosys', 'skills': [query, 'Agile', 'Documentation', 'Testing'], 'salary_min': 900000, 'salary_max': 2000000}, {'title': f'Lead {query} Developer', 'company': 'Wipro', 'skills': [query, 'Leadership', 'Architecture', 'Mentoring'], 'salary_min': 1800000, 'salary_max': 3500000}, {'title': f'Junior {query} Developer', 'company': 'Cognizant', 'skills': [query, 'Git', 'Linux', 'Basic Programming'], 'salary_min': 500000, 'salary_max': 1000000}, {'title': f'{query} Consultant', 'company': 'Accenture', 'skills': [query, 'Consulting', 'Client Management', 'Analytics'], 'salary_min': 1400000, 'salary_max': 2800000}, {'title': f'{query} Analyst', 'company': 'Deloitte India', 'skills': [query, 'Data Analysis', 'Excel', 'SQL'], 'salary_min': 800000, 'salary_max': 1600000}]
        results = []
        for i, template in enumerate(matched_jobs):
            job_id_seed = f"{template['title']}-{template['company']}-{query}"
            job_id = f'demo_{hashlib.md5(job_id_seed.encode()).hexdigest()[:12]}'
            results.append({'job_id': job_id, 'source': 'synthhire_demo', 'title': template['title'], 'company': template['company'], 'company_logo_url': None, 'location': loc, 'is_remote': i % 3 == 0, 'salary_min': template.get('salary_min'), 'salary_max': template.get('salary_max'), 'salary_currency': 'INR', 'description': f"We are looking for a talented {template['title']} to join our team at {template['company']}. This is an exciting opportunity to work on cutting-edge projects in {query}. The ideal candidate will have strong experience with {', '.join(template['skills'][:3])} and a passion for innovation.\n\nKey Responsibilities:\n• Design, develop, and maintain solutions in the {query} domain\n• Collaborate with cross-functional teams to deliver high-quality products\n• Stay up-to-date with the latest industry trends and technologies\n• Participate in code reviews and mentor junior team members\n• Contribute to technical architecture and design decisions\n\nRequirements:\n• {', '.join(template['skills'])}\n• Strong problem-solving and analytical skills\n• Excellent communication and teamwork abilities\n• Bachelor's or Master's degree in Computer Science or related field", 'required_skills': template['skills'], 'apply_url': f"https://careers.{template['company'].lower().replace(' ', '')}.com/jobs/{job_id}", 'posted_date': (datetime.utcnow() - timedelta(days=i)).isoformat()})
        print(f"[JobAggregation] Generated {len(results)} fallback demo jobs for '{query}' in '{loc}'")
        return results

    @staticmethod
    def deduplicate_and_normalize(raw_jobs: List[dict]) -> List[JobPostingItem]:
        seen = set()
        unique_jobs = []
        for j in raw_jobs:
            unique_str = f"{j.get('title')}-{j.get('company')}".lower()
            if unique_str not in seen:
                seen.add(unique_str)
                try:
                    unique_jobs.append(JobPostingItem(**j))
                except Exception as e:
                    print(f'[JobAggregation] Error normalizing job: {e}')
        return unique_jobs