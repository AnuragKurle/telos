"use client";

import { useState, useEffect, createContext, useContext } from "react";
import {
  getAuth,
  signInWithEmailAndPassword,
  onAuthStateChanged,
  signOut,
  type User,
} from "firebase/auth";
import { app } from "@/lib/firebase";
import { verifyAdminAccess } from "@/lib/admin-api";
import Link from "next/link";
import { usePathname } from "next/navigation";

const AuthContext = createContext<{ user: User | null; loading: boolean }>({
  user: null,
  loading: true,
});

export function useAdminAuth() {
  return useContext(AuthContext);
}

const NAV_ITEMS = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/waitlist", label: "Waitlist" },
  { href: "/admin/campaigns", label: "Campaigns" },
  { href: "/admin/users", label: "Users" },
  { href: "/admin/referrals", label: "Referrals" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminCheckDone, setAdminCheckDone] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [signingIn, setSigningIn] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const auth = getAuth(app);
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u);
      setLoading(false);
      // Reset admin state on auth change
      if (!u) {
        setIsAdmin(false);
        setAdminCheckDone(false);
      }
    });
    return unsub;
  }, []);

  // Verify admin access on the backend after authentication
  useEffect(() => {
    if (user && !adminCheckDone) {
      verifyAdminAccess().then((result) => {
        setIsAdmin(result);
        setAdminCheckDone(true);
      });
    }
  }, [user, adminCheckDone]);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSigningIn(true);
    try {
      const auth = getAuth(app);
      await signInWithEmailAndPassword(auth, email, password);
    } catch (err: any) {
      setError(err.message || "Sign in failed");
    } finally {
      setSigningIn(false);
    }
  };

  const handleSignOut = async () => {
    const auth = getAuth(app);
    await signOut(auth);
  };

  if (loading || (user && !adminCheckDone)) {
    return (
      <div className="min-h-screen bg-neutral-950 flex items-center justify-center">
        <div className="text-neutral-400 font-mono text-sm animate-pulse">Loading...</div>
      </div>
    );
  }

  // Authenticated but not admin - show access denied
  if (user && adminCheckDone && !isAdmin) {
    return (
      <div className="min-h-screen bg-neutral-950 flex items-center justify-center px-4">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-bold text-white font-mono">Access Denied</h1>
          <p className="text-neutral-500 text-sm">You do not have admin privileges.</p>
          <button
            onClick={handleSignOut}
            className="px-6 py-2 text-sm bg-neutral-800 hover:bg-neutral-700 text-white rounded-md transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-neutral-950 flex items-center justify-center px-4">
        <form onSubmit={handleSignIn} className="w-full max-w-sm space-y-4">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-white font-mono">
              <span className="text-emerald-500">telos</span> admin
            </h1>
            <p className="text-neutral-500 text-sm mt-2">Sign in with your admin account</p>
          </div>

          {error && (
            <div className="text-xs text-red-400 bg-red-950/30 border border-red-900/50 rounded px-3 py-2 font-mono">
              {error}
            </div>
          )}

          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@telos.dev"
            required
            className="w-full px-4 py-3 bg-neutral-900 border border-neutral-800 rounded-md text-white placeholder:text-neutral-600 focus:outline-none focus:border-emerald-500 font-mono text-sm"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            required
            className="w-full px-4 py-3 bg-neutral-900 border border-neutral-800 rounded-md text-white placeholder:text-neutral-600 focus:outline-none focus:border-emerald-500 font-mono text-sm"
          />
          <button
            type="submit"
            disabled={signingIn}
            className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-md transition-colors text-sm"
          >
            {signingIn ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, loading }}>
      <div className="min-h-screen bg-neutral-950 text-white">
        {/* Top Nav */}
        <header className="border-b border-neutral-800 bg-neutral-950/90 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
            <div className="flex items-center gap-6">
              <Link href="/admin" className="font-mono font-bold text-lg">
                <span className="text-emerald-500">telos</span>
                <span className="text-neutral-500 text-sm ml-1.5">admin</span>
              </Link>

              <nav className="hidden md:flex items-center gap-1">
                {NAV_ITEMS.map((item) => {
                  const isActive =
                    item.href === "/admin"
                      ? pathname === "/admin"
                      : pathname.startsWith(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`px-3 py-1.5 rounded text-sm transition-colors ${
                        isActive
                          ? "bg-neutral-800 text-white"
                          : "text-neutral-400 hover:text-white hover:bg-neutral-900"
                      }`}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-neutral-500 font-mono hidden sm:block">
                {user.email}
              </span>
              <button
                onClick={handleSignOut}
                className="text-xs text-neutral-500 hover:text-white transition-colors"
              >
                Sign out
              </button>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
      </div>
    </AuthContext.Provider>
  );
}
