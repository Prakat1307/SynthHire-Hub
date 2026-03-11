"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import api from "@/src/lib/api";
import { motion } from "framer-motion";
import CyberButton from "@/components/ui/CyberButton";
import GlassCard from "@/components/ui/GlassCard";
import { UserCircle, Building2, BrainCircuit, Target, Zap } from "lucide-react";
import Link from "next/link";
const { apiClient } = api;
export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, user } = useAuthStore();
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      apiClient
        .get("/onboarding/status")
        .then((res: { data: { onboarding_completed: boolean } }) => {
          if (!res.data.onboarding_completed) {
            router.push("/onboarding");
          } else if (
            user?.account_type === "company" ||
            user?.role === "Recruiter"
          ) {
            router.push("/company/dashboard");
          } else {
            router.push("/dashboard");
          }
        })
        .catch(() => {
          if (user?.account_type === "company" || user?.role === "Recruiter") {
            router.push("/company/dashboard");
          } else {
            router.push("/dashboard");
          }
        });
    }
  }, [isAuthenticated, isLoading, router, user]);
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-white">
        <div className="animate-spin w-10 h-10 border-4 border-blue-500 rounded-full border-t-transparent"></div>
      </div>
    );
  }
  return (
    <div className="min-h-screen flex flex-col pt-8 px-4 relative">
      { }
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-purple-500/8 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-cyan-500/8 rounded-full blur-[120px] pointer-events-none"></div>
      <main className="flex-1 flex flex-col items-center max-w-6xl mx-auto w-full z-10">
        { }
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mt-12 mb-16 space-y-6 max-w-3xl"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm text-zinc-300 mb-4 hover:bg-white/10 transition-colors cursor-pointer">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
            Introducing SynthHire v2.0
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight leading-tight">
            Master Your Next <br />
            <span className="text-gradient-purple">Tech Interview</span>
          </h1>
          <p className="text-lg md:text-xl text-[#94A3B8]">
            SynthHire uses state-of-the-art AI to simulate real-world
            interviews, assess your skills across 10 dimensions, and connect top
            talent with forward-thinking companies.
          </p>
        </motion.div>
        { }
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl"
        >
          { }
          <GlassCard className="p-8 flex flex-col items-center text-center group hover:-translate-y-2 transition-transform duration-500">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-blue-500/10 text-blue-400 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <UserCircle size={32} />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              For Candidates
            </h2>
            <p className="text-zinc-400 mb-8 flex-1">
              Practice with AI personas, get detailed multidimensional feedback,
              and land your ideal engineering role.
            </p>
            <Link href="/login" className="w-full">
              <CyberButton variant="primary" className="w-full">
                Start Practicing
              </CyberButton>
            </Link>
          </GlassCard>
          { }
          <GlassCard className="p-8 flex flex-col items-center text-center group hover:-translate-y-2 transition-transform duration-500">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-violet-500/10 text-violet-400 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Building2 size={32} />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              For Companies
            </h2>
            <p className="text-zinc-400 mb-8 flex-1">
              Streamline your technical hiring. Screen candidates automatically
              with unbiased, comprehensive AI assessments.
            </p>
            <div className="w-full cursor-not-allowed">
              <CyberButton variant="secondary" className="w-full opacity-50 pointer-events-none">
                Coming Soon
              </CyberButton>
            </div>
          </GlassCard>
        </motion.div>
        { }
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="mt-24 w-full grid grid-cols-1 md:grid-cols-3 gap-6 mb-20"
        >
          <div className="text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-zinc-800 flex items-center justify-center text-blue-400 border border-white/5">
              <BrainCircuit size={24} />
            </div>
            <h3 className="text-xl font-semibold text-white">Adaptive AI</h3>
            <p className="text-sm text-zinc-500">
              Our interviewers dynamically adapt to your responses, pushing your
              limits just like a real engineering manager.
            </p>
          </div>
          <div className="text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-zinc-800 flex items-center justify-center text-violet-400 border border-white/5">
              <Target size={24} />
            </div>
            <h3 className="text-xl font-semibold text-white">10-Dim Scoring</h3>
            <p className="text-sm text-[#64748B]">
              We evaluate communication, system design, coding, cultural fit,
              and more for a truly holistic skill profile.
            </p>
          </div>
          <div className="text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-zinc-800 flex items-center justify-center text-emerald-400 border border-white/5">
              <Zap size={24} />
            </div>
            <h3 className="text-xl font-semibold text-white">
              Instant Feedback
            </h3>
            <p className="text-sm text-zinc-500">
              Stop waiting weeks for recruiter feedback. Get an actionable
              performance report seconds after your interview ends.
            </p>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
