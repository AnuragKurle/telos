import Link from "next/link";
import { Terminal } from "lucide-react";

export default function PrivacyPolicy() {
    return (
        <main className="min-h-screen bg-terminal-black flex flex-col text-neutral-300">
            {/* Navigation / Header */}
            <header className="fixed top-0 w-full z-50 bg-terminal-black/80 backdrop-blur-md border-b border-terminal-border">
                <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2 text-white font-bold text-xl tracking-tight">
                        <Terminal className="w-6 h-6 text-terminal-green" />
                        <span>telos</span>
                    </Link>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 pt-32 pb-20 px-4">
                <div className="max-w-3xl mx-auto">
                    <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-terminal-green to-emerald-600 mb-2">
                        Privacy Guarantee
                    </h1>
                    <p className="text-xl text-neutral-400 mb-12">
                        The "Zen of Telos" is built on trust and transparency.
                    </p>

                    <div className="space-y-12">
                        <section>
                            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                                <span className="w-1 h-6 bg-terminal-green rounded-full"></span>
                                Local-First Data Storage
                            </h2>
                            <p className="text-neutral-400 leading-relaxed">
                                Your data belongs to you. Telos stores your activity logs, screenshots, and productivity metrics locally on your device using a secure SQLite database. We do not maintain a central database of your personal activity.
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                                <span className="w-1 h-6 bg-terminal-green rounded-full"></span>
                                No Images Sent to Backend
                            </h2>
                            <p className="text-neutral-400 leading-relaxed">
                                We understand that your screen content is private. Telos processes screenshots locally on your machine to generate metadata and insights. The actual image files never leave your device and are never uploaded to our servers.
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                                <span className="w-1 h-6 bg-terminal-green rounded-full"></span>
                                No Third-Party Tracking
                            </h2>
                            <p className="text-neutral-400 leading-relaxed">
                                We have zero interest in selling your data or tracking your behavior for advertising. Telos contains no third-party analytics pixels, trackers, or telemetry SDKs that monitor your usage habits.
                            </p>
                        </section>

                        <section>
                            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                                <span className="w-1 h-6 bg-terminal-green rounded-full"></span>
                                User Ownership
                            </h2>
                            <p className="text-neutral-400 leading-relaxed">
                                You have full control over your data. Because everything is stored locally, you can delete your history, export your database, or uninstall the application at any time without leaving a digital footprint on our end.
                            </p>
                        </section>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="border-t border-terminal-border bg-neutral-950 py-12 px-4">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-2 text-neutral-500">
                        <Terminal className="w-5 h-5" />
                        <span className="text-sm">© {new Date().getFullYear()} Telos. Know where your time goes.</span>
                    </div>

                    <div className="flex items-center gap-6 text-sm">
                        <Link href="/" className="text-neutral-500 hover:text-white transition-colors">
                            Home
                        </Link>
                    </div>
                </div>
            </footer>
        </main>
    );
}
