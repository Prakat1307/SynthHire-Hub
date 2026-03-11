'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/stores/authStore';
import api from '@/src/lib/api';
import toast, { Toaster } from 'react-hot-toast';
import { Users, Code2, Brain, CheckCircle2, AlertTriangle, Play } from 'lucide-react';
import GlassCard from '@/components/ui/GlassCard';
import CyberButton from '@/components/ui/CyberButton';
const { apiClient, getServiceUrl } = api;
interface TemplateResponse {
    id: string;
    role: string;
    round_type: string;
    persona_type: string;
    is_public: boolean;
    duration_minutes: number;
}
export default function AcceptChallengePage() {
    const params = useParams();
    const router = useRouter();
    const { isAuthenticated, accessToken, isLoading: authLoading } = useAuthStore();
    const [template, setTemplate] = useState<TemplateResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isStarting, setIsStarting] = useState(false);
    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            toast.error('You must log in to accept challenges.');
            router.push('/login');
        } else if (isAuthenticated) {
            fetchTemplate();
        }
    }, [isAuthenticated, authLoading]);
    const fetchTemplate = async () => {
        try {
            const sessionUrl = getServiceUrl('session');
            const res = await apiClient.get(`${sessionUrl}/templates/${params.id}`);
            setTemplate(res.data);
            setIsLoading(false);
        } catch (e: any) {
            toast.error('Challenge not found or invalid link.');
            setTimeout(() => router.push('/dashboard'), 2000);
        }
    };
    const handleAcceptChallenge = async () => {
        setIsStarting(true);
        try {
            const sessionUrl = getServiceUrl('session');
            const response = await apiClient.post(
                `${sessionUrl}/sessions`,
                {
                    custom_company_name: 'Peer Challenge',
                    session_type: template?.round_type || 'mixed',
                    persona_type: template?.persona_type || 'tough_lead',
                    coaching_mode: 'simulation',
                    difficulty_level: 8,
                    target_role: template?.role || 'Software Engineer',
                    webcam_enabled: false,
                },
                { headers: { Authorization: `Bearer ${accessToken}` } }
            );
            const sessionId = response.data.id;
            toast.success('Challenge Accepted! Entering Arena...');
            router.push(`/interview/room/${sessionId}`);
        } catch (error: any) {
            toast.error('Failed to initialize challenge session.');
            setIsStarting(false);
        }
    };
    if (isLoading) {
        return <div className="min-h-screen bg-cyber-slate-950 flex items-center justify-center p-4">
            <div className="text-white text-xl animate-pulse">Loading peer challenge...</div>
        </div>;
    }
    if (!template) return null;
    return (
        <div className="min-h-screen bg-cyber-slate-950 text-white flex items-center justify-center p-4">
            <Toaster position="top-center" />
            <div className="max-w-lg w-full">
                <GlassCard className="p-8 text-center border-t-4 border-t-pink-500 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5">
                        <AlertTriangle className="w-32 h-32 text-pink-500" />
                    </div>
                    <div className="w-16 h-16 bg-pink-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-pink-500/20">
                        <Users className="w-8 h-8 text-pink-400" />
                    </div>
                    <h1 className="text-2xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400">
                        You've been challenged!
                    </h1>
                    <p className="text-slate-400 mb-8">A peer has invited you to complete a custom SynthHire simulation.</p>
                    <div className="bg-cyber-slate-900/50 rounded-xl p-4 text-left border border-white/5 mb-8 space-y-3 relative z-10">
                        <div className="flex justify-between items-center">
                            <span className="text-slate-400 text-sm">Target Role:</span>
                            <span className="font-bold text-white">{template.role}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-400 text-sm">Focus Area:</span>
                            <span className="text-cyber-teal-400 font-medium capitalize">{template.round_type.replace('_', ' ')}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-400 text-sm">Persona:</span>
                            <span className="text-pink-400 font-medium capitalize">{template.persona_type.replace('_', ' ')}</span>
                        </div>
                    </div>
                    <CyberButton
                        onClick={handleAcceptChallenge}
                        disabled={isStarting}
                        className="w-full py-4 text-lg bg-pink-600 border-none hover:bg-pink-500"
                    >
                        <Play className="w-5 h-5 mr-2" />
                        {isStarting ? 'Loading Simulation...' : 'Accept Challenge'}
                    </CyberButton>
                </GlassCard>
            </div>
        </div>
    );
}
