import Link from "next/link";
import { Terminal, Plug, MessageSquare, BarChart3, Clock, Search, Cpu, Copy } from "lucide-react";

function CodeBlock({ title, language, children }: { title?: string; language: string; children: string }) {
  return (
    <div className="rounded-lg border border-terminal-border bg-neutral-950 overflow-hidden font-mono text-sm my-4">
      {title && (
        <div className="flex items-center justify-between px-4 py-2 bg-neutral-900 border-b border-terminal-border">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
          </div>
          <span className="text-xs text-neutral-500">{title}</span>
          <div className="w-12" />
        </div>
      )}
      <pre className="p-4 overflow-x-auto text-neutral-300 leading-relaxed">
        <code>{children}</code>
      </pre>
    </div>
  );
}

function ToolCard({
  name,
  description,
  icon: Icon,
  example,
}: {
  name: string;
  description: string;
  icon: React.ElementType;
  example: string;
}) {
  return (
    <div className="border border-terminal-border rounded-lg p-5 bg-neutral-900/30 hover:bg-neutral-900/60 transition-colors">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-9 h-9 rounded-md bg-terminal-green/10 flex items-center justify-center">
          <Icon className="w-5 h-5 text-terminal-green" />
        </div>
        <code className="text-terminal-green font-bold text-base">{name}</code>
      </div>
      <p className="text-neutral-400 text-sm leading-relaxed mb-3">{description}</p>
      <div className="rounded bg-neutral-950 border border-terminal-border px-3 py-2">
        <p className="text-xs text-neutral-500 mb-1">Try asking:</p>
        <p className="text-sm text-terminal-amber italic">&quot;{example}&quot;</p>
      </div>
    </div>
  );
}

