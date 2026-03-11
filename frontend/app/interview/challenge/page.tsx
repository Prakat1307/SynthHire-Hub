'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/stores/authStore';
import api from '@/src/lib/api';
import toast, { Toaster } from 'react-hot-toast';
import { ArrowLeft, Link as LinkIcon, Share2, Target, Users, Settings2, ShieldAlert } from 'lucide-react';
import GlassCard from '@/components/ui/GlassCard';
import CyberButton from '@/components/ui/CyberButton';
import { motion, AnimatePresence } from 'framer-motion';
const { apiClient, getServiceUrl } = api;
export default function CreateChallengePage() {
    const router = useRouter();
    const { accessToken } = useAuthStore();
    const [role, setRole] = useState('Senior Software Engineer');
    const [roundType, setRoundType] = useState('coding');
    const [personaType, setPersonaType] = useState('tough_lead');
    const [systemPrompt, setSystemPrompt] = useState('You are interviewing a candidate for a Senior Software Engineer role. Focus heavily on system design and scalable architecture. Ask tricky edge case questions.');
    const [durationText, setDurationText] = useState('45');
    const [isCreating, setIsCreating] = useState(false);
    const [shareUrl, setShareUrl] = useState<string | null>(null);
    const handleCreateTemplate = async () => {
        setIsCreating(true);
        try {
            const sessionUrl = getServiceUrl('session');
            const response = await apiClient.post(
                `${sessionUrl}/templates`,
                {
                    role,
                    round_type: roundType,
                    persona_type: personaType,
                    system_prompt: systemPrompt,
                    difficulty_range: { min: 7, max: 10 },
                    duration_minutes: parseInt(durationText) || 45,
                    is_public: true
                },
                { headers: { Authorization: `Bearer ${accessToken}` } }
            );
            const templateId = response.data.id;
            const baseUrl = window.location.origin;
            const generatedUrl = `${baseUrl}/interview/challenge/${templateId}`;
            setShareUrl(generatedUrl);
            toast.success('Challenge created! Link ready to share.');
        } catch (error: any) {
            console.error(error);
            toast.error('Failed to create custom challenge.');
        } finally {
            setIsCreating(false);
        }
    };
    const copyToClipboard = () => {
        if (shareUrl) {
            navigator.clipboard.writeText(shareUrl);
            toast.success('Link copied to clipboard!');
        }
    };
    return (
        <div className="min-h-screen bg-cyber-slate-950 text-white relative overflow-hidden py-10 px-4 sm:px-6 lg:px-8">
            <Toaster position="top-right" />
            <div className="max-w-3xl mx-auto space-y-8">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="p-2 bg-cyber-slate-800/50 hover:bg-cyber-slate-700 text-slate-300 rounded-full transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-3">
                            <Share2 className="w-8 h-8 text-pink-500" />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-cyber-purple-400">
                                Create Custom Challenge
                            </span>
                        </h1>
                        <p className="text-slate-400 mt-1">Design a specific scenario, choose an aggressive persona, and challenge your peers.</p>
                    </div>
                </div>
                <AnimatePresence mode="wait">
                    {!shareUrl ? (
                        <motion.div
                            key="form"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                        >
                            <GlassCard className="p-6 md:p-8 space-y-6">
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                                            <Target className="w-4 h-4 text-cyber-teal-400" />
                                            Target Role & Title
                                        </label>
                                        <input
                                            type="text"
                                            value={role}
                                            onChange={(e) => setRole(e.target.value)}
                                            className="w-full bg-cyber-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-pink-500 transition-colors"
                                        />
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                                                <Settings2 className="w-4 h-4 text-cyber-purple-400" />
                                                Round Type
                                            </label>
                                            <select
                                                value={roundType}
                                                onChange={(e) => setRoundType(e.target.value)}
                                                className="w-full bg-cyber-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-pink-500 transition-colors appearance-none"
                                            >
                                                <option value="coding">Coding (Data Structures)</option>
                                                <option value="system_design">System Design</option>
                                                <option value="behavioral">Behavioral (Leadership)</option>
                                                <option value="mixed">Mixed (Full Loop)</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                                                <Users className="w-4 h-4 text-emerald-400" />
                                                Interviewer Persona
                                            </label>
                                            <select
                                                value={personaType}
                                                onChange={(e) => setPersonaType(e.target.value)}
                                                className="w-full bg-cyber-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-pink-500 transition-colors appearance-none"
                                            >
                                                <option value="tough_lead">Tough Tech Lead 🧐</option>
                                                <option value="tricky_hr">Tricky HR Recruiter 🎭</option>
                                                <option value="kind_mentor">Kind Mentor 😊</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                                            <ShieldAlert className="w-4 h-4 text-amber-500" />
                                            Custom System Prompt (Define the exact rules)
                                        </label>
                                        <textarea
                                            value={systemPrompt}
                                            onChange={(e) => setSystemPrompt(e.target.value)}
                                            rows={4}
                                            className="w-full bg-cyber-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-pink-500 transition-colors"
                                        />
                                        <p className="text-xs text-slate-500 mt-2">The AI interviewer will strictly abide by these rules. Use this to construct impossible scenarios!</p>
                                    </div>
                                </div>
                                <CyberButton
                                    onClick={handleCreateTemplate}
                                    disabled={isCreating}
                                    className="w-full mt-8 py-4 bg-pink-600 hover:bg-pink-500 hover:shadow-[0_0_20px_rgba(236,72,153,0.5)] border border-pink-400 font-bold"
                                >
                                    {isCreating ? 'Generating Links...' : 'Generate Shareable Link'}
                                </CyberButton>
                            </GlassCard>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="success"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="text-center space-y-6"
                        >
                            <GlassCard className="p-8 border-pink-500/50 shadow-[0_0_30px_rgba(236,72,153,0.2)]">
                                <Share2 className="w-16 h-16 text-pink-500 mx-auto mb-6" />
                                <h2 className="text-2xl font-bold text-white mb-2">Challenge Live!</h2>
                                <p className="text-slate-400 mb-8">Send this uniquely generated link to challenge your friends, colleagues, or students.</p>
                                <div className="flex items-center gap-2 bg-cyber-slate-900/80 p-2 rounded-xl border border-slate-700">
                                    <div className="w-12 h-12 flex items-center justify-center bg-cyber-slate-800 rounded-lg">
                                        <LinkIcon className="w-6 h-6 text-pink-400" />
                                    </div>
                                    <input
                                        type="text"
                                        readOnly
                                        value={shareUrl}
                                        className="flex-grow bg-transparent text-slate-300 focus:outline-none px-2 text-sm sm:text-base"
                                    />
                                    <CyberButton
                                        onClick={copyToClipboard}
                                        className="px-6 py-3 whitespace-nowrap bg-pink-600 border-none hover:bg-pink-500"
                                    >
                                        Copy Link
                                    </CyberButton>
                                </div>
                            </GlassCard>
                            <button
                                onClick={() => router.push('/dashboard')}
                                className="text-slate-400 hover:text-white transition-colors underline underline-offset-4"
                            >
                                Return to Dashboard
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
