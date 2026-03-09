"use client";
import {
  LayoutDashboard,
  Users,
  Briefcase,
  Settings,
  LogOut,
  Menu,
  X,
  Building2,
  BarChart3,
} from "lucide-react";
import { useState } from "react";
import clsx from "clsx";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "@/lib/stores/authStore";
import { useRouter, usePathname } from "next/navigation";
const companyNavItems = [
  { name: "Dashboard", href: "/company/dashboard", icon: LayoutDashboard },
  { name: "Roles & Templates", href: "/company/roles", icon: Briefcase },
  { name: "Candidates", href: "/company/candidates", icon: Users },
  { name: "Analytics", href: "/company/analytics", icon: BarChart3 },
  { name: "Settings", href: "/company/settings", icon: Settings },
];
export default function CompanyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { logout, user } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const handleLogout = () => {
    logout();
    router.push("/login");
  };
  return (
    <div className="min-h-screen flex flex-col md:flex-row overflow-hidden font-sans">
      {}
      <div className="md:hidden flex items-center justify-between p-4 bg-zinc-900 border-b border-white/5 z-50">
        <div className="flex items-center gap-2">
          <Building2 className="w-6 h-6 text-violet-500" />
          <span className="font-bold text-lg text-white tracking-widest">
            SYNTHHIRE <span className="text-violet-500">B2B</span>
          </span>
        </div>
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="p-2 text-zinc-400 hover:text-white transition-colors"
        >
          {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>
      {}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}
      </AnimatePresence>
      {}
      <motion.div
        className={clsx(
          "fixed md:static inset-y-0 left-0 w-64 bg-zinc-900/80 backdrop-blur-xl border-r border-white/5",
          "flex flex-col z-50 transform md:transform-none transition-transform duration-300 ease-in-out",
          isSidebarOpen
            ? "translate-x-0"
            : "-translate-x-full md:translate-x-0",
        )}
      >
        <div className="hidden md:flex p-6 items-center gap-3">
          <div className="p-2 bg-violet-500/10 rounded-xl border border-violet-500/20 shadow-inner">
            <Building2 className="w-6 h-6 text-violet-400" />
          </div>
          <span className="font-bold text-xl text-white tracking-wider">
            SYNTH<span className="text-violet-500 font-light">HIRE</span>
          </span>
        </div>
        <div className="px-6 pb-4">
          <div className="px-3 py-1.5 rounded-md bg-zinc-800/50 border border-white/5 text-xs font-semibold text-zinc-300 flex items-center justify-center tracking-widest uppercase shadow-inner">
            Enterprise Portal
          </div>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {companyNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setIsSidebarOpen(false)}
                className={clsx(
                  "flex items-center gap-3 px-4 py-3 rounded-xl transition-all group relative overflow-hidden",
                  isActive
                    ? "text-white bg-white/5 border border-white/10 shadow-[0_0_15px_rgba(139,92,246,0.15)]"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-white/5",
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="company-active-nav"
                    className="absolute left-0 top-0 bottom-0 w-1 bg-violet-500"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.2 }}
                  />
                )}
                <Icon
                  size={20}
                  className={clsx(
                    "transition-colors",
                    isActive
                      ? "text-violet-400"
                      : "group-hover:text-violet-400/70",
                  )}
                />
                <span
                  className={clsx(
                    "font-medium",
                    isActive ? "tracking-wide" : "",
                  )}
                >
                  {item.name}
                </span>
              </Link>
            );
          })}
        </nav>
        <div className="p-4 mt-auto border-t border-white/5">
          <div className="px-4 py-3 mb-2 rounded-xl bg-zinc-800/20 border border-white/5 font-medium text-zinc-300">
            <p className="text-xs text-zinc-500 mb-1 font-semibold uppercase tracking-wider">
              Workspace
            </p>
            <p className="text-sm truncate font-semibold text-white">
              {user?.company_id ? "Acme Corp" : "Loading..."}
            </p>{" "}
            {}
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center w-full gap-3 px-4 py-3 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-xl transition-colors border border-transparent hover:border-rose-500/20"
          >
            <LogOut size={20} />
            <span className="font-semibold">Logout</span>
          </button>
        </div>
      </motion.div>
      {}
      <main className="flex-1 overflow-x-hidden overflow-y-auto relative h-screen">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-500/10 blur-[120px] pointer-events-none" />
        <div className="absolute top-[30%] right-[-10%] w-[40%] h-[40%] rounded-full bg-violet-500/10 blur-[100px] pointer-events-none" />
        <div className="relative z-10">{children}</div>
      </main>
    </div>
  );
}
