"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/authStore";
import api from "@/src/lib/api";
import GlassCard from "@/components/ui/GlassCard";
import CyberButton from "@/components/ui/CyberButton";
import {
  Settings,
  Users,
  Link2,
  Key,
  Shield,
  AlertTriangle,
} from "lucide-react";
import toast, { Toaster } from "react-hot-toast";
const { apiClient, getServiceUrl } = api;
export default function CompanySettingsPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [atsIntegrations, setAtsIntegrations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!isAuthenticated) return;
    const companyId =
      user?.company_id || "00000000-0000-0000-0000-000000000001";
    fetchATS(companyId);
  }, [isAuthenticated, user]);
  const fetchATS = async (companyId: string) => {
    try {
      const res = await apiClient.get(
        `${getServiceUrl("company")}/companies/${companyId}/ats`,
      );
      setAtsIntegrations(res.data);
    } catch (err: any) {
      if (err.response?.status !== 404) {
      }
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <Toaster position="top-right" />
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
          <Settings className="text-slate-400" />
          Company Settings
        </h1>
        <p className="text-slate-400 mt-1">
          Manage your team, billing, and ATS integrations.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {}
        <div className="space-y-2">
          <button className="w-full text-left px-4 py-3 rounded-lg bg-violet-500/20 text-violet-400 border border-violet-500/30 font-medium">
            ATS Integrations
          </button>
          <button className="w-full text-left px-4 py-3 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors font-medium">
            Team Members
          </button>
          <button className="w-full text-left px-4 py-3 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors font-medium">
            Billing & Quotas
          </button>
          <button className="w-full text-left px-4 py-3 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors font-medium">
            Assessment Branding
          </button>
        </div>
        {}
        <div className="md:col-span-2 space-y-6">
          <GlassCard className="p-6">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-xl font-bold text-white">
                  ATS Integrations
                </h2>
                <p className="text-sm text-slate-400">
                  Sync candidates directly to your Applicant Tracking System.
                </p>
              </div>
              <CyberButton>Add Integration</CyberButton>
            </div>
            {atsIntegrations.length === 0 ? (
              <div className="p-8 bg-slate-900/50 rounded-xl border border-slate-800 text-center">
                <Link2 className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <h3 className="text-white font-medium mb-1">
                  No integrations active
                </h3>
                <p className="text-sm text-slate-400">
                  Connect Greenhouse, Lever, Workday, or configure a custom
                  webhook.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {atsIntegrations.map((ats) => (
                  <div
                    key={ats.id}
                    className="p-4 bg-slate-900/50 rounded-xl border border-slate-800 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center">
                        <span className="font-bold text-white capitalize">
                          {ats.provider.substring(0, 1)}
                        </span>
                      </div>
                      <div>
                        <h4 className="font-bold text-white capitalize">
                          {ats.provider}
                        </h4>
                        <p className="text-xs text-slate-400">
                          Status:{" "}
                          <span className="text-emerald-400">
                            Active • Last sync:{" "}
                            {ats.last_sync_at
                              ? new Date(ats.last_sync_at).toLocaleTimeString()
                              : "Never"}
                          </span>
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button className="p-2 text-slate-400 hover:text-white transition-colors">
                        <Settings size={18} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
          <GlassCard className="p-6">
            <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
              <Key className="w-5 h-5 text-violet-400" /> API Access
            </h2>
            <p className="text-sm text-slate-400 mb-6">
              Create API keys for custom backend integrations.
            </p>
            <div className="p-4 bg-slate-900 rounded-lg border border-slate-800 flex justify-between items-center bg-[url('/grid-pattern.svg')]">
              <div>
                <p className="font-mono text-sm text-slate-300">
                  pk_live_*************************
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Created on Oct 12, 2026
                </p>
              </div>
              <button className="text-sm font-medium text-rose-400 hover:text-rose-300 px-3 py-1.5 rounded-lg hover:bg-rose-500/10 transition-colors">
                Revoke
              </button>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
