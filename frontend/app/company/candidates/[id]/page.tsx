"use client";
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import api from "@/src/lib/api";
import GlassCard from "@/components/ui/GlassCard";
import CyberButton from "@/components/ui/CyberButton";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  PlayCircle,
  MessageSquare,
  Star,
  User,
  Building,
} from "lucide-react";
import toast, { Toaster } from "react-hot-toast";
const { apiClient, getServiceUrl } = api;
interface CandidateDetail {
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
  reviews: any[];
}
export default function CandidateReviewPage() {
  const router = useRouter();
  const params = useParams();
  const assignmentId = params.id as string;
  const { isAuthenticated, user } = useAuthStore();
  const [candidate, setCandidate] = useState<CandidateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewNotes, setReviewNotes] = useState("");
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    const companyId =
      user?.company_id || "00000000-0000-0000-0000-000000000001";
    fetchCandidate(companyId);
  }, [isAuthenticated, user, assignmentId]);
  const fetchCandidate = async (companyId: string) => {
    try {
      const res = await apiClient.get(
        `${getServiceUrl("company")}/companies/${companyId}/candidates/${assignmentId}`,
      );
      setCandidate(res.data);
    } catch (err: any) {
      console.error("Failed to load candidate:", err);
      if (err.response?.status !== 404) {
        toast.error("Error loading candidate details");
      }
    } finally {
      setLoading(false);
    }
  };
  const submitReview = async (decision: string) => {
    const companyId =
      user?.company_id || "00000000-0000-0000-0000-000000000001";
    try {
      const res = await apiClient.post(
        `${getServiceUrl("company")}/companies/${companyId}/candidates/${assignmentId}/review`,
        {
          decision,
          notes: reviewNotes,
          confidence_level: "high",
        },
      );
      toast.success(`Candidate marked as ${decision}`);
      setCandidate((prev) =>
        prev ? { ...prev, status: res.data.assignment_status } : null,
      );
      setReviewNotes("");
      // Re-fetch to get the new review in the list
      fetchCandidate(companyId);
    } catch (error) {
      toast.error("Failed to submit review");
    }
  };
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-10 h-10 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin" />
      </div>
    );
  }
  if (!candidate)
    return <div className="p-8 text-white">Candidate not found</div>;
  const scores = candidate.dimension_scores || {};
  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <Toaster position="top-right" />
      {}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1 text-sm font-medium text-slate-400 hover:text-white transition-colors mb-2"
          >
            <ChevronLeft size={16} /> Back to Pipeline
          </button>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-violet-500/20 to-cyan-500/20 border border-violet-500/30 flex items-center justify-center text-2xl font-bold text-white shadow-[0_0_15px_rgba(139,92,246,0.2)]">
              {candidate.candidate_name.substring(0, 2).toUpperCase()}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white tracking-tight">
                {candidate.candidate_name}
              </h1>
              <p className="text-slate-400">{candidate.candidate_email}</p>
            </div>
            <div className="ml-4 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border bg-slate-800/80 border-slate-700">
              {candidate.status}
            </div>
          </div>
        </div>
        <div className="flex gap-3">
          <CyberButton
            onClick={() => submitReview("reject")}
            className="bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border-rose-500/30"
          >
            <XCircle size={18} className="mr-2" /> Reject
          </CyberButton>
          <CyberButton
            onClick={() => submitReview("hold")}
            className="bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border-amber-500/30"
          >
            <AlertTriangle size={18} className="mr-2" /> Hold
          </CyberButton>
          <CyberButton
            onClick={() => submitReview("pass")}
            className="bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
          >
            <CheckCircle2 size={18} className="mr-2" /> Shortlist
          </CyberButton>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {}
        <div className="lg:col-span-2 space-y-6">
          <GlassCard className="p-6">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Star className="text-violet-400" /> Scorecard Summary
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 text-center">
                <p className="text-sm font-medium text-slate-400 mb-1">
                  Company Score (Weighted)
                </p>
                <p className="text-4xl font-bold text-white">
                  {candidate.weighted_score
                    ? `${Math.round(candidate.weighted_score)}%`
                    : "--"}
                </p>
              </div>
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 text-center">
                <p className="text-sm font-medium text-slate-400 mb-1">
                  Raw Assessment Score
                </p>
                <p className="text-4xl font-bold text-slate-300">
                  {candidate.overall_score
                    ? `${Math.round(candidate.overall_score * 100)}%`
                    : "--"}
                </p>
              </div>
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 text-center">
                <p className="text-sm font-medium text-slate-400 mb-1">
                  Role Fit Score
                </p>
                <p
                  className={`text-4xl font-bold ${candidate.fit_score >= 1.0 ? "text-emerald-400" : candidate.fit_score > 0.7 ? "text-amber-400" : "text-rose-400"}`}
                >
                  {candidate.fit_score
                    ? `${Math.round(candidate.fit_score * 100)}%`
                    : "--"}
                </p>
              </div>
            </div>
            <h3 className="text-lg font-semibold text-white mb-4">
              Dimension Breakdown
            </h3>
            <div className="space-y-4">
              {Object.entries(scores).map(([dim, score]) => (
                <div key={dim} className="flex items-center gap-4">
                  <div className="w-48 text-sm font-medium text-slate-300 capitalize">
                    {dim.replace(/_/g, " ")}
                  </div>
                  <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-violet-500 to-cyan-500 rounded-full"
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                  <div className="w-12 text-right text-sm font-bold text-white">
                    {Math.round(score * 100)}%
                  </div>
                </div>
              ))}
              {Object.keys(scores).length === 0 && (
                <p className="text-slate-500 text-sm">
                  No dimension scores available yet.
                </p>
              )}
            </div>
          </GlassCard>
          {}
          <GlassCard className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <PlayCircle className="text-cyan-400" /> Interview Highlights
              </h2>
              <button className="text-sm text-cyan-400 hover:text-cyan-300 font-medium">
                View Full Transcript
              </button>
            </div>
            <div className="aspect-video bg-slate-900 rounded-xl border border-slate-800 flex items-center justify-center">
              <div className="text-center text-slate-500">
                <PlayCircle size={48} className="mx-auto mb-2 opacity-50" />
                <p>Video snippets and transcript replay will appear here</p>
              </div>
            </div>
          </GlassCard>
        </div>
        {}
        <div className="space-y-6">
          <GlassCard className="p-6">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <MessageSquare className="text-amber-400" /> Reviewer Notes
            </h2>
            <div className="space-y-4 mb-6 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
              {candidate.reviews?.length === 0 ? (
                <p className="text-slate-500 text-sm italic">
                  No reviews submitted yet.
                </p>
              ) : (
                candidate.reviews?.map((review, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs font-bold text-slate-300 flex items-center gap-1">
                        <User size={12} /> Reviewer
                      </span>
                      <span
                        className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-sm ${
                          review.decision === "pass"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : review.decision === "reject"
                              ? "bg-rose-500/20 text-rose-400"
                              : "bg-amber-500/20 text-amber-400"
                        }`}
                      >
                        {review.decision}
                      </span>
                    </div>
                    <p className="text-sm text-slate-300 whitespace-pre-wrap">
                      {review.notes || "No notes provided."}
                    </p>
                  </div>
                ))
              )}
            </div>
            <div className="space-y-3">
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Add your evaluation notes here..."
                className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-sm text-white resize-none min-h-[100px] focus:outline-none focus:border-violet-500/50"
              />
              <CyberButton
                onClick={() => submitReview("pass")}
                className="w-full justify-center"
                disabled={!reviewNotes.trim()}
              >
                Submit Note & Pass
              </CyberButton>
            </div>
          </GlassCard>
          <GlassCard className="p-6">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Building className="text-emerald-400" /> ATS Sync
            </h2>
            <div className="p-3 bg-slate-900/50 border border-slate-800 rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-sm text-slate-300 font-medium">
                  Greenhouse
                </span>
              </div>
              <span className="text-xs text-slate-500">Synced 2m ago</span>
            </div>
            <button className="w-full mt-3 py-2 text-sm text-slate-400 hover:text-white border border-slate-800 hover:bg-slate-800 transition-colors rounded-lg font-medium">
              Force Manual Sync
            </button>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
