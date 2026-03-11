import uuid
import json
import traceback
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import update
from shared.models.tables import User, UserProfile, PersonalStory, UserPreferences, ResumeVersion, AnswerTone, AnswerLength, AnswerFormat
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
RESUME_PARSE_PROMPT = 'You are a resume parser. Extract structured information from the following resume text.\nReturn a JSON object with these exact keys:\n{\n  "name": "Full Name",\n  "contact": {"email": "", "phone": "", "location": "", "linkedin": "", "github": ""},\n  "summary": "Professional summary if present",\n  "skills": ["skill1", "skill2"],\n  "experience": [\n    {\n      "company": "Company Name",\n      "role": "Job Title",\n      "start_date": "YYYY-MM",\n      "end_date": "YYYY-MM or Present",\n      "bullets": ["Achievement 1", "Achievement 2"]\n    }\n  ],\n  "education": [\n    {\n      "institution": "School Name",\n      "degree": "Degree Type",\n      "field": "Field of Study",\n      "graduation_date": "YYYY-MM"\n    }\n  ],\n  "certifications": ["Cert 1", "Cert 2"],\n  "projects": [\n    {\n      "name": "Project Name",\n      "description": "Brief description",\n      "technologies": ["tech1", "tech2"]\n    }\n  ]\n}\n\nFill in what you can find. Use null for missing fields. Do NOT invent information.\nReturn ONLY the JSON, no markdown formatting.\n\nResume text:\n'

