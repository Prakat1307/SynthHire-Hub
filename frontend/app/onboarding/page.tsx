'use client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/stores/authStore';
import api from '@/src/lib/api';
import CyberButton from '@/components/ui/CyberButton';
import GlassCard from '@/components/ui/GlassCard';
import { motion, AnimatePresence } from 'framer-motion';
import toast, { Toaster } from 'react-hot-toast';
import {
    Upload, Target, BookOpen, Settings2, CreditCard,
    CheckCircle2, ChevronRight, ChevronLeft, X, Plus, Sparkles, FileText
} from 'lucide-react';
const { apiClient } = api;
const STEPS = [
    { id: 1, title: 'Resume Upload', icon: Upload, description: 'Upload your resume for AI parsing' },
    { id: 2, title: 'Job Targeting', icon: Target, description: 'Tell us what role you want' },
    { id: 3, title: 'Personal Stories', icon: BookOpen, description: 'Share your real work stories' },
    { id: 4, title: 'Preferences', icon: Settings2, description: 'How should answers sound?' },
    { id: 5, title: 'Get Started', icon: CreditCard, description: 'Choose your plan' },
];
const STORY_TAG_OPTIONS = [
    'leadership', 'technical', 'conflict_resolution', 'deadline_pressure',
    'teamwork', 'innovation', 'failure', 'success', 'problem_solving',
    'communication', 'mentoring', 'customer_focused', 'data_driven',
    'cross_functional', 'system_design', 'debugging', 'optimization',
];
export default function OnboardingPage() {
    const router = useRouter();
    const { user, isAuthenticated, isLoading: authLoading } = useAuthStore();
    const [currentStep, setCurrentStep] = useState(1);
    const [isLoading, setIsLoading] = useState(false);
    const [resumeText, setResumeText] = useState('');
    const [resumeFile, setResumeFile] = useState<File | null>(null);
    const [resumeFileName, setResumeFileName] = useState('');
    const [parsedResume, setParsedResume] = useState<any>(null);
    
    const [targetRole, setTargetRole] = useState('');
    const [industry, setIndustry] = useState('');
    const [targetCompanies, setTargetCompanies] = useState<string[]>([]);
    const [companyInput, setCompanyInput] = useState('');
    const [yearsExp, setYearsExp] = useState<number>(0);
    const [workPreference, setWorkPreference] = useState('remote');
    const [expLevel, setExpLevel] = useState('mid');
    const [stories, setStories] = useState<any[]>([]);
    const [showStoryForm, setShowStoryForm] = useState(false);
    const [storyForm, setStoryForm] = useState({
        title: '', situation: '', task: '', action: '', result: '',
        tags: [] as string[], company_name: '', role_at_time: '',
    });
    
    const [tone, setTone] = useState('conversational');
    const [answerLength, setAnswerLength] = useState('medium');
    const [answerFormat, setAnswerFormat] = useState('star');
    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push('/login');
        }
    }, [authLoading, isAuthenticated, router]);
    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setResumeFileName(file.name);
        setResumeFile(file); 
        if (file.type === 'text/plain') {
            const text = await file.text();
            setResumeText(text);
        } else {
            setResumeText(''); 
        }
    };
    
    const handleParseResume = async () => {
        if (!resumeText.trim() && !resumeFile) {
            toast.error('Please enter or upload your resume text/file');
            return;
        }
        setIsLoading(true);
        try {
            const formData = new FormData();
            if (resumeText) formData.append('resume_text', resumeText);
            if (resumeFile) formData.append('resume_file', resumeFile);
            if (resumeFileName) formData.append('file_name', resumeFileName);
            const res = await apiClient.post('/onboarding/resume/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setParsedResume(res.data.parsed);
            toast.success('Resume parsed successfully!');
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || 'Failed to parse resume');
        } finally {
            setIsLoading(false);
        }
    };
    const handleSaveTargeting = async () => {
        if (!targetRole.trim()) {
            toast.error('Please enter your target role');
            return;
        }
        setIsLoading(true);
        try {
            await apiClient.post('/onboarding/job-targeting', {
                target_role: targetRole,
                industry,
                target_companies: targetCompanies,
                years_of_experience: yearsExp,
                work_preference: workPreference,
                experience_level: expLevel,
            });
            toast.success('Job targeting saved!');
            setCurrentStep(3);
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || 'Failed to save');
        } finally {
            setIsLoading(false);
        }
    };
    const handleCreateStory = async () => {
        if (!storyForm.title || !storyForm.situation || !storyForm.task || !storyForm.action || !storyForm.result) {
            toast.error('Please fill in all STAR fields');
            return;
        }
        setIsLoading(true);
        try {
            const res = await apiClient.post('/onboarding/stories', storyForm);
            setStories([...stories, res.data]);
            setStoryForm({
                title: '', situation: '', task: '', action: '', result: '',
                tags: [], company_name: '', role_at_time: '',
            });
            setShowStoryForm(false);
            toast.success('Story added!');
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || 'Failed to add story');
        } finally {
            setIsLoading(false);
        }
    };
    const handleSavePreferences = async () => {
        setIsLoading(true);
        try {
            await apiClient.post('/onboarding/preferences', {
                tone,
                answer_length: answerLength,
                answer_format: answerFormat,
            });
            toast.success('Preferences saved!');
            setCurrentStep(5);
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || 'Failed to save');
        } finally {
            setIsLoading(false);
        }
    };
    const handleComplete = async () => {
        setIsLoading(true);
        try {
            await apiClient.post('/onboarding/complete');
            toast.success('Welcome to SynthHire!');
            setTimeout(() => router.push('/dashboard'), 1000);
        } catch (err: any) {
            toast.error('Failed to complete onboarding');
        } finally {
            setIsLoading(false);
        }
    };
    const toggleTag = (tag: string) => {
        setStoryForm(prev => ({
            ...prev,
            tags: prev.tags.includes(tag)
                ? prev.tags.filter(t => t !== tag)
                : [...prev.tags, tag],
        }));
    };
    const addCompany = () => {
        if (companyInput.trim() && !targetCompanies.includes(companyInput.trim())) {
            setTargetCompanies([...targetCompanies, companyInput.trim()]);
            setCompanyInput('');
        }
    };
    if (authLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin w-10 h-10 border-4 border-blue-500 rounded-full border-t-transparent" />
            </div>
        );
    }
    return (
        <div className="min-h-screen flex flex-col items-center px-4 py-8 relative overflow-hidden">
            <Toaster position="top-right" toastOptions={{
                style: { background: '#1e293b', color: '#fff', border: '1px solid rgba(255,255,255,0.1)' }
            }} />
            {}
            <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[150px] pointer-events-none" />
            <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-[150px] pointer-events-none" />
            {}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-8 z-10"
            >
                <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
                    Set Up Your <span className="text-gradient">Interview Profile</span>
                </h1>
                <p className="text-slate-400 text-sm">
                    This information powers every AI-generated answer across the platform
                </p>
            </motion.div>
            {}
            <div className="w-full max-w-3xl mb-8 z-10">
                <div className="flex items-center justify-between mb-4">
                    {STEPS.map((step, idx) => {
                        const Icon = step.icon;
                        const isActive = currentStep === step.id;
                        const isComplete = currentStep > step.id;
                        return (
                            <div key={step.id} className="flex items-center flex-1">
                                <div className="flex flex-col items-center">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${isComplete ? 'bg-emerald-500/20 text-emerald-400 border-2 border-emerald-500/50' :
                                        isActive ? 'bg-blue-500/20 text-blue-400 border-2 border-blue-500/50 shadow-lg shadow-blue-500/20' :
                                            'bg-white/5 text-slate-500 border border-white/10'
                                        }`}>
                                        {isComplete ? <CheckCircle2 size={18} /> : <Icon size={18} />}
                                    </div>
                                    <span className={`text-xs mt-1 hidden md:block ${isActive ? 'text-white font-medium' : 'text-slate-500'}`}>
                                        {step.title}
                                    </span>
                                </div>
                                {idx < STEPS.length - 1 && (
                                    <div className={`flex-1 h-0.5 mx-2 transition-colors duration-300 ${currentStep > step.id ? 'bg-emerald-500/50' : 'bg-white/10'
                                        }`} />
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
            {}
            <AnimatePresence mode="wait">
                <motion.div
                    key={currentStep}
                    initial={{ opacity: 0, x: 30 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -30 }}
                    transition={{ duration: 0.3 }}
                    className="w-full max-w-3xl z-10"
                >
                    {}
                    {currentStep === 1 && (
                        <GlassCard className="p-8 space-y-6">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
                                    <Upload size={20} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">Upload Your Resume</h2>
                                    <p className="text-sm text-slate-400">We&apos;ll extract and structure your experience using AI</p>
                                </div>
                            </div>
                            {}
                            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-white/10 rounded-xl cursor-pointer hover:border-blue-500/50 hover:bg-blue-500/5 transition-all group">
                                <FileText size={28} className="text-slate-500 group-hover:text-blue-400 transition-colors mb-2" />
                                <span className="text-sm text-slate-400 group-hover:text-slate-300">
                                    {resumeFileName || 'Click to upload PDF, DOCX, or TXT'}
                                </span>
                                <input type="file" accept=".pdf,.docx,.txt,.doc" onChange={handleFileUpload} className="hidden" />
                            </label>
                            <div className="relative">
                                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-white/10" /></div>
                                <div className="relative flex justify-center text-sm">
                                    <span className="px-3 bg-[#0f1724] text-slate-500">or paste text directly</span>
                                </div>
                            </div>
                            <textarea
                                value={resumeText}
                                onChange={(e) => setResumeText(e.target.value)}
                                placeholder="Paste your resume text here..."
                                className="w-full h-48 px-4 py-3 glass-input rounded-xl text-sm text-slate-200 placeholder-slate-500 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                            />
                            <CyberButton
                                onClick={handleParseResume}
                                variant="primary"
                                isLoading={isLoading}
                                className="w-full justify-center"
                            >
                                <Sparkles size={16} className="mr-2" />
                                Parse with AI
                            </CyberButton>
                            {}
                            {parsedResume && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="space-y-4"
                                >
                                    <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
                                        <CheckCircle2 size={16} />
                                        Resume parsed successfully — review and continue
                                    </div>
                                    <div className="bg-white/5 rounded-xl p-4 space-y-3 border border-white/5 max-h-64 overflow-y-auto">
                                        {parsedResume.name && (
                                            <p className="text-white font-semibold">{parsedResume.name}</p>
                                        )}
                                        {parsedResume.skills?.length > 0 && (
                                            <div>
                                                <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Skills</p>
                                                <div className="flex flex-wrap gap-1">
                                                    {parsedResume.skills.map((s: string, i: number) => (
                                                        <span key={i} className="px-2 py-0.5 text-xs rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/20">{s}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        {parsedResume.experience?.length > 0 && (
                                            <div>
                                                <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Experience</p>
                                                {parsedResume.experience.map((exp: any, i: number) => (
                                                    <div key={i} className="text-sm text-slate-300 mb-1">
                                                        <span className="font-medium text-white">{exp.role}</span>
                                                        {exp.company && <span className="text-slate-400"> at {exp.company}</span>}
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                    <CyberButton onClick={() => setCurrentStep(2)} variant="primary" className="w-full justify-center">
                                        Continue <ChevronRight size={16} className="ml-1" />
                                    </CyberButton>
                                </motion.div>
                            )}
                        </GlassCard>
                    )}
                    {}
                    {currentStep === 2 && (
                        <GlassCard className="p-8 space-y-6">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-10 h-10 rounded-xl bg-violet-500/10 text-violet-400 flex items-center justify-center">
                                    <Target size={20} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">Job Targeting</h2>
                                    <p className="text-sm text-slate-400">What role are you preparing for?</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-300">Target Role *</label>
                                    <input
                                        value={targetRole}
                                        onChange={(e) => setTargetRole(e.target.value)}
                                        placeholder="e.g. Senior Product Manager"
                                        className="w-full px-4 py-3 glass-input rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-violet-500/50"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-300">Industry</label>
                                    <input
                                        value={industry}
                                        onChange={(e) => setIndustry(e.target.value)}
                                        placeholder="e.g. Fintech, Healthtech"
                                        className="w-full px-4 py-3 glass-input rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-violet-500/50"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-300">Years of Experience</label>
                                    <input
                                        type="number"
                                        value={yearsExp}
                                        onChange={(e) => setYearsExp(parseInt(e.target.value) || 0)}
                                        className="w-full px-4 py-3 glass-input rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-violet-500/50"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-300">Experience Level</label>
                                    <select
                                        value={expLevel}
                                        onChange={(e) => setExpLevel(e.target.value)}
                                        className="w-full px-4 py-3 glass-input rounded-xl text-sm bg-transparent focus:outline-none focus:ring-1 focus:ring-violet-500/50"
                                    >
                                        <option value="junior" className="bg-slate-900">Junior</option>
                                        <option value="mid" className="bg-slate-900">Mid-Level</option>
                                        <option value="senior" className="bg-slate-900">Senior</option>
                                        <option value="staff" className="bg-slate-900">Staff / Principal</option>
                                        <option value="lead" className="bg-slate-900">Lead / Manager</option>
                                    </select>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-300">Work Preference</label>
                                <div className="flex gap-3">
                                    {['remote', 'hybrid', 'onsite'].map(pref => (
                                        <button
                                            key={pref}
                                            onClick={() => setWorkPreference(pref)}
                                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${workPreference === pref
                                                ? 'bg-violet-500/20 text-violet-300 border border-violet-500/50'
                                                : 'bg-white/5 text-slate-400 border border-white/10 hover:bg-white/10'
                                                }`}
                                        >
                                            {pref.charAt(0).toUpperCase() + pref.slice(1)}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-300">Target Companies</label>
                                <div className="flex gap-2">
                                    <input
                                        value={companyInput}
                                        onChange={(e) => setCompanyInput(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && addCompany()}
                                        placeholder="Type company name and press Enter"
                                        className="flex-1 px-4 py-3 glass-input rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-violet-500/50"
                                    />
                                    <button
                                        onClick={addCompany}
                                        className="px-3 rounded-xl bg-white/5 text-slate-300 hover:bg-white/10 border border-white/10 transition-all"
                                    >
                                        <Plus size={18} />
                                    </button>
                                </div>
                                {targetCompanies.length > 0 && (
                                    <div className="flex flex-wrap gap-2 mt-2">
                                        {targetCompanies.map((c, i) => (
                                            <span key={i} className="inline-flex items-center gap-1 px-3 py-1 text-xs rounded-full bg-violet-500/10 text-violet-300 border border-violet-500/20">
                                                {c}
                                                <button onClick={() => setTargetCompanies(targetCompanies.filter((_, j) => j !== i))} className="hover:text-white">
                                                    <X size={12} />
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <div className="flex gap-3 pt-2">
                                <CyberButton onClick={() => setCurrentStep(1)} variant="ghost" className="border border-white/10">
                                    <ChevronLeft size={16} className="mr-1" /> Back
                                </CyberButton>
                                <CyberButton onClick={handleSaveTargeting} variant="primary" isLoading={isLoading} className="flex-1 justify-center">
                                    Continue <ChevronRight size={16} className="ml-1" />
                                </CyberButton>
                            </div>
                        </GlassCard>
                    )}
                    {}
                    {currentStep === 3 && (
                        <GlassCard className="p-8 space-y-6">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
                                    <BookOpen size={20} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">Personal Stories</h2>
                                    <p className="text-sm text-slate-400">Add real work stories in STAR format — this is what makes your answers unique</p>
                                </div>
                            </div>
                            {}
                            {stories.length > 0 && (
                                <div className="space-y-3">
                                    {stories.map((story, i) => (
                                        <div key={story.id || i} className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2">
                                            <div className="flex items-center justify-between">
                                                <h3 className="text-sm font-semibold text-white">{story.title}</h3>
                                                <CheckCircle2 size={16} className="text-emerald-400" />
                                            </div>
                                            <div className="flex flex-wrap gap-1">
                                                {(story.tags || []).map((tag: string, j: number) => (
                                                    <span key={j} className="px-2 py-0.5 text-[10px] rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">{tag}</span>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {}
                            {showStoryForm ? (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    className="space-y-4 border border-white/10 rounded-xl p-4"
                                >
                                    <input
                                        value={storyForm.title}
                                        onChange={(e) => setStoryForm({ ...storyForm, title: e.target.value })}
                                        placeholder="Story title (e.g. Led backend migration at Flipkart)"
                                        className="w-full px-4 py-3 glass-input rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-amber-500/50"
                                    />
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        <input
                                            value={storyForm.company_name}
                                            onChange={(e) => setStoryForm({ ...storyForm, company_name: e.target.value })}
                                            placeholder="Company (optional)"
                                            className="px-4 py-2 glass-input rounded-lg text-sm focus:outline-none"
                                        />
                                        <input
                                            value={storyForm.role_at_time}
                                            onChange={(e) => setStoryForm({ ...storyForm, role_at_time: e.target.value })}
                                            placeholder="Your role (optional)"
                                            className="px-4 py-2 glass-input rounded-lg text-sm focus:outline-none"
                                        />
                                    </div>
                                    {['situation', 'task', 'action', 'result'].map((field) => (
                                        <div key={field} className="space-y-1">
                                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                                {field === 'situation' ? '📍 Situation' :
                                                    field === 'task' ? '🎯 Task' :
                                                        field === 'action' ? '⚡ Action' : '✅ Result'}
                                            </label>
                                            <textarea
                                                value={(storyForm as any)[field]}
                                                onChange={(e) => setStoryForm({ ...storyForm, [field]: e.target.value })}
                                                placeholder={`Describe the ${field}...`}
                                                className="w-full px-4 py-2 glass-input rounded-lg text-sm resize-none h-20 focus:outline-none focus:ring-1 focus:ring-amber-500/50"
                                            />
                                        </div>
                                    ))}
                                    <div className="space-y-2">
                                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tags</label>
                                        <div className="flex flex-wrap gap-1.5">
                                            {STORY_TAG_OPTIONS.map(tag => (
                                                <button
                                                    key={tag}
                                                    onClick={() => toggleTag(tag)}
                                                    className={`px-2.5 py-1 text-xs rounded-full transition-all ${storyForm.tags.includes(tag)
                                                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50'
                                                        : 'bg-white/5 text-slate-400 border border-white/10 hover:bg-white/10'
                                                        }`}
                                                >
                                                    {tag.replace('_', ' ')}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <CyberButton onClick={() => setShowStoryForm(false)} variant="ghost" className="border border-white/10">
                                            Cancel
                                        </CyberButton>
                                        <CyberButton onClick={handleCreateStory} variant="primary" isLoading={isLoading} className="flex-1 justify-center">
                                            Save Story
                                        </CyberButton>
                                    </div>
                                </motion.div>
                            ) : (
                                <button
                                    onClick={() => setShowStoryForm(true)}
                                    className="w-full py-4 rounded-xl border-2 border-dashed border-white/10 text-slate-400 hover:border-amber-500/40 hover:text-amber-400 hover:bg-amber-500/5 transition-all flex items-center justify-center gap-2 text-sm"
                                >
                                    <Plus size={18} /> Add a Personal Story
                                </button>
                            )}
                            <p className="text-xs text-slate-500 italic">
                                You can add up to 10 stories. More stories = better personalized answers.
                                {stories.length === 0 && ' Add at least one to continue.'}
                            </p>
                            <div className="flex gap-3 pt-2">
                                <CyberButton onClick={() => setCurrentStep(2)} variant="ghost" className="border border-white/10">
                                    <ChevronLeft size={16} className="mr-1" /> Back
                                </CyberButton>
                                <CyberButton
                                    onClick={() => setCurrentStep(4)}
                                    variant="primary"
                                    className="flex-1 justify-center"
                                    disabled={stories.length === 0}
                                >
                                    Continue <ChevronRight size={16} className="ml-1" />
                                </CyberButton>
                            </div>
                        </GlassCard>
                    )}
                    {}
                    {currentStep === 4 && (
                        <GlassCard className="p-8 space-y-6">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-10 h-10 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center">
                                    <Settings2 size={20} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">Answer Preferences</h2>
                                    <p className="text-sm text-slate-400">How should your AI-generated answers sound?</p>
                                </div>
                            </div>
                            {}
                            <div className="space-y-3">
                                <label className="text-sm font-medium text-slate-300">Tone</label>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                    {[
                                        { value: 'formal', label: 'Formal', desc: 'Professional & polished' },
                                        { value: 'conversational', label: 'Conversational', desc: 'Natural & friendly' },
                                        { value: 'assertive', label: 'Assertive', desc: 'Confident & direct' },
                                        { value: 'warm', label: 'Warm', desc: 'Empathetic & approachable' },
                                    ].map(opt => (
                                        <button
                                            key={opt.value}
                                            onClick={() => setTone(opt.value)}
                                            className={`p-3 rounded-xl text-left transition-all ${tone === opt.value
                                                ? 'bg-teal-500/15 border-2 border-teal-500/50 shadow-lg shadow-teal-500/10'
                                                : 'bg-white/5 border border-white/10 hover:bg-white/10'
                                                }`}
                                        >
                                            <p className={`text-sm font-medium ${tone === opt.value ? 'text-teal-300' : 'text-white'}`}>{opt.label}</p>
                                            <p className="text-xs text-slate-500 mt-0.5">{opt.desc}</p>
                                        </button>
                                    ))}
                                </div>
                            </div>
                            {}
                            <div className="space-y-3">
                                <label className="text-sm font-medium text-slate-300">Answer Length</label>
                                <div className="grid grid-cols-3 gap-3">
                                    {[
                                        { value: 'short', label: 'Short', desc: '2-3 sentences' },
                                        { value: 'medium', label: 'Medium', desc: '4-6 sentences' },
                                        { value: 'detailed', label: 'Detailed', desc: 'With bullet points' },
                                    ].map(opt => (
                                        <button
                                            key={opt.value}
                                            onClick={() => setAnswerLength(opt.value)}
                                            className={`p-3 rounded-xl text-left transition-all ${answerLength === opt.value
                                                ? 'bg-teal-500/15 border-2 border-teal-500/50'
                                                : 'bg-white/5 border border-white/10 hover:bg-white/10'
                                                }`}
                                        >
                                            <p className={`text-sm font-medium ${answerLength === opt.value ? 'text-teal-300' : 'text-white'}`}>{opt.label}</p>
                                            <p className="text-xs text-slate-500 mt-0.5">{opt.desc}</p>
                                        </button>
                                    ))}
                                </div>
                            </div>
                            {}
                            <div className="space-y-3">
                                <label className="text-sm font-medium text-slate-300">Answer Format</label>
                                <div className="grid grid-cols-3 gap-3">
                                    {[
                                        { value: 'star', label: 'STAR', desc: 'Situation-Task-Action-Result' },
                                        { value: 'bullet_points', label: 'Bullet Points', desc: 'Structured bullets' },
                                        { value: 'flowing', label: 'Flowing', desc: 'Natural paragraphs' },
                                    ].map(opt => (
                                        <button
                                            key={opt.value}
                                            onClick={() => setAnswerFormat(opt.value)}
                                            className={`p-3 rounded-xl text-left transition-all ${answerFormat === opt.value
                                                ? 'bg-teal-500/15 border-2 border-teal-500/50'
                                                : 'bg-white/5 border border-white/10 hover:bg-white/10'
                                                }`}
                                        >
                                            <p className={`text-sm font-medium ${answerFormat === opt.value ? 'text-teal-300' : 'text-white'}`}>{opt.label}</p>
                                            <p className="text-xs text-slate-500 mt-0.5">{opt.desc}</p>
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="flex gap-3 pt-2">
                                <CyberButton onClick={() => setCurrentStep(3)} variant="ghost" className="border border-white/10">
                                    <ChevronLeft size={16} className="mr-1" /> Back
                                </CyberButton>
                                <CyberButton onClick={handleSavePreferences} variant="primary" isLoading={isLoading} className="flex-1 justify-center">
                                    Continue <ChevronRight size={16} className="ml-1" />
                                </CyberButton>
                            </div>
                        </GlassCard>
                    )}
                    {}
                    {currentStep === 5 && (
                        <GlassCard className="p-8 space-y-8 text-center">
                            <motion.div
                                initial={{ scale: 0.8, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                transition={{ type: 'spring', damping: 15 }}
                            >
                                <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-emerald-500/20 to-blue-500/20 flex items-center justify-center mb-4 border-2 border-emerald-500/30">
                                    <Sparkles size={36} className="text-emerald-400" />
                                </div>
                                <h2 className="text-2xl font-bold text-white mb-2">You&apos;re All Set!</h2>
                                <p className="text-slate-400 max-w-md mx-auto">
                                    Your profile is configured. Every AI-generated answer will now use your resume,
                                    personal stories, and preferences for authentic, personalized responses.
                                </p>
                            </motion.div>
                            {}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-left">
                                {[
                                    { label: 'Resume', value: parsedResume ? '✅ Uploaded' : '⏭ Skipped', color: parsedResume ? 'text-emerald-400' : 'text-slate-500' },
                                    { label: 'Target Role', value: targetRole || 'Not set', color: targetRole ? 'text-emerald-400' : 'text-slate-500' },
                                    { label: 'Stories', value: `${stories.length} added`, color: stories.length > 0 ? 'text-emerald-400' : 'text-slate-500' },
                                    { label: 'Preferences', value: `${tone}, ${answerLength}`, color: 'text-emerald-400' },
                                ].map((item, i) => (
                                    <div key={i} className="p-3 rounded-xl bg-white/5 border border-white/5">
                                        <p className="text-xs text-slate-500 mb-1">{item.label}</p>
                                        <p className={`text-sm font-medium ${item.color}`}>{item.value}</p>
                                    </div>
                                ))}
                            </div>
                            <div className="flex gap-3 pt-2">
                                <CyberButton onClick={() => setCurrentStep(4)} variant="ghost" className="border border-white/10">
                                    <ChevronLeft size={16} className="mr-1" /> Back
                                </CyberButton>
                                <CyberButton onClick={handleComplete} variant="primary" isLoading={isLoading} className="flex-1 justify-center text-lg py-4">
                                    🚀 Launch Dashboard
                                </CyberButton>
                            </div>
                        </GlassCard>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}
