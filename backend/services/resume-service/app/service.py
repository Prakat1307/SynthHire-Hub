import json
import uuid
import traceback
from typing import List, Optional
from sqlalchemy.orm import Session
from shared.models.tables import ResumeVersion, User, UserPreferences, PersonalStory, PrepAnswerHistory
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
ATS_ANALYSIS_PROMPT = 'You are an expert, highly critical ATS (Applicant Tracking System) strict analyzer, similar to a top-tier FAANG recruiter or Claude\'s analysis engine.\n\nCompare the following resume against the job description strictly. Do NOT hallucinate matches. Be brutally honest about gaps. Return a JSON object:\n{{\n  "match_score": <0-100 overall match percentage. Be strict!>,\n  "matched_keywords": [{{"keyword": "React", "found": true, "context": "2 years experience"}}],\n  "missing_keywords": ["Django", "Golang"],\n  "suggestions": [\n    "Quickly build a mini Django or Golang project to align with their stack.",\n    "Add \'Willing to relocate to Hyderabad\' in your resume header."\n  ],\n  "key_strength_matches": [\n    {{\n      "category": "Tech Stack",\n      "match_percentage": 90,\n      "explanation": "You have React, Node.js - strong overlap, but missing Django."\n    }},\n    {{\n      "category": "Startup & Ownership Mindset",\n      "match_percentage": 100,\n      "explanation": "Multiple hackathons and self-driven projects."\n    }},\n    {{\n      "category": "Tech Stack Gap",\n      "match_percentage": 20,\n      "explanation": "Django and Golang are missing, though transferable skills apply."\n    }}\n  ],\n  "category_scores": {{\n    "hard_skills": <0-100>,\n    "soft_skills": <0-100>,\n    "experience_match": <0-100>,\n    "education_match": <0-100>,\n    "industry_fit": <0-100>\n  }}\n}}\n\nReturn ONLY valid JSON. No markdown backticks. Extract all key metrics and give strict actionable advice under \'suggestions\'. Provide 5-7 distinct \'key_strength_matches\' categories with tailored explanations.\n\nRESUME:\n{resume}\n\nJOB DESCRIPTION:\n{jd}\n'
BULLET_REWRITE_PROMPT = 'You are a resume writing expert. Rewrite this resume bullet point to better match the job description.\nRules:\n- Start with a strong action verb\n- Include quantified metrics where possible\n- Use keywords from the JD naturally\n- Keep it concise (1-2 lines)\n- Tone: {tone}\n\nReturn JSON: {{"original": "...", "rewritten": "...", "improvement_notes": "..."}}\nReturn ONLY valid JSON.\n\nORIGINAL BULLET: {bullet}\nJOB DESCRIPTION: {jd}\n'
COVER_LETTER_PROMPT = 'Write a compelling cover letter for this job application.\n\nGuidelines:\n- Angle: {angle}\n- Length: 250-350 words\n- Address to: {hiring_manager}\n- Company: {company}\n- Reference specific JD requirements\n- Use the candidate\'s real experience from their resume\n- Sound authentic, not generic\n{stories_context}\n\nReturn JSON: {{"cover_letter": "...", "word_count": <int>, "key_points": ["point 1", "point 2"]}}\nReturn ONLY valid JSON.\n\nRESUME:\n{resume}\n\nJOB DESCRIPTION:\n{jd}\n'
RESUME_OPTIMIZE_PROMPT = 'You are a resume optimization expert. Optimize this resume to better match the job description.\nFor each section (summary, experience bullets, skills), suggest specific improvements.\n\nReturn JSON:\n{{\n  "optimized_summary": "New professional summary",\n  "optimized_skills": ["skill1", "skill2"],\n  "bullet_rewrites": [\n    {{"original": "old bullet", "rewritten": "new bullet"}}\n  ],\n  "changes_made": ["Added missing keyword X", "Quantified achievement Y"],\n  "estimated_match_improvement": <percentage points improvement>\n}}\n\nReturn ONLY valid JSON.\n\nRESUME:\n{resume}\n\nJOB DESCRIPTION:\n{jd}\n'

