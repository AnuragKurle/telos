"use client";

import { useState, useEffect } from "react";
import { fetchReferrals, type ReferralsResponse } from "@/lib/admin-api";

export default function ReferralsPage() {
  const [data, setData] = useState<ReferralsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const res = await fetchReferrals();
      setData(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="text-neutral-500 font-mono text-sm animate-pulse">Loading referrals...</div>;
  }

  if (error) {
    return (
      <div className="text-red-400 font-mono text-sm bg-red-950/20 border border-red-900/30 rounded p-4">
        Error: {error}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Referral Program</h1>
          <p className="text-neutral-500 text-sm mt-1">Track referral performance and credits</p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 text-sm bg-neutral-800 hover:bg-neutral-700 rounded-md transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-5">
          <p className="text-xs text-neutral-500 uppercase tracking-wider font-mono mb-2">
            Total Referrals
          </p>
          <p className="text-3xl font-bold font-mono text-purple-400">{data.totalReferrals}</p>
        </div>
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-5">
          <p className="text-xs text-neutral-500 uppercase tracking-wider font-mono mb-2">
            Activated
          </p>
          <p className="text-3xl font-bold font-mono text-emerald-400">
            {data.activatedReferrals}
          </p>
          <p className="text-xs text-neutral-500 mt-1">
            {data.totalReferrals > 0
              ? `${Math.round((data.activatedReferrals / data.totalReferrals) * 100)}% conversion`
              : "—"}
          </p>
        </div>
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-5">
          <p className="text-xs text-neutral-500 uppercase tracking-wider font-mono mb-2">
            Pro Credits Awarded
          </p>
          <p className="text-3xl font-bold font-mono text-amber-400">{data.creditsAwarded} mo</p>
        </div>
      </div>

      {/* Top Referrers */}
      {data.topReferrers.length > 0 && (
        <section>
          <h2 className="text-sm font-mono text-neutral-500 uppercase tracking-wider mb-4">
            Top Referrers
          </h2>
          <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-800 text-neutral-500 text-xs uppercase">
                  <th className="text-left px-4 py-3 font-medium">#</th>
                  <th className="text-left px-4 py-3 font-medium">Email</th>
                  <th className="text-left px-4 py-3 font-medium">Referrals</th>
                </tr>
              </thead>
              <tbody>
                {data.topReferrers.map((r, i) => (
                  <tr key={r.email} className="border-b border-neutral-800/50 last:border-0">
                    <td className="px-4 py-3 text-neutral-500 font-mono">{i + 1}</td>
                    <td className="px-4 py-3 font-mono text-neutral-300">{r.email}</td>
                    <td className="px-4 py-3 font-mono text-purple-400">{r.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* All Referrals */}
      <section>
        <h2 className="text-sm font-mono text-neutral-500 uppercase tracking-wider mb-4">
          All Referrals
        </h2>
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800 text-neutral-500 text-xs uppercase">
                <th className="text-left px-4 py-3 font-medium">Referrer</th>
                <th className="text-left px-4 py-3 font-medium">Referee</th>
                <th className="text-left px-4 py-3 font-medium">Code</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-left px-4 py-3 font-medium">Credit</th>
                <th className="text-left px-4 py-3 font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {data.referrals.map((r) => (
                <tr key={r.id} className="border-b border-neutral-800/50 last:border-0">
                  <td className="px-4 py-3 font-mono text-neutral-300 text-xs">
                    {r.referrerEmail || "—"}
                  </td>
                  <td className="px-4 py-3 font-mono text-neutral-300 text-xs">
                    {r.refereeEmail || "—"}
                  </td>
                  <td className="px-4 py-3 font-mono text-emerald-400 text-xs">{r.referralCode}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 text-xs rounded border font-mono ${
                        r.status === "trial_active"
                          ? "bg-emerald-900/30 text-emerald-400 border-emerald-800/50"
                          : "bg-amber-900/30 text-amber-400 border-amber-800/50"
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {r.proCreditAwarded ? (
                      <span className="text-xs text-emerald-400">Awarded</span>
                    ) : (
                      <span className="text-xs text-neutral-600">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-neutral-500 text-xs">
                    {r.createdAt ? new Date(r.createdAt).toLocaleDateString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {data.referrals.length === 0 && (
            <div className="text-center py-12 text-neutral-600 text-sm">
              No referrals yet
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
