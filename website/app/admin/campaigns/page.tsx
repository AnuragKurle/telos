"use client";

import { useState, useEffect } from "react";
import { fetchCampaigns, type Campaign } from "@/lib/admin-api";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const data = await fetchCampaigns();
      setCampaigns(data.campaigns);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="text-neutral-500 font-mono text-sm animate-pulse">Loading campaigns...</div>;
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
          <h1 className="text-2xl font-bold">Email Campaigns</h1>
          <p className="text-neutral-500 text-sm mt-1">
            History of batch email sends. Create new campaigns from the{" "}
            <a href="/admin/waitlist" className="text-emerald-400 hover:underline">
              Waitlist page
            </a>
            .
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 text-sm bg-neutral-800 hover:bg-neutral-700 rounded-md transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 text-neutral-500 text-xs uppercase">
              <th className="text-left px-4 py-3 font-medium">Campaign</th>
              <th className="text-left px-4 py-3 font-medium">Template</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium">Sent</th>
              <th className="text-left px-4 py-3 font-medium">Failed</th>
              <th className="text-left px-4 py-3 font-medium">Duration</th>
              <th className="text-left px-4 py-3 font-medium">Created By</th>
              <th className="text-left px-4 py-3 font-medium">Date</th>
            </tr>
          </thead>
          <tbody>
            {campaigns.map((c) => (
              <tr key={c.id} className="border-b border-neutral-800/50 last:border-0">
                <td className="px-4 py-3 font-mono text-neutral-300">{c.name}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 text-xs rounded bg-neutral-800 text-neutral-400 border border-neutral-700 font-mono">
                    {c.template}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-0.5 text-xs rounded border font-mono ${
                      c.status === "sent"
                        ? "bg-emerald-900/30 text-emerald-400 border-emerald-800/50"
                        : c.status === "failed"
                          ? "bg-red-900/30 text-red-400 border-red-800/50"
                          : c.status === "sending"
                            ? "bg-blue-900/30 text-blue-400 border-blue-800/50"
                            : "bg-neutral-800 text-neutral-400 border-neutral-700"
                    }`}
                  >
                    {c.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-emerald-400 font-mono">
                  {c.sentCount}/{c.recipientCount}
                </td>
                <td className="px-4 py-3 font-mono text-red-400">
                  {c.failedCount > 0 ? c.failedCount : "—"}
                </td>
                <td className="px-4 py-3 text-neutral-500 font-mono">
                  {c.durationMs ? `${Math.round(c.durationMs / 1000)}s` : "—"}
                </td>
                <td className="px-4 py-3 text-neutral-500 text-xs">{c.createdBy}</td>
                <td className="px-4 py-3 text-neutral-500 text-xs">
                  {c.createdAt ? new Date(c.createdAt).toLocaleDateString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {campaigns.length === 0 && (
          <div className="text-center py-12 text-neutral-600 text-sm">
            No campaigns yet. Send your first batch from the Waitlist page.
          </div>
        )}
      </div>
    </div>
  );
}
