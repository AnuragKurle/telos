"use client";

import { useState, useEffect } from "react";
import { fetchUsers, type AdminUser } from "@/lib/admin-api";

const STATUS_COLORS: Record<string, string> = {
  trial: "bg-blue-900/30 text-blue-400 border-blue-800/50",
  pro: "bg-emerald-900/30 text-emerald-400 border-emerald-800/50",
  expired: "bg-red-900/30 text-red-400 border-red-800/50",
};

export default function UsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  useEffect(() => {
    loadData();
  }, [filterStatus]);

  async function loadData() {
    try {
      setLoading(true);
      const data = await fetchUsers(filterStatus ? { status: filterStatus } : undefined);
      setUsers(data.users);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function timeAgo(dateStr: string | null): string {
    if (!dateStr) return "never";
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  if (loading) {
    return <div className="text-neutral-500 font-mono text-sm animate-pulse">Loading users...</div>;
  }

  if (error) {
    return (
      <div className="text-red-400 font-mono text-sm bg-red-950/20 border border-red-900/30 rounded p-4">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Users</h1>
          <p className="text-neutral-500 text-sm mt-1">{users.length} users</p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 text-sm bg-neutral-800 hover:bg-neutral-700 rounded-md transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-neutral-500 font-mono uppercase">Filter:</span>
        {["", "trial", "pro", "expired"].map((s) => (
          <button
            key={s}
            onClick={() => setFilterStatus(s)}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              filterStatus === s
                ? "bg-emerald-600 text-white"
                : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700"
            }`}
          >
            {s || "All"}
          </button>
        ))}
      </div>

      <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 text-neutral-500 text-xs uppercase">
              <th className="text-left px-4 py-3 font-medium">Email</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium">Mode</th>
              <th className="text-left px-4 py-3 font-medium">Signed Up</th>
              <th className="text-left px-4 py-3 font-medium">Last Active</th>
              <th className="text-left px-4 py-3 font-medium">Trial Ends</th>
              <th className="text-left px-4 py-3 font-medium">Referral Code</th>
              <th className="text-left px-4 py-3 font-medium">Referrals</th>
              <th className="text-left px-4 py-3 font-medium">Credits</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.uid} className="border-b border-neutral-800/50 last:border-0 hover:bg-neutral-800/30">
                <td className="px-4 py-3 font-mono text-neutral-300 text-xs">{u.email || "—"}</td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-0.5 text-xs rounded border font-mono ${
                      STATUS_COLORS[u.accessStatus] || "bg-neutral-800 text-neutral-400 border-neutral-700"
                    }`}
                  >
                    {u.accessStatus}
                  </span>
                </td>
                <td className="px-4 py-3 text-neutral-500 text-xs">{u.mode}</td>
                <td className="px-4 py-3 text-neutral-500 text-xs">
                  {u.createdAt ? new Date(u.createdAt).toLocaleDateString() : "—"}
                </td>
                <td className="px-4 py-3 text-neutral-500 text-xs">{timeAgo(u.lastActiveAt)}</td>
                <td className="px-4 py-3 text-neutral-500 text-xs">
                  {u.trialEndDate ? new Date(u.trialEndDate).toLocaleDateString() : "—"}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-emerald-400">
                  {u.referralCode || "—"}
                </td>
                <td className="px-4 py-3 font-mono text-purple-400">{u.referralCount || 0}</td>
                <td className="px-4 py-3 font-mono text-amber-400">
                  {u.proCreditsEarned ? `${u.proCreditsEarned} mo` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {users.length === 0 && (
          <div className="text-center py-12 text-neutral-600 text-sm">No users found</div>
        )}
      </div>
    </div>
  );
}
