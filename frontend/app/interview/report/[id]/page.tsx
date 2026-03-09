'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/stores/authStore';
import api from '@/src/lib/api';
import { ArrowLeft, Target, TrendingUp, AlertTriangle, CheckCircle2, Award, Activity, HeartPulse, Sparkles, Brain, MessageSquare, Shield, Eye, Users, Clock, Home } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import GlassCard from '@/components/ui/GlassCard';
import { Skeleton } from '@/components/ui/Skeleton';
import { motion } from 'framer-motion';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';

const { apiClient, getServiceUrl } = api;

interface ReportData {
    id: string;
    session_id: string;
    dimension_details: Record<string, number>;
    coaching_narrative: string;
    strengths: string[];
    improvement_areas: string[];
    action_items: string[];
    readiness_score: number;
}

interface SessionData {
    id: string;
    session_type: string;
    target_role: string;
    overall_score: number;
    emotional_summary?: {
        average_confidence: number;
        average_stress: number;
        filler_words_count?: number;
        speaking_pace_wpm?: number;
    }
}

const DIMENSIONS = [
    { key: 'technical_correctness', label: 'Technical Depth', shortLabel: 'Tech', icon: Brain, color: '#3b82f6' },
    { key: 'communication_clarity', label: 'Communication', shortLabel: 'Comm', icon: MessageSquare, color: '#8b5cf6' },
    { key: 'handling_ambiguity', label: 'Emotional Intelligence', shortLabel: 'EQ', icon: Shield, color: '#06b6d4' },
    { key: 'problem_decomposition', label: 'Problem Solving', shortLabel: 'PS', icon: Target, color: '#10b981' },
    { key: 'edge_case_awareness', label: 'Domain Knowledge', shortLabel: 'Domain', icon: Eye, color: '#f59e0b' },
    { key: 'collaborative_signals', label: 'Collaboration', shortLabel: 'Collab', icon: Users, color: '#ec4899' },
    { key: 'time_management', label: 'Adaptability', shortLabel: 'Adapt', icon: Clock, color: '#f97316' },
    { key: 'growth_mindset', label: 'Confidence', shortLabel: 'Conf', icon: Sparkles, color: '#a855f7' },
];

