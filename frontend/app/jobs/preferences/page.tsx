"use client"
import React from 'react'
import { Settings, Save, AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import CyberButton from '@/components/ui/CyberButton'
import Link from 'next/link'
export default function JobPreferences() {
    return (
        <div className="min-h-[calc(100vh-73px)] p-8 bg-[var(--bg-deep)] text-[var(--text-primary)] relative overflow-hidden">
            {}
            <div className="absolute top-0 right-0 w-96 h-96 bg-amber-500/10 rounded-full blur-[100px] pointer-events-none" />
            <div className="max-w-5xl mx-auto relative z-10">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
                            <Settings className="text-amber-400" size={32} /> Job Matching Preferences
                        </h1>
                        <p className="text-[var(--text-secondary)]">Configure the AI engine for scoring jobs and applying automatically.</p>
                    </div>
                    <Link href="/jobs">
                        <CyberButton variant="outline" className="flex items-center gap-2 border-[var(--card-border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
                            Back to Jobs <ArrowRight size={16} />
                        </CyberButton>
                    </Link>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {}
                    <div className="space-y-6">
                        <h2 className="text-xl font-semibold border-b border-white/10 pb-2">Target Criteria</h2>
                        <GlassCard className="p-5 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Target Roles</label>
                                <div className="flex flex-wrap gap-2 mb-2">
                                    <span className="px-3 py-1 rounded-full bg-cyber-purple-500/20 text-cyber-purple-300 text-sm border border-cyber-purple-500/30">AI Engineer</span>
                                    <span className="px-3 py-1 rounded-full bg-cyber-purple-500/20 text-cyber-purple-300 text-sm border border-cyber-purple-500/30">Machine Learning Engineer</span>
                                </div>
                                <input type="text" placeholder="Add role + Enter" className="w-full bg-[var(--bg-deep)] border border-[var(--card-border)] rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-cyber-purple-500" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Locations</label>
                                <div className="flex flex-wrap gap-2 mb-2">
                                    <span className="px-3 py-1 rounded-full bg-cyber-blue-500/20 text-cyber-blue-300 text-sm border border-cyber-blue-500/30">Chennai</span>
                                </div>
                                <input type="text" placeholder="Add location + Enter" className="w-full bg-[var(--bg-deep)] border border-[var(--card-border)] rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-cyber-purple-500" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Min Salary (LPA)</label>
                                    <input type="number" placeholder="15" className="w-full bg-[var(--bg-deep)] border border-[var(--card-border)] rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-cyber-purple-500" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Remote Rules</label>
                                    <select className="w-full bg-[var(--bg-deep)] border border-[var(--card-border)] rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-cyber-purple-500">
                                        <option>Any</option>
                                        <option>Only Remote</option>
                                        <option>Hybrid Ok</option>
                                    </select>
                                </div>
                            </div>
                        </GlassCard>
                    </div>
                    {}
                    <div className="space-y-6">
                        <h2 className="text-xl font-semibold border-b border-white/10 pb-2">Auto-Apply Engine</h2>
                        <GlassCard className="p-5 space-y-5 border-amber-500/20">
                            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 flex gap-3 text-sm">
                                <ShieldCheck className="text-amber-400 shrink-0" size={20} />
                                <p className="text-amber-200/80">Playwright will securely navigate application forms on your behalf using these settings.</p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Daily Apply Limit</label>
                                <select className="w-full bg-[var(--bg-deep)] border border-[var(--card-border)] rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-cyber-purple-500">
                                    <option>5 applications / day</option>
                                    <option selected>10 applications / day (Recommended)</option>
                                    <option>20 applications / day</option>
                                </select>
                            </div>
                            <label className="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-deep)] border border-[var(--card-border)] cursor-pointer hover:border-cyber-purple-500/50 transition-colors">
                                <input type="checkbox" defaultChecked className="w-5 h-5 rounded border-white/20 text-cyber-purple-500 focus:ring-cyber-purple-500/0 bg-white/5" />
                                <div>
                                    <p className="text-sm font-medium">Require manual review before applying</p>
                                    <p className="text-xs text-[var(--text-secondary)]">Shows the pre-apply modal for final confirmation</p>
                                </div>
                            </label>
                            <label className="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-deep)] border border-[var(--card-border)] cursor-pointer hover:border-cyber-purple-500/50 transition-colors">
                                <input type="checkbox" defaultChecked className="w-5 h-5 rounded border-white/20 text-cyber-purple-500 focus:ring-cyber-purple-500/0 bg-white/5" />
                                <div>
                                    <p className="text-sm font-medium">Skip previously applied jobs</p>
                                    <p className="text-xs text-[var(--text-secondary)]">Cross-references your tracker database</p>
                                </div>
                            </label>
                        </GlassCard>
                        <div className="flex justify-end pt-4">
                            <CyberButton variant="primary" className="px-8 flex items-center gap-2">
                                <Save size={18} /> Save Settings
                            </CyberButton>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
