"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import toast, { Toaster } from "react-hot-toast";
import CyberButton from "@/components/ui/CyberButton";
import GlassCard from "@/components/ui/GlassCard";
import { motion } from "framer-motion";
import { Eye, EyeOff } from "lucide-react";
export default function LoginPage() {
  const router = useRouter();
  const { login, register, isAuthenticated, isLoading, error } = useAuthStore();
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isLoginMode) {
        await login(email, password);
        toast.success("Welcome back!");
      } else {
        await register(email, password, fullName);
        toast.success("Account created successfully!");
      }
    } catch (err: any) {
      let message = error || "Authentication failed";
      if (err?.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          message = detail
            .map((d: any) => `${d.loc.join(".")}: ${d.msg}`)
            .join(", ");
        } else if (typeof detail === "string") {
          message = detail;
        } else if (typeof detail === "object") {
          message = JSON.stringify(detail);
        }
      } else if (err?.response?.status >= 500) {
        message =
          "The server is starting up or temporarily unavailable. Please wait a moment and try again.";
      } else if (err?.code === "ERR_NETWORK") {
        message =
          "Cannot connect to the server. Please check your connection or wait for the server to start.";
      } else if (err?.message) {
        message = err.message;
      }
      toast.error(message);
    }
  };
  return (
    <div className="min-h-screen flex overflow-hidden relative">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#1e293b",
            color: "#fff",
            border: "1px solid rgba(255,255,255,0.1)",
          },
        }}
      />
      { }
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-cyber-teal-500/20 rounded-full blur-[128px] animate-pulse-slow"></div>
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-cyber-purple-500/20 rounded-full blur-[128px] animate-pulse-slow delay-1000"></div>
      </div>
      { }
      <motion.div
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8 }}
        className="hidden lg:flex w-1/2 relative items-center justify-center p-12 z-10"
      >
        <div className="max-w-xl space-y-8">
          <GlassCard className="inline-block p-4 bg-white/5">
            <div className="w-12 h-12 bg-gradient-to-br from-cyber-teal-500 to-cyber-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-cyber-teal-500/30">
              <span className="text-2xl font-bold text-white">SH</span>
            </div>
          </GlassCard>
          <h1 className="text-5xl font-bold tracking-tight">
            Master Your
            <br />
            <span className="text-gradient">Technical Interview</span>
          </h1>
          <p className="text-lg text-slate-400 leading-relaxed max-w-lg">
            Practice with AI-powered personas ranging from supportive mentors to
            tough tech leads. Get real-time feedback and detailed performance
            analytics.
          </p>
          <div className="flex gap-4 pt-4">
            <div className="flex -space-x-4">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="w-10 h-10 rounded-full border-2 border-cyber-slate-900 bg-cyber-slate-800 flex items-center justify-center text-xs font-medium text-slate-300"
                >
                  {String.fromCharCode(64 + i)}
                </div>
              ))}
            </div>
            <div className="flex items-center text-sm font-medium text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
              10k+ Developers Practicing
            </div>
          </div>
        </div>
      </motion.div>
      { }
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="w-full lg:w-1/2 flex items-center justify-center p-8 relative z-10"
      >
        <GlassCard className="max-w-md w-full p-8 space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-white mb-2">
              {isLoginMode ? "Welcome Back" : "Create Account"}
            </h2>
            <p className="text-slate-400">
              {isLoginMode
                ? "Enter your credentials to access your workspace"
                : "Start your journey to interview mastery today"}
            </p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-5">
            {!isLoginMode && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">
                  Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-4 py-3 glass-input focus:outline-none"
                  placeholder="John Doe"
                  required
                />
              </div>
            )}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 glass-input focus:outline-none"
                placeholder="name@company.com"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 glass-input focus:outline-none pr-12 text-left"
                  placeholder="••••••••"
                  minLength={8}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white hover:text-cyber-teal-400 transition-all z-50"
                  style={{ background: "transparent", border: "none" }}
                >
                  {showPassword ? (
                    <EyeOff size={20} className="drop-shadow-sm" />
                  ) : (
                    <Eye size={20} className="drop-shadow-sm" />
                  )}
                </button>
              </div>
            </div>
            <CyberButton
              type="submit"
              variant="primary"
              isLoading={isLoading}
              className="w-full justify-center"
            >
              {isLoginMode ? "Sign In" : "Create Account"}
            </CyberButton>
          </form>

          <p className="text-center text-sm text-slate-400 mt-6">
            {isLoginMode
              ? "Don't have an account?"
              : "Already have an account?"}{" "}
            <button
              onClick={() => setIsLoginMode(!isLoginMode)}
              className="font-medium text-cyber-teal-400 hover:text-cyber-teal-300 transition-colors"
            >
              {isLoginMode ? "Register now" : "Sign in"}
            </button>
          </p>
        </GlassCard>
      </motion.div>
    </div>
  );
}