class ResumeService:

    def __init__(self, db: Session, gemini_api_key: str='', gemini_model: str='gemini-2.5-flash'):
        self.db = db
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model

    def _call_gemini(self, prompt: str) -> dict:
        if not GEMINI_AVAILABLE or not self.gemini_api_key:
            raise ValueError('Gemini API not available. Set GEMINI_API_KEY.')
        genai.configure(api_key=self.gemini_api_key)
        model = genai.GenerativeModel(self.gemini_model)
        response = model.generate_content(prompt)
        text = response.text.strip()
        import re
        json_match = re.search('```(?:json)?\\s*(.*?)\\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1).strip()
        else:
            text = text.removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        return json.loads(text)

    def _get_resume_text(self, user_id: str, resume_version_id: str=None) -> str:
        if resume_version_id:
            resume = self.db.query(ResumeVersion).filter(ResumeVersion.id == resume_version_id, ResumeVersion.user_id == user_id).first()
        else:
            resume = self.db.query(ResumeVersion).filter(ResumeVersion.user_id == user_id, ResumeVersion.is_master == True).first()
        if not resume:
            user = self.db.query(User).filter(User.id == user_id).first()
            return user.resume_text if user and user.resume_text else ''
        return resume.raw_text or ''

    def _get_user_stories(self, user_id: str) -> str:
        stories = self.db.query(PersonalStory).filter(PersonalStory.user_id == user_id, PersonalStory.is_active == True).all()
        if not stories:
            return ''
        context = "\n\nCandidate's real experiences (use these for authentic storytelling):\n"
        for s in stories:
            context += f'- {s.title}: {s.situation} → {s.action} → {s.result}\n'
        return context

    async def analyze_ats(self, user_id: str, resume_text: str, job_description: str) -> dict:
        prompt = ATS_ANALYSIS_PROMPT.format(resume=resume_text, jd=job_description)
        result = self._call_gemini(prompt)
        return result

    async def rewrite_bullet(self, original_bullet: str, job_description: str, tone: str='professional') -> dict:
        prompt = BULLET_REWRITE_PROMPT.format(bullet=original_bullet, jd=job_description, tone=tone)
        result = self._call_gemini(prompt)
        return result

    async def generate_cover_letter(self, user_id: str, job_description: str, company_name: str, hiring_manager: str='Hiring Manager', angle: str='balanced') -> dict:
        resume_text = self._get_resume_text(user_id)
        stories_context = self._get_user_stories(user_id)
        prompt = COVER_LETTER_PROMPT.format(resume=resume_text, jd=job_description, company=company_name, hiring_manager=hiring_manager, angle=angle, stories_context=stories_context)
        result = self._call_gemini(prompt)
        return result

    async def optimize_resume(self, user_id: str, resume_version_id: str, job_description: str) -> dict:
        resume_text = self._get_resume_text(user_id, resume_version_id)
        if not resume_text:
            raise ValueError('No resume found to optimize')
        current_analysis = await self.analyze_ats(user_id, resume_text, job_description)
        score_before = current_analysis.get('match_score', 0)
        prompt = RESUME_OPTIMIZE_PROMPT.format(resume=resume_text, jd=job_description)
        optimization = self._call_gemini(prompt)
        optimized_parts = []
        if optimization.get('optimized_summary'):
            optimized_parts.append(optimization['optimized_summary'])
        if optimization.get('bullet_rewrites'):
            for bw in optimization['bullet_rewrites']:
                optimized_parts.append(bw.get('rewritten', ''))
        optimized_text = resume_text
        for bw in optimization.get('bullet_rewrites', []):
            original = bw.get('original', '')
            rewritten = bw.get('rewritten', '')
            if original and rewritten and (original in optimized_text):
                optimized_text = optimized_text.replace(original, rewritten)
        new_analysis = await self.analyze_ats(user_id, optimized_text, job_description)
        score_after = new_analysis.get('match_score', score_before)
        existing_count = self.db.query(ResumeVersion).filter(ResumeVersion.user_id == user_id).count()
        jd_label = job_description[:60].replace('\n', ' ').strip()
        new_version = ResumeVersion(user_id=user_id, label=f'Tailored: {jd_label}...', is_master=False, raw_text=optimized_text, parsed_json=optimization, tailored_for_jd=job_description, match_score=score_after, version_number=existing_count + 1)
        self.db.add(new_version)
        self.db.commit()
        self.db.refresh(new_version)
        return {'new_version_id': str(new_version.id), 'match_score_before': score_before, 'match_score_after': score_after, 'changes_made': optimization.get('changes_made', [])}

    async def evaluate_prep_answer(self, user_id: str, data: 'PrepEvaluateRequest') -> dict:
        if not GEMINI_AVAILABLE:
            raise Exception('Gemini API not available')
        prompt = f"You are an elite AI Interview Coach. Evaluate the candidate's answer to this interview question.\n        \nQuestion: {data.question}\nCandidate Answer: {data.answer}\n"
        if data.job_description:
            prompt += f'\nTarget Job Description context: {data.job_description[:500]}...'
        resume_content = data.resume_summary
        if not resume_content:
            from shared.models.tables import ResumeVersion
            master_resume = self.db.query(ResumeVersion).filter_by(user_id=user_id, is_master=True).first()
            if master_resume and master_resume.raw_text:
                resume_content = master_resume.raw_text
        if resume_content:
            prompt += f'\nCandidate Background context (Resume): {resume_content[:1000]}...'
        prompt += '\nCRITICAL INSTRUCTION: You MUST dynamically read the Candidate Answer and grade it honestly. Do NOT output a generic template. \n- If the answer is short or bad, give it a low score (e.g., 20) and point out missing details.\n- If the answer is excellent and uses the STAR method perfectly, give it a high score (e.g., 90+).\n- The \'improved_answer\' must be directly related to their original thought but significantly improved.\n- The \'tone\' must be passive, neutral, or confident based on the words they actually used.\n\nReturn strictly a JSON object matching this schema:\n{\n  "scores": {\n    "clarity": <1-10>,\n    "relevance": <1-10>,\n    "structure": <1-10>,\n    "confidence": <1-10>,\n    "depth": <1-10>\n  },\n  "star_detected": {\n    "situation": <bool>,\n    "task": <bool>,\n    "action": <bool>,\n    "result": <bool>\n  },\n  "tone": "<passive|neutral|confident>",\n  "hedging_words_found": ["<words>", ...],\n  "improvement_tips": ["<tip1>", "<tip2>", ...],\n  "improved_answer": "<a rewritten, excellent version of their answer>",\n  "overall_score": <1-100>\n}\n'
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt, generation_config={'temperature': 0.4})
        text = response.text
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1:
            raise Exception('Failed to parse AI evaluation JSON')
        parsed = json.loads(text[start:end + 1])
        history_record = PrepAnswerHistory(user_id=user_id, question_id=data.question[:250], answer_text=data.answer, scores_json=parsed.get('scores', {}), overall_score=parsed.get('overall_score', 0))
        self.db.add(history_record)
        self.db.commit()
        return parsed

    async def analyze_prep_jd(self, user_id: str, data: 'PrepJdAnalyzeRequest') -> dict:
        if not GEMINI_AVAILABLE:
            raise Exception('Gemini API not available')
        prompt = f'You are an elite AI Interview Coach analyzing a Job Description to prepare a candidate.\n\nTarget Job Description:\n{data.job_description[:2000]}\n'
        resume_content = data.resume_summary
        if not resume_content:
            from shared.models.tables import ResumeVersion
            master_resume = self.db.query(ResumeVersion).filter_by(user_id=user_id, is_master=True).first()
            if master_resume and master_resume.raw_text:
                resume_content = master_resume.raw_text
        if resume_content:
            prompt += f'\nCandidate Background summary (Resume): {resume_content[:1500]}'
        if data.practice_types and len(data.practice_types) > 0:
            prompt += f"\n\nCRITICAL REQUIREMENT: The user specifically requested to practice the following types of rounds/skills: {', '.join(data.practice_types)}."
            prompt += f'\nYou MUST ONLY generate interview rounds that match these exact practice types. DO NOT generate Technical or Coding rounds if they were not explicitly selected.'
        else:
            prompt += f'\n\nGenerate a balanced mix of realistic interview rounds (e.g. Technical, Behavioral, System Design).'
        prompt += '\nExtract the key signals from this JD to help the candidate prepare, and Architect a complete Targeted Interview Plan containing realistic interview rounds.\n\nReturn strictly a JSON object:\n{\n  "matched_skills": ["<skill1>", ...],\n  "missing_skills": ["<skill1>", ...],\n  "culture_signals": ["<fast-paced>", "<ownership>", ...],\n  "keyword_gaps": ["<gap1>", ...],\n  "interview_rounds": [\n    {\n      "title": "<round name e.g. Technical Round 1: Algorithms>",\n      "description": "<what this round evaluates>",\n      "questions": [\n        {\n          "id": "<unique_string_id>",\n          "text": "<the actual interview question>",\n          "category": "<e.g. SYSTEM_DESIGN, BEHAVIORAL, ALGORITHMS>",\n          "difficulty": "<easy|medium|hard>",\n          "tags": ["<tag1>", "<tag2>"]\n        },\n        ... (3-5 questions per round)\n      ]\n    },\n    ... (3-5 rounds)\n  ]\n}\n\nIMPORTANT: You MUST include the \'interview_rounds\' array in your response with at least one round filled with valid questions, otherwise the application will crash.\n'
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt, generation_config={'temperature': 0.1})
        text = response.text
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1:
            raise Exception('Failed to parse JD Analysis JSON')
        return json.loads(text[start:end + 1])

    async def get_prep_history(self, user_id: str, question_id: str) -> dict:
        history = self.db.query(PrepAnswerHistory).filter(PrepAnswerHistory.user_id == user_id, PrepAnswerHistory.question_id == question_id[:250]).order_by(PrepAnswerHistory.created_at.desc()).all()
        return {'history': [{'id': str(h.id), 'created_at': h.created_at.isoformat() if h.created_at else '', 'answer_text': h.answer_text, 'scores_json': h.scores_json, 'overall_score': h.overall_score} for h in history]}

    async def generate_prep_draft(self, user_id: str, data: 'PrepDraftRequest') -> dict:
        if not GEMINI_AVAILABLE:
            raise Exception('Gemini API not available. Cannot generate draft.')
        jd_context = f'\nTarget Job context: {data.job_description[:1000]}' if data.job_description else ''
        resume_context = data.resume_summary
        if not resume_context:
            from shared.models.tables import ResumeVersion
            master_resume = self.db.query(ResumeVersion).filter_by(user_id=user_id, is_master=True).first()
            if master_resume and master_resume.raw_text:
                resume_context = master_resume.raw_text
        resume_prompt = f"\nCandidate's Background (Resume): {resume_context[:1500]}" if resume_context else ''
        prompt = f'\nYou are an expert Interview Coach. The candidate needs a high-quality draft answer to the following interview question:\n"{data.question}"\n{jd_context}{resume_prompt}\n\nWrite a professional, compelling, and structured target answer using the STAR method (Situation, Task, Action, Result) if applicable to the question type. \nDo not include any introductory or concluding remarks like "Here is a draft". Just write the text of the actual drafted answer from the first-person perspective of the candidate. Keep it between 3-5 concise paragraphs.\n'
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt, generation_config={'temperature': 0.4})
        return {'draft_text': response.text.strip()}

    async def linkedin_optimize(self, section: str, resume_data: str, target_role: Optional[str]=None, jd: Optional[str]=None, existing: Optional[str]=None) -> dict:
        if not GEMINI_AVAILABLE:
            raise Exception('Gemini API not available')
        target = target_role or 'their next ideal role'
        jd_context = f'\nTarget Job Description features: {jd}' if jd else ''
        existing_context = f'\nExisting LinkedIn content (for reference only, improve this): {existing}' if existing else ''
        section_prompts = {'headline': f'Generate a highly optimized LinkedIn headline (max 220 chars) for a candidate targeting {target}. Use this resume data: {resume_data}. Include current role/status + top skills + value prop. Make it ATS friendly. {jd_context}. {existing_context}', 'about': f'Write a LinkedIn About section (max 2600 chars) targeting {target}. 3 paragraphs: 1) Who they are (hook), 2) What they do (key skills/experience), 3) What they are looking for. Storytelling tone. Use resume: {resume_data}. {jd_context}. {existing_context}', 'experience': f'Rewrite this experience entry or infer one from the resume for LinkedIn targeting {target} (max 2000 chars). Use bullet points starting with action verbs, add quantified achievements. Use resume: {resume_data}. {jd_context}. {existing_context}', 'skills': f'Extract top 15-20 comma-separated skills from this resume for a LinkedIn Skills section targeting {target}. Prioritize technical depth and JD relevance. Resume: {resume_data}. {jd_context}. {existing_context}', 'projects': f'Rewrite project descriptions for LinkedIn targeting {target} (max 2000 chars). Format: [Project name] - [Summary]. 3-4 bullets on tech used and impact. Resume: {resume_data}. {jd_context}. {existing_context}', 'open_to_work': f"Suggest up to 5 comma-separated job titles for LinkedIn's 'Open To Work' feature. Based on resume: {resume_data} and target: {target}. {jd_context}"}
        if section not in section_prompts:
            raise ValueError('Invalid section type for LinkedIn optimization.')
        prompt = section_prompts[section] + '\n\nOutput a pure JSON object (no markdown code blocks, just raw JSON) matching exactly this schema:\n{\n    "optimized_text": "<The generated optimized string ready to copy>",\n    "char_count": <int count of text>,\n    "char_limit": <220 for headline, 2600 for about, 2000 else>,\n    "keywords_added": ["<keyword1>", "<keyword2>"],\n    "score_before": <0-100 estimate of current/resume text strength>,\n    "score_after": <0-100 estimate of this new text\'s strength>,\n    "tips": ["<tip 1>", "<tip 2>", "<tip 3>"]\n}\n'
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt, generation_config={'temperature': 0.4})
        text = response.text.strip()
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1:
            raise Exception(f'Failed to parse LinkedIn Optimization JSON: {text[:100]}')
        return json.loads(text[start:end + 1])

    async def linkedin_keyword_match(self, resume_skills: List[str], jd_keywords: List[str], linkedin_skills: Optional[List[str]]=None) -> dict:
        if not GEMINI_AVAILABLE:
            raise Exception('Gemini API not available')
        l_skills_prompt = f'Existing LinkedIn Skills: {linkedin_skills}' if linkedin_skills else ''
        prompt = f"""Compare the candidate's skills against the Job Description keywords to find LinkedIn gaps.\nResume Skills: {resume_skills}\nJD Keywords: {jd_keywords}\n{l_skills_prompt}\n\nOutput a pure JSON object (no markdown) exactly:\n{'matched': [\"<skill1>\", \"<skill2>\"],\n    \"missing_from_resume\": [\"<keyword gap 1>\", \"<keyword gap 2>\"],\n    \"missing_from_linkedin\": [\"<already on resume but missed on linkedin>\"],\n    \"priority_adds\": [\"<Top 2-3 absolute missing critical keywords to add to linkedin>\"]\n} \n"""
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt, generation_config={'temperature': 0.1})
        text = response.text.strip()
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1:
            raise Exception('Failed to parse Keyword Match JSON')
        return json.loads(text[start:end + 1])

    async def fetch_linkedin_profile(self, url: str) -> dict:
        if not GEMINI_AVAILABLE:
            raise Exception('Gemini API not available')
        try:
            prompt = f"""\nYou are an expert HR assistant with access to the web. Your task is to find and extract public profile information for the following LinkedIn URL.\nLinkedIn URL: {url}\n\nSearch the web for this person's LinkedIn profile and extract their headline, about summary, experience, education, and skills.\nCombine all the found information into a detailed, formatted string.\n\nReturn ONLY a pure JSON object mapping EXACTLY to this schema (no extra text or markdown):\n{'profile_text': \"Detailed contents of their headline, about, experience, education, etc. combined into a formatted string.\",\n    \"is_auth_wall\": false\n} \n\nIf you absolutely cannot find any public information for this person on the internet, return "is_auth_wall": true.\n"""
            model = genai.GenerativeModel(self.gemini_model)
            response = model.generate_content(prompt, generation_config={'temperature': 0.2})
            text = response.text.strip()
            import re
            json_match = re.search('```(?:json)?\\s*(.*?)\\s*```', text, re.DOTALL)
            if json_match:
                text = json_match.group(1).strip()
            else:
                start = text.find('{')
                end = text.rfind('}')
                if start != -1 and end != -1:
                    text = text[start:end + 1]
            try:
                parsed = json.loads(text)
                return {'profile_text': parsed.get('profile_text', ''), 'is_auth_wall': parsed.get('is_auth_wall', False)}
            except json.JSONDecodeError:
                return {'profile_text': text, 'is_auth_wall': False}
        except Exception as e:
            traceback.print_exc()
            return {'profile_text': '', 'is_auth_wall': True}