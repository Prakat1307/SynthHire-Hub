'use client';
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/authStore';
import { useTheme } from '@/components/providers/ThemeProvider';
import {
    User, Link as LinkIcon, Cpu, Palette, CreditCard, LogOut,
    Github, Linkedin, Twitter, Mail, Code2, ShieldAlert, Download,
    Trash2, Monitor, Moon, Sun, Bell, CheckCircle2, Settings, Volume2
} from 'lucide-react';
import GlassCard from '@/components/ui/GlassCard';
import CyberButton from '@/components/ui/CyberButton';
import toast, { Toaster } from 'react-hot-toast';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
type TabId = 'profile' | 'integrations' | 'ai' | 'appearance' | 'billing';
const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
    { id: 'profile', label: 'User Profile', icon: User },
    { id: 'integrations', label: 'Integrations', icon: LinkIcon },
    { id: 'ai', label: 'AI Preferences', icon: Cpu },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'billing', label: 'Billing & Usage', icon: CreditCard },
];
const MOCK_AVATARS = [
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Aneka",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Jasper",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Mia",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Leah",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Caleb",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Avery",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Jude"
];
export default function SettingsPage() {
    const authState = useAuthStore() as any;
    const { user, logout, updateAvatar } = authState;
    const router = useRouter();
    const { theme, toggleTheme } = useTheme();
    const [activeTab, setActiveTab] = useState<TabId>('profile');
    const [coachVerbosity, setCoachVerbosity] = useState('detailed');
    const [codingLang, setCodingLang] = useState('Python');
    const [notifications, setNotifications] = useState(true);
    const [selectedAvatar, setSelectedAvatar] = useState<string>('');
    useEffect(() => {
        const savedAvatar = localStorage.getItem('synthhire_avatar');
        if (savedAvatar) {
            setSelectedAvatar(savedAvatar);
        } else if (!selectedAvatar && user?.full_name) {
            setSelectedAvatar(user.full_name.charAt(0));
        }
    }, [user, selectedAvatar]);
    const handleSelectAvatar = (avatar: string) => {
        setSelectedAvatar(avatar);
        if (updateAvatar) updateAvatar(avatar);
        else localStorage.setItem('synthhire_avatar', avatar);
    };
    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onloadend = () => {
            const base64String = reader.result as string;
            handleSelectAvatar(base64String);
            toast.success('Avatar updated successfully!');
        };
        reader.readAsDataURL(file);
    };
    const handleLogout = async () => {
        await logout();
        router.push('/login');
        toast.success('Logged out successfully');
    };
    const handleSave = () => {
        toast.success('Settings synchronized successfully!');
    };
    const handleMockAction = (actionName: string) => {
        toast(`${actionName} integration workflow is currently in development.`, { icon: '🚧', id: 'mock-action' });
    };
    const handleMockExport = () => {
        toast.loading('Simulating data compilation...', { duration: 3000, id: 'mock-export' });
        setTimeout(() => toast.success('Simulation Complete: In production, an archive link is emailed.', { id: 'mock-export', duration: 5000 }), 3100);
    };
    const handleMockUpgrade = () => {
        toast('Redirecting to secure Stripe Checkout...', { icon: '💳', id: 'mock-upgrade' });
    };
    const renderProfileTab = () => (
        <div className="space-y-6">
            <GlassCard className="space-y-6">
                <div className="flex items-center gap-4 border-b border-[var(--card-border)] pb-6">
                    <div className="p-3 rounded-xl bg-cyber-teal-500/10 text-cyber-teal-400">
                        <User className="w-6 h-6" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-[var(--text-primary)]">Profile Information</h2>
                        <p className="text-sm text-[var(--text-secondary)]">Update your personal identity details.</p>
                    </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-[var(--text-secondary)]">Full Name</label>
                        <input type="text" defaultValue={user?.full_name} className="w-full px-4 py-2 bg-[var(--bg-deep)] border border-[var(--card-border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-cyber-purple-500 transition-colors" />
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-[var(--text-secondary)]">Email Address</label>
                        <input type="email" defaultValue={user?.email} disabled className="w-full px-4 py-2 bg-[var(--bg-deep)] border border-[var(--card-border)] rounded-lg text-[var(--text-secondary)] opacity-50 cursor-not-allowed" />
                    </div>
                    <div className="space-y-4 md:col-span-2">
                        <label className="text-sm font-medium text-[var(--text-secondary)]">Avatar</label>
                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 rounded-full bg-cyber-purple-500/20 border border-cyber-purple-500/30 flex items-center justify-center text-cyber-purple-400 font-bold text-xl uppercase overflow-hidden">
                                {selectedAvatar.startsWith('http') || selectedAvatar.startsWith('data:image') ? (
                                    <img src={selectedAvatar} alt="Avatar" className="w-full h-full object-cover" />
                                ) : (
                                    selectedAvatar || 'U'
                                )}
                            </div>
                            <div className="relative">
                                <input
                                    type="file"
                                    accept="image/*"
                                    onChange={handleFileUpload}
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                />
                                <CyberButton variant="outline" className="text-xs">Upload New Photo</CyberButton>
                            </div>
                        </div>
                        <div className="mt-4 p-4 rounded-xl bg-[var(--card-bg)] border border-[var(--card-border)]">
                            <p className="text-xs font-medium text-[var(--text-secondary)] mb-3 uppercase tracking-wider">Or Choose an AI Avatar</p>
                            <div className="flex flex-wrap gap-3">
                                {MOCK_AVATARS.map((avatar, i) => (
                                    <button
                                        key={i}
                                        onClick={() => handleSelectAvatar(avatar)}
                                        className={`w-12 h-12 rounded-full overflow-hidden border-2 transition-all ${selectedAvatar === avatar ? 'border-cyber-purple-500 scale-110 shadow-[0_0_15px_rgba(139,92,246,0.5)]' : 'border-transparent hover:border-cyber-purple-500/50 hover:scale-105'}`}
                                    >
                                        <img src={avatar} alt={`Avatar ${i}`} className="w-full h-full object-cover bg-white/5" />
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </GlassCard>
            <GlassCard className="space-y-6 border-red-500/20 bg-red-500/5">
                <div className="flex items-center gap-3 border-b border-red-500/20 pb-4">
                    <ShieldAlert className="w-5 h-5 text-red-500" />
                    <h2 className="text-lg font-bold text-red-400">Danger Zone</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <button onClick={handleMockExport} className="w-full flex items-center justify-center gap-2 p-3 rounded-lg bg-[var(--card-bg)] hover:bg-[var(--bg-deep)] transition-colors border border-[var(--card-border)] text-[var(--text-primary)] text-sm font-medium">
                        <Download className="w-4 h-4" /> Export Platform Data
                    </button>
                    <button onClick={() => toast.error('Account deletion is locked for Beta testers. Contact support.')} className="w-full flex items-center justify-center gap-2 p-3 rounded-lg border border-red-500/30 hover:bg-red-500/10 transition-colors text-red-500 text-sm font-medium">
                        <Trash2 className="w-4 h-4" /> Delete Account
                    </button>
                </div>
            </GlassCard>
        </div>
    );
    const renderIntegrationsTab = () => (
        <GlassCard className="space-y-6">
            <div className="flex items-center gap-4 border-b border-[var(--card-border)] pb-6">
                <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400">
                    <LinkIcon className="w-6 h-6" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-[var(--text-primary)]">Connected Accounts</h2>
                    <p className="text-sm text-[var(--text-secondary)]">Link platforms to automate fetching context and sync data.</p>
                </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {}
                <div className="flex flex-col justify-between p-5 rounded-xl bg-[var(--bg-deep)] border border-cyber-purple-500/30 shadow-[0_0_15px_rgba(139,92,246,0.1)] transition-all">
                    <div className="flex items-start justify-between mb-4">
                        <div className="p-2.5 bg-[#181717] rounded-lg text-white">
                            <Github className="w-6 h-6" />
                        </div>
                        <span className="px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-md text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Connected
                        </span>
                    </div>
                    <div>
                        <h3 className="font-bold text-[var(--text-primary)] mb-1">GitHub</h3>
                        <p className="text-xs text-[var(--text-secondary)] mb-4 leading-relaxed">Sync repositories and commits for interview code context.</p>
                        <div className="flex items-center justify-between mt-auto">
                            <p className="text-xs font-medium text-cyber-purple-400">@Prakat1307</p>
                            <a href="https://github.com/Prakat1307" className="px-3 py-1.5 bg-white/5 hover:bg-emerald-500/10 border border-white/10 hover:border-emerald-500/30 text-xs font-bold rounded-md transition-colors text-[var(--text-primary)] hover:text-emerald-400">
                                View Profile
                            </a>
                        </div>
                    </div>
                </div>
                {}
                <div className="flex flex-col justify-between p-5 rounded-xl bg-[var(--card-bg)] border border-[var(--card-border)] hover:border-[#0A66C2]/50 transition-all">
                    <div className="flex items-start justify-between mb-4">
                        <div className="p-2.5 bg-[#0A66C2] rounded-lg text-white">
                            <Linkedin className="w-6 h-6" />
                        </div>
                    </div>
                    <div>
                        <h3 className="font-bold text-[var(--text-primary)] mb-1">LinkedIn</h3>
                        <p className="text-xs text-[var(--text-secondary)] mb-4 leading-relaxed">Fetch employment history directly without manual entry.</p>
                        <a href="https://linkedin.com/" className="w-full text-center py-2 bg-[#0A66C2]/10 hover:bg-[#0A66C2]/20 border border-[#0A66C2]/20 hover:border-[#0A66C2]/40 text-sm font-medium rounded-lg transition-colors text-[#0A66C2]">
                            Visit LinkedIn Profile
                        </a>
                    </div>
                </div>
                {}
                <div className="flex flex-col justify-between p-5 rounded-xl bg-[var(--card-bg)] border border-[var(--card-border)] hover:border-[#EA4335]/50 transition-all">
                    <div className="flex items-start justify-between mb-4">
                        <div className="p-2.5 bg-white rounded-lg text-black">
                            <Mail className="w-6 h-6 text-[#EA4335]" />
                        </div>
                    </div>
                    <div>
                        <h3 className="font-bold text-[var(--text-primary)] mb-1">Google Workspace</h3>
                        <p className="text-xs text-[var(--text-secondary)] mb-4 leading-relaxed">Sync upcoming interviews with your Google Calendar.</p>
                        <button onClick={() => handleMockAction('Google OAuth Provider')} className="w-full py-2 bg-white/5 hover:bg-[#EA4335]/10 border border-white/10 hover:border-[#EA4335]/30 text-sm font-medium rounded-lg transition-colors text-[var(--text-primary)] hover:text-[#EA4335]">
                            Connect Account
                        </button>
                    </div>
                </div>
                {}
                <div className="flex flex-col justify-between p-5 rounded-xl bg-[var(--card-bg)] border border-[var(--card-border)] hover:border-[#1DA1F2]/50 transition-all">
                    <div className="flex items-start justify-between mb-4">
                        <div className="p-2.5 bg-[#1DA1F2] rounded-lg text-white">
                            <Twitter className="w-6 h-6" />
                        </div>
                    </div>
                    <div>
                        <h3 className="font-bold text-[var(--text-primary)] mb-1">X (Twitter)</h3>
                        <p className="text-xs text-[var(--text-secondary)] mb-4 leading-relaxed">Include your public threads in AI background parsing.</p>
                        <a href="https://x.com/" className="w-full text-center py-2 bg-[#1DA1F2]/10 hover:bg-[#1DA1F2]/20 border border-[#1DA1F2]/20 hover:border-[#1DA1F2]/40 text-sm font-medium rounded-lg transition-colors text-[#1DA1F2]">
                            Visit X Profile
                        </a>
                    </div>
                </div>
                {}
                <div className="flex flex-col justify-between p-5 rounded-xl bg-[var(--card-bg)] border border-[var(--card-border)] hover:border-[#FFA116]/50 transition-all md:col-span-2">
                    <div className="flex items-center gap-4">
                        <div className="p-2.5 bg-[#FFA116] rounded-lg text-black shrink-0">
                            <Code2 className="w-6 h-6" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-bold text-[var(--text-primary)] mb-1">LeetCode / Programming Profiles</h3>
                            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">Link your competitive programming profiles to calibrate AI difficulty baseline.</p>
                        </div>
                        <a href="https://leetcode.com/" className="px-4 py-2 shrink-0 bg-[#FFA116]/10 hover:bg-[#FFA116]/20 border border-[#FFA116]/20 hover:border-[#FFA116]/40 text-sm font-bold rounded-lg transition-colors text-[#FFA116]">
                            View LeetCode
                        </a>
                    </div>
                </div>
            </div>
        </GlassCard>
    );
    const renderAITab = () => (
        <GlassCard className="space-y-6">
            <div className="flex items-center gap-4 border-b border-[var(--card-border)] pb-6">
                <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400">
                    <Cpu className="w-6 h-6" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-[var(--text-primary)]">AI Model Behavior</h2>
                    <p className="text-sm text-[var(--text-secondary)]">Tune how the underlying Gemini pipelines process your sessions.</p>
                </div>
            </div>
            <div className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-[var(--bg-deep)] border border-[var(--card-border)] gap-4">
                    <div>
                        <p className="font-medium text-[var(--text-primary)]">Coach Verbosity</p>
                        <p className="text-xs text-[var(--text-secondary)] mt-1">Determine how lengthy and detailed the AI feedback should be.</p>
                    </div>
                    <select
                        className="bg-[var(--card-bg)] border border-[var(--card-border)] text-[var(--text-primary)] text-sm rounded-lg px-4 py-2 focus:border-cyber-purple-500 outline-none w-full sm:w-48"
                        value={coachVerbosity}
                        onChange={(e) => setCoachVerbosity(e.target.value)}
                    >
                        <option value="brief">Brief & Direct</option>
                        <option value="detailed">Detailed & Explanatory</option>
                        <option value="pedantic">Pedantic (Expert Mode)</option>
                    </select>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-[var(--bg-deep)] border border-[var(--card-border)] gap-4">
                    <div>
                        <p className="font-medium text-[var(--text-primary)]">Primary Coding Language</p>
                        <p className="text-xs text-[var(--text-secondary)] mt-1">Default language for syntax highlighting and AI code generation.</p>
                    </div>
                    <select
                        className="bg-[var(--card-bg)] border border-[var(--card-border)] text-[var(--text-primary)] text-sm rounded-lg px-4 py-2 focus:border-cyber-purple-500 outline-none w-full sm:w-48"
                        value={codingLang}
                        onChange={(e) => setCodingLang(e.target.value)}
                    >
                        <option value="Python">Python</option>
                        <option value="JavaScript">JavaScript / TypeScript</option>
                        <option value="Java">Java</option>
                        <option value="Cpp">C++</option>
                        <option value="Go">Go</option>
                    </select>
                </div>
                <div className="p-4 rounded-xl bg-cyber-purple-500/10 border border-cyber-purple-500/20 flex gap-3">
                    <Settings className="w-5 h-5 text-cyber-purple-400 shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-bold text-cyber-purple-300">Model Architecture</h4>
                        <p className="text-xs text-cyber-purple-200/70 mt-1">
                            Your account is currently locked to <strong>Gemini 2.5 Flash Lite</strong>. Upgrading to a Pro license unlocks Gemini 2.5 Pro for enhanced reasoning capabilities.
                        </p>
                    </div>
                </div>
            </div>
        </GlassCard>
    );
    const renderAppearanceTab = () => (
        <GlassCard className="space-y-6">
            <div className="flex items-center gap-4 border-b border-[var(--card-border)] pb-6">
                <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400">
                    <Palette className="w-6 h-6" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-[var(--text-primary)]">Appearance & Alerts</h2>
                    <p className="text-sm text-[var(--text-secondary)]">Customize the look and feel of SynthHire.</p>
                </div>
            </div>
            <div className="space-y-6">
                <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-muted)] mb-3">Color Theme</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <button onClick={toggleTheme} className={`flex items-center justify-center gap-2 p-3 rounded-xl border ${theme === 'dark' ? 'bg-cyber-purple-500/20 border-cyber-purple-500 text-cyber-purple-400' : 'bg-[var(--bg-deep)] border-[var(--card-border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'} transition-all`}>
                            <Moon className="w-4 h-4" /> Dark Mode
                        </button>
                        <button onClick={toggleTheme} className={`flex items-center justify-center gap-2 p-3 rounded-xl border ${theme === 'light' ? 'bg-cyber-purple-500/20 border-cyber-purple-500 text-cyber-purple-400' : 'bg-[var(--bg-deep)] border-[var(--card-border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'} transition-all`}>
                            <Sun className="w-4 h-4" /> Light Mode
                        </button>
                        <button className="flex items-center justify-center gap-2 p-3 rounded-xl border bg-[var(--bg-deep)] border-[var(--card-border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all">
                            <Monitor className="w-4 h-4" /> System Default
                        </button>
                    </div>
                </div>
                <div>
                    <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-muted)] mb-3">Notifications</h3>
                    <div className="space-y-3">
                        <label className="flex items-center justify-between p-4 rounded-xl bg-[var(--bg-deep)] border border-[var(--card-border)] cursor-pointer hover:border-cyber-purple-500/40 transition-colors">
                            <div className="flex items-center gap-3">
                                <Bell className="w-5 h-5 text-[var(--text-muted)]" />
                                <div>
                                    <p className="font-medium text-[var(--text-primary)]">Job Match Alerts</p>
                                    <p className="text-xs text-[var(--text-secondary)]">Receive emails when new jobs match your AI profile.</p>
                                </div>
                            </div>
                            <input type="checkbox" checked={notifications} onChange={() => setNotifications(!notifications)} className="w-4 h-4 rounded border-gray-300 text-cyber-purple-500 focus:ring-cyber-purple-500 bg-transparent" />
                        </label>
                        <label className="flex items-center justify-between p-4 rounded-xl bg-[var(--bg-deep)] border border-[var(--card-border)] cursor-pointer hover:border-cyber-purple-500/40 transition-colors">
                            <div className="flex items-center gap-3">
                                <Volume2 className="w-5 h-5 text-[var(--text-muted)]" />
                                <div>
                                    <p className="font-medium text-[var(--text-primary)]">Platform Sounds</p>
                                    <p className="text-xs text-[var(--text-secondary)]">Play chimes when the AI finishes downloading data.</p>
                                </div>
                            </div>
                            <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-gray-300 text-cyber-purple-500 focus:ring-cyber-purple-500 bg-transparent" />
                        </label>
                    </div>
                </div>
            </div>
        </GlassCard>
    );
    const renderBillingTab = () => (
        <GlassCard className="space-y-6">
            <div className="flex items-center gap-4 border-b border-[var(--card-border)] pb-6">
                <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
                    <CreditCard className="w-6 h-6" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-[var(--text-primary)]">Billing & Quotas</h2>
                    <p className="text-sm text-[var(--text-secondary)]">Manage your subscription tier and API limits.</p>
                </div>
            </div>
            <div className="p-6 rounded-xl bg-gradient-to-br from-cyber-purple-500/10 to-transparent border border-cyber-purple-500/20 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-cyber-purple-500/20 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />
                <h3 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2 mb-1">
                    Free Tier <span className="px-2 py-0.5 rounded text-[10px] uppercase font-black tracking-widest bg-cyber-purple-500/20 text-cyber-purple-400 border border-cyber-purple-500/30">Active</span>
                </h3>
                <p className="text-sm text-[var(--text-secondary)] mb-6">You are currently operating on the community license.</p>
                <div className="space-y-2 mb-6">
                    <div className="flex justify-between text-xs font-medium">
                        <span className="text-[var(--text-secondary)]">Interview Simulation Minutes</span>
                        <span className="text-[var(--text-primary)]">42 / 120 mins</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-[var(--bg-deep)] overflow-hidden">
                        <div className="h-full bg-cyber-purple-500 rounded-full" style={{ width: '35%' }} />
                    </div>
                </div>
                <CyberButton onClick={handleMockUpgrade} variant="primary" className="w-full shadow-lg shadow-cyber-purple-500/20">
                    Upgrade to Pro — $15/mo
                </CyberButton>
            </div>
        </GlassCard>
    );
    return (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-[calc(100vh-64px)] flex flex-col">
            <Toaster position="top-right" toastOptions={{
                style: { background: 'var(--card-bg)', color: 'var(--text-primary)', border: '1px solid var(--card-border)' }
            }} />
            <div className="flex items-center justify-between mb-8 shrink-0">
                <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
                    <h1 className="text-3xl font-bold text-gradient flex items-center gap-3">
                        <Settings className="w-8 h-8 text-cyber-purple-500" /> System Config
                    </h1>
                    <p className="text-[var(--text-secondary)] mt-1">Manage your centralized platform infrastructure.</p>
                </motion.div>
                <div className="flex gap-3">
                    <CyberButton variant="ghost" onClick={handleLogout} className="border border-red-500/30 text-red-400 hover:bg-red-500/10">
                        <LogOut className="w-4 h-4 mr-2" /> Sign Out
                    </CyberButton>
                    <CyberButton onClick={handleSave}>
                        Save All Changes
                    </CyberButton>
                </div>
            </div>
            <div className="flex-1 flex flex-col lg:flex-row gap-8 overflow-hidden">
                {}
                <motion.aside
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="w-full lg:w-64 shrink-0 flex flex-col gap-2 overflow-y-auto custom-scrollbar"
                >
                    {TABS.map((tab) => {
                        const isActive = activeTab === tab.id;
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full flex items-center gap-3 p-3.5 rounded-xl text-sm font-bold transition-all ${isActive
                                    ? 'bg-cyber-purple-500 text-white shadow-lg shadow-cyber-purple-500/20 border-transparent'
                                    : 'bg-[var(--card-bg)] text-[var(--text-secondary)] hover:bg-[var(--bg-surface)] border border-[var(--card-border)] hover:border-cyber-purple-500/30 hover:text-[var(--text-primary)]'
                                    }`}
                            >
                                <Icon className={`w-5 h-5 ${isActive ? 'text-white' : ''}`} />
                                {tab.label}
                            </button>
                        );
                    })}
                </motion.aside>
                {}
                <div className="flex-1 overflow-y-auto custom-scrollbar pb-10">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={activeTab}
                            initial={{ opacity: 0, y: 10, scale: 0.98 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -10, scale: 0.98 }}
                            transition={{ duration: 0.2 }}
                            className="max-w-3xl"
                        >
                            {activeTab === 'profile' && renderProfileTab()}
                            {activeTab === 'integrations' && renderIntegrationsTab()}
                            {activeTab === 'ai' && renderAITab()}
                            {activeTab === 'appearance' && renderAppearanceTab()}
                            {activeTab === 'billing' && renderBillingTab()}
                        </motion.div>
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}
