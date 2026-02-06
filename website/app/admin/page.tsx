"use client";

import { useState, useEffect } from "react";
import { fetchStats, triggerDigest, type DashboardStats } from "@/lib/admin-api";

function StatCard({
  label,
  value,
  sub,
  color = "emerald",
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  const colorMap: Record<string, string> = {
    emerald: "text-emerald-400",
    blue: "text-blue-400",
    purple: "text-purple-400",
    amber: "text-amber-400",
    red: "text-red-400",
    neutral: "text-neutral-300",
  };

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-5">
      <p className="text-xs text-neutral-500 uppercase tracking-wider font-mono mb-2">{label}</p>
      <p className={`text-3xl font-bold font-mono ${colorMap[color] || colorMap.emerald}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-neutral-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [digestSending, setDigestSending] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    try {
      setLoading(true);
      const data = await fetchStats();
      setStats(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDigest() {
    setDigestSending(true);
    try {
      await triggerDigest();
      alert("Digest sent to Slack!");
    } catch (err: any) {
      alert(`Failed: ${err.message}`);
    } finally {
      setDigestSending(false);
    }
  }

  if (loading) {
    return <div className="text-neutral-500 font-mono text-sm animate-pulse">Loading stats...</div>;
  }

  if (error) {
    return (
      <div className="text-red-400 font-mono text-sm bg-red-950/20 border border-red-900/30 rounded p-4">
        Error: {error}
        <button onClick={loadStats} className="ml-4 text-red-300 underline">
          Retry
        </button>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Beta Dashboard</h1>
          <p className="text-neutral-500 text-sm mt-1">Overview of your beta launch metrics</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleDigest}
            disabled={digestSending}
            className="px-4 py-2 text-sm bg-neutral-800 hover:bg-neutral-700 disabled:opacity-50 rounded-md transition-colors"
          >
            {digestSending ? "Sending..." : "Send Slack Digest"}
          </button>
          <button
            onClick={loadStats}
            className="px-4 py-2 text-sm bg-neutral-800 hover:bg-neutral-700 rounded-md transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Waitlist Pipeline */}
      <section>
        <h2 className="text-sm font-mono text-neutral-500 uppercase tracking-wider mb-4">
          Waitlist Pipeline
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Signups" value={stats.waitlist.total} color="neutral" />
          <StatCard label="Pending" value={stats.waitlist.pending} color="amber" />
          <StatCard label="Invited" value={stats.waitlist.invited} color="blue" />
          <StatCard
            label="Activated"
            value={stats.waitlist.activated}
            color="emerald"
            sub={`${stats.activationRate}% activation rate`}
          />
        </div>
      </section>

      {/* Users */}
      <section>
        <h2 className="text-sm font-mono text-neutral-500 uppercase tracking-wider mb-4">Users</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard label="Total Users" value={stats.users.total} color="neutral" />
          <StatCard label="Trial" value={stats.users.trial} color="blue" />
          <StatCard label="Pro" value={stats.users.pro} color="emerald" />
          <StatCard label="Expired" value={stats.users.expired} color="red" />
          <StatCard label="Active (24h)" value={stats.users.activeToday} color="emerald" />
        </div>
      </section>

      {/* Referrals */}
      <section>
        <h2 className="text-sm font-mono text-neutral-500 uppercase tracking-wider mb-4">
          Referrals
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <StatCard label="Total Referrals" value={stats.referrals.totalReferrals} color="purple" />
          <StatCard
            label="Activated"
            value={stats.referrals.activatedReferrals}
            color="emerald"
          />
          <StatCard
            label="Pro Credits Awarded"
            value={`${stats.referrals.proCreditsAwarded} mo`}
            color="amber"
          />
        </div>
      </section>

      {/* Recent Campaigns */}
      {stats.recentCampaigns.length > 0 && (
        <section>
          <h2 className="text-sm font-mono text-neutral-500 uppercase tracking-wider mb-4">
            Recent Campaigns
          </h2>
          <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-800 text-neutral-500 text-xs uppercase">
                  <th className="text-left px-4 py-3 font-medium">Campaign</th>
                  <th className="text-left px-4 py-3 font-medium">Sent</th>
                  <th className="text-left px-4 py-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {stats.recentCampaigns.map((c) => (
                  <tr key={c.id} className="border-b border-neutral-800/50 last:border-0">
                    <td className="px-4 py-3 font-mono text-neutral-300">{c.name}</td>
                    <td className="px-4 py-3 text-emerald-400 font-mono">{c.sentCount}</td>
                    <td className="px-4 py-3 text-neutral-500">
                      {c.createdAt ? new Date(c.createdAt).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