export default function MCPPage() {
  return (
    <main className="min-h-screen bg-terminal-black flex flex-col text-neutral-300">
      {/* Header */}
      <header className="fixed top-0 w-full z-50 bg-terminal-black/80 backdrop-blur-md border-b border-terminal-border">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 text-white font-bold text-xl tracking-tight"
          >
            <Terminal className="w-6 h-6 text-terminal-green" />
            <span>telos</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-sm text-neutral-400 hover:text-white transition-colors"
            >
              Home
            </Link>
            <span className="px-3 py-1.5 text-xs font-medium text-terminal-green border border-terminal-green/30 rounded-md bg-terminal-green/5">
              MCP Server
            </span>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div className="flex-1 pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Page Title */}
          <div className="mb-16">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-terminal-green/10 border border-terminal-green/20 flex items-center justify-center">
                <Plug className="w-6 h-6 text-terminal-green" />
              </div>
              <span className="px-2 py-0.5 text-xs font-medium text-terminal-amber border border-terminal-amber/30 rounded bg-terminal-amber/5 uppercase tracking-wider">
                New
              </span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-terminal-green to-emerald-600 mb-4">
              Telos MCP Server
            </h1>
            <p className="text-xl text-neutral-400 leading-relaxed max-w-2xl">
              Connect your screen-tracking data to Claude Desktop, Cursor,
              or other MCP-compatible AI tools. Query your work patterns,
              productivity, and time usage in plain English -- all from your
              local database, no cloud required.
            </p>
            <div className="mt-4 flex items-center gap-3 text-sm">
              <span className="px-3 py-1.5 bg-terminal-green/10 border border-terminal-green/30 rounded text-terminal-green">
                Works with: Claude Desktop
              </span>
              <span className="px-3 py-1.5 bg-terminal-green/10 border border-terminal-green/30 rounded text-terminal-green">
                Cursor IDE
              </span>
              <span className="px-3 py-1.5 bg-neutral-800 border border-neutral-700 rounded text-neutral-400">
                ChatGPT (not yet)
              </span>
            </div>
          </div>

          {/* What is MCP */}
          <section className="mb-16">
            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-terminal-green rounded-full"></span>
              What is MCP?
            </h2>
            <p className="text-neutral-400 leading-relaxed mb-4">
              The{" "}
              <a
                href="https://modelcontextprotocol.io"
                className="text-terminal-green hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                Model Context Protocol
              </a>{" "}
              is an open standard that lets AI assistants access external
              data sources and tools. The Telos MCP Server exposes your
              local activity database so any MCP-compatible client can
              query your work history, sessions, and productivity data.
            </p>
            <p className="text-neutral-400 leading-relaxed">
              Your data never leaves your machine. The MCP server reads
              directly from your local Telos database -- no cloud, no
              third-party access.
            </p>
          </section>

          {/* How It Connects to Your Data */}
          <section className="mb-16">
            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-terminal-green rounded-full"></span>
              How It Connects to Your Data
            </h2>
            <p className="text-neutral-400 leading-relaxed mb-4">
              The Telos MCP server is a small Python script that runs on your
              local machine. When you configure it in Claude Desktop or Cursor,
              here&apos;s what happens:
            </p>
            <div className="space-y-4">
              <div className="border border-terminal-border rounded-lg p-4 bg-neutral-900/30">
                <div className="flex items-start gap-3">
                  <span className="w-8 h-8 rounded-full bg-terminal-green/10 border border-terminal-green/30 flex items-center justify-center text-terminal-green text-sm font-bold shrink-0 mt-0.5">
                    1
                  </span>
                  <div>
                    <h3 className="text-white font-medium mb-1">You ask a question</h3>
                    <p className="text-neutral-400 text-sm">
                      In Claude Desktop or Cursor, you type: &quot;What did I work on today?&quot;
                    </p>
                  </div>
                </div>
              </div>
              <div className="border border-terminal-border rounded-lg p-4 bg-neutral-900/30">
                <div className="flex items-start gap-3">
                  <span className="w-8 h-8 rounded-full bg-terminal-green/10 border border-terminal-green/30 flex items-center justify-center text-terminal-green text-sm font-bold shrink-0 mt-0.5">
                    2
                  </span>
                  <div>
                    <h3 className="text-white font-medium mb-1">AI picks the right tool</h3>
                    <p className="text-neutral-400 text-sm">
                      Claude/Cursor sees the Telos tools are available and automatically
                      calls <code className="text-terminal-green text-xs">get_activity_today()</code> on
                      your local machine.
                    </p>
                  </div>
                </div>
              </div>
              <div className="border border-terminal-border rounded-lg p-4 bg-neutral-900/30">
                <div className="flex items-start gap-3">
                  <span className="w-8 h-8 rounded-full bg-terminal-green/10 border border-terminal-green/30 flex items-center justify-center text-terminal-green text-sm font-bold shrink-0 mt-0.5">
                    3
                  </span>
                  <div>
                    <h3 className="text-white font-medium mb-1">Server reads your local database</h3>
                    <p className="text-neutral-400 text-sm">
                      The MCP server opens <code className="text-terminal-green text-xs">~/.telos/tracker.db</code> (your
                      local SQLite database) and retrieves your captures, sessions, and stats.
                      <strong className="text-white"> This never leaves your computer.</strong>
                    </p>
                  </div>
                </div>
              </div>
              <div className="border border-terminal-border rounded-lg p-4 bg-neutral-900/30">
                <div className="flex items-start gap-3">
                  <span className="w-8 h-8 rounded-full bg-terminal-green/10 border border-terminal-green/30 flex items-center justify-center text-terminal-green text-sm font-bold shrink-0 mt-0.5">
                    4
                  </span>
                  <div>
                    <h3 className="text-white font-medium mb-1">AI receives the text response</h3>
                    <p className="text-neutral-400 text-sm">
                      The tool returns a formatted text summary (like &quot;Today: 142 min work,
                      23 min learning...&quot;) to Claude/Cursor, which uses it to answer your question.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-6 p-4 border border-terminal-amber/30 rounded-lg bg-terminal-amber/5">
              <p className="text-sm text-neutral-300">
                <strong className="text-terminal-amber">Important:</strong> Your Telos database
                stays on your machine. Only the <em>text output</em> from the tools (like
                &quot;You worked 2h on coding&quot;) is sent to the AI model. No raw database files,
                no screenshots, no sensitive data.
              </p>
            </div>
          </section>

          {/* Quick Setup */}
          <section className="mb-16">
            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-terminal-green rounded-full"></span>
              Quick Setup
            </h2>

            <div className="space-y-6">
              {/* Step 1 */}
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="w-7 h-7 rounded-full bg-terminal-green/10 border border-terminal-green/30 flex items-center justify-center text-terminal-green text-sm font-bold">
                    1
                  </span>
                  <h3 className="text-lg font-medium text-white">
                    Install the MCP package
                  </h3>
                </div>
                <CodeBlock title="terminal" language="bash">
                  {`pip install mcp`}
                </CodeBlock>
              </div>

              {/* Step 2 */}
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="w-7 h-7 rounded-full bg-terminal-green/10 border border-terminal-green/30 flex items-center justify-center text-terminal-green text-sm font-bold">
                    2
                  </span>
                  <h3 className="text-lg font-medium text-white">
                    Configure your MCP client
                  </h3>
                </div>
                <p className="text-neutral-400 text-sm mb-3 ml-10">
                  Add this to your client&apos;s MCP configuration file. Replace the path with where you installed Telos.
                </p>

                <div className="space-y-4 ml-10">
                  <div>
                    <p className="text-xs text-neutral-500 mb-1 uppercase tracking-wider">
                      Claude Desktop &mdash;{" "}
                      <code className="text-neutral-400">
                        ~/Library/Application Support/Claude/claude_desktop_config.json
                      </code>
                    </p>
                    <CodeBlock title="claude_desktop_config.json" language="json">
{`{
  "mcpServers": {
    "telos": {
      "command": "python",
      "args": ["/path/to/telos/client/mcp_server.py"]
    }
  }
}`}
                    </CodeBlock>
                  </div>

                  <div>
                    <p className="text-xs text-neutral-500 mb-1 uppercase tracking-wider">
                      Cursor &mdash;{" "}
                      <code className="text-neutral-400">
                        .cursor/mcp.json
                      </code>{" "}
                      (in your project root)
                    </p>
                    <CodeBlock title=".cursor/mcp.json" language="json">
{`{
  "mcpServers": {
    "telos": {
      "command": "python",
      "args": ["/path/to/telos/client/mcp_server.py"]
    }
  }
}`}
                    </CodeBlock>
                  </div>
                </div>
              </div>

              {/* Step 3 */}
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="w-7 h-7 rounded-full bg-terminal-green/10 border border-terminal-green/30 flex items-center justify-center text-terminal-green text-sm font-bold">
                    3
                  </span>
                  <h3 className="text-lg font-medium text-white">
                    Start asking questions
                  </h3>
                </div>
                <p className="text-neutral-400 text-sm ml-10">
                  Restart your MCP client (fully quit and reopen).
                  The Telos tools will appear automatically. Just ask
                  in natural language.
                </p>
              </div>
            </div>
          </section>

          {/* Available Tools */}
          <section className="mb-16">
            <h2 className="text-2xl font-semibold text-white mb-6 flex items-center gap-2">
              <span className="w-1 h-6 bg-terminal-green rounded-full"></span>
              Available Tools
            </h2>
            <p className="text-neutral-400 mb-6">
              The Telos MCP server exposes 7 tools. Your AI assistant picks
              the right one automatically based on what you ask.
            </p>

            <div className="grid md:grid-cols-2 gap-4">
              <ToolCard
                name="get_activity_today"
                description="Today's complete activity breakdown: time spent per category, top apps, total captures, and latest activity."
                icon={Clock}
                example="What did I do today?"
              />
              <ToolCard
                name="get_sessions"
                description="Work sessions with AI summaries, focus scores, apps used, and duration. Filter by date."
                icon={BarChart3}
                example="Show me my work sessions from yesterday"
              />
              <ToolCard
                name="get_daily_summary"
                description="AI-generated daily narrative with productivity score, key learnings, and focus blocks."
                icon={MessageSquare}
                example="Give me my daily summary for Monday"
              />
              <ToolCard
                name="query_activity"
                description="Natural language search across all activity data -- captures, sessions, and summaries."
                icon={Search}
                example="How much time did I spend coding this week?"
              />
              <ToolCard
                name="get_recent_captures"
                description="Granular screen captures with detected app, task, files, URLs, and AI context."
                icon={Cpu}
                example="What was I working on 30 minutes ago?"
              />
              <ToolCard
                name="get_productivity_trends"
                description="Multi-day productivity scores and time breakdowns to spot patterns."
                icon={BarChart3}
                example="Show my productivity trend for the last week"
              />
              <ToolCard
                name="get_top_apps"
                description="Most-used applications and category breakdown over a configurable time range."
                icon={Terminal}
                example="Which apps did I use most this week?"
              />
            </div>
          </section>

          {/* Example Conversations */}
          <section className="mb-16">
            <h2 className="text-2xl font-semibold text-white mb-6 flex items-center gap-2">
              <span className="w-1 h-6 bg-terminal-green rounded-full"></span>
              Example Conversations
            </h2>
            <p className="text-neutral-400 mb-4">
              Here are real examples of what you can ask once the MCP
              server is connected. These work in <strong className="text-white">Claude Desktop</strong> and{" "}
              <strong className="text-white">Cursor</strong> (other MCP-compatible clients coming soon).
            </p>
            <div className="mb-6 p-3 border border-neutral-700 rounded-lg bg-neutral-900/30">
              <p className="text-xs text-neutral-400">
                <strong className="text-neutral-300">Note:</strong> ChatGPT doesn&apos;t support MCP yet,
                so these examples won&apos;t work there. Use Claude Desktop (desktop app) or Cursor IDE instead.
              </p>
            </div>

            <div className="space-y-6">
              {/* Example 1 */}
              <div className="border border-terminal-border rounded-lg overflow-hidden">
                <div className="px-4 py-3 bg-neutral-900 border-b border-terminal-border">
                  <span className="text-xs text-neutral-500 uppercase tracking-wider">
                    Quick Status Check
                  </span>
                </div>
                <div className="p-4 space-y-3">
                  <div className="flex gap-3">
                    <span className="text-terminal-amber text-xs font-bold mt-1 shrink-0">YOU</span>
                    <p className="text-neutral-300 text-sm">How&apos;s my day going so far?</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-terminal-green text-xs font-bold mt-1 shrink-0">AI</span>
                    <div className="text-neutral-400 text-sm space-y-1">
                      <p>You&apos;ve been at it for about 4 hours today. Here&apos;s the breakdown:</p>
                      <p className="font-mono text-xs text-neutral-500 pl-3 border-l border-terminal-border">
                        Work: 142 min &middot; Learning: 23 min &middot; Browsing: 31 min<br />
                        Top apps: VS Code (45 captures), Chrome (28), Terminal (12)<br />
                        68 total captures across 8 sessions
                      </p>
                      <p>Most of your morning was in VS Code working on the API refactor. You had a solid 45-minute deep focus block around 10am.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Example 2 */}
              <div className="border border-terminal-border rounded-lg overflow-hidden">
                <div className="px-4 py-3 bg-neutral-900 border-b border-terminal-border">
                  <span className="text-xs text-neutral-500 uppercase tracking-wider">
                    Deep Activity Query
                  </span>
                </div>
                <div className="p-4 space-y-3">
                  <div className="flex gap-3">
                    <span className="text-terminal-amber text-xs font-bold mt-1 shrink-0">YOU</span>
                    <p className="text-neutral-300 text-sm">What did I work on between 2pm and 5pm yesterday? I need to fill out my timesheet.</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-terminal-green text-xs font-bold mt-1 shrink-0">AI</span>
                    <div className="text-neutral-400 text-sm space-y-1">
                      <p>Here&apos;s your afternoon breakdown from yesterday:</p>
                      <p className="font-mono text-xs text-neutral-500 pl-3 border-l border-terminal-border">
                        14:00-14:45 &middot; VS Code &middot; Fixing pagination bug in user dashboard<br />
                        14:50-15:20 &middot; Slack + Zoom &middot; Sprint planning meeting<br />
                        15:25-16:30 &middot; VS Code + Terminal &middot; Writing integration tests for auth module<br />
                        16:35-17:00 &middot; Chrome + Notion &middot; Updating project documentation
                      </p>
                      <p>For your timesheet: ~1.5h coding (bug fix + tests), 30min meeting, 25min documentation.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Example 3 */}
              <div className="border border-terminal-border rounded-lg overflow-hidden">
                <div className="px-4 py-3 bg-neutral-900 border-b border-terminal-border">
                  <span className="text-xs text-neutral-500 uppercase tracking-wider">
                    Productivity Analysis
                  </span>
                </div>
                <div className="p-4 space-y-3">
                  <div className="flex gap-3">
                    <span className="text-terminal-amber text-xs font-bold mt-1 shrink-0">YOU</span>
                    <p className="text-neutral-300 text-sm">Am I spending too much time context-switching? Show me my app usage patterns this week.</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-terminal-green text-xs font-bold mt-1 shrink-0">AI</span>
                    <div className="text-neutral-400 text-sm space-y-1">
                      <p>Looking at your last 7 days, you used 14 different apps with 724 total captures:</p>
                      <p className="font-mono text-xs text-neutral-500 pl-3 border-l border-terminal-border">
                        VS Code: 38% &middot; Chrome: 22% &middot; Slack: 12% &middot; Terminal: 8%<br />
                        Categories: 65% work, 25% browsing, 8% learning, 2% entertainment
                      </p>
                      <p>You&apos;re actually doing well -- 65% focused work time is above average. But I notice Slack captures spike between 11am-12pm every day. Consider batching your messages to protect your morning focus blocks.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Example 4 */}
              <div className="border border-terminal-border rounded-lg overflow-hidden">
                <div className="px-4 py-3 bg-neutral-900 border-b border-terminal-border">
                  <span className="text-xs text-neutral-500 uppercase tracking-wider">
                    Integration with Coding Workflow
                  </span>
                </div>
                <div className="p-4 space-y-3">
                  <div className="flex gap-3">
                    <span className="text-terminal-amber text-xs font-bold mt-1 shrink-0">YOU</span>
                    <p className="text-neutral-300 text-sm">I&apos;m writing a standup update. What did I accomplish since yesterday morning?</p>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-terminal-green text-xs font-bold mt-1 shrink-0">AI</span>
                    <div className="text-neutral-400 text-sm space-y-1">
                      <p>Based on your tracked activity since yesterday 9am:</p>
                      <p className="font-mono text-xs text-neutral-500 pl-3 border-l border-terminal-border">
                        Yesterday: Fixed pagination bug, wrote auth integration tests, updated docs<br />
                        Today: Started API refactor (mcp_server.py), reviewed PR #142, pair-programmed on deploy script
                      </p>
                      <p>Here&apos;s a draft for your standup:</p>
                      <p className="text-neutral-300 italic pl-3 border-l border-terminal-green/30">
                        &quot;Yesterday: Closed the pagination bug, added integration tests for auth, updated project docs.
                        Today: Working on the API refactor and deploy pipeline. No blockers.&quot;
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Advanced Configuration */}
          <section className="mb-16">
            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-terminal-green rounded-full"></span>
              Advanced Configuration
            </h2>

            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-white mb-2">
                  Custom Database Path
                </h3>
                <p className="text-neutral-400 text-sm mb-3">
                  If your Telos database is in a non-default location,
                  set the <code className="text-terminal-green">TELOS_DB_PATH</code> environment
                  variable:
                </p>
                <CodeBlock title="claude_desktop_config.json" language="json">
{`{
  "mcpServers": {
    "telos": {
      "command": "python",
      "args": ["/path/to/telos/client/mcp_server.py"],
      "env": {
        "TELOS_DB_PATH": "/custom/path/to/tracker.db"
      }
    }
  }
}`}
                </CodeBlock>
              </div>

              <div>
                <h3 className="text-lg font-medium text-white mb-2">
                  HTTP Transport
                </h3>
                <p className="text-neutral-400 text-sm mb-3">
                  For network-accessible setups, you can run the server
                  with HTTP transport:
                </p>
                <CodeBlock title="terminal" language="bash">
                  {`python mcp_server.py --transport http\n# Server starts at http://localhost:8000/mcp`}
                </CodeBlock>
              </div>

              <div>
                <h3 className="text-lg font-medium text-white mb-2">
                  Testing with MCP Inspector
                </h3>
                <p className="text-neutral-400 text-sm mb-3">
                  Use the official MCP Inspector to test and debug:
                </p>
                <CodeBlock title="terminal" language="bash">
                  {`npx @modelcontextprotocol/inspector python client/mcp_server.py`}
                </CodeBlock>
              </div>
            </div>
          </section>

          {/* Supported Clients */}
          <section className="mb-16">
            <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-1 h-6 bg-terminal-green rounded-full"></span>
              Which AI Assistants Support MCP?
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="border border-terminal-green/30 rounded-lg p-5 bg-terminal-green/5">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-terminal-green"></div>
                  <h3 className="text-white font-semibold">Claude Desktop</h3>
                </div>
                <p className="text-neutral-400 text-sm mb-3">
                  Anthropic&apos;s desktop app with full MCP support. Works on macOS and Windows.
                </p>
                <p className="text-xs text-neutral-500">
                  Download:{" "}
                  <a
                    href="https://claude.ai/download"
                    className="text-terminal-green hover:underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    claude.ai/download
                  </a>
                </p>
              </div>

              <div className="border border-terminal-green/30 rounded-lg p-5 bg-terminal-green/5">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-terminal-green"></div>
                  <h3 className="text-white font-semibold">Cursor IDE</h3>
                </div>
                <p className="text-neutral-400 text-sm mb-3">
                  AI-powered code editor with MCP integration. Perfect for developer workflows.
                </p>
                <p className="text-xs text-neutral-500">
                  Download:{" "}
                  <a
                    href="https://cursor.sh"
                    className="text-terminal-green hover:underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    cursor.sh
                  </a>
                </p>
              </div>

              <div className="border border-neutral-700 rounded-lg p-5 bg-neutral-900/30">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-neutral-600"></div>
                  <h3 className="text-neutral-400 font-semibold">ChatGPT</h3>
                </div>
                <p className="text-neutral-500 text-sm">
                  OpenAI&apos;s ChatGPT doesn&apos;t support MCP yet. You can use their API
                  with custom code, but not the web/desktop app.
                </p>
              </div>

              <div className="border border-neutral-700 rounded-lg p-5 bg-neutral-900/30">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-neutral-600"></div>
                  <h3 className="text-neutral-400 font-semibold">Other Clients</h3>
                </div>
                <p className="text-neutral-500 text-sm">
                  More MCP-compatible clients are launching. Check{" "}
                  <a
                    href="https://modelcontextprotocol.io"
                    className="text-terminal-green hover:underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    modelcontextprotocol.io
                  </a>{" "}
                  for updates.
                </p>
              </div>
            </div>
          </section>

          {/* Privacy Note */}
          <section className="mb-16">
            <div className="border border-terminal-green/20 rounded-lg p-6 bg-terminal-green/5">
              <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                <span className="text-terminal-green">Privacy Note</span>
              </h3>
              <p className="text-neutral-400 text-sm leading-relaxed">
                The Telos MCP server runs entirely on your machine.
                It reads from your local SQLite database at{" "}
                <code className="text-terminal-green text-xs">~/.telos/tracker.db</code>.
                No data is sent to external servers.
                When you use it with Claude or Cursor, only the text
                output of the tools is shared with the AI model -- never
                raw screenshots or database files.
              </p>
            </div>
          </section>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-terminal-border bg-neutral-950 py-12 px-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2 text-neutral-500">
            <Terminal className="w-5 h-5" />
            <span className="text-sm">
              &copy; {new Date().getFullYear()} Telos. Know where your time goes.
            </span>
          </div>

          <div className="flex items-center gap-6 mt-4 md:mt-0">
            <Link
              href="/"
              className="text-xs text-neutral-600 hover:text-neutral-400 transition-colors"
            >
              Home
            </Link>
            <Link
              href="/privacy"
              className="text-xs text-neutral-600 hover:text-neutral-400 transition-colors"
            >
              Privacy Policy
            </Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
