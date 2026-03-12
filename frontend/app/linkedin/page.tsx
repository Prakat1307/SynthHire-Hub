'use client';
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/lib/stores/authStore';
import api from '@/src/lib/api';
import {
    Briefcase, Lightbulb, FileText, Target, Layers, UserCircle,
    CheckCircle2, Circle, Wand2, Copy, Download, Linkedin,
    RefreshCw, Info, ChevronDown, ChevronUp, Search, AlertTriangle,
    Link as LinkIcon, ClipboardPaste,
} from 'lucide-react';
import GlassCard from '@/components/ui/GlassCard';
import CyberButton from '@/components/ui/CyberButton';
import toast, { Toaster } from 'react-hot-toast';
type SectionId = 'headline' | 'about' | 'experience' | 'skills' | 'projects' | 'open_to_work';
const SECTIONS: { id: SectionId; label: string; icon: React.ElementType; points: number }[] = [
    { id: 'headline', label: 'Headline', icon: UserCircle, points: 15 },
    { id: 'about', label: 'About / Summary', icon: FileText, points: 20 },
    { id: 'experience', label: 'Experience', icon: Briefcase, points: 30 },
    { id: 'skills', label: 'Skills', icon: Target, points: 20 },
    { id: 'projects', label: 'Projects', icon: Layers, points: 15 },
    { id: 'open_to_work', label: 'Open To Work', icon: Lightbulb, points: 0 },
];
export default function LinkedInOptimizerPage() {
    const authState = useAuthStore() as any;
    const { profile } = authState;
    const [activeSection, setActiveSection] = useState<SectionId>('headline');
    const [targetRole, setTargetRole] = useState('');
    const [jdContext, setJdContext] = useState('');
    
    const [linkedInUrl, setLinkedInUrl] = useState('');
    const [linkedInContext, setLinkedInContext] = useState('');
    const [resumeContext, setResumeContext] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const [isFetching, setIsFetching] = useState(false);
    const [fetchError, setFetchError] = useState('');
    const [inputMode, setInputMode] = useState<'url' | 'paste'>('url');
    const [isGenerating, setIsGenerating] = useState(false);
    const [sectionData, setSectionData] = useState<Record<SectionId, any>>({
        headline: null, about: null, experience: null, skills: null, projects: null, open_to_work: null,
    });
    const [completedSections, setCompletedSections] = useState<Record<SectionId, boolean>>({
        headline: false, about: false, experience: false, skills: false, projects: false, open_to_work: false,
    });
    useEffect(() => {
        if (profile?.resume_text && !resumeContext) setResumeContext(profile.resume_text);
    }, [profile, resumeContext]);
    const totalScore = SECTIONS.reduce((acc, s) => acc + (completedSections[s.id] ? s.points : 0), 0);
    const handleFetchLinkedIn = async () => {
        if (!linkedInUrl.trim()) { toast.error('Enter a LinkedIn profile URL.'); return; }
        if (!linkedInUrl.includes('linkedin.com/in/')) { toast.error('Please enter a valid LinkedIn profile URL (e.g. linkedin.com/in/username)'); return; }
        setIsFetching(true);
        setFetchError('');
        try {
            const res = await api.apiClient.post(api.getServiceUrl('resume') + '/linkedin/fetch-profile', {
                url: linkedInUrl.trim()
            });
            if (res.data?.is_auth_wall || !res.data?.profile_text) {
                setFetchError('LinkedIn blocked automatic fetching (auth wall). Please switch to paste mode below and paste your profile text manually.');
                setInputMode('paste');
                toast.error('LinkedIn blocked fetch — please paste profile text manually.', { duration: 5000 });
            } else {
                setLinkedInContext(res.data.profile_text);
                setFetchError('');
                toast.success(`Profile fetched! ${res.data.profile_text.length.toLocaleString()} chars loaded.`);
            }
        } catch (err: any) {
            setFetchError('Failed to fetch profile. Try paste mode instead.');
            setInputMode('paste');
            toast.error('Fetch failed — please paste profile text manually.');
        } finally {
            setIsFetching(false);
        }
    };
    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setIsUploading(true);
        const formData = new FormData();
        formData.append('resume_file', file);
        try {
            const res = await api.apiClient.post(
                api.getServiceUrl('onboarding') + '/onboarding/resume/upload',
                formData, { headers: { 'Content-Type': 'multipart/form-data' } }
            );
            setResumeContext(res.data.raw_text);
            toast.success('Resume parsed successfully!');
        } catch { toast.error('Failed to parse resume.'); }
        finally { setIsUploading(false); }
    };
    const handleOptimize = async () => {
        if (!resumeContext && !linkedInContext) {
            toast.error('Upload a resume or fetch/paste your LinkedIn profile first.');
            return;
        }
        setIsGenerating(true);
        try {
            const res = await api.apiClient.post(api.getServiceUrl('resume') + '/linkedin/optimize', {
                section: activeSection,
                resume_data: resumeContext || linkedInContext || 'No resume provided.',
                target_role: targetRole || undefined,
                job_description: jdContext || undefined,
                existing_linkedin_text: linkedInContext || undefined,
            });
            setSectionData(prev => ({ ...prev, [activeSection]: res.data }));
            toast.success('Section optimized!');
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Optimization failed.');
        } finally { setIsGenerating(false); }
    };
    const handleCopy = () => {
        const text = sectionData[activeSection]?.optimized_text;
        if (text) { navigator.clipboard.writeText(text); toast.success('Copied!'); }
    };
    const markSectionDone = () => {
        setCompletedSections(prev => ({ ...prev, [activeSection]: true }));
        toast.success(`${SECTIONS.find(s => s.id === activeSection)?.label} done!`);
    };
    const handleDownloadReport = () => {
        if (totalScore === 0) {
            toast.error("Generate and complete at least one section before downloading.");
            return;
        }
        let reportText = `SYNTHHIRE LINKEDIN OPTIMIZATION REPORT\n`;
        reportText += `Target Role: ${targetRole || 'Not Specified'}\n`;
        reportText += `Total Score: ${totalScore} / 100\n`;
        reportText += `Generated At: ${new Date().toLocaleString()}\n\n`;
        reportText += `=================================================\n\n`;
        SECTIONS.forEach(section => {
            if (completedSections[section.id] && sectionData[section.id]) {
                const data = sectionData[section.id];
                reportText += `[ ✨ ${section.label.toUpperCase()} ]\n\n`;
                reportText += `${data.optimized_text}\n\n`;
                if (data.keywords_added && data.keywords_added.length > 0) {
                    reportText += `Keywords Hit: ${data.keywords_added.join(', ')}\n\n`;
                }
                reportText += `-------------------------------------------------\n\n`;
            }
        });
        const blob = new Blob([reportText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `LinkedIn_Report_${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("Report downloaded!");
    };
    const activeData = sectionData[activeSection];
    return (
        <div className="min-h-screen text-[var(--text-primary)] font-sans flex flex-col h-[calc(100vh-64px)] overflow-hidden">
            <Toaster position="top-right" toastOptions={{
                style: { background: 'var(--card-bg)', color: 'var(--text-primary)', border: '1px solid var(--card-border)' }
            }} />
            {}
            <header className="h-16 flex-shrink-0 border-b border-[var(--card-border)] bg-[var(--bg-surface)]/50 flex items-center px-6 gap-3">
                <Linkedin className="text-blue-500 w-6 h-6" />
                <div>
                    <h1 className="text-lg font-bold">LinkedIn Optimizer</h1>
                    <p className="text-xs text-[var(--text-muted)]">AI-powered profile optimizer — fetch or paste your LinkedIn profile</p>
                </div>
            </header>
            {}
            <div className="flex-1 flex overflow-hidden">
                {}
                <div className="w-[240px] flex-shrink-0 border-r border-[var(--card-border)] bg-[var(--bg-surface)]/30 flex flex-col">
                    <div className="flex-1 w-full overflow-y-auto p-4 space-y-2">
                        {SECTIONS.map((section) => {
                            const isActive = activeSection === section.id;
                            const isDone = completedSections[section.id];
                            const Icon = section.icon;
                            return (
                                <button key={section.id} onClick={() => setActiveSection(section.id)}
                                    className={`w-full flex items-center justify-between p-3 rounded-lg text-sm font-medium transition-all ${isActive
                                        ? 'bg-purple-500/10 text-purple-400 border-l-4 border-l-purple-500'
                                        : 'text-[var(--text-secondary)] hover:bg-[var(--card-border)] hover:text-[var(--text-primary)] border-l-4 border-l-transparent'
                                        }`}>
                                    <div className="flex items-center gap-3"><Icon className="w-4 h-4" />{section.label}</div>
                                    {isDone && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
                                </button>
                            );
                        })}
                    </div>
                    <div className="p-4 border-t border-[var(--card-border)]">
                        <a href="https://linkedin.com/in/" target="_blank" rel="noreferrer"
                            className="w-full flex items-center justify-center gap-2 p-3 text-sm font-medium rounded-lg bg-[#0A66C2]/10 text-[#0A66C2] hover:bg-[#0A66C2]/20 transition-colors border border-[#0A66C2]/20">
                            <Linkedin className="w-4 h-4" />Open My LinkedIn
                        </a>
                    </div>
                </div>
                {}
                <div className="flex-1 overflow-y-auto bg-[var(--bg-deep)] p-6">
                    <div className="max-w-3xl mx-auto space-y-6">
                        {}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <GlassCard className="p-4 flex flex-col gap-2">
                                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Target Role (Optional)</label>
                                <input type="text" value={targetRole} onChange={e => setTargetRole(e.target.value)}
                                    placeholder="e.g. ML Engineer at FAANG"
                                    className="w-full bg-[var(--bg-surface)] border border-[var(--card-border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-purple-500 transition-colors" />
                            </GlassCard>
                            <GlassCard className="p-4 flex flex-col gap-2">
                                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Job Description (Optional)</label>
                                <input type="text" value={jdContext} onChange={e => setJdContext(e.target.value)}
                                    placeholder="Paste job description keywords"
                                    className="w-full bg-[var(--bg-surface)] border border-[var(--card-border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-purple-500 transition-colors" />
                            </GlassCard>
                        </div>
                        {}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {}
                            <GlassCard className="p-4 flex flex-col gap-2">
                                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Resume Context</label>
                                <div className="flex items-center gap-2">
                                    <input type="file" accept=".pdf,.txt,.doc,.docx" onChange={handleFileUpload} disabled={isUploading}
                                        className="text-xs w-full text-[var(--text-secondary)] file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:bg-purple-500/10 file:text-purple-500 hover:file:bg-purple-500/20 cursor-pointer" />
                                    {isUploading && <RefreshCw className="w-4 h-4 animate-spin text-purple-500 shrink-0" />}
                                </div>
                                <div className="p-2 rounded bg-[var(--bg-surface)] border border-[var(--card-border)] text-[10px] text-[var(--text-muted)] h-24 overflow-y-auto whitespace-pre-wrap leading-tight">
                                    {resumeContext || 'No resume context. Upload a PDF above or it auto-loads from your profile.'}
                                </div>
                            </GlassCard>
                            {}
                            <GlassCard className="p-4 flex flex-col gap-2">
                                <div className="flex items-center justify-between">
                                    <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">LinkedIn Profile</label>
                                    <div className="flex gap-1">
                                        <button onClick={() => setInputMode('url')}
                                            className={`px-2 py-0.5 rounded text-[10px] font-bold transition-colors ${inputMode === 'url' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'}`}>
                                            <LinkIcon className="w-3 h-3 inline mr-1" />URL
                                        </button>
                                        <button onClick={() => setInputMode('paste')}
                                            className={`px-2 py-0.5 rounded text-[10px] font-bold transition-colors ${inputMode === 'paste' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'}`}>
                                            <ClipboardPaste className="w-3 h-3 inline mr-1" />Paste
                                        </button>
                                    </div>
                                </div>
                                {inputMode === 'url' ? (
                                    <>
                                        <div className="flex gap-2">
                                            <input type="text" value={linkedInUrl} onChange={e => setLinkedInUrl(e.target.value)}
                                                placeholder="https://linkedin.com/in/username"
                                                className="flex-1 bg-[var(--bg-surface)] border border-[var(--card-border)] rounded-md px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
                                                onKeyDown={e => e.key === 'Enter' && handleFetchLinkedIn()} />
                                            <button onClick={handleFetchLinkedIn} disabled={isFetching}
                                                className="px-4 py-2 rounded-md bg-[#0A66C2] text-[var(--text-primary)] text-sm font-bold hover:bg-[#0A66C2]/80 disabled:opacity-50 transition-colors flex items-center gap-2">
                                                {isFetching ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                                                {isFetching ? 'Fetching...' : 'Fetch'}
                                            </button>
                                        </div>
                                        {fetchError && (
                                            <div className="flex items-start gap-2 p-2 rounded bg-amber-500/10 border border-amber-500/20 text-[10px] text-amber-400">
                                                <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                                                <span>{fetchError}</span>
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <>
                                        <textarea value={linkedInContext} onChange={e => setLinkedInContext(e.target.value)}
                                            placeholder={"Paste your LinkedIn profile text here.\n\nHow: Open your LinkedIn → Ctrl+A → Ctrl+C → paste here"}
                                            className="w-full h-28 bg-[var(--bg-surface)] border border-[var(--card-border)] rounded-md px-3 py-2 text-[11px] text-[var(--text-secondary)] focus:outline-none focus:border-purple-500 transition-colors resize-none placeholder:text-gray-600 leading-relaxed" />
                                    </>
                                )}
                                {linkedInContext && (
                                    <div className="text-[10px] text-emerald-400 flex items-center gap-1">
                                        <CheckCircle2 className="w-3 h-3" />
                                        {linkedInContext.length.toLocaleString()} chars loaded — AI will use this for optimization
                                    </div>
                                )}
                            </GlassCard>
                        </div>
                        {}
                        <div className="space-y-2">
                            <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                                <Wand2 className="w-4 h-4 text-purple-500" />
                                AI Optimized — <span className="text-purple-400 capitalize">{activeSection.replace('_', ' ')}</span>
                            </h3>
                            <motion.div className="rounded-xl bg-gradient-to-br from-purple-500/20 via-cyan-500/20 to-transparent p-[1px]"
                                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} key={activeSection}>
                                <div className="bg-[var(--card-bg)] rounded-[11px] p-4 flex flex-col h-64 border border-[var(--card-border)]">
                                    <textarea
                                        className={`w-full flex-1 bg-transparent resize-none outline-none text-sm ${isGenerating ? 'text-[var(--text-muted)] animate-pulse' : 'text-[var(--text-primary)]'}`}
                                        placeholder={isGenerating ? '✨ AI is generating...' : 'Click Generate to get optimized LinkedIn content.'}
                                        value={activeData?.optimized_text || ''}
                                        onChange={e => { if (activeData) setSectionData(prev => ({ ...prev, [activeSection]: { ...prev[activeSection], optimized_text: e.target.value } })); }}
                                        disabled={isGenerating} />
                                    <div className="text-right text-xs text-[var(--text-muted)] pt-2 border-t border-[var(--card-border)] mt-2">
                                        {activeData ? activeData.optimized_text.length : 0} / {activeData ? activeData.char_limit : 2000} chars
                                    </div>
                                </div>
                            </motion.div>
                            <div className="flex flex-wrap items-center gap-3 pt-2">
                                <CyberButton variant="ghost" className="text-sm py-1.5 px-4" onClick={handleOptimize} disabled={isGenerating}>
                                    <RefreshCw className={`w-4 h-4 mr-2 ${isGenerating ? 'animate-spin' : ''}`} />
                                    {isGenerating ? 'Generating...' : activeData ? 'Regenerate' : 'Generate'}
                                </CyberButton>
                                <CyberButton variant="ghost" className="text-sm py-1.5 px-4 mr-auto" onClick={handleCopy} disabled={!activeData}>
                                    <Copy className="w-4 h-4 mr-2" />Copy
                                </CyberButton>
                                <CyberButton onClick={markSectionDone} className="text-sm py-1.5 px-6" disabled={!activeData || completedSections[activeSection]}>
                                    <CheckCircle2 className="w-4 h-4 mr-2" />
                                    {completedSections[activeSection] ? 'Done ✓' : 'Mark Done'}
                                </CyberButton>
                            </div>
                            {activeData && (
                                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                                    className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-6">
                                    <GlassCard className="p-4 space-y-3 border-emerald-500/20 bg-emerald-500/5">
                                        <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Keywords Added</h4>
                                        <div className="flex flex-wrap gap-2">
                                            {activeData.keywords_added?.map((kw: string, i: number) => (
                                                <span key={i} className="px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">{kw}</span>
                                            ))}
                                            {(!activeData.keywords_added || activeData.keywords_added.length === 0) && (
                                                <span className="text-xs text-[var(--text-muted)]">No specific keywords.</span>
                                            )}
                                        </div>
                                    </GlassCard>
                                    <GlassCard className="p-4 space-y-2 border-purple-500/20 bg-purple-500/5">
                                        <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider">AI Tips</h4>
                                        <ul className="text-xs text-[var(--text-secondary)] space-y-1 list-disc pl-4">
                                            {activeData.tips?.map((tip: string, i: number) => (<li key={i}>{tip}</li>))}
                                        </ul>
                                    </GlassCard>
                                </motion.div>
                            )}
                        </div>
                    </div>
                </div>
                {}
                <div className="w-[280px] flex-shrink-0 border-l border-[var(--card-border)] bg-[var(--bg-surface)]/30 flex flex-col items-center">
                    <div className="p-8 w-full flex flex-col items-center border-b border-[var(--card-border)]">
                        <div className="relative w-32 h-32 flex items-center justify-center">
                            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                                <circle cx="50" cy="50" r="45" fill="none" stroke="var(--card-border)" strokeWidth="8" />
                                <motion.circle cx="50" cy="50" r="45" fill="none"
                                    stroke={totalScore >= 80 ? '#10b981' : totalScore >= 50 ? '#8b5cf6' : '#ec4899'}
                                    strokeWidth="8" strokeDasharray="283" strokeDashoffset={283 - (283 * totalScore) / 100}
                                    strokeLinecap="round" className="transition-all duration-1000 ease-out" />
                            </svg>
                            <div className="absolute flex flex-col items-center">
                                <span className="text-3xl font-black text-[var(--text-primary)]">{totalScore}</span>
                                <span className="text-xs text-[var(--text-muted)] font-bold uppercase tracking-widest">Score</span>
                            </div>
                        </div>
                        <p className="text-xs text-[var(--text-muted)] text-center mt-3">
                            {totalScore === 0 ? 'Generate sections to build your score'
                                : totalScore >= 80 ? '🎉 Excellent profile!'
                                    : 'Keep optimizing sections'}
                        </p>
                    </div>
                    <div className="flex-1 w-full p-6 space-y-4">
                        <h3 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Profile Checklist</h3>
                        <div className="space-y-3">
                            {SECTIONS.filter(s => s.points > 0).map(section => (
                                <div key={`check-${section.id}`} className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        {completedSections[section.id]
                                            ? <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                                            : <Circle className="w-4 h-4 text-[var(--card-border-hover)]" />}
                                        <span className={`text-sm ${completedSections[section.id] ? 'text-[var(--text-primary)] font-medium' : 'text-[var(--text-secondary)]'}`}>
                                            {section.label}
                                        </span>
                                    </div>
                                    <span className="text-xs text-[var(--text-muted)]">{section.points} pts</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="p-6 w-full mt-auto border-t border-[var(--card-border)]">
                        <button onClick={handleDownloadReport} className="w-full flex items-center justify-center gap-2 p-3 text-sm font-bold rounded-lg bg-[var(--card-bg)] text-[var(--text-primary)] hover:bg-[var(--bg-deep)] transition-colors border border-[var(--card-border)] shadow-sm">
                            <Download className="w-4 h-4" />Download Report
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