class OnboardingService:

    def __init__(self, db: Session, gemini_api_key: str='', gemini_model: str='gemini-2.5-flash'):
        self.db = db
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model

    def _ensure_profile(self, user_id: str) -> UserProfile:
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def _update_onboarding_step(self, user_id: str, step: int):
        profile = self._ensure_profile(user_id)
        if step > profile.onboarding_step:
            profile.onboarding_step = step
            self.db.commit()

    async def parse_resume(self, user_id: str, raw_text: str, file_name: str=None) -> dict:
        parsed = {}
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel(self.gemini_model)
                response = model.generate_content(RESUME_PARSE_PROMPT + raw_text)
                text = response.text.strip()
                if text.startswith('```'):
                    text = text.split('\n', 1)[1] if '\n' in text else text[3:]
                if text.endswith('```'):
                    text = text[:-3]
                if text.startswith('json'):
                    text = text[4:]
                parsed = json.loads(text.strip())
            except Exception as e:
                print(f'Gemini resume parsing failed: {e}')
                traceback.print_exc()
                parsed = {'name': '', 'contact': {}, 'summary': '', 'skills': [], 'experience': [], 'education': [], 'certifications': [], 'projects': []}
        else:
            parsed = {'name': '', 'contact': {}, 'summary': '', 'skills': [], 'experience': [], 'education': [], 'certifications': [], 'projects': []}
        existing_master = self.db.query(ResumeVersion).filter(ResumeVersion.user_id == user_id, ResumeVersion.is_master == True).first()
        version_number = 1
        if existing_master:
            max_version = self.db.query(ResumeVersion).filter(ResumeVersion.user_id == user_id).count()
            version_number = max_version + 1
        resume = ResumeVersion(user_id=user_id, label='Master Resume' if not existing_master else f'Resume v{version_number}', is_master=not existing_master, raw_text=raw_text, parsed_json=parsed, file_name=file_name, version_number=version_number)
        self.db.add(resume)
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.resume_text = raw_text
            user.resume_parsed_json = parsed
            from datetime import datetime, timezone
            user.resume_uploaded_at = datetime.now(timezone.utc)
        self._update_onboarding_step(user_id, 1)
        self.db.commit()
        self.db.refresh(resume)
        return {'raw_text': raw_text, 'parsed': parsed, 'resume_version_id': str(resume.id)}

    def get_resume_versions(self, user_id: str) -> List[ResumeVersion]:
        return self.db.query(ResumeVersion).filter(ResumeVersion.user_id == user_id, ResumeVersion.is_active == True).order_by(ResumeVersion.is_master.desc(), ResumeVersion.created_at.desc()).all()

    def delete_resume_version(self, user_id: str, version_id: str) -> None:
        resume = self.db.query(ResumeVersion).filter(ResumeVersion.id == version_id, ResumeVersion.user_id == user_id).first()
        if not resume:
            raise ValueError('Resume not found')
        self.db.delete(resume)
        self.db.commit()

    def update_resume_parsed(self, user_id: str, resume_id: str, parsed_json: dict) -> ResumeVersion:
        resume = self.db.query(ResumeVersion).filter(ResumeVersion.id == resume_id, ResumeVersion.user_id == user_id).first()
        if not resume:
            raise ValueError('Resume version not found')
        resume.parsed_json = parsed_json
        if resume.is_master:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.resume_parsed_json = parsed_json
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def save_job_targeting(self, user_id: str, data: dict) -> UserProfile:
        profile = self._ensure_profile(user_id)
        profile.target_role = data.get('target_role')
        profile.industry = data.get('industry')
        profile.target_companies = data.get('target_companies', [])
        profile.years_of_experience = data.get('years_of_experience')
        profile.work_preference = data.get('work_preference')
        profile.experience_level = data.get('experience_level')
        self._update_onboarding_step(user_id, 2)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def create_story(self, user_id: str, data: dict) -> PersonalStory:
        count = self.db.query(PersonalStory).filter(PersonalStory.user_id == user_id, PersonalStory.is_active == True).count()
        story = PersonalStory(user_id=user_id, title=data['title'], situation=data['situation'], task=data['task'], action=data['action'], result=data['result'], tags=data.get('tags', []), company_name=data.get('company_name'), role_at_time=data.get('role_at_time'), sort_order=count)
        self.db.add(story)
        if count == 0:
            self._update_onboarding_step(user_id, 3)
        self.db.commit()
        self.db.refresh(story)
        return story

    def get_stories(self, user_id: str) -> List[PersonalStory]:
        return self.db.query(PersonalStory).filter(PersonalStory.user_id == user_id, PersonalStory.is_active == True).order_by(PersonalStory.sort_order).all()

    def update_story(self, user_id: str, story_id: str, data: dict) -> PersonalStory:
        story = self.db.query(PersonalStory).filter(PersonalStory.id == story_id, PersonalStory.user_id == user_id).first()
        if not story:
            raise ValueError('Story not found')
        for key, value in data.items():
            if value is not None and hasattr(story, key):
                setattr(story, key, value)
        self.db.commit()
        self.db.refresh(story)
        return story

    def delete_story(self, user_id: str, story_id: str) -> bool:
        story = self.db.query(PersonalStory).filter(PersonalStory.id == story_id, PersonalStory.user_id == user_id).first()
        if not story:
            raise ValueError('Story not found')
        story.is_active = False
        self.db.commit()
        return True

    def save_preferences(self, user_id: str, data: dict) -> UserPreferences:
        prefs = self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        tone_map = {'formal': AnswerTone.FORMAL, 'conversational': AnswerTone.CONVERSATIONAL, 'assertive': AnswerTone.ASSERTIVE, 'warm': AnswerTone.WARM}
        length_map = {'short': AnswerLength.SHORT, 'medium': AnswerLength.MEDIUM, 'detailed': AnswerLength.DETAILED}
        format_map = {'star': AnswerFormat.STAR, 'bullet_points': AnswerFormat.BULLET_POINTS, 'flowing': AnswerFormat.FLOWING}
        if prefs:
            prefs.tone = tone_map.get(data.get('tone', 'conversational'), AnswerTone.CONVERSATIONAL)
            prefs.answer_length = length_map.get(data.get('answer_length', 'medium'), AnswerLength.MEDIUM)
            prefs.answer_format = format_map.get(data.get('answer_format', 'star'), AnswerFormat.STAR)
        else:
            prefs = UserPreferences(user_id=user_id, tone=tone_map.get(data.get('tone', 'conversational'), AnswerTone.CONVERSATIONAL), answer_length=length_map.get(data.get('answer_length', 'medium'), AnswerLength.MEDIUM), answer_format=format_map.get(data.get('answer_format', 'star'), AnswerFormat.STAR))
            self.db.add(prefs)
        self._update_onboarding_step(user_id, 4)
        self.db.commit()
        self.db.refresh(prefs)
        return prefs

    def get_preferences(self, user_id: str) -> Optional[UserPreferences]:
        return self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()

    def complete_onboarding(self, user_id: str) -> UserProfile:
        profile = self._ensure_profile(user_id)
        profile.onboarding_completed = True
        profile.onboarding_step = 5
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_onboarding_status(self, user_id: str) -> dict:
        profile = self._ensure_profile(user_id)
        resume_count = self.db.query(ResumeVersion).filter(ResumeVersion.user_id == user_id, ResumeVersion.is_active == True).count()
        stories_count = self.db.query(PersonalStory).filter(PersonalStory.user_id == user_id, PersonalStory.is_active == True).count()
        prefs = self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        job_targeting_done = bool(profile.target_role)
        return {'onboarding_completed': profile.onboarding_completed, 'current_step': profile.onboarding_step, 'resume_uploaded': resume_count > 0, 'job_targeting_done': job_targeting_done, 'stories_count': stories_count, 'preferences_set': prefs is not None}