"use client";
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import api from "@/src/lib/api";
import GlassCard from "@/components/ui/GlassCard";
import CyberButton from "@/components/ui/CyberButton";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  Filter,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  ArrowUpRight,
  PlayCircle,
  Users,
} from "lucide-react";
import toast, { Toaster } from "react-hot-toast";
import clsx from "clsx";
const { apiClient, getServiceUrl } = api;
interface CandidateAssignment {
  id: string;
  candidate_name: string;
  candidate_email: string;
  status: string;
  overall_score: number;
  weighted_score: number;
  fit_score: number;
  dimension_scores: Record<string, number>;
  invited_at: string;
  assessed_at: string | null;
  tags: string[];
}
interface RoleTemplate {
  id: string;
  title: string;
  candidates_assessed: number;
  candidates_shortlisted: number;
}
export default function RoleCandidatesPipeline() {
  const router = useRouter();
  const params = useParams();
  const roleId = params.id as string;
  const { isAuthenticated, user } = useAuthStore();
  const [candidates, setCandidates] = useState<CandidateAssignment[]>([]);
  const [role, setRole] = useState<RoleTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>("all");
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    const companyId =
      user?.company_id || "00000000-0000-0000-0000-000000000001";
    fetchData(companyId);
  }, [isAuthenticated, user, roleId]);
  const fetchData = async (companyId: string) => {
    try {
      const [roleRes, candRes] = await Promise.all([
        apiClient.get(
          `${getServiceUrl("company")}/companies/${companyId}/roles/${roleId}`,
        ),
        apiClient.get(
          `${getServiceUrl("company")}/companies/${companyId}/roles/${roleId}/candidates`,
        ),
      ]);
      setRole(roleRes.data);
      setCandidates(candRes.data);
    } catch (err: any) {
      console.error("Failed to load data:", err);
      if (err.response?.status !== 404) {
        toast.error("Error loading candidates");
      }
    } finally {
      setLoading(false);
    }
  };
  const updateStatus = async (assignmentId: string, newStatus: string) => {
    const companyId =
      user?.company_id || "00000000-0000-0000-0000-000000000001";
    try {
      await apiClient.put(
        `${getServiceUrl("company")}/companies/${companyId}/candidates/${assignmentId}/status?status=${newStatus}`,
      );
      toast.success(`Candidate marked as ${newStatus}`);
      setCandidates((prev) =>
        prev.map((c) =>
          c.id === assignmentId ? { ...c, status: newStatus } : c,
        ),
      );
    } catch (error) {
      toast.error("Failed to update status");
    }
  };
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-10 h-10 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin" />
      </div>
    );
  }
  const filteredCandidates =
    filterStatus === "all"
      ? candidates
      : candidates.filter((c) => c.status === filterStatus);
  return (
    <div className="p-8 max-w-7xl mx-auto">
      <Toaster position="top-right" />
      {}
      <div className="mb-8">
        <button
          onClick={() => router.push("/company/roles")}
          className="flex items-center gap-1 text-sm font-medium text-slate-400 hover:text-white transition-colors mb-4"
        >
          <ChevronLeft size={16} /> Back to Roles
        </button>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-4">
              {role?.title || "Unknown Role"}
            </h1>
            <p className="text-slate-400 mt-2 flex gap-4">
              <span>Total Candidates: {candidates.length}</span>
              <span>Assessed: {role?.candidates_assessed || 0}</span>
              <span className="text-emerald-400">
                Shortlisted: {role?.candidates_shortlisted || 0}
              </span>
            </p>
          </div>
        </div>
      </div>
      {}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 w-5 h-5" />
          <input
            type="text"
            placeholder="Search by name, email, or skill..."
            className="w-full bg-slate-900 border border-slate-700/50 rounded-xl py-2 pl-10 pr-4 text-white focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/50 transition-all font-medium"
          />
        </div>
        <div className="flex bg-slate-900 rounded-xl p-1 border border-slate-800">
          {["all", "pending", "assessed", "shortlisted", "rejected"].map(
            (status) => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                className={clsx(
                  "px-4 py-1.5 rounded-lg text-sm font-medium transition-all capitalize",
                  filterStatus === status
                    ? "bg-slate-800 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200",
                )}
              >
                {status === "all" ? "All" : status}
                <span className="ml-2 px-1.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-xs">
                  {status === "all"
                    ? candidates.length
                    : candidates.filter((c) => c.status === status).length}
                </span>
              </button>
            ),
          )}
        </div>
      </div>
      {}
      <div className="space-y-4">
        {filteredCandidates.length === 0 ? (
          <GlassCard className="p-12 text-center">
            <Users className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-bold text-white mb-2">
              No candidates found
            </h3>
            <p className="text-slate-400">
              Try adjusting your filters or invite more candidates.
            </p>
          </GlassCard>
        ) : (
          filteredCandidates.map((candidate, i) => (
            <motion.div
              key={candidate.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <div
                onClick={() =>
                  router.push(`/company/candidates/${candidate.id}`)
                }
                className="cursor-pointer group"
              >
                <GlassCard className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-6 hover:border-violet-500/40 transition-colors">
                  <div className="flex items-center gap-4 min-w-[300px]">
                    <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-violet-500/20 to-cyan-500/20 border border-violet-500/30 flex items-center justify-center text-lg font-bold text-white shadow-inner">
                      {candidate.candidate_name.substring(0, 2).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <h3 className="font-bold text-white truncate">
                          {candidate.candidate_name}
                        </h3>
                        {candidate.status === "shortlisted" && (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        )}
                        {candidate.status === "rejected" && (
                          <XCircle className="w-4 h-4 text-rose-400" />
                        )}
                        {candidate.status === "assessed" && (
                          <Clock className="w-4 h-4 text-amber-400" />
                        )}
                      </div>
                      <p className="text-xs text-slate-400 truncate">
                        {candidate.candidate_email}
                      </p>
                    </div>
                  </div>
                  <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-4 px-4 border-l border-r border-slate-800/50">
                    <div className="text-center">
                      <p className="text-xs text-slate-500 mb-1">
                        Company Score
                      </p>
                      <p className="font-bold text-white">
                        {candidate.weighted_score
                          ? `${Math.round(candidate.weighted_score)}%`
                          : "--"}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-slate-500 mb-1">Raw Score</p>
                      <p className="font-bold text-slate-300">
                        {candidate.overall_score
                          ? `${Math.round(candidate.overall_score * 100)}%`
                          : "--"}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-slate-500 mb-1">Role Fit</p>
                      <div className="flex items-center justify-center gap-1">
                        <div className="w-full max-w-[40px] h-1.5 bg-slate-800 rounded-full overflow-hidden flex-1">
                          <div
                            className={`h-full rounded-full ${candidate.fit_score >= 1.0 ? "bg-emerald-500" : candidate.fit_score > 0.7 ? "bg-amber-500" : "bg-rose-500"}`}
                            style={{
                              width: `${(candidate.fit_score || 0) * 100}%`,
                            }}
                          />
                        </div>
                        <span className="text-xs font-medium text-white">
                          {candidate.fit_score
                            ? `${Math.round(candidate.fit_score * 100)}%`
                            : "--"}
                        </span>
                      </div>
                    </div>
                    <div className="text-center flex items-center justify-center">
                      <p className="text-xs text-slate-500 text-left">
                        {candidate.assessed_at
                          ? `Assessed on ${new Date(candidate.assessed_at).toLocaleDateString()}`
                          : "Awaiting Assessment"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 min-w-[140px] justify-end">
                    {candidate.status === "assessed" && (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            updateStatus(candidate.id, "shortlisted");
                          }}
                          className="p-2 text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-colors border border-transparent hover:border-emerald-500/20"
                          title="Shortlist"
                        >
                          <CheckCircle2 size={18} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            updateStatus(candidate.id, "rejected");
                          }}
                          className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors border border-transparent hover:border-rose-500/20"
                          title="Reject"
                        >
                          <XCircle size={18} />
                        </button>
                      </>
                    )}
                    <button className="text-sm font-medium text-violet-400 flex items-center gap-1 group-hover:text-violet-300 transition-colors">
                      Review <ArrowUpRight size={16} />
                    </button>
                  </div>
                </GlassCard>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
