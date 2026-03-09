"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import api from "@/src/lib/api";
import { Trophy, Medal, Crown, Star, ArrowLeft } from "lucide-react";
import toast, { Toaster } from "react-hot-toast";
import GlassCard from "@/components/ui/GlassCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { motion } from "framer-motion";
const { apiClient, getServiceUrl } = api;
interface LeaderboardEntry {
  rank: number;
  user_id: string;
  name: string;
  avatar_url?: string;
  level: number;
  total_xp: number;
  streak: number;
}
export default function LeaderboardPage() {
  const router = useRouter();
  const { isAuthenticated, user, accessToken } = useAuthStore();
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    if (!isAuthenticated && !useAuthStore.getState().isLoading) {
      router.push("/login");
    } else if (isAuthenticated) {
      fetchLeaderboard();
    }
  }, [isAuthenticated, router]);
  const fetchLeaderboard = async () => {
    try {
      const analyticsUrl = getServiceUrl("analytics");
      const res = await apiClient
        .get(`${analyticsUrl}/leaderboard?limit=50`)
        .catch(() => ({ data: { leaderboard: [] } }));
      setLeaderboard(res.data.leaderboard || []);
      setIsLoading(false);
    } catch (error) {
      console.error("Leaderboard error:", error);
      toast.error("Failed to load the global leaderboard.");
      setIsLoading(false);
    }
  };
  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return (
          <Crown className="w-8 h-8 text-yellow-400 drop-shadow-[0_0_8px_rgba(250,204,21,0.8)]" />
        );
      case 2:
        return (
          <Medal className="w-7 h-7 text-slate-300 drop-shadow-[0_0_8px_rgba(203,213,225,0.6)]" />
        );
      case 3:
        return (
          <Medal className="w-7 h-7 text-amber-600 drop-shadow-[0_0_8px_rgba(217,119,6,0.5)]" />
        );
      default:
        return (
          <span className="font-bold text-slate-500 w-8 text-center">
            {rank}
          </span>
        );
    }
  };
  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 space-y-6">
        <Skeleton className="h-10 w-64 mb-8" />
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-20 w-full rounded-2xl" />
        ))}
      </div>
    );
  }
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.05 },
    },
  };
  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    show: { opacity: 1, x: 0 },
  };
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <Toaster position="top-right" />
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/dashboard")}
          className="p-2 bg-cyber-slate-800/50 hover:bg-cyber-slate-700 text-slate-300 rounded-full transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Trophy className="w-8 h-8 text-cyber-purple-400" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyber-purple-400 to-cyber-teal-400">
              Global Leaderboard
            </span>
          </h1>
          <p className="text-slate-400 mt-1">
            Top SynthHire candidates ranked by Experience Points (XP).
          </p>
        </div>
      </div>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="space-y-4"
      >
        {leaderboard.length === 0 ? (
          <GlassCard className="py-16 text-center">
            <Trophy className="w-12 h-12 text-slate-600 mx-auto mb-4 opacity-50" />
            <h3 className="text-xl text-slate-300 font-medium">
              The leaderboard is currently empty.
            </h3>
            <p className="text-slate-500 mt-2">
              Complete a practice interview to claim the #1 spot!
            </p>
          </GlassCard>
        ) : (
          leaderboard.map((entry, idx) => (
            <motion.div key={entry.user_id} variants={itemVariants}>
              <GlassCard
                className={`flex items-center justify-between p-4 sm:p-6 hover:bg-cyber-slate-800/80 transition-all ${entry.user_id === user?.id ? "border-cyber-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.2)]" : ""}`}
              >
                <div className="flex items-center gap-4 sm:gap-6">
                  <div className="flex items-center justify-center w-10">
                    {getRankIcon(entry.rank)}
                  </div>
                  <div className="relative">
                    {entry.avatar_url ? (
                      <img
                        src={entry.avatar_url}
                        alt={entry.name}
                        className="w-12 h-12 rounded-full border-2 border-slate-700 object-cover"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-cyber-slate-800 border-2 border-slate-700 flex items-center justify-center text-lg font-bold text-slate-300">
                        {entry.name[0]?.toUpperCase()}
                      </div>
                    )}
                    {entry.user_id === user?.id && (
                      <div className="absolute -bottom-1 -right-1 bg-cyber-purple-500 text-xs px-1.5 rounded text-white font-bold border border-slate-900">
                        YOU
                      </div>
                    )}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-200">
                      {entry.name}
                    </h3>
                    <div className="flex items-center gap-3 text-xs sm:text-sm mt-1">
                      <span className="flex items-center gap-1 text-cyber-purple-400 font-medium">
                        <Star className="w-3.5 h-3.5" /> Level {entry.level}
                      </span>
                      <span className="text-slate-500">•</span>
                      <span className="text-amber-400/80">
                        {entry.streak} Day Streak 🔥
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-slate-400">
                    {entry.total_xp.toLocaleString()}{" "}
                    <span className="text-sm font-medium text-slate-500">
                      XP
                    </span>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          ))
        )}
      </motion.div>
    </div>
  );
}
