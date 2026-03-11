"use client"
import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Kanban, List as ListIcon, Search, ArrowRight, BarChart3, Clock, CheckCircle2, ChevronDown, Check, Briefcase, MapPin, DollarSign, Building, MoreVertical } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import CyberButton from '@/components/ui/CyberButton'
import Link from 'next/link'
type ApplicationStatus = 'applied' | 'screening' | 'interviewing' | 'offer' | 'rejected'
interface JobApplication {
    id: string;
    job_title: string;
    company: string;
    company_logo?: string;
    location: string;
    salary?: string;
    status: ApplicationStatus;
    applied_date: string;
    match_score: number;
}
const MOCK_APPLICATIONS: JobApplication[] = [];
export default function ApplicationTracker() {
    const [viewMode, setViewMode] = useState<'kanban' | 'table'>('kanban')
    const [applications, setApplications] = useState<JobApplication[]>(MOCK_APPLICATIONS)
    const columns: { id: ApplicationStatus, label: string, color: string }[] = [
        { id: 'applied', label: 'Applied', color: 'border-cyber-blue-500/30 text-cyber-blue-400' },
        { id: 'screening', label: 'Screening', color: 'border-amber-500/30 text-amber-400' },
        { id: 'interviewing', label: 'Interviewing', color: 'border-cyber-purple-500/30 text-cyber-purple-400' },
        { id: 'offer', label: 'Offer', color: 'border-emerald-500/30 text-emerald-400' },
        { id: 'rejected', label: 'Rejected', color: 'border-rose-500/30 text-rose-400' }
    ]
    const handleDragStart = (e: React.DragEvent, appId: string) => {
        e.dataTransfer.setData('jobId', appId)
    }
    const handleDrop = (e: React.DragEvent, targetStatus: ApplicationStatus) => {
        const appId = e.dataTransfer.getData('jobId')
        if (appId) {
            setApplications(prev => prev.map(app =>
                app.id === appId ? { ...app, status: targetStatus } : app
            ))
        }
    }
    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault() 
    }
    return (
        <div className="min-h-[calc(100vh-73px)] p-8 bg-[var(--bg-deep)] text-[var(--text-primary)] relative overflow-hidden">
            {}
            <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyber-purple-500/10 rounded-full blur-[100px] pointer-events-none" />
            <div className="max-w-7xl mx-auto relative z-10 space-y-8">
                {}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
                            <Kanban className="text-cyber-purple-400" size={32} /> Application Tracker
                        </h1>
                        <p className="text-[var(--text-secondary)]">Manage and track your active job applications across platforms.</p>
                    </div>
                    <div className="flex gap-4 items-center">
                        <div className="flex bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg p-1">
                            <button
                                onClick={() => setViewMode('kanban')}
                                className={`px-4 py-1.5 rounded flex items-center gap-2 text-sm font-medium transition-colors ${viewMode === 'kanban' ? 'bg-cyber-purple-500 text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
                            >
                                <Kanban size={16} /> Board
                            </button>
                            <button
                                onClick={() => setViewMode('table')}
                                className={`px-4 py-1.5 rounded flex items-center gap-2 text-sm font-medium transition-colors ${viewMode === 'table' ? 'bg-cyber-purple-500 text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
                            >
                                <ListIcon size={16} /> Table
                            </button>
                        </div>
                        <Link href="/jobs">
                            <CyberButton variant="outline" className="flex items-center gap-2 border-[var(--card-border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
                                <Search size={16} /> Find Jobs
                            </CyberButton>
                        </Link>
                    </div>
                </div>
                {}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {[
                        { title: 'Total Applied', value: applications.length, icon: Briefcase, color: 'text-cyber-blue-400' },
                        { title: 'Screening', value: applications.filter(a => a.status === 'screening').length, icon: BarChart3, color: 'text-cyber-purple-400' },
                        { title: 'Interviews', value: applications.filter(a => a.status === 'interviewing').length, icon: Clock, color: 'text-amber-400' },
                        { title: 'Offers', value: applications.filter(a => a.status === 'offer').length, icon: CheckCircle2, color: 'text-emerald-400' },
                    ].map((stat, i) => (
                        <GlassCard key={i} className="p-5 flex items-center justify-between">
                            <div>
                                <p className="text-sm text-[var(--text-secondary)] mb-1">{stat.title}</p>
                                <p className="text-3xl font-bold">{stat.value}</p>
                            </div>
                            <div className={`p-3 rounded-xl bg-white/5 ${stat.color} border border-white/5`}>
                                <stat.icon size={24} />
                            </div>
                        </GlassCard>
                    ))}
                </div>
                {}
                {viewMode === 'kanban' ? (
                    <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar min-h-[500px]">
                        {columns.map(col => {
                            const colApps = applications.filter(app => app.status === col.id)
                            return (
                                <div
                                    key={col.id}
                                    className="flex-none w-[320px] flex flex-col gap-3"
                                    onDrop={(e) => handleDrop(e, col.id)}
                                    onDragOver={handleDragOver}
                                >
                                    <div className={`flex items-center justify-between p-3 rounded-lg bg-[var(--card-bg)] border ${col.color.split(' ')[0]}`}>
                                        <h3 className={`font-semibold text-sm ${col.color.split(' ')[1]}`}>{col.label}</h3>
                                        <span className="px-2 py-0.5 rounded-full bg-white/10 text-xs font-medium">{colApps.length}</span>
                                    </div>
                                    <div className="flex-1 flex flex-col gap-3 min-h-[100px] rounded-xl bg-[var(--bg-deep)]/30 border border-dashed border-white/5 p-2">
                                        <AnimatePresence>
                                            {colApps.map(app => (
                                                <motion.div
                                                    key={app.id}
                                                    layout
                                                    initial={{ opacity: 0, y: 10 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    exit={{ opacity: 0, scale: 0.95 }}
                                                    draggable
                                                    onDragStart={(e: any) => handleDragStart(e, app.id)}
                                                    className="p-4 rounded-xl border bg-[var(--card-bg)] border-[var(--card-border)] hover:border-cyber-purple-500/40 hover:bg-white/5 cursor-grab active:cursor-grabbing group transition-colors shadow-sm"
                                                >
                                                    <div className="flex justify-between items-start mb-2">
                                                        <h4 className="font-semibold text-[var(--text-primary)] text-sm leading-tight group-hover:text-cyber-purple-400 transition-colors">{app.job_title}</h4>
                                                        <button className="text-[var(--text-secondary)] opacity-0 group-hover:opacity-100 transition-opacity hover:text-[var(--text-primary)]">
                                                            <MoreVertical size={14} />
                                                        </button>
                                                    </div>
                                                    <div className="flex items-center gap-2 mb-3">
                                                        <div className="w-5 h-5 rounded bg-white/5 flex items-center justify-center border border-white/10 shrink-0">
                                                            <Building size={10} className="text-[var(--text-secondary)]" />
                                                        </div>
                                                        <span className="text-xs text-[var(--text-secondary)] font-medium truncate">{app.company}</span>
                                                    </div>
                                                    <div className="flex flex-wrap gap-2 mb-3">
                                                        <span className="px-2 py-0.5 rounded bg-white/5 text-[10px] text-[var(--text-secondary)] border border-white/5 flex items-center gap-1">
                                                            <MapPin size={10} /> {app.location}
                                                        </span>
                                                        {app.salary && (
                                                            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-[10px] text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                                                                <DollarSign size={10} /> {app.salary}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="flex justify-between items-center pt-3 border-t border-[var(--card-border)]">
                                                        <span className="text-[10px] text-[var(--text-secondary)] flex items-center gap-1">
                                                            <Clock size={10} /> {new Date(app.applied_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                                        </span>
                                                        <div className="flex items-center gap-1 text-[10px] font-medium text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                                                            <span>{app.match_score}% Match</span>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            ))}
                                        </AnimatePresence>
                                        {colApps.length === 0 && (
                                            <div className="h-full flex flex-col items-center justify-center text-[var(--text-secondary)] opacity-30 py-8">
                                                <Kanban size={24} className="mb-2" />
                                                <p className="text-xs">Drag jobs here</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                ) : (
                    <div className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-xl overflow-hidden mt-6">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-[var(--card-border)] bg-white/5 text-[var(--text-secondary)] text-sm">
                                    <th className="p-4 font-medium">Role & Company</th>
                                    <th className="p-4 font-medium">Status</th>
                                    <th className="p-4 font-medium">Location</th>
                                    <th className="p-4 font-medium">Date Applied</th>
                                    <th className="p-4 font-medium text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {applications.map((app) => (
                                    <tr key={app.id} className="border-b border-[var(--card-border)] hover:bg-white/5 transition-colors group">
                                        <td className="p-4">
                                            <p className="font-semibold text-[var(--text-primary)]">{app.job_title}</p>
                                            <p className="text-sm text-[var(--text-secondary)] flex items-center gap-1 mt-1">
                                                <Building size={12} /> {app.company}
                                            </p>
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2.5 py-1 text-xs font-medium rounded-full bg-white/5 border capitalize
                                                ${app.status === 'applied' ? 'text-cyber-blue-400 border-cyber-blue-500/30 bg-cyber-blue-500/10' : ''}
                                                ${app.status === 'screening' ? 'text-amber-400 border-amber-500/30 bg-amber-500/10' : ''}
                                                ${app.status === 'interviewing' ? 'text-cyber-purple-400 border-cyber-purple-500/30 bg-cyber-purple-500/10' : ''}
                                                ${app.status === 'offer' ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' : ''}
                                                ${app.status === 'rejected' ? 'text-rose-400 border-rose-500/30 bg-rose-500/10' : ''}
                                            `}>
                                                {app.status}
                                            </span>
                                        </td>
                                        <td className="p-4 text-sm text-[var(--text-secondary)]">{app.location}</td>
                                        <td className="p-4 text-sm text-[var(--text-secondary)]">
                                            {new Date(app.applied_date).toLocaleDateString()}
                                        </td>
                                        <td className="p-4 text-right">
                                            <CyberButton variant="ghost" className="px-3 py-1.5 text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                                                Details
                                            </CyberButton>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
