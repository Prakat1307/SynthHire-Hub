"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import api from "@/src/lib/api";
import GlassCard from "@/components/ui/GlassCard";
import CyberButton from "@/components/ui/CyberButton";
import { motion } from "framer-motion";
import {
  Briefcase,
  Plus,
  Users,
  Clock,
  Settings,
  ArrowRight,
} from "lucide-react";
import toast, { Toaster } from "react-hot-toast";
const { apiClient, getServiceUrl } = api;
interface RoleTemplate {
  id: string;
  title: string;
  department: string;
  experience_level: string;
  interview_type: string;
  duration_minutes: number;
  is_active: string;
  candidates_assessed: number;
  candidates_shortlisted: number;
  auto_shortlist_enabled: boolean;
  created_at: string;
}
export default function CompanyRolesList() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [roles, setRoles] = useState<RoleTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    const companyId =
      user?.company_id || "00000000-0000-0000-0000-000000000001";
    fetchRoles(companyId);
  }, [isAuthenticated, user]);
  const fetchRoles = async (companyId: string) => {
    try {
      const res = await apiClient.get(
        `${getServiceUrl("company")}/companies/${companyId}/roles`,
      );
      setRoles(res.data);
    } catch (err: any) {
      console.error("Failed to load roles:", err);
      if (err.response?.status !== 404) {
        toast.error("Failed to load roles");
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
  return (
    <div className="p-8 max-w-6xl mx-auto">
      <Toaster position="top-right" />
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <Briefcase className="text-violet-500" />
            Role Templates
          </h1>
          <p className="text-slate-400 mt-1">
            Manage job requirements, assessment rubrics, and automated
            shortlisting rules.
          </p>
        </div>
        <CyberButton
          onClick={() => router.push("/company/roles/new")}
          className="gap-2 shrink-0"
        >
          <Plus size={18} />
          Create Template
        </CyberButton>
      </div>
      {roles.length === 0 ? (
        <GlassCard className="p-12 text-center">
          <div className="w-16 h-16 bg-slate-800/50 text-slate-500 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-700/50">
            <Briefcase size={32} />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">
            No roles created yet
          </h3>
          <p className="text-slate-400 mb-6 max-w-md mx-auto">
            Create your first role template to generate shareable assessment
            links and start evaluating candidates automatically.
          </p>
          <CyberButton onClick={() => router.push("/company/roles/new")}>
            Create First Role
          </CyberButton>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {roles.map((role, i) => (
            <motion.div
              key={role.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <GlassCard className="p-0 h-full flex flex-col hover:border-violet-500/40 transition-all group overflow-hidden relative">
                {}
                {role.is_active && (
                  <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-cyan-500 opacity-80" />
                )}
                <div className="p-6 flex-1">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <span className="text-xs font-semibold uppercase tracking-wider text-violet-400 mb-1 block">
                        {role.department || "Engineering"}
                      </span>
                      <h3 className="text-lg font-bold text-white leading-tight">
                        {role.title}
                      </h3>
                    </div>
                    <div className="flex gap-1">
                      <button className="p-1.5 text-slate-500 hover:text-white bg-slate-800/50 hover:bg-slate-700 rounded transition-colors">
                        <Settings size={16} />
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-xs font-medium text-slate-400 mb-6">
                    <span className="flex items-center gap-1.5 bg-slate-800/50 px-2 py-1 rounded">
                      <Users size={14} className="text-cyan-500" />
                      {role.experience_level || "Any"}
                    </span>
                    <span className="flex items-center gap-1.5 bg-slate-800/50 px-2 py-1 rounded">
                      <Clock size={14} className="text-amber-500" />
                      {role.duration_minutes}m
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-3 text-center">
                      <p className="text-xs text-slate-500 mb-1">Assessed</p>
                      <p className="text-xl font-bold text-white">
                        {role.candidates_assessed}
                      </p>
                    </div>
                    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-3 text-center">
                      <p className="text-xs text-slate-500 mb-1">Pass Rate</p>
                      <p className="text-xl font-bold text-emerald-400">
                        {role.candidates_assessed > 0
                          ? Math.round(
                              (role.candidates_shortlisted /
                                role.candidates_assessed) *
                                100,
                            )
                          : 0}
                        %
                      </p>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-slate-900/80 border-t border-slate-800 flex justify-between items-center mt-auto">
                  <div className="text-xs font-medium flex items-center gap-2">
                    {role.auto_shortlist_enabled ? (
                      <span className="text-emerald-400 flex items-center gap-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />{" "}
                        Auto-Shortlisting ON
                      </span>
                    ) : (
                      <span className="text-slate-500">Manual Review Only</span>
                    )}
                  </div>
                  <button
                    onClick={() =>
                      router.push(`/company/roles/${role.id}/candidates`)
                    }
                    className="text-sm font-medium text-white group-hover:text-violet-400 flex items-center gap-1 transition-colors"
                  >
                    View Pipeline <ArrowRight size={16} />
                  </button>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
