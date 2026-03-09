"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import api from "@/src/lib/api";
import GlassCard from "@/components/ui/GlassCard";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  TrendingUp,
  Target,
  Zap,
  MessageSquare,
  Shield,
  Users,
  Clock,
  Sparkles,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Activity,
  BarChart3,
  Eye,
} from "lucide-react";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Area,
  AreaChart,
  CartesianGrid,
} from "recharts";
const { apiClient, getServiceUrl } = api;
const DIMENSIONS = [
  {
    key: "technical_correctness",
    label: "Technical Depth",
    shortLabel: "Tech",
    icon: Brain,
    color: "#3b82f6",
    gradient: "from-blue-500 to-blue-600",
    description: "Correctness, optimization, and algorithmic thinking",
    tips: [
      "Practice edge case identification",
      "Study time/space complexity trade-offs",
      "Review common design patterns",
    ],
  },
  {
    key: "communication_clarity",
    label: "Communication",
    shortLabel: "Comm",
    icon: MessageSquare,
    color: "#8b5cf6",
    gradient: "from-violet-500 to-violet-600",
    description:
      "Clarity of explanation, structured thinking, minimal filler words",
    tips: [
      'Structure answers with "First, then, finally"',
      'Avoid filler words like "um" and "basically"',
      "Summarize before diving into details",
    ],
  },
  {
    key: "handling_ambiguity",
    label: "Emotional Intelligence",
    shortLabel: "EQ",
    icon: Shield,
    color: "#06b6d4",
    gradient: "from-cyan-500 to-cyan-600",
    description:
      "Composure under pressure, empathy, handling unclear requirements",
    tips: [
      "Ask clarifying questions before solving",
      "Stay calm when requirements change",
      "Acknowledge trade-offs explicitly",
    ],
  },
  {
    key: "problem_decomposition",
    label: "Problem Solving",
    shortLabel: "PS",
    icon: Target,
    color: "#10b981",
    gradient: "from-emerald-500 to-emerald-600",
    description: "Breaking problems into sub-problems, creative approaches",
    tips: [
      "Start with brute force, then optimize",
      "Draw out the problem before coding",
      "Identify patterns from similar problems",
    ],
  },
  {
    key: "edge_case_awareness",
    label: "Domain Knowledge",
    shortLabel: "Domain",
    icon: Eye,
    color: "#f59e0b",
    gradient: "from-amber-500 to-amber-600",
    description: "Industry-specific accuracy, edge case awareness",
    tips: [
      "Study domain-specific terminology",
      "Consider boundary conditions",
      "Think about real-world constraints",
    ],
  },
  {
    key: "collaborative_signals",
    label: "Collaboration",
    shortLabel: "Collab",
    icon: Users,
    color: "#ec4899",
    gradient: "from-pink-500 to-pink-600",
    description: "Pairing cues, openness to feedback, response balance",
    tips: [
      'Ask "does that make sense?" periodically',
      "Incorporate interviewer suggestions",
      "Think out loud collaboratively",
    ],
  },
  {
    key: "time_management",
    label: "Adaptability",
    shortLabel: "Adapt",
    icon: Clock,
    color: "#f97316",
    gradient: "from-orange-500 to-orange-600",
    description: "Context switching, time allocation, pivoting when stuck",
    tips: [
      "Set mental time bounds per section",
      "Recognize when to pivot approaches",
      "Prioritize working solution over perfection",
    ],
  },
  {
    key: "growth_mindset",
    label: "Confidence",
    shortLabel: "Conf",
    icon: Sparkles,
    color: "#a855f7",
    gradient: "from-purple-500 to-purple-600",
    description: "Assertiveness, willingness to learn, voice steadiness",
    tips: [
      "State your approach confidently",
      "Embrace mistakes as learning points",
      "End answers with a clear conclusion",
    ],
  },
];
interface SkillProfile {
  technical_knowledge: number;
  problem_solving: number;
  communication: number;
  coding_correctness: number;
  system_design: number;
  behavioral_fit: number;
  leadership: number;
  culture_fit: number;
  overall: number;
  score_history: Array<{ date: string; scores: Record<string, number> }>;
  total_assessments: number;
  industry_percentile: number | null;
}
interface SessionSummary {
  id: string;
  session_type: string;
  persona_type: string;
  overall_score: number | null;
  dimension_scores: Record<string, number> | null;
  created_at: string;
  status: string;
}
function generateMockData() {
  const mockScores: Record<string, number> = {};
  DIMENSIONS.forEach((d) => {
    mockScores[d.key] = Math.random() * 40 + 50;
  });
  const mockHistory = Array.from({ length: 10 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (10 - i) * 3);
    const scores: Record<string, number> = {};
    DIMENSIONS.forEach((d) => {
      scores[d.key] = Math.max(
        30,
        Math.min(
          95,
          (mockScores[d.key] || 60) + (Math.random() - 0.4) * 15 * (i / 10),
        ),
      );
    });
    return { date: date.toISOString().split("T")[0], scores };
  });
  const mockSessions: SessionSummary[] = Array.from({ length: 6 }, (_, i) => ({
    id: `mock-${i}`,
    session_type: ["coding", "system_design", "behavioral", "mixed"][i % 4],
    persona_type: [
      "kind_mentor",
      "tough_lead",
      "tricky_hr",
      "collaborative_peer",
    ][i % 4],
    overall_score: Math.random() * 40 + 55,
    dimension_scores: Object.fromEntries(
      DIMENSIONS.map((d) => [d.key, Math.random() * 40 + 50]),
    ),
    created_at: new Date(Date.now() - i * 86400000 * 2).toISOString(),
    status: "completed",
  }));
  return { mockScores, mockHistory, mockSessions };
}
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-panel rounded-lg p-3 border border-white/10 text-xs">
      <p className="text-zinc-400 mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} style={{ color: entry.color }} className="font-medium">
          {entry.name}:{" "}
          {typeof entry.value === "number"
            ? entry.value.toFixed(1)
            : entry.value}
        </p>
      ))}
    </div>
  );
}
export default function AnalyticsPage() {
  const router = useRouter();
  const { user, accessToken } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [dimensionScores, setDimensionScores] = useState<
    Record<string, number>
  >({});
  const [scoreHistory, setScoreHistory] = useState<
    Array<{ date: string; scores: Record<string, number> }>
  >([]);
  const [recentSessions, setRecentSessions] = useState<SessionSummary[]>([]);
  const [totalAssessments, setTotalAssessments] = useState(0);
  const [overallScore, setOverallScore] = useState(0);
  const [selectedDimension, setSelectedDimension] = useState<string | null>(
    null,
  );
  const [activeTab, setActiveTab] = useState<"radar" | "timeline">("radar");
  useEffect(() => {
    if (!user || !accessToken) {
      router.push("/login");
      return;
    }
    loadAnalyticsData();
  }, [user, accessToken]);
  async function loadAnalyticsData() {
    setLoading(true);
    try {
      const userServiceUrl = getServiceUrl("auth");
      const [profileRes, sessionsRes] = await Promise.allSettled([
        apiClient.get(`${userServiceUrl}/user/profile`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        }),
        apiClient.get(`${userServiceUrl}/user/sessions?limit=10`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        }),
      ]);
      let scores: Record<string, number> = {};
      let history: Array<{ date: string; scores: Record<string, number> }> = [];
      let sessions: SessionSummary[] = [];
      let total = 0;
      let overall = 0;
      if (
        profileRes.status === "fulfilled" &&
        profileRes.value.data?.skill_profile
      ) {
        const sp = profileRes.value.data.skill_profile;
        DIMENSIONS.forEach((d) => {
          scores[d.key] = (sp[d.key] || 0) as number;
        });
        history = sp.score_history || [];
        total = sp.total_assessments || 0;
        overall = sp.overall || 0;
      }
      if (sessionsRes.status === "fulfilled" && sessionsRes.value.data) {
        sessions = sessionsRes.value.data.filter(
          (s: any) => s.status === "completed",
        );
      }
      const hasRealData = Object.values(scores).some((v) => v > 0);
      if (!hasRealData) {
        const mock = generateMockData();
        scores = mock.mockScores;
        history = mock.mockHistory;
        sessions = mock.mockSessions;
        total = sessions.length;
        overall =
          Object.values(scores).reduce((a, b) => a + b, 0) /
          Object.keys(scores).length;
      }
      setDimensionScores(scores);
      setScoreHistory(history);
      setRecentSessions(sessions);
      setTotalAssessments(total);
      setOverallScore(overall);
    } catch (err) {
      const mock = generateMockData();
      setDimensionScores(mock.mockScores);
      setScoreHistory(mock.mockHistory);
      setRecentSessions(mock.mockSessions);
      setTotalAssessments(mock.mockSessions.length);
      setOverallScore(
        Object.values(mock.mockScores).reduce((a, b) => a + b, 0) /
          Object.keys(mock.mockScores).length,
      );
    } finally {
      setLoading(false);
    }
  }
  const radarData = DIMENSIONS.map((d) => ({
    dimension: d.shortLabel,
    score: dimensionScores[d.key] || 0,
    fullMark: 100,
  }));
  const growthData = scoreHistory.map((entry) => ({
    date: new Date(entry.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    ...DIMENSIONS.reduce(
      (acc, d) => ({ ...acc, [d.shortLabel]: entry.scores[d.key] || 0 }),
      {},
    ),
    overall:
      Object.values(entry.scores).reduce((a, b) => a + b, 0) /
      Math.max(Object.keys(entry.scores).length, 1),
  }));
  function getTrend(key: string): "up" | "down" | "flat" {
    if (scoreHistory.length < 2) return "flat";
    const recent = scoreHistory[scoreHistory.length - 1]?.scores[key] || 0;
    const previous = scoreHistory[scoreHistory.length - 2]?.scores[key] || 0;
    if (recent > previous + 2) return "up";
    if (recent < previous - 2) return "down";
    return "flat";
  }
  const TrendIcon = ({ trend }: { trend: "up" | "down" | "flat" }) => {
    if (trend === "up")
      return <ArrowUpRight className="w-4 h-4 text-emerald-400" />;
    if (trend === "down")
      return <ArrowDownRight className="w-4 h-4 text-red-400" />;
    return <Minus className="w-4 h-4 text-zinc-500" />;
  };
  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <div className="h-10 w-64 bg-zinc-800 rounded-lg animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-80 bg-zinc-900/50 rounded-2xl animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 border border-blue-500/20">
              <Brain className="w-7 h-7 text-blue-400" />
            </div>
            Your Professional Brain
          </h1>
          <p className="text-zinc-400 mt-1">
            Track your growth across 8 dimensions of interview excellence
          </p>
        </div>
        <div className="hidden md:flex items-center gap-3">
          <div className="text-right">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">
              Overall Score
            </p>
            <p className="text-2xl font-bold text-white">
              {overallScore.toFixed(0)}
              <span className="text-sm text-zinc-500">/100</span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">
              Assessments
            </p>
            <p className="text-2xl font-bold text-blue-400">
              {totalAssessments}
            </p>
          </div>
        </div>
      </motion.div>
      {}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {}
        <GlassCard className="!p-0 overflow-hidden">
          <div className="p-5 pb-0 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              Neural Map
            </h2>
            <div className="flex gap-1 rounded-lg bg-zinc-800/50 p-0.5">
              <button
                onClick={() => setActiveTab("radar")}
                className={`px-3 py-1 text-xs rounded-md transition-all ${activeTab === "radar" ? "bg-blue-500/20 text-blue-400" : "text-zinc-500 hover:text-zinc-300"}`}
              >
                Radar
              </button>
              <button
                onClick={() => setActiveTab("timeline")}
                className={`px-3 py-1 text-xs rounded-md transition-all ${activeTab === "timeline" ? "bg-blue-500/20 text-blue-400" : "text-zinc-500 hover:text-zinc-300"}`}
              >
                Timeline
              </button>
            </div>
          </div>
          <div className="h-80 p-4">
            <AnimatePresence mode="wait">
              {activeTab === "radar" ? (
                <motion.div
                  key="radar"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="w-full h-full"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart
                      data={radarData}
                      cx="50%"
                      cy="50%"
                      outerRadius="75%"
                    >
                      <PolarGrid stroke="#27272a" strokeDasharray="3 3" />
                      <PolarAngleAxis
                        dataKey="dimension"
                        tick={{
                          fill: "#a1a1aa",
                          fontSize: 11,
                          fontWeight: 500,
                        }}
                      />
                      <PolarRadiusAxis
                        angle={90}
                        domain={[0, 100]}
                        tick={{ fill: "#52525b", fontSize: 9 }}
                        axisLine={false}
                      />
                      <Radar
                        name="Your Score"
                        dataKey="score"
                        stroke="#3b82f6"
                        fill="#3b82f6"
                        fillOpacity={0.15}
                        strokeWidth={2}
                        dot={{ fill: "#3b82f6", r: 4, strokeWidth: 0 }}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </motion.div>
              ) : (
                <motion.div
                  key="timeline"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="w-full h-full"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={growthData}>
                      <defs>
                        <linearGradient
                          id="colorOverall"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="5%"
                            stopColor="#3b82f6"
                            stopOpacity={0.3}
                          />
                          <stop
                            offset="95%"
                            stopColor="#3b82f6"
                            stopOpacity={0}
                          />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis
                        dataKey="date"
                        tick={{ fill: "#71717a", fontSize: 10 }}
                      />
                      <YAxis
                        domain={[0, 100]}
                        tick={{ fill: "#71717a", fontSize: 10 }}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Area
                        type="monotone"
                        dataKey="overall"
                        stroke="#3b82f6"
                        fill="url(#colorOverall)"
                        strokeWidth={2}
                        name="Overall"
                        dot={{ fill: "#3b82f6", r: 3 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </GlassCard>
        {}
        <GlassCard className="!p-0 overflow-hidden">
          <div className="p-5 pb-0">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Growth Trajectory
            </h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              Score evolution across your last {scoreHistory.length} sessions
            </p>
          </div>
          <div className="h-80 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={growthData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#71717a", fontSize: 10 }}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fill: "#71717a", fontSize: 10 }}
                />
                <Tooltip content={<CustomTooltip />} />
                {DIMENSIONS.slice(0, 4).map((d) => (
                  <Line
                    key={d.key}
                    type="monotone"
                    dataKey={d.shortLabel}
                    stroke={d.color}
                    strokeWidth={2}
                    dot={false}
                    name={d.label}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>
      {}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-violet-400" />
          Dimension Breakdown
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {DIMENSIONS.map((dim, i) => {
            const score = dimensionScores[dim.key] || 0;
            const trend = getTrend(dim.key);
            const Icon = dim.icon;
            const isSelected = selectedDimension === dim.key;
            return (
              <motion.div
                key={dim.key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05, duration: 0.4 }}
                onClick={() =>
                  setSelectedDimension(isSelected ? null : dim.key)
                }
                className={`cursor-pointer group relative rounded-2xl p-5 border transition-all duration-300 overflow-hidden
                                    ${
                                      isSelected
                                        ? "border-blue-500/30 bg-zinc-900/80 shadow-lg shadow-blue-500/10"
                                        : "border-white/5 bg-zinc-900/40 hover:border-white/15 hover:shadow-xl hover:shadow-blue-500/5 hover:-translate-y-0.5"
                                    }`}
              >
                {}
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${dim.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-500`}
                />
                <div className="relative z-10">
                  {}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div
                        className={`p-1.5 rounded-lg bg-gradient-to-br ${dim.gradient} bg-opacity-10`}
                      >
                        <Icon
                          className="w-4 h-4"
                          style={{ color: dim.color }}
                        />
                      </div>
                      <span className="text-sm font-medium text-zinc-300">
                        {dim.label}
                      </span>
                    </div>
                    <TrendIcon trend={trend} />
                  </div>
                  {}
                  <div className="flex items-end gap-1 mb-3">
                    <span className="text-3xl font-bold text-white">
                      {score.toFixed(0)}
                    </span>
                    <span className="text-sm text-zinc-500 mb-1">/100</span>
                  </div>
                  {}
                  <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${score}%` }}
                      transition={{ duration: 1, delay: 0.3 + i * 0.05 }}
                      className="h-full rounded-full"
                      style={{
                        background: `linear-gradient(to right, ${dim.color}, ${dim.color}99)`,
                      }}
                    />
                  </div>
                  {}
                  <AnimatePresence>
                    {isSelected && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-4 border-t border-white/5 mt-4">
                          <p className="text-xs text-zinc-400 mb-3">
                            {dim.description}
                          </p>
                          <p className="text-xs font-semibold text-zinc-300 mb-2 flex items-center gap-1">
                            <Zap className="w-3 h-3 text-amber-400" />
                            Micro-Drills
                          </p>
                          <ul className="space-y-1.5">
                            {dim.tips.map((tip, j) => (
                              <li
                                key={j}
                                className="text-xs text-zinc-500 flex items-start gap-1.5"
                              >
                                <ChevronRight className="w-3 h-3 mt-0.5 text-zinc-600 flex-shrink-0" />
                                {tip}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
      {}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-orange-400" />
          Recent Sessions
        </h2>
        <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent">
          {recentSessions.map((session, i) => (
            <motion.div
              key={session.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
              className="flex-shrink-0 w-64 rounded-2xl border border-white/5 bg-zinc-900/40 p-4 hover:border-white/15 transition-all cursor-pointer hover:shadow-lg hover:shadow-blue-500/5"
              onClick={() =>
                router.push(`/interview/report?session_id=${session.id}`)
              }
            >
              {}
              <div className="h-28 -mx-2 -mt-1">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart
                    data={DIMENSIONS.map((d) => ({
                      dimension: d.shortLabel,
                      score: session.dimension_scores?.[d.key] || 0,
                    }))}
                  >
                    <PolarGrid stroke="#27272a" />
                    <Radar
                      dataKey="score"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.1}
                      strokeWidth={1.5}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              {}
              <div className="mt-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-zinc-300 capitalize">
                    {session.session_type.replace("_", " ")}
                  </span>
                  <span className="text-lg font-bold text-white">
                    {session.overall_score?.toFixed(0) ?? "—"}
                  </span>
                </div>
                <p className="text-xs text-zinc-500 mt-1">
                  {new Date(session.created_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </p>
                <p className="text-xs text-zinc-600 mt-0.5 capitalize">
                  {session.persona_type.replace("_", " ")}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
      {}
      <GlassCard className="!p-0 overflow-hidden">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-1">
            <Sparkles className="w-5 h-5 text-purple-400" />
            Professional Brain — Neural Signature
          </h2>
          <p className="text-xs text-zinc-500 mb-6">
            Your unique interview "fingerprint" — watch it evolve with practice
          </p>
          {}
          <div className="relative w-full h-64 flex items-center justify-center">
            {}
            <motion.div
              animate={{
                scale: [1, 1.1, 1],
                boxShadow: [
                  "0 0 20px rgba(59, 130, 246, 0.3)",
                  "0 0 40px rgba(59, 130, 246, 0.5)",
                  "0 0 20px rgba(59, 130, 246, 0.3)",
                ],
              }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              className="absolute w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center z-10"
            >
              <span className="text-white text-lg font-bold">
                {overallScore.toFixed(0)}
              </span>
            </motion.div>
            {}
            {DIMENSIONS.map((dim, i) => {
              const angle = (i / DIMENSIONS.length) * Math.PI * 2 - Math.PI / 2;
              const radius = 110;
              const x = Math.cos(angle) * radius;
              const y = Math.sin(angle) * radius;
              const score = dimensionScores[dim.key] || 0;
              const size = 28 + (score / 100) * 16;
              const Icon = dim.icon;
              return (
                <motion.div
                  key={dim.key}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{
                    opacity: 1,
                    scale: 1,
                    x: x,
                    y: y,
                  }}
                  transition={{ delay: 0.1 + i * 0.08, duration: 0.5 }}
                  className="absolute flex flex-col items-center gap-1"
                  style={{ zIndex: 5 }}
                >
                  {}
                  <svg
                    className="absolute pointer-events-none"
                    style={{
                      width: Math.abs(x) + 20,
                      height: Math.abs(y) + 20,
                      left: x > 0 ? -x : 0,
                      top: y > 0 ? -y : 0,
                    }}
                  />
                  <motion.div
                    animate={{
                      scale: [1, 1.05, 1],
                    }}
                    transition={{
                      duration: 2 + Math.random() * 2,
                      repeat: Infinity,
                      delay: i * 0.3,
                    }}
                    className="rounded-full flex items-center justify-center border border-white/10"
                    style={{
                      width: size,
                      height: size,
                      background: `${dim.color}20`,
                      boxShadow: `0 0 ${score / 5}px ${dim.color}40`,
                    }}
                  >
                    <Icon
                      className="w-3.5 h-3.5"
                      style={{ color: dim.color }}
                    />
                  </motion.div>
                  <span className="text-[9px] text-zinc-500 font-medium whitespace-nowrap">
                    {dim.shortLabel}
                  </span>
                </motion.div>
              );
            })}
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