export default function ReportPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = params.id as string;
    const { isAuthenticated } = useAuthStore();

    const [report, setReport] = useState<ReportData | null>(null);
    const [session, setSession] = useState<SessionData | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        if (!isAuthenticated) router.push('/login');
        else if (sessionId) fetchReportAndSession();
    }, [isAuthenticated, sessionId, router]);

    const fetchReportAndSession = async () => {
        try {
            const reportUrl = getServiceUrl('report');
            const sessionUrl = getServiceUrl('session');

            const [reportRes, sessionRes] = await Promise.all([
                apiClient.get(`${reportUrl}/report/${sessionId}`).catch(() => ({ data: null })),
                apiClient.get(`${sessionUrl}/sessions/${sessionId}`)
            ]);

            setReport(reportRes.data);
            setSession(sessionRes.data);
            setIsLoading(false);

            if (!reportRes.data) {
                toast('Report is still generating... please wait.', { icon: '⏳' });
                setTimeout(fetchReportAndSession, 5000);
            }
        } catch (error: any) {
            console.error('Failed to load report:', error);
            if (error?.response?.status === 401) {
                toast.error('Session expired. Please log in again.');
                router.push('/login');
            } else {
                toast.error('Failed to load interview report details.');
            }
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="max-w-6xl mx-auto px-4 py-12 space-y-8">
                <Skeleton className="h-10 w-64 mb-8" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Skeleton className="h-64 rounded-2xl md:col-span-1" />
                    <Skeleton className="h-64 rounded-2xl md:col-span-2" />
                </div>
                <Skeleton className="h-[400px] w-full rounded-2xl" />
            </div>
        );
    }

    if (!report || !session) {
        return (
            <div className="max-w-4xl mx-auto px-4 py-16 text-center">
                <Activity className="w-12 h-12 text-cyber-purple-400 mx-auto mb-4 animate-pulse" />
                <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyber-purple-400 to-pink-500 mb-2">Analyzing Session Data...</h2>
                <p className="text-slate-400">Our ML models are crunching the numbers. This usually takes a few seconds.</p>
            </div>
        );
    }

    const radarData = DIMENSIONS.map(dim => ({
        subject: dim.label,
        score: Math.round((report.dimension_details[dim.key] || 0) * 100),
        fullMark: 100,
    }));

    const readinessScore = Math.round(report.readiness_score);

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10"
        >
            <Toaster position="top-right" />

            {/* Header */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 pb-4 border-b border-white/10">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="p-3 bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 rounded-xl transition-all hover:scale-105"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyber-teal-400 to-cyber-purple-400 tracking-tight">
                            Interactive Report
                        </h1>
                        <div className="flex items-center gap-3 mt-2">
                            <span className="px-3 py-1 bg-cyber-slate-800 border border-cyber-slate-700 rounded-full text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                {session.target_role}
                            </span>
                            <span className="px-3 py-1 bg-cyber-purple-500/20 border border-cyber-purple-500/30 rounded-full text-xs font-semibold text-cyber-purple-300 uppercase tracking-wider">
                                {session.session_type.replace('_', ' ')}
                            </span>
                        </div>
                    </div>
                </div>
                <div className="flex flex-col items-end">
                    <div className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-1">Readiness Score</div>
                    <div className="flex items-baseline gap-1">
                        <span className="text-5xl font-black text-white">{readinessScore}</span>
                        <span className="text-xl text-slate-500 font-bold">/100</span>
                    </div>
                    {readinessScore >= 80 ? (
                        <div className="text-emerald-400 text-sm font-semibold mt-1 flex items-center gap-1"><CheckCircle2 className="w-4 h-4" /> Outstanding</div>
                    ) : readinessScore >= 50 ? (
                        <div className="text-yellow-400 text-sm font-semibold mt-1 flex items-center gap-1"><TrendingUp className="w-4 h-4" /> On Track</div>
                    ) : (
                        <div className="text-red-400 text-sm font-semibold mt-1 flex items-center gap-1"><AlertTriangle className="w-4 h-4" /> Needs Practice</div>
                    )}
                </div>
            </div>

            {/* Narrative Area */}
            <GlassCard className="p-8 border-l-4 border-l-cyber-purple-500 relative overflow-hidden group hover:border-l-cyber-teal-400 transition-colors">
                <div className="absolute -top-10 -right-10 p-4 opacity-5 pointer-events-none group-hover:scale-110 transition-transform duration-500">
                    <Brain className="w-64 h-64 text-cyber-purple-500" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3 relative z-10">
                    <Sparkles className="w-6 h-6 text-cyber-teal-400" />
                    AI Coach Narrative
                </h3>
                <div className="prose prose-invert max-w-none text-slate-300 text-lg leading-relaxed relative z-10 font-medium tracking-wide">
                    {report.coaching_narrative}
                </div>
            </GlassCard>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                {/* Fixed Interactive Radar Chart */}
                <GlassCard className="p-6 xl:col-span-1 flex flex-col items-center">
                    <div className="w-full flex items-center justify-between mb-4">
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <Target className="w-5 h-5 text-purple-400" />
                            Neural Signature
                        </h3>
                        <div className="text-xs bg-white/10 px-2 py-1 rounded text-slate-300">Interactive</div>
                    </div>
                    <p className="text-sm text-slate-400 text-center w-full mb-2">Hover over the radar to explore dimensions</p>

                    <div className="w-full h-80 my-auto">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                                <PolarGrid stroke="#334155" strokeDasharray="3 3" />
                                <PolarAngleAxis dataKey="subject" tick={{ fill: '#cbd5e1', fontSize: 13, fontWeight: 500 }} />
                                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11 }} tickCount={5} />
                                <Radar
                                    name="Score"
                                    dataKey="score"
                                    stroke="#8b5cf6"
                                    strokeWidth={3}
                                    fill="url(#colorUv)"
                                    fillOpacity={0.6}
                                    activeDot={{ r: 6, fill: '#2dd4bf', stroke: '#fff', strokeWidth: 2 }}
                                />
                                <defs>
                                    <linearGradient id="colorUv" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                                        <stop offset="95%" stopColor="#2dd4bf" stopOpacity={0.2} />
                                    </linearGradient>
                                </defs>
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc', borderRadius: '12px', padding: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.5)' }}
                                    itemStyle={{ color: '#2dd4bf', fontWeight: 'bold' }}
                                />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                </GlassCard>

                {/* Right Side Info blocks */}
                <div className="xl:col-span-2 flex flex-col gap-8">
                    {/* Emotional Stats (If available) */}
                    {session.emotional_summary && (
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                            <motion.div whileHover={{ y: -5 }} className="bg-cyber-slate-800/80 rounded-2xl p-5 border border-white/5 text-center shadow-lg transition-colors cursor-pointer hover:border-pink-500/50">
                                <HeartPulse className="w-6 h-6 text-pink-500 mx-auto mb-3" />
                                <div className="text-3xl font-black text-white">{Math.round(session.emotional_summary.average_stress || 0)}%</div>
                                <div className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-2">Avg Stress</div>
                            </motion.div>
                            <motion.div whileHover={{ y: -5 }} className="bg-cyber-slate-800/80 rounded-2xl p-5 border border-white/5 text-center shadow-lg transition-colors cursor-pointer hover:border-cyber-teal-500/50">
                                <Award className="w-6 h-6 text-cyber-teal-400 mx-auto mb-3" />
                                <div className="text-3xl font-black text-white">{Math.round(session.emotional_summary.average_confidence || 0)}%</div>
                                <div className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-2">Confidence</div>
                            </motion.div>
                            <motion.div whileHover={{ y: -5 }} className="bg-cyber-slate-800/80 rounded-2xl p-5 border border-white/5 text-center shadow-lg transition-colors cursor-pointer hover:border-yellow-500/50">
                                <Activity className="w-6 h-6 text-yellow-400 mx-auto mb-3" />
                                <div className="text-3xl font-black text-white">{session.emotional_summary.filler_words_count || 0}</div>
                                <div className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-2">Filler Words</div>
                            </motion.div>
                            <motion.div whileHover={{ y: -5 }} className="bg-cyber-slate-800/80 rounded-2xl p-5 border border-white/5 text-center shadow-lg transition-colors cursor-pointer hover:border-cyber-purple-500/50">
                                <Activity className="w-6 h-6 text-cyber-purple-400 mx-auto mb-3" />
                                <div className="text-3xl font-black text-white">{session.emotional_summary.speaking_pace_wpm || 0}</div>
                                <div className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-2">Pace (WPM)</div>
                            </motion.div>
                        </div>
                    )}

                    {/* Action Items */}
                    <GlassCard className="p-8 flex-grow flex flex-col">
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                            <TrendingUp className="w-6 h-6 text-cyber-teal-400" />
                            Next Steps & Action Items
                        </h3>
                        <div className="space-y-4">
                            {report.action_items.map((item, idx) => (
                                <motion.div
                                    whileHover={{ x: 5 }}
                                    key={idx}
                                    className="flex items-start gap-4 p-4 rounded-xl bg-gradient-to-r from-cyber-slate-800 to-transparent border border-white/5"
                                >
                                    <div className="mt-1 bg-cyber-teal-500/20 rounded-full p-1.5 border border-cyber-teal-500/40 text-cyber-teal-400 flex-shrink-0">
                                        <CheckCircle2 className="w-4 h-4" />
                                    </div>
                                    <p className="text-slate-300 font-medium leading-relaxed">{item}</p>
                                </motion.div>
                            ))}
                        </div>
                    </GlassCard>
                </div>
            </div>

            {/* Strengths & Weaknesses */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <GlassCard className="p-8 border-t-4 border-t-emerald-500">
                    <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                        <Award className="w-6 h-6 text-emerald-400" />
                        Key Strengths Identified
                    </h3>
                    <ul className="space-y-4">
                        {report.strengths.map((str, i) => (
                            <li key={i} className="flex items-start gap-3 text-slate-300 bg-white/5 p-4 rounded-lg">
                                <span className="text-emerald-500 font-bold text-lg leading-none mt-0.5">•</span>
                                <span className="font-medium">{str}</span>
                            </li>
                        ))}
                    </ul>
                </GlassCard>
                <GlassCard className="p-8 border-t-4 border-t-amber-500">
                    <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                        <AlertTriangle className="w-6 h-6 text-amber-400" />
                        Areas For Improvement
                    </h3>
                    <ul className="space-y-4">
                        {report.improvement_areas.map((area, i) => (
                            <li key={i} className="flex items-start gap-3 text-slate-300 bg-white/5 p-4 rounded-lg">
                                <span className="text-amber-500 font-bold text-lg leading-none mt-0.5">•</span>
                                <span className="font-medium">{area}</span>
                            </li>
                        ))}
                    </ul>
                </GlassCard>
            </div>

            {/* STAR Method Analysis */}
            <GlassCard className="p-8">
                <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
                    <div>
                        <h3 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
                            <Target className="w-6 h-6 text-blue-400" />
                            STAR Method Breakdown
                        </h3>
                        <p className="text-slate-400 font-medium">How well your answers followed the Situation-Task-Action-Result format</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {[
                        { label: 'Situation', desc: 'Set the scene clearly', key: 'handling_ambiguity', color: '#3b82f6', hex: '59,130,246', emoji: '📍' },
                        { label: 'Task', desc: 'Defined your responsibility', key: 'problem_decomposition', color: '#8b5cf6', hex: '139,92,246', emoji: '🎯' },
                        { label: 'Action', desc: 'Explained your specific actions', key: 'technical_correctness', color: '#10b981', hex: '16,185,129', emoji: '⚡' },
                        { label: 'Result', desc: 'Quantified the outcome', key: 'communication_clarity', color: '#f59e0b', hex: '245,158,11', emoji: '✅' },
                    ].map((step, i) => {
                        const score = Math.round((report.dimension_details[step.key] || 0) * 100);
                        return (
                            <motion.div
                                key={step.label}
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.15, duration: 0.5 }}
                                whileHover={{ scale: 1.05, y: -5 }}
                                className="p-6 rounded-2xl text-center relative overflow-hidden group cursor-default shadow-lg"
                                style={{
                                    background: `rgba(${step.hex}, 0.05)`,
                                    border: `1px solid rgba(${step.hex}, 0.2)`
                                }}
                            >
                                <div className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500" style={{ background: `radial-gradient(circle at center, ${step.color} 0%, transparent 70%)` }} />
                                <span className="text-3xl mb-3 block transform group-hover:scale-110 transition-transform">{step.emoji}</span>
                                <h4 className="text-lg font-bold text-white mb-1">{step.label}</h4>
                                <p className="text-xs text-slate-400 mb-4 font-medium">{step.desc}</p>
                                <div className="relative w-full h-3 rounded-full bg-slate-800 overflow-hidden mb-2">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        whileInView={{ width: `${score}%` }}
                                        viewport={{ once: true }}
                                        transition={{ duration: 1.5, delay: 0.3 + i * 0.1 }}
                                        className="h-full rounded-full shadow-[inset_0_2px_4px_rgba(255,255,255,0.3)]"
                                        style={{ backgroundColor: step.color }}
                                    />
                                </div>
                                <p className="text-xl font-black" style={{ color: step.color }}>{score}%</p>
                            </motion.div>
                        );
                    })}
                </div>
            </GlassCard>

            {/* Follow-Up Questions */}
            <GlassCard className="p-8">
                <h3 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
                    <MessageSquare className="w-6 h-6 text-amber-400" />
                    Likely Follow-Up Questions
                </h3>
                <p className="text-slate-400 font-medium mb-8">Based on your lower-scoring areas, interviewers would likely probe these topics next</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {(() => {
                        const weakDimensions = DIMENSIONS
                            .map(d => ({ ...d, score: report.dimension_details[d.key] || 0 }))
                            .sort((a, b) => a.score - b.score)
                            .slice(0, 3);

                        const followUpMap: Record<string, string[]> = {
                            technical_correctness: ['Can you walk me through the technical architecture of that solution in more detail?', 'How did you test and validate that approach?'],
                            communication_clarity: ['Could you give me a more specific example with measurable outcomes?', 'How would you explain this decision to a non-technical stakeholder?'],
                            handling_ambiguity: ['What did you do when the requirements changed mid-project?', 'How do you typically handle situations with incomplete information?'],
                            problem_decomposition: ['How did you break down the problem into manageable pieces?', 'What was your framework for prioritizing parts?'],
                            edge_case_awareness: ['What edge cases or failure scenarios did you consider?', 'How would this approach scale if the user base grew 10x?'],
                            collaborative_signals: ['How did you get buy-in from other teams?', 'Tell me about a disagreement with a colleague and the resolution.'],
                            time_management: ['How did you adjust when timelines shifted?', 'What would you do differently with more time?'],
                            growth_mindset: ['What would you do differently if you could approach this again?', 'How has this experience shaped your coding approach?'],
                        };

                        return weakDimensions.map((dim, i) => {
                            const questions = followUpMap[dim.key] || ['Tell me more about your approach.'];
                            const Icon = dim.icon;
                            return (
                                <motion.div
                                    whileHover={{ y: -5 }}
                                    key={dim.key}
                                    className="p-6 rounded-2xl bg-white/[0.03] border border-white/10 hover:border-amber-500/30 transition-colors shadow-lg"
                                >
                                    <div className="flex items-center gap-3 mb-4 pb-4 border-b border-white/10">
                                        <div className="p-2 rounded-lg" style={{ backgroundColor: `${dim.color}20` }}>
                                            <Icon className="w-5 h-5" style={{ color: dim.color }} />
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-sm font-bold text-white">{dim.label}</span>
                                            <span className="text-xs text-slate-400">{Math.round(dim.score * 100)}% Proficiency Focus</span>
                                        </div>
                                    </div>
                                    <ul className="space-y-4">
                                        {questions.map((q, j) => (
                                            <li key={j} className="flex items-start gap-3 text-sm text-slate-300">
                                                <span className="text-amber-400 font-bold mt-0.5">Q:</span>
                                                <span className="font-medium leading-relaxed italic">{q}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </motion.div>
                            );
                        });
                    })()}
                </div>
            </GlassCard>

            {/* End Review Button Section */}
            <div className="flex justify-center pt-8 pb-16">
                <motion.button
                    whileHover={{ scale: 1.05, boxShadow: "0 0 30px rgba(45, 212, 191, 0.4)" }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => router.push('/dashboard')}
                    className="flex text-lg items-center gap-3 px-10 py-5 bg-gradient-to-r from-cyber-purple-600 to-cyber-teal-600 text-white font-black rounded-2xl shadow-xl transition-all"
                >
                    <Home className="w-6 h-6" />
                    End Review & Return Home
                </motion.button>
            </div>
        </motion.div>
    );
}