"use client";
import { useAuthStore } from '@/lib/stores/authStore';
import { useRouter, usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    Code2,
    History,
    Settings,
    LogOut,
    Menu,
    X,
    Sparkles,
    Award,
    BookOpen,
    Briefcase
} from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
const navItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Practice Arena', href: '/interview/setup', icon: Code2 },
    { name: 'Discover Jobs', href: '/jobs', icon: Briefcase },
    { name: 'Certifications', href: '/dashboard/certifications', icon: Award },
    { name: 'Learning', href: '/dashboard/learning', icon: BookOpen },
    { name: 'History', href: '/history', icon: History },
    { name: 'Settings', href: '/settings', icon: Settings },
];
const sidebarVariants = {
    hidden: { x: '-100%' },
    visible: { x: 0, transition: { type: 'spring', stiffness: 300, damping: 30 } },
    exit: { x: '-100%', transition: { duration: 0.2 } },
};
const navItemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: (i: number) => ({
        opacity: 1,
        x: 0,
        transition: { delay: i * 0.06, duration: 0.3 },
    }),
};
export default function AppShell({ children }: { children: React.ReactNode }) {
    const { user, logout } = useAuthStore();
    const router = useRouter();
    const pathname = usePathname();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const handleLogout = () => {
        logout();
        router.push('/login');
    };
    return (
        <div className="min-h-screen bg-cyber-slate-950 text-white flex">
            {}
            <AnimatePresence>
                {isSidebarOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm"
                        onClick={() => setIsSidebarOpen(false)}
                    />
                )}
            </AnimatePresence>
            {}
            <aside className={clsx(
                "fixed lg:static inset-y-0 left-0 z-50 w-72 bg-cyber-slate-900/80 backdrop-blur-xl border-r border-white/5 transform transition-transform duration-300 lg:translate-x-0 flex flex-col",
                isSidebarOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                {}
                <div className="p-6 flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-cyber-teal-500 to-cyber-purple-500 rounded-xl flex items-center justify-center shadow-lg shadow-cyber-teal-500/20">
                        <Sparkles className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xl font-bold text-gradient">
                        SynthHire
                    </span>
                    <button
                        className="ml-auto lg:hidden text-slate-400 hover:text-white transition-colors"
                        onClick={() => setIsSidebarOpen(false)}
                    >
                        <X size={24} />
                    </button>
                </div>
                {}
                <nav className="flex-1 px-4 py-6 space-y-2">
                    {navItems.map((item, i) => {
                        const Icon = item.icon;
                        const isActive = pathname === item.href;
                        return (
                            <motion.div
                                key={item.name}
                                custom={i}
                                initial="hidden"
                                animate="visible"
                                variants={navItemVariants}
                            >
                                <Link
                                    href={item.href}
                                    onClick={() => setIsSidebarOpen(false)}
                                    className={clsx(
                                        "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group",
                                        isActive
                                            ? "bg-cyber-teal-500/10 text-cyber-teal-400 border border-cyber-teal-500/20 shadow-lg shadow-cyber-teal-900/20"
                                            : "text-slate-400 hover:bg-white/5 hover:text-white"
                                    )}
                                >
                                    <Icon size={20} className={clsx(
                                        "transition-colors",
                                        isActive ? "text-cyber-teal-400" : "text-slate-500 group-hover:text-white"
                                    )} />
                                    <span className="font-medium">{item.name}</span>
                                    {isActive && (
                                        <div className="ml-auto w-1.5 h-1.5 rounded-full bg-cyber-teal-400 shadow-[0_0_8px_rgba(20,184,166,0.6)]" />
                                    )}
                                </Link>
                            </motion.div>
                        );
                    })}
                </nav>
                {}
                <div className="p-4 border-t border-white/5">
                    <div className="p-4 rounded-xl bg-cyber-slate-800/50 border border-white/5 mb-4">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-cyber-teal-500 to-cyber-purple-500 flex items-center justify-center text-sm font-bold shadow-lg shadow-cyber-teal-500/10">
                                {user?.full_name?.[0] || 'U'}
                            </div>
                            <div className="overflow-hidden">
                                <p className="text-sm font-medium truncate">{user?.full_name || 'User'}</p>
                                <p className="text-xs text-slate-400 truncate">{user?.email}</p>
                            </div>
                        </div>
                        <div className="w-full bg-cyber-slate-700 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-gradient-to-r from-cyber-teal-500 to-cyber-purple-500 w-3/4 h-full rounded-full" />
                        </div>
                        <p className="text-xs text-slate-400 mt-2 flex justify-between">
                            <span>Weekly Goal</span>
                            <span className="text-white font-medium">75%</span>
                        </p>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-slate-400 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/20 border border-transparent transition-all"
                    >
                        <LogOut size={20} />
                        <span className="font-medium">Sign Out</span>
                    </button>
                </div>
            </aside>
            {}
            <main className="flex-1 flex flex-col min-w-0 bg-cyber-slate-950 relative">
                {}
                <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-cyber-teal-900/10 to-transparent pointer-events-none" />
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-cyber-purple-500/5 rounded-full blur-[100px] pointer-events-none" />
                <header className="h-16 lg:hidden flex items-center px-4 border-b border-white/5 bg-cyber-slate-900/50 backdrop-blur-md sticky top-0 z-30">
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        className="text-slate-400 hover:text-white transition-colors"
                    >
                        <Menu size={24} />
                    </button>
                    <span className="ml-4 font-bold text-lg text-gradient">SynthHire</span>
                </header>
                <div className="flex-1 overflow-y-auto p-4 lg:p-8 relative z-10">
                    {children}
                </div>
            </main>
        </div>
    );
}
