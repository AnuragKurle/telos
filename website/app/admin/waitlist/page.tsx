"use client";

import { useState, useEffect } from "react";
import {
  fetchWaitlist,
  sendBatchEmail,
  updateWaitlistStatus,
  fetchEmailPreviewHTML,
  type WaitlistEntry,
} from "@/lib/admin-api";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-amber-900/30 text-amber-400 border-amber-800/50",
  invited: "bg-blue-900/30 text-blue-400 border-blue-800/50",
  activated: "bg-emerald-900/30 text-emerald-400 border-emerald-800/50",
  active: "bg-green-900/30 text-green-400 border-green-800/50",
  churned: "bg-red-900/30 text-red-400 border-red-800/50",
};

function StatusBadge({ status }: { status: string }) {
  const cls = STATUS_COLORS[status] || "bg-neutral-800 text-neutral-400 border-neutral-700";
  return (
    <span className={`inline-block px-2 py-0.5 text-xs rounded border font-mono ${cls}`}>
      {status}
    </span>
  );
}

export default function WaitlistPage() {
  const [entries, setEntries] = useState<WaitlistEntry[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [filterStatus, setFilterStatus] = useState("");
  const [sending, setSending] = useState(false);
  const [campaignName, setCampaignName] = useState("");
  const [template, setTemplate] = useState<"invitation" | "reminder" | "referral_nudge">("invitation");
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [filterStatus]);

  async function loadData() {
    try {
      setLoading(true);
      const data = await fetchWaitlist(filterStatus ? { status: filterStatus } : undefined);
      setEntries(data.entries);
      setStats(data.stats);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function toggleSelect(email: string) {
    const next = new Set(selected);
    if (next.has(email)) next.delete(email);
    else next.add(email);
    setSelected(next);
  }

  function selectAll() {
    if (selected.size === entries.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(entries.map((e) => e.email)));
    }
  }

  function selectByStatus(status: string) {
    setSelected(new Set(entries.filter((e) => e.status === status).map((e) => e.email)));
  }

  async function handleSendBatch() {
    if (selected.size === 0) return;
    if (!campaignName.trim()) {
      alert("Please enter a campaign name");
      return;
    }

    const confirmed = confirm(
      `Send ${template} emails to ${selected.size} recipients?\n\nCampaign: ${campaignName}`
    );
    if (!confirmed) return;

    setSending(true);
    try {
      const result = await sendBatchEmail({
        emails: Array.from(selected),
        template,
        campaignName: campaignName.trim(),
      });

      const failedDetails = result.results
        ?.filter((r: any) => !r.success)
        .map((r: any) => `  • ${r.email}: ${r.error || "Unknown error"}`)
        .join("\n");
      
      alert(
        `Campaign complete!\n\nSent: ${result.sentCount}/${result.totalEmails}\nFailed: ${result.failedCount}\nDuration: ${Math.round(result.durationMs / 1000)}s${failedDetails ? `\n\nFailed details:\n${failedDetails}` : ""}`
      );
      setSelected(new Set());
      setCampaignName("");
      loadData();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setSending(false);
    }
  }

  async function handlePreview() {
    setPreviewLoading(true);
    try {
      const html = await fetchEmailPreviewHTML(template);
      const blob = new Blob([html], { type: "text/html; charset=utf-8" });
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
      // Revoke after a short delay so the tab can load
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    } catch (err: any) {
      alert(`Preview error: ${err.message}`);
    } finally {
      setPreviewLoading(false);
    }
  }

  if (loading) {
    return <div className="text-neutral-500 font-mono text-sm animate-pulse">Loading waitlist...</div>;
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
          <h1 className="text-2xl font-bold">Waitlist Management</h1>
          <p className="text-neutral-500 text-sm mt-1">
            {stats?.total || 0} total entries
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 text-sm bg-neutral-800 hover:bg-neutral-700 rounded-md transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Status Filter */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-neutral-500 font-mono uppercase">Filter:</span>
        {["", "pending", "invited", "activated", "active", "churned"].map((s) => (
          <button
            key={s}
            onClick={() => setFilterStatus(s)}
            className={`px-3 py-1 text-xs rounded-md transition-colors ${
              filterStatus === s
                ? "bg-emerald-600 text-white"
                : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700"
            }`}
          >
            {s || "All"} {s && stats ? `(${stats[s] || 0})` : ""}
          </button>
        ))}
      </div>

      {/* Batch Actions */}
      {selected.size > 0 && (
        <div className="bg-neutral-900 border border-emerald-900/30 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-4">
            <span className="text-sm text-emerald-400 font-mono">
              {selected.size} selected
            </span>
            <button
              onClick={() => setSelected(new Set())}
              className="text-xs text-neutral-500 hover:text-white"
            >
              Clear
            </button>
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Campaign Name</label>
              <input
                value={campaignName}
                onChange={(e) => setCampaignName(e.target.value)}
                placeholder="Batch 1 - Early Adopters"
                className="px-3 py-2 bg-neutral-800 border border-neutral-700 rounded text-sm text-white placeholder:text-neutral-600 w-64"
              />
            </div>
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Template</label>
              <select
                value={template}
                onChange={(e) => setTemplate(e.target.value as any)}
                className="px-3 py-2 bg-neutral-800 border border-neutral-700 rounded text-sm text-white"
              >
                <option value="invitation">Invitation</option>
                <option value="reminder">Reminder</option>
                <option value="referral_nudge">Referral Nudge</option>
              </select>
            </div>
            <button
              onClick={handlePreview}
              disabled={previewLoading}
              className="px-4 py-2 bg-neutral-700 hover:bg-neutral-600 disabled:opacity-50 text-white text-sm rounded-md transition-colors"
            >
              {previewLoading ? "Loading..." : "Preview Email"}
            </button>
            <button
              onClick={handleSendBatch}
              disabled={sending || !campaignName.trim()}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-md transition-colors"
            >
              {sending ? "Sending..." : `Send ${template} to ${selected.size}`}
            </button>
          </div>
        </div>
      )}

      {/* Quick Select */}
      <div className="flex gap-2">
        <button onClick={selectAll} className="text-xs text-neutral-500 hover:text-white">
          {selected.size === entries.length ? "Deselect All" : "Select All"}
        </button>
        <span className="text-neutral-700">|</span>
        <button
          onClick={() => selectByStatus("pending")}
          className="text-xs text-amber-500 hover:text-amber-300"
        >
          Select Pending
        </button>
        <button
          onClick={() => selectByStatus("invited")}
          className="text-xs text-blue-500 hover:text-blue-300"
        >
          Select Invited
        </button>
      </div>

      {/* Table */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 text-neutral-500 text-xs uppercase">
              <th className="text-left px-4 py-3 w-8">
                <input
                  type="checkbox"
                  checked={selected.size === entries.length && entries.length > 0}
                  onChange={selectAll}
                  className="accent-emerald-500"
                />
              </th>
              <th className="text-left px-4 py-3 font-medium">Email</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium">Batch</th>
              <th className="text-left px-4 py-3 font-medium">Signed Up</th>
              <th className="text-left px-4 py-3 font-medium">Invited</th>
              <th className="text-left px-4 py-3 font-medium">Activated</th>
              <th className="text-left px-4 py-3 font-medium">Source</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr
                key={entry.email}
                className={`border-b border-neutral-800/50 last:border-0 hover:bg-neutral-800/30 cursor-pointer ${
                  selected.has(entry.email) ? "bg-emerald-950/20" : ""
                }`}
                onClick={() => toggleSelect(entry.email)}
              >
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selected.has(entry.email)}
                    onChange={() => toggleSelect(entry.email)}
                    className="accent-emerald-500"
                    onClick={(e) => e.stopPropagation()}
                  />
                </td>
                <td className="px-4 py-3 font-mono text-neutral-300">{entry.email}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={entry.status} />
                </td>
                <td className="px-4 py-3 text-neutral-500 font-mono">
                  {entry.batch || "—"}
                </td>
                <td className="px-4 py-3 text-neutral-500 text-xs">
                  {entry.timestamp ? new Date(entry.timestamp).toLocaleDateString() : "—"}
                </td>
                <td className="px-4 py-3 text-neutral-500 text-xs">
                  {entry.invitedAt ? new Date(entry.invitedAt).toLocaleDateString() : "—"}
                </td>
                <td className="px-4 py-3 text-neutral-500 text-xs">
                  {entry.activatedAt ? new Date(entry.activatedAt).toLocaleDateString() : "—"}
                </td>
                <td className="px-4 py-3 text-neutral-600 text-xs">{entry.source || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {entries.length === 0 && (
          <div className="text-center py-12 text-neutral-600 text-sm">
            No entries found{filterStatus ? ` with status "${filterStatus}"` : ""}
          </div>
        )}
      </div>
    </div>
  );
}
