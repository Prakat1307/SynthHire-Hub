"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import api from "@/src/lib/api";
import GlassCard from "@/components/ui/GlassCard";
import CyberButton from "@/components/ui/CyberButton";
import {
  ChevronLeft,
  Briefcase,
  Target,
  BrainCircuit,
  Sliders,
  CheckCircle2,
} from "lucide-react";
import toast, { Toaster } from "react-hot-toast";
import { motion } from "framer-motion";
const { apiClient, getServiceUrl } = api;
export default function CreateRoleTemplate() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    title: "",
    department: "",
    experience_level: "mid",
    description: "",
    duration_minutes: 45,
    interview_type: "technical",
  });
  const [weights, setWeights] = useState({
    technical_correctness: 20,
    problem_decomposition: 10,
    communication_clarity: 15,
    handling_ambiguity: 10,
    edge_case_awareness: 10,
    semantic_quality: 15,
    problem_structure: 10,
    collaborative_signals: 10,
  });
  const [autoShortlist, setAutoShortlist] = useState({
    enabled: false,
    threshold: 70,
  });
  const handleWeightChange = (key: string, value: string) => {
    setWeights((prev) => ({ ...prev, [key]: parseInt(value) || 0 }));
  };
  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
  const handleSubmit = async () => {
    if (totalWeight !== 100) {
      toast.error("Rubric weights must sum to exactly 100%");
      return;
    }
    if (!formData.title) {
      toast.error("Role title is required");
      return;
    }
    setLoading(true);
    const companyId =
      user?.company_id || "00000000-0000-0000-0000-000000000001";
    try {
      const normalizeWeights = Object.fromEntries(
        Object.entries(weights).map(([k, v]) => [k, v / 100]),
      );
      const profileRes = await apiClient.post(
        `${getServiceUrl("company")}/companies/${companyId}/scoring-profiles`,
        {
          name: `${formData.title} Rubric`,
          weights: normalizeWeights,
          pass_threshold: autoShortlist.threshold,
        },
      );
      await apiClient.post(
        `${getServiceUrl("company")}/companies/${companyId}/roles`,
        {
          ...formData,
          scoring_profile_id: profileRes.data.id,
          auto_shortlist_enabled: autoShortlist.enabled,
          auto_shortlist_threshold: autoShortlist.threshold,
        },
      );
      toast.success("Role template created!");
      setTimeout(() => {
        router.push("/company/roles");
      }, 1000);
    } catch (err) {
      console.error(err);
      toast.error("Failed to create role");
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6 pb-24">
      <Toaster position="top-right" />
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm font-medium text-slate-400 hover:text-white transition-colors mb-4"
      >
        <ChevronLeft size={16} /> Cancel
      </button>
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
          <Briefcase className="text-violet-500" />
          Create Role Template
        </h1>
        <p className="text-slate-400 mt-1">
          Configure the job requirements and assessment parameters.
        </p>
      </div>
      {}
      <div className="flex items-center justify-between mb-8 max-w-lg relative">
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-800 -z-10" />
        <div
          className="absolute top-1/2 left-0 h-0.5 bg-violet-500 transition-all duration-500"
          style={{ width: step === 1 ? "0%" : step === 2 ? "50%" : "100%" }}
        />
        <div
          className={`flex flex-col items-center gap-2 ${step >= 1 ? "text-violet-400" : "text-slate-500"}`}
        >
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center font-bold bg-slate-950 border-2 ${step >= 1 ? "border-violet-500 text-violet-400 shadow-[0_0_15px_rgba(139,92,246,0.3)]" : "border-slate-800"}`}
          >
            1
          </div>
          <span className="text-xs font-medium">Details</span>
        </div>
        <div
          className={`flex flex-col items-center gap-2 ${step >= 2 ? "text-violet-400" : "text-slate-500"}`}
        >
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center font-bold bg-slate-950 border-2 ${step >= 2 ? "border-violet-500 text-violet-400 shadow-[0_0_15px_rgba(139,92,246,0.3)]" : "border-slate-800"}`}
          >
            2
          </div>
          <span className="text-xs font-medium">Rubric</span>
        </div>
        <div
          className={`flex flex-col items-center gap-2 ${step >= 3 ? "text-violet-400" : "text-slate-500"}`}
        >
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center font-bold bg-slate-950 border-2 ${step >= 3 ? "border-violet-500 text-violet-400 shadow-[0_0_15px_rgba(139,92,246,0.3)]" : "border-slate-800"}`}
          >
            3
          </div>
          <span className="text-xs font-medium">Auto-Rules</span>
        </div>
      </div>
      <GlassCard className="p-8">
        {step === 1 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Target className="text-violet-400" /> Basic Information
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Role Title <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) =>
                    setFormData({ ...formData, title: e.target.value })
                  }
                  placeholder="e.g. Senior Backend Engineer"
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Department
                  </label>
                  <input
                    type="text"
                    value={formData.department}
                    onChange={(e) =>
                      setFormData({ ...formData, department: e.target.value })
                    }
                    placeholder="e.g. Engineering"
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Experience Level
                  </label>
                  <select
                    value={formData.experience_level}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        experience_level: e.target.value,
                      })
                    }
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 appearance-none"
                  >
                    <option value="junior">Junior (0-2 yrs)</option>
                    <option value="mid">Mid-Level (3-5 yrs)</option>
                    <option value="senior">Senior (5-8+ yrs)</option>
                    <option value="staff">Staff/Principal</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Interview Type
                  </label>
                  <select
                    value={formData.interview_type}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        interview_type: e.target.value,
                      })
                    }
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 appearance-none"
                  >
                    <option value="technical">Technical / Coding</option>
                    <option value="system_design">System Design</option>
                    <option value="behavioral">Behavioral</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Duration (Minutes)
                  </label>
                  <input
                    type="number"
                    value={formData.duration_minutes}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        duration_minutes: parseInt(e.target.value) || 45,
                      })
                    }
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Role Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="Internal notes or job spec..."
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 min-h-[100px]"
                />
              </div>
            </div>
            <div className="flex justify-end pt-4">
              <CyberButton onClick={() => setStep(2)}>
                Next: Configure Rubric
              </CyberButton>
            </div>
          </motion.div>
        )}
        {step === 2 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <BrainCircuit className="text-violet-400" /> Scoring Rubric
              </h2>
              <div
                className={`px-4 py-1.5 rounded-full text-sm font-bold ${totalWeight === 100 ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "bg-rose-500/20 text-rose-400 border border-rose-500/30"}`}
              >
                Total: {totalWeight}%{" "}
                {totalWeight !== 100 && "(Must equal 100%)"}
              </div>
            </div>
            <p className="text-sm text-slate-400 mb-6">
              Allocate relative importance to different assessment dimensions
              for this role.
            </p>
            <div className="space-y-4 max-w-2xl">
              {Object.entries(weights).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center gap-4 p-4 bg-slate-900/50 border border-slate-800 rounded-xl"
                >
                  <div className="flex-1">
                    <p className="font-medium text-white capitalize">
                      {key.replace(/_/g, " ")}
                    </p>
                  </div>
                  <div className="w-full max-w-[200px] flex items-center gap-3">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      value={value}
                      onChange={(e) => handleWeightChange(key, e.target.value)}
                      className="w-full accent-violet-500"
                    />
                    <div className="w-16 flex items-center gap-1">
                      <input
                        type="number"
                        value={value}
                        onChange={(e) =>
                          handleWeightChange(key, e.target.value)
                        }
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-center text-sm"
                      />
                      <span className="text-slate-400 text-sm">%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-between pt-8">
              <button
                onClick={() => setStep(1)}
                className="px-6 py-2 rounded-lg font-medium text-slate-300 hover:text-white transition-colors"
              >
                Back
              </button>
              <CyberButton
                onClick={() =>
                  totalWeight === 100
                    ? setStep(3)
                    : toast.error("Weights must equal 100%")
                }
                disabled={totalWeight !== 100}
              >
                Next: Auto-Rules
              </CyberButton>
            </div>
          </motion.div>
        )}
        {step === 3 && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Sliders className="text-cyan-400" /> Shortlisting Rules
            </h2>
            <div className="p-6 bg-slate-900/50 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between mb-6 border-b border-slate-800 pb-6">
                <div>
                  <h3 className="font-bold text-white mb-1 flex items-center gap-2">
                    Enable Auto-Shortlisting
                  </h3>
                  <p className="text-sm text-slate-400">
                    Automatically move candidates to "Shortlisted" if they meet
                    the threshold.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={autoShortlist.enabled}
                    onChange={() =>
                      setAutoShortlist((p) => ({ ...p, enabled: !p.enabled }))
                    }
                  />
                  <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                </label>
              </div>
              <div
                className={`transition-opacity duration-300 ${autoShortlist.enabled ? "opacity-100" : "opacity-40 pointer-events-none"}`}
              >
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Overall Score Minimum Threshold (%)
                </label>
                <div className="flex items-center gap-4 mb-2">
                  <input
                    type="range"
                    min="50"
                    max="95"
                    step="1"
                    value={autoShortlist.threshold}
                    onChange={(e) =>
                      setAutoShortlist((p) => ({
                        ...p,
                        threshold: parseInt(e.target.value),
                      }))
                    }
                    className="w-full accent-emerald-500"
                  />
                  <div className="w-20 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white font-bold text-center">
                    {autoShortlist.threshold}%
                  </div>
                </div>
                <p className="text-xs text-slate-500 italic">
                  Scores below this will remain in "Assessed" for manual review.
                </p>
              </div>
            </div>
            <div className="flex justify-between pt-8">
              <button
                onClick={() => setStep(2)}
                className="px-6 py-2 rounded-lg font-medium text-slate-300 hover:text-white transition-colors"
              >
                Back
              </button>
              <CyberButton
                onClick={handleSubmit}
                disabled={loading}
                className="px-8 bg-emerald-500/20 text-emerald-400 border-emerald-500/50 hover:bg-emerald-500/30"
              >
                {loading ? (
                  "Saving..."
                ) : (
                  <>
                    <CheckCircle2 size={18} className="mr-2" /> Publish Role
                    Template
                  </>
                )}
              </CyberButton>
            </div>
          </motion.div>
        )}
      </GlassCard>
    </div>
  );
}
