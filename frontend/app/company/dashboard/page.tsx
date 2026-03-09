"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import api from "@/src/lib/api";
import GlassCard from "@/components/ui/GlassCard";
import CyberButton from "@/components/ui/CyberButton";
import { motion } from "framer-motion";
import {
  Users,
  Briefcase,
  Clock,
  CheckCircle2,
  XCircle,
  TrendingUp,
  MoreHorizontal,
  ArrowUpRight,
} from "lucide-react";
import toast, { Toaster } from "react-hot-toast";
const { apiClient, getServiceUrl } = api;
interface DashboardStats {
  total_roles: number;
  active_roles: number;
  total_candidates: number;
  assessed: number;
  shortlisted: number;
  rejected: number;
  pending: number;
}
export default function CompanyDashboard() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    if (user?.account_type !== "company" && user?.account_type !== "admin") {
      console.warn("User is not a company account");
    }
    const companyId =
      user?.company_id || "00000000-0000-0000-0000-000000000001";
    fetchStats(companyId);
  }, [isAuthenticated, user]);
  const fetchStats = async (companyId: string) => {
    try {
      const res = await apiClient.get(
        `${getServiceUrl("company")}/companies/${companyId}/dashboard`,
      );
      setStats(res.data);
    } catch (err: any) {
      console.error("Failed to load company stats:", err);
      if (err.response?.status === 404) {
        setStats({
          total_roles: 0,
          active_roles: 0,
          total_candidates: 0,
          assessed: 0,
          shortlisted: 0,
          rejected: 0,
          pending: 0,
        });
      } else {
        toast.error("Failed to load dashboard data");
      }
    } finally {
      setLoading(false);
    }
  };
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-10 h-10 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin" />
      </div>
    );
  }
  const statCards = [
    {
      title: "Total Candidates",
      value: stats?.total_candidates || 0,
      icon: Users,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    },
    {
      title: "Pending Review",
      value: stats?.pending || 0,
      icon: Clock,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
    },
    {
      title: "Shortlisted",
      value: stats?.shortlisted || 0,
      icon: CheckCircle2,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
    },
    {
      title: "Active Roles",
      value: stats?.active_roles || 0,
      icon: Briefcase,
      color: "text-violet-400",
      bg: "bg-violet-500/10",
    },
  ];
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <Toaster position="top-right" />
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            Overview
          </h1>
          <p className="text-zinc-400 mt-1">
            Welcome back. Here's what's happening with your hiring pipeline.
          </p>
        </div>
        <CyberButton
          onClick={() => router.push("/company/roles/new")}
          className="gap-2"
        >
          <Briefcase size={16} />
          Create New Role
        </CyberButton>
      </div>
      {}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <GlassCard className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div
                    className={`p-3 rounded-xl border border-white/5 ${stat.bg} ${stat.color}`}
                  >
                    <Icon size={24} />
                  </div>
                  <span className="flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                    <TrendingUp size={12} /> +12%
                  </span>
                </div>
                <h3 className="text-zinc-400 text-sm font-semibold uppercase tracking-wider">
                  {stat.title}
                </h3>
                <p className="text-3xl font-bold text-white mt-2">
                  {stat.value}
                </p>
              </GlassCard>
            </motion.div>
          );
        })}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="w-1.5 h-6 bg-blue-500 rounded-full"></span>
              Recent Candidates
            </h2>
            <button className="text-sm text-zinc-400 hover:text-white transition-colors flex items-center gap-1 font-medium">
              View All <ArrowUpRight size={16} />
            </button>
          </div>
          <div className="space-y-4">
            {[1, 2, 3].map((_, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
              >
                <GlassCard className="p-5 flex items-center justify-between group hover:border-white/20 hover:bg-white/5 transition-colors cursor-pointer rounded-xl">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-zinc-800 border border-white/5 flex items-center justify-center text-zinc-300 font-semibold group-hover:text-blue-400 transition-colors shadow-inner">
                      CN
                    </div>
                    <div>
                      <h4 className="text-white font-semibold group-hover:text-blue-400 transition-colors">
                        Candidate Name {i + 1}
                      </h4>
                      <p className="text-xs text-zinc-400 mt-1">
                        Senior Frontend Engineer • Assessed 2h ago
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right hidden sm:block">
                      <p className="text-xs text-zinc-500 font-medium mb-1">
                        Score
                      </p>
                      <p className="text-lg font-bold text-white">8{i}.5%</p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        className="p-2 text-zinc-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-colors border border-transparent hover:border-emerald-500/20"
                        title="Shortlist"
                      >
                        <CheckCircle2 size={18} />
                      </button>
                      <button
                        className="p-2 text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors border border-transparent hover:border-rose-500/20"
                        title="Reject"
                      >
                        <XCircle size={18} />
                      </button>
                      <button className="p-2 text-zinc-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors border border-transparent hover:border-white/10">
                        <MoreHorizontal size={18} />
                      </button>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </div>
        {}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="w-1.5 h-6 bg-violet-500 rounded-full"></span>
              Pipeline Funnel
            </h2>
          </div>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <GlassCard className="p-6">
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-zinc-400 font-medium">Invited</span>
                    <span className="text-white font-bold">
                      {stats?.total_candidates || 0}
                    </span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden border border-white/5">
                    <div className="bg-zinc-400 h-full rounded-full w-full"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-zinc-400 font-medium">Assessed</span>
                    <span className="text-white font-bold">
                      {stats?.assessed || 0}
                    </span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden border border-white/5">
                    <div
                      className="bg-violet-500 h-full rounded-full"
                      style={{ width: "80%" }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-zinc-400 font-medium">
                      Shortlisted
                    </span>
                    <span className="text-white font-bold">
                      {stats?.shortlisted || 0}
                    </span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden border border-white/5">
                    <div
                      className="bg-emerald-500 h-full rounded-full"
                      style={{ width: "40%" }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-zinc-400 font-medium">Hired</span>
                    <span className="text-white font-bold">0</span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden border border-white/5">
                    <div
                      className="bg-blue-500 h-full rounded-full"
                      style={{ width: "10%" }}
                    ></div>
                  </div>
                </div>
              </div>
            </GlassCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
