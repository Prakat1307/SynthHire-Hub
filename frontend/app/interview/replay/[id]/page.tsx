'use client';
import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '@/lib/stores/authStore';
import api from '@/src/lib/api';
import GlassCard from '@/components/ui/GlassCard';
import CyberButton from '@/components/ui/CyberButton';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Play, Pause, SkipForward, SkipBack, Rewind,
    MessageSquare, Code2, Brain, Zap, Clock, ArrowLeft,
    TrendingUp, AlertCircle, CheckCircle, Lightbulb,
    ChevronRight, Sparkles, Shield, AlertTriangle
} from 'lucide-react';
import {
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts';
const { apiClient, getServiceUrl } = api;
const DIMENSIONS = [
    { key: 'technical_correctness', label: 'Technical', color: '#3b82f6' },
    { key: 'communication_clarity', label: 'Communication', color: '#8b5cf6' },
    { key: 'handling_ambiguity', label: 'EQ', color: '#06b6d4' },
    { key: 'problem_decomposition', label: 'Problem Solving', color: '#10b981' },
    { key: 'edge_case_awareness', label: 'Domain', color: '#f59e0b' },
    { key: 'collaborative_signals', label: 'Collaboration', color: '#ec4899' },
    { key: 'time_management', label: 'Adaptability', color: '#f97316' },
    { key: 'growth_mindset', label: 'Confidence', color: '#a855f7' },
];
interface Exchange {
    exchange_number: number;
    interviewer_text: string;
    candidate_text: string;
    dimension_scores: Record<string, number> | null;
    coaching_hints_sent: any[] | null;
    question_type: string;
    timestamp_start: string;
    timestamp_end: string;
}
interface SessionData {
    id: string;
    session_type: string;
    persona_type: string;
    coaching_mode: string;
    overall_score: number | null;
    dimension_scores: Record<string, number> | null;
    started_at: string;
    completed_at: string;
    duration_seconds: number;
    company_slug: string;
    target_role: string;
}
function generateMockReplay() {
    const mockSession: SessionData = {
        id: 'mock-replay',
        session_type: 'coding',
        persona_type: 'tough_lead',
        coaching_mode: 'training',
        overall_score: 72.5,
        dimension_scores: Object.fromEntries(DIMENSIONS.map(d => [d.key, Math.random() * 40 + 50])),
        started_at: new Date(Date.now() - 3600000).toISOString(),
        completed_at: new Date().toISOString(),
        duration_seconds: 2700,
        company_slug: 'google',
        target_role: 'Software Engineer',
    };
    const mockExchanges: Exchange[] = Array.from({ length: 8 }, (_, i) => ({
        exchange_number: i + 1,
        interviewer_text: [
            "Let's start with a warm-up. Can you tell me about your experience with distributed systems?",
            "Great. Now, given a sorted array of integers, write a function to find two numbers that add up to a target sum.",
            "Good approach. What's the time complexity? Can you optimize it?",
            "Now let's move to system design. How would you design a URL shortener like bit.ly?",
            "How would you handle high traffic? What about database scaling?",
            "Tell me about a time you had a disagreement with a team member. How did you resolve it?",
            "Interesting. What would you do differently if that situation happened again?",
            "We're almost out of time. Any questions for me?",
        ][i] || "Next question...",
        candidate_text: [
            "I've worked extensively with microservices and event-driven architectures. At my previous role, I built a real-time data pipeline using Kafka and Redis.",
            "I'd use a two-pointer approach. Start with pointers at both ends, move them inward based on the sum comparison.",
            "The two-pointer approach gives O(n) time and O(1) space, which is optimal for a sorted array.",
            "I'd use a hash-based approach. Generate short codes, store mappings in a database with caching layer...",
            "For high traffic, I'd add a load balancer, use Redis for caching popular URLs, and shard the database by hash prefix.",
            "In my last project, a colleague and I disagreed on the API design. I proposed we each prototype our approach and compare results with the team.",
            "I'd bring up the disagreement earlier and set clear decision criteria upfront to avoid wasted effort.",
            "What's the team culture like? How do you handle technical debt?",
        ][i] || "My answer...",
        dimension_scores: Object.fromEntries(
            DIMENSIONS.map(d => [d.key, Math.max(30, Math.min(95, 50 + Math.random() * 40 + i * 2))])
        ),
        coaching_hints_sent: i % 3 === 0 ? [{ hint: "Consider mentioning edge cases", dimension: "edge_case_awareness", priority: "medium" }] : null,
        question_type: ['behavioral', 'coding', 'coding', 'system_design', 'system_design', 'behavioral', 'behavioral', 'general'][i],
        timestamp_start: new Date(Date.now() - 3600000 + i * 300000).toISOString(),
        timestamp_end: new Date(Date.now() - 3600000 + (i + 1) * 300000).toISOString(),
    }));
    return { mockSession, mockExchanges };
}
export default function ReplayPage() {
    const router = useRouter();
    const params = useParams();
    const sessionId = params?.id as string;
    const { accessToken } = useAuthStore();
    const [session, setSession] = useState<SessionData | null>(null);
    const [exchanges, setExchanges] = useState<Exchange[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeExchange, setActiveExchange] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [showFixIt, setShowFixIt] = useState(false);
    const [fixItSuggestion, setFixItSuggestion] = useState('');
    const [fixItLoading, setFixItLoading] = useState(false);
    useEffect(() => {
        loadReplayData();
    }, [sessionId]);
    useEffect(() => {
        if (!isPlaying) return;
        const timer = setInterval(() => {
            setActiveExchange(prev => {
                if (prev >= exchanges.length - 1) {
                    setIsPlaying(false);
                    return prev;
                }
                return prev + 1;
            });
        }, 4000);
        return () => clearInterval(timer);
    }, [isPlaying, exchanges.length]);
    async function loadReplayData() {
        setLoading(true);
        try {
            const sessionUrl = getServiceUrl('session');
            const [sessionRes, exchangesRes] = await Promise.allSettled([
                apiClient.get(`${sessionUrl}/sessions/${sessionId}`, {
                    headers: { Authorization: `Bearer ${accessToken}` },
                }),
                apiClient.get(`${sessionUrl}/sessions/${sessionId}/exchanges`, {
                    headers: { Authorization: `Bearer ${accessToken}` },
                }),
            ]);
            if (sessionRes.status === 'fulfilled') setSession(sessionRes.value.data);
            if (exchangesRes.status === 'fulfilled') setExchanges(exchangesRes.value.data || []);
        } catch {
        }
        if (!session || exchanges.length === 0) {
            const mock = generateMockReplay();
            setSession(mock.mockSession);
            setExchanges(mock.mockExchanges);
        }
        setLoading(false);
    }
    async function handleFixIt(exchangeIndex: number) {
        setShowFixIt(true);
        setFixItLoading(true);
        const exchange = exchanges[exchangeIndex];
        try {
            const assessUrl = getServiceUrl('assessment');
            const res = await apiClient.post(`${assessUrl}/coaching-hints`, {
                response_text: exchange.candidate_text,
                question_text: exchange.interviewer_text,
                dimension_scores: exchange.dimension_scores,
            });
            setFixItSuggestion(res.data?.hints?.[0]?.hint || "Try to be more specific and provide concrete examples.");
        } catch {
            const weakest = exchange.dimension_scores
                ? Object.entries(exchange.dimension_scores).sort((a, b) => a[1] - b[1])[0]
                : null;
            const dim = DIMENSIONS.find(d => d.key === weakest?.[0]);
            setFixItSuggestion(
                `Your weakest area in this exchange was ${dim?.label || 'Problem Solving'}. ` +
                `Try restructuring your answer to explicitly address ${dim?.label || 'the core concept'}. ` +
                `For example, start with your approach, then walk through the implementation, and finish with edge cases and trade-offs.`
            );
        }
        setFixItLoading(false);
    }
    const scoreTimeline = exchanges.map((ex, i) => ({
        exchange: `Q${i + 1}`,
        ...Object.fromEntries(DIMENSIONS.map(d => [d.label, ex.dimension_scores?.[d.key] || 0])),
        overall: ex.dimension_scores
            ? Object.values(ex.dimension_scores).reduce((a, b) => a + b, 0) / Object.keys(ex.dimension_scores).length
            : 0,
    }));
    const currentExchange = exchanges[activeExchange];
    const currentRadar = DIMENSIONS.map(d => ({
        dimension: d.label,
        score: currentExchange?.dimension_scores?.[d.key] || 0,
    }));
    function getScoreColor(score: number) {
        if (score >= 75) return 'text-emerald-400';
        if (score >= 50) return 'text-amber-400';
        return 'text-red-400';
    }
    if (loading) {
        return (
            <div className="min-h-screen bg-cyber-slate-950 flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-400 rounded-full animate-spin" />
            </div>
        );
    }
    return (
        <div className="min-h-screen bg-cyber-slate-950 text-white">
            {}
            <div className="border-b border-[#2A3045] bg-[#0D0E17]/80 backdrop-blur-xl sticky top-0 z-30">
                <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button onClick={() => router.back()} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
                            <ArrowLeft className="w-5 h-5 text-[#64748B]" />
                        </button>
                        <div>
                            <h1 className="text-lg font-bold flex items-center gap-2 text-white">
                                <Shield className="w-5 h-5 text-purple-400" />
                                Flight Data Recorder
                            </h1>
                            <p className="text-xs text-[#64748B]">
                                {session?.session_type?.replace('_', ' ')} • {session?.persona_type?.replace('_', ' ')} • Score: {session?.overall_score?.toFixed(0) ?? '—'}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-[#64748B]">
                        <Clock className="w-3.5 h-3.5" />
                        {session?.duration_seconds ? `${Math.floor(session.duration_seconds / 60)}m` : '—'}
                    </div>
                </div>
            </div>
            <div className="max-w-7xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
                {}
                <div className="lg:col-span-2 space-y-4">
                    {}
                    <GlassCard className="!p-3 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setActiveExchange(Math.max(0, activeExchange - 1))}
                                className="p-2 rounded-lg hover:bg-white/5 text-zinc-400 hover:text-white transition-colors"
                            >
                                <SkipBack className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => setIsPlaying(!isPlaying)}
                                className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 hover:bg-blue-500/20 transition-colors"
                            >
                                {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                            </button>
                            <button
                                onClick={() => setActiveExchange(Math.min(exchanges.length - 1, activeExchange + 1))}
                                className="p-2 rounded-lg hover:bg-white/5 text-zinc-400 hover:text-white transition-colors"
                            >
                                <SkipForward className="w-4 h-4" />
                            </button>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-sm text-[#64748B]">
                                Exchange {activeExchange + 1} of {exchanges.length}
                            </span>
                            <div className="flex gap-1">
                                {exchanges.map((ex, i) => {
                                    const avgScore = ex.dimension_scores
                                        ? Object.values(ex.dimension_scores).reduce((a, b) => a + b, 0) / Object.keys(ex.dimension_scores).length
                                        : 0;
                                    const segColor = avgScore >= 75 ? 'bg-emerald-400' : avgScore >= 50 ? 'bg-amber-400' : 'bg-red-400';
                                    const segGlow = avgScore >= 75 ? 'shadow-emerald-400/40' : avgScore >= 50 ? 'shadow-amber-400/40' : 'shadow-red-400/40';
                                    return (
                                        <button
                                            key={i}
                                            onClick={() => setActiveExchange(i)}
                                            title={`Q${i + 1}: ${avgScore.toFixed(0)}%`}
                                            className={`w-3 h-3 rounded-full transition-all ${segColor} ${i === activeExchange ? `scale-150 shadow-md ${segGlow}` : 'opacity-60 hover:opacity-100'
                                                }`}
                                        />
                                    );
                                })}
                            </div>
                        </div>
                    </GlassCard>
                    {}
                    <div className="space-y-3">
                        {exchanges.map((exchange, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{
                                    opacity: i <= activeExchange ? 1 : 0.3,
                                    y: 0,
                                    scale: i === activeExchange ? 1 : 0.98,
                                }}
                                transition={{ duration: 0.3 }}
                                className={`rounded-2xl border p-5 transition-all ${i === activeExchange
                                    ? 'border-blue-500/30 bg-zinc-900/80 shadow-lg shadow-blue-500/5'
                                    : 'border-white/5 bg-zinc-900/40'
                                    }`}
                                onClick={() => setActiveExchange(i)}
                            >
                                {}
                                <div className="flex items-center justify-between mb-3">
                                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${exchange.question_type === 'coding' ? 'bg-blue-500/10 text-blue-400' :
                                        exchange.question_type === 'system_design' ? 'bg-violet-500/10 text-violet-400' :
                                            'bg-emerald-500/10 text-emerald-400'
                                        }`}>
                                        {exchange.question_type}
                                    </span>
                                    <span className="text-[10px] text-zinc-600">Q{exchange.exchange_number}</span>
                                </div>
                                {}
                                <div className="mb-3">
                                    <div className="flex items-center gap-2 mb-1.5">
                                        <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center">
                                            <Brain className="w-3 h-3 text-blue-400" />
                                        </div>
                                        <span className="text-xs font-medium text-blue-400">Interviewer</span>
                                    </div>
                                    <p className="text-sm text-zinc-300 ml-8">{exchange.interviewer_text}</p>
                                </div>
                                {}
                                <div className="mb-3">
                                    <div className="flex items-center gap-2 mb-1.5">
                                        <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                                            <MessageSquare className="w-3 h-3 text-emerald-400" />
                                        </div>
                                        <span className="text-xs font-medium text-emerald-400">You</span>
                                    </div>
                                    <p className="text-sm text-zinc-300 ml-8">{exchange.candidate_text}</p>
                                </div>
                                {}
                                {exchange.dimension_scores && i === activeExchange && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: 'auto' }}
                                        className="mt-3 pt-3 border-t border-white/5"
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex flex-wrap gap-1.5">
                                                {DIMENSIONS.slice(0, 4).map(d => {
                                                    const score = exchange.dimension_scores?.[d.key] || 0;
                                                    return (
                                                        <span key={d.key} className={`text-[10px] px-1.5 py-0.5 rounded ${getScoreColor(score)} bg-white/5`}>
                                                            {d.label}: {score.toFixed(0)}
                                                        </span>
                                                    );
                                                })}
                                            </div>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleFixIt(i); }}
                                                className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1 transition-colors"
                                            >
                                                <Lightbulb className="w-3 h-3" /> Fix-It
                                            </button>
                                        </div>
                                        {}
                                        {exchange.coaching_hints_sent && exchange.coaching_hints_sent.length > 0 && (
                                            <div className="text-xs text-cyan-400/70 flex items-start gap-1.5 mt-1">
                                                <Zap className="w-3 h-3 mt-0.5 flex-shrink-0" />
                                                <span>{exchange.coaching_hints_sent[0].hint}</span>
                                            </div>
                                        )}
                                    </motion.div>
                                )}
                            </motion.div>
                        ))}
                    </div>
                </div>
                {}
                <div className="space-y-4">
                    {}
                    <GlassCard className="!p-0 overflow-hidden">
                        <div className="p-4 pb-0">
                            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                                <TrendingUp className="w-4 h-4 text-blue-400" />
                                Exchange {activeExchange + 1} Scores
                            </h3>
                        </div>
                        <div className="h-52 p-2">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart data={currentRadar}>
                                    <PolarGrid stroke="#27272a" />
                                    <PolarAngleAxis dataKey="dimension" tick={{ fill: '#71717a', fontSize: 9 }} />
                                    <Radar dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} strokeWidth={2} />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </GlassCard>
                    {}
                    <GlassCard className="!p-0 overflow-hidden">
                        <div className="p-4 pb-0 flex items-center justify-between">
                            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                                <Sparkles className="w-4 h-4 text-violet-400" />
                                Score Progression
                            </h3>
                            <div className="flex items-center gap-3 text-[10px]">
                                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400" /> ≥75</span>
                                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400" /> 50-74</span>
                                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400" /> &lt;50</span>
                            </div>
                        </div>
                        <div className="h-40 p-2">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={scoreTimeline}>
                                    <defs>
                                        <linearGradient id="replayGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1E2337" />
                                    <XAxis dataKey="exchange" tick={{ fill: '#64748B', fontSize: 10 }} />
                                    <YAxis domain={[0, 100]} tick={{ fill: '#64748B', fontSize: 10 }} />
                                    <Area type="monotone" dataKey="overall" stroke="#8b5cf6" fill="url(#replayGrad)" strokeWidth={2} dot={(props: any) => {
                                        const score = props.payload?.overall || 0;
                                        const fill = score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444';
                                        return <circle cx={props.cx} cy={props.cy} r={4} fill={fill} stroke="#151925" strokeWidth={2} />;
                                    }} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </GlassCard>
                    {}
                    <GlassCard>
                        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                            Session Summary
                        </h3>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-zinc-400">Overall Score</span>
                                <span className={`font-bold ${getScoreColor(session?.overall_score || 0)}`}>
                                    {session?.overall_score?.toFixed(0) ?? '—'}/100
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-zinc-400">Exchanges</span>
                                <span className="text-white">{exchanges.length}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-zinc-400">Duration</span>
                                <span className="text-white">{session?.duration_seconds ? `${Math.floor(session.duration_seconds / 60)}m` : '—'}</span>
                            </div>
                        </div>
                        <div className="mt-4">
                            <CyberButton
                                onClick={() => router.push(`/interview/report?session_id=${sessionId}`)}
                                className="w-full text-sm"
                            >
                                View Full Report <ChevronRight className="w-4 h-4" />
                            </CyberButton>
                        </div>
                    </GlassCard>
                </div>
            </div>
            {}
            <AnimatePresence>
                {showFixIt && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                        onClick={() => setShowFixIt(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="w-full max-w-lg glass-panel rounded-2xl p-6 border border-amber-500/20"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 rounded-xl bg-amber-500/10">
                                    <Lightbulb className="w-6 h-6 text-amber-400" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-white">Fix-It Coach</h3>
                                    <p className="text-xs text-zinc-400">AI coaching for Exchange {activeExchange + 1}</p>
                                </div>
                            </div>
                            {fixItLoading ? (
                                <div className="flex items-center justify-center py-8">
                                    <div className="w-6 h-6 border-2 border-amber-500/30 border-t-amber-400 rounded-full animate-spin" />
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    <div className="bg-zinc-800/50 rounded-xl p-4">
                                        <p className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">Your Answer</p>
                                        <p className="text-sm text-zinc-300">{currentExchange?.candidate_text}</p>
                                    </div>
                                    <div className="bg-amber-500/5 rounded-xl p-4 border border-amber-500/10">
                                        <p className="text-xs text-amber-400 mb-1 uppercase tracking-wider flex items-center gap-1">
                                            <Sparkles className="w-3 h-3" /> AI Suggestion
                                        </p>
                                        <p className="text-sm text-zinc-300">{fixItSuggestion}</p>
                                    </div>
                                    <button
                                        onClick={() => setShowFixIt(false)}
                                        className="w-full py-2.5 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-zinc-300 transition-colors"
                                    >
                                        Got it, thanks!
                                    </button>
                                </div>
                            )}
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
