<<<<<<< HEAD
# Hermes Agent

AI Agent with advanced tool calling capabilities, real-time logging, and extensible toolsets.

## Features

- 🤖 **Multi-model Support**: Works with Claude, GPT-4, and other OpenAI-compatible models
- 🔧 **Rich Tool Library**: Web search, content extraction, vision analysis, terminal execution, and more
- 📊 **Real-time Logging**: WebSocket-based logging system for monitoring agent execution
- 🖥️ **Desktop UI**: Modern PySide6 frontend with real-time event streaming
- 🎯 **Flexible Toolsets**: Predefined toolset combinations for different use cases
- 💾 **Trajectory Saving**: Save conversation flows for training and analysis
- 🔄 **Auto-retry**: Built-in error handling and retry logic

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```bash
python run_agent.py \
  --enabled_toolsets web \
  --query "Search for the latest AI news"
```

### With Real-time Logging

```bash
# Terminal 1: Start API endpoint server
python api_endpoint/logging_server.py

# Terminal 2: Run agent
python run_agent.py \
  --enabled_toolsets web \
  --enable_websocket_logging \
  --query "Your question here"
```

### With Desktop UI (Recommended)

The easiest way to use Hermes Agent is through the desktop UI:

```bash
# One-command launch (starts server + UI)
cd ui && ./start_hermes_ui.sh

# Or manually:
# Terminal 1: Start server
python api_endpoint/logging_server.py

# Terminal 2: Start UI
python ui/hermes_ui.py
```

The UI provides:
- 🖱️ Point-and-click query submission
- 🎛️ Easy model and tool selection
- 📊 Real-time event visualization
- 🔄 Automatic WebSocket connection
- 📝 Session history

## Project Structure

```
Hermes-Agent/
├── run_agent.py              # Main agent runner
├── model_tools.py            # Tool definitions and handling
├── toolsets.py               # Predefined toolset combinations
├── requirements.txt          # Python dependencies
│
├── ui/                      # Desktop UI ⭐ NEW
│   ├── hermes_ui.py         # PySide6 desktop application
│   ├── start_hermes_ui.sh   # UI launcher script
│   └── test_ui_flow.py      # UI integration tests
│
├── tools/                    # Tool implementations
│   ├── web_tools.py         # Web search, extract, crawl
│   ├── vision_tools.py      # Image analysis
│   ├── terminal_tool.py     # Command execution
│   ├── image_generation_tool.py
│   └── ...
│
├── api_endpoint/            # FastAPI + WebSocket logging endpoint
│   ├── logging_server.py    # WebSocket server + Agent API ⭐ ENHANCED
│   ├── websocket_logger.py  # Client library
│   ├── README.md           # API endpoint docs
│   └── ...
│
├── logs/                    # Log files
│   └── realtime/           # WebSocket session logs
│
└── tests/                   # Test files
```

## Available Toolsets

### Basic Toolsets
- **web**: Web search, extract, and crawl
- **terminal**: Command execution
- **vision**: Image analysis
- **creative**: Image generation
- **reasoning**: Mixture of agents

### Composite Toolsets
- **research**: Web + vision tools
- **development**: Web + terminal + vision
- **analysis**: Web + vision + reasoning
- **full_stack**: All tools enabled

### Usage Examples

```bash
# Research with web and vision
python run_agent.py --enabled_toolsets research --query "..."

# Development with terminal access
python run_agent.py --enabled_toolsets development --query "..."

# Combine multiple toolsets
python run_agent.py --enabled_toolsets web,vision --query "..."
```

## Real-time Logging System

Monitor your agent's execution in real-time with the FastAPI WebSocket endpoint using a **persistent connection pool** architecture.

### Architecture

The logging system uses a **singleton WebSocket connection** that persists across multiple agent runs:
- ✅ **No timeouts** - connection stays alive indefinitely
- ✅ **No reconnection overhead** - connect once, reuse forever
- ✅ **Parallel execution** - multiple agents share one connection
- ✅ **Production-ready** - graceful shutdown with signal handlers

See [`api_endpoint/PERSISTENT_CONNECTION_GUIDE.md`](api_endpoint/PERSISTENT_CONNECTION_GUIDE.md) for technical details.

### Features
- Track all API calls and responses
- **Persistent connection** - one WebSocket for all sessions
- Monitor tool executions with parameters and timing
- Capture errors and completion status
- REST API for querying sessions
- Real-time WebSocket broadcasting

### Documentation
See [`api_endpoint/README.md`](api_endpoint/README.md) for complete documentation.

### Quick Start
```bash
# Start API endpoint server
python api_endpoint/logging_server.py

# Run agent with logging
python run_agent.py --enable_websocket_logging --query "..."

# View logs
curl http://localhost:8000/sessions
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Keys
ANTHROPIC_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_key_here
NOUS_API_KEY=your_key_here
FAL_KEY=your_key_here

# Optional
WEB_TOOLS_DEBUG=true  # Enable web tools debug logging
```

### Command-Line Options

```bash
python run_agent.py --help
```

Key options:
- `--query`: Your question/task
- `--model`: Model to use (default: claude-sonnet-4-5-20250929)
- `--enabled_toolsets`: Toolsets to enable
- `--max_turns`: Maximum conversation turns
- `--enable_websocket_logging`: Enable real-time logging
- `--verbose`: Verbose debug output
- `--save_trajectories`: Save conversation trajectories

## Parallel Execution

The persistent connection pool enables true parallel agent execution. Multiple agents can run simultaneously, all sharing the same WebSocket connection for logging.

### Test Parallel Execution

```bash
python test_parallel_execution.py
```

This script runs three tests:
1. **Sequential** - baseline (3 queries one after another)
2. **Parallel** - 3 queries simultaneously  
3. **High Concurrency** - 10 queries simultaneously

**Expected Results:**
- ⚡ ~3x speedup with parallel execution
- ✅ All queries logged to same connection
- ✅ No connection timeouts or errors

### Custom Parallel Code

```python
import asyncio
from run_agent import AIAgent

async def main():
    agent1 = AIAgent(enable_websocket_logging=True)
    agent2 = AIAgent(enable_websocket_logging=True)
    
    # Run in parallel - both use shared connection!
    results = await asyncio.gather(
        agent1.run_conversation("Query 1"),
        agent2.run_conversation("Query 2")
    )

asyncio.run(main())
```

## Examples

### Investment Research
```bash
python run_agent.py \
  --enabled_toolsets web \
  --query "Find publicly traded companies in renewable energy"
```

### Code Analysis
```bash
python run_agent.py \
  --enabled_toolsets development \
  --query "Analyze the codebase and suggest improvements"
```

### Image Analysis
```bash
python run_agent.py \
  --enabled_toolsets vision \
  --query "Analyze this chart and explain the trends"
```

## Development

### Adding New Tools

1. Create tool in `tools/` directory
2. Register in `model_tools.py`
3. Add to appropriate toolset in `toolsets.py`

### Running Tests

```bash
# Test web tools
python tests/test_web_tools.py

# Test API endpoint / logging
cd api_endpoint
./test_websocket_logging.sh
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or PR.

## Support

For questions or issues:
1. Check documentation in `api_endpoint/`
2. Review example usage in this README
3. Open a GitHub issue

---

Built with ❤️ for advanced AI agent workflows
=======
<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent" width="100%">
</p>

# Hermes Agent ☤
<p align="center">
  <a href="https://hermes-agent.nousresearch.com/">Hermes Agent</a> | <a href="https://hermes-agent.nousresearch.com/">Hermes Desktop</a>
</p>
<p align="center">
  <a href="https://hermes-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Docs-hermes--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/NousResearch/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://nousresearch.com"><img src="https://img.shields.io/badge/Built%20by-Nous%20Research-blueviolet?style=for-the-badge" alt="Built by Nous Research"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-اردو-green?style=for-the-badge" alt="اردو"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Lang-Español-orange?style=for-the-badge" alt="Español"></a>
</p>

**The self-improving AI agent built by [Nous Research](https://nousresearch.com).** It's the only agent with a built-in learning loop — it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions. Run it on a $5 VPS, a GPU cluster, or serverless infrastructure that costs nearly nothing when idle. It's not tied to your laptop — talk to it from Telegram while it works on a cloud VM.

Use any model you want — [Nous Portal](https://portal.nousresearch.com), OpenRouter, OpenAI, your own endpoint, and [many others](https://hermes-agent.nousresearch.com/docs/integrations/providers). Switch with `hermes model` — no code changes, no lock-in.

<table>
<tr><td><b>A real terminal interface</b></td><td>Full TUI with multiline editing, slash-command autocomplete, conversation history, interrupt-and-redirect, and streaming tool output.</td></tr>
<tr><td><b>Lives where you do</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal, and CLI — all from a single gateway process. Voice memo transcription, cross-platform conversation continuity.</td></tr>
<tr><td><b>A closed learning loop</b></td><td>Agent-curated memory with periodic nudges. Autonomous skill creation after complex tasks. Skills self-improve during use. FTS5 session search with LLM summarization for cross-session recall. <a href="https://github.com/plastic-labs/honcho">Honcho</a> dialectic user modeling. Compatible with the <a href="https://agentskills.io">agentskills.io</a> open standard.</td></tr>
<tr><td><b>Scheduled automations</b></td><td>Built-in cron scheduler with delivery to any platform. Daily reports, nightly backups, weekly audits — all in natural language, running unattended.</td></tr>
<tr><td><b>Delegates and parallelizes</b></td><td>Spawn isolated subagents for parallel workstreams. Write Python scripts that call tools via RPC, collapsing multi-step pipelines into zero-context-cost turns.</td></tr>
<tr><td><b>Runs anywhere, not just your laptop</b></td><td>Six terminal backends — local, Docker, SSH, Singularity, Modal, and Daytona. Daytona and Modal offer serverless persistence — your agent's environment hibernates when idle and wakes on demand, costing nearly nothing between sessions. Run it on a $5 VPS or a GPU cluster.</td></tr>
<tr><td><b>Research-ready</b></td><td>Batch trajectory generation, trajectory compression for training the next generation of tool-calling models.</td></tr>
</table>

---

## Quick Install

### Linux, macOS, WSL2, Termux

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

### Windows (native, PowerShell)

> **Heads up:** Native Windows runs Hermes without WSL — CLI, gateway, TUI, and tools all work natively. If you'd rather use WSL2, the Linux/macOS one-liner above works there too. Found a bug? Please [file issues](https://github.com/NousResearch/hermes-agent/issues).

Run this in PowerShell:

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

The installer handles everything: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **and a portable Git Bash** (MinGit, unpacked to `%LOCALAPPDATA%\hermes\git` — no admin required, completely isolated from any system Git install). Hermes uses this bundled Git Bash to run shell commands.

If you already have Git installed, the installer detects it and uses that instead. Otherwise a ~45MB MinGit download is all you need — it won't touch or interfere with any system Git.

> **Android / Termux:** The tested manual path is documented in the [Termux guide](https://hermes-agent.nousresearch.com/docs/getting-started/termux). On Termux, Hermes installs a curated `.[termux]` extra because the full `.[all]` extra currently pulls Android-incompatible voice dependencies.
>
> **Windows:** Native Windows is fully supported — the PowerShell one-liner above installs everything. If you'd rather use WSL2, the Linux command works there too. Native Windows install lives under `%LOCALAPPDATA%\hermes`; WSL2 installs under `~/.hermes` as on Linux.

After installation:

```bash
source ~/.bashrc    # reload shell (or: source ~/.zshrc)
hermes              # start chatting!
```

### Troubleshooting

#### Windows Defender or antivirus flags `uv.exe` as malware

If your antivirus (Bitdefender, Windows Defender, etc.) quarantines `uv.exe` from the Hermes `bin` folder (`%LOCALAPPDATA%\hermes\bin\uv.exe`), this is a **false positive**. The file is Astral's `uv` — the Rust Python package manager Hermes bundles to manage its Python environment. ML-based antivirus engines commonly flag unsigned Rust binaries that download and install packages.

**To verify your copy is authentic:**

```powershell
# Install GitHub CLI if needed
winget install --id GitHub.cli

# Login to GitHub
gh auth login

# Run verification
$uv = "$env:LOCALAPPDATA\hermes\bin\uv.exe"
$ver = (& $uv --version).Split(' ')[1]
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$zip = "$env:TEMP\uv.zip"
Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$ver/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
gh attestation verify $zip --repo astral-sh/uv
Expand-Archive $zip "$env:TEMP\uv_x" -Force
(Get-FileHash "$env:TEMP\uv_x\uv.exe").Hash -eq (Get-FileHash $uv).Hash
```

If attestation says "Verification succeeded" and the last line prints `True`, you're good.

**To whitelist Hermes:**
- **Windows Defender:** Run PowerShell as Admin → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\hermes\bin"`
- **Bitdefender:** Add an exception in the Bitdefender console (Protection > Antivirus > Settings > Manage Exceptions)
- Whitelist the **folder**, not the file hash — Hermes updates `uv` and the hash changes every version

For more context, see the upstream Astral reports: [astral-sh/uv#13553](https://github.com/astral-sh/uv/issues/13553), [astral-sh/uv#15011](https://github.com/astral-sh/uv/issues/15011), [astral-sh/uv#10079](https://github.com/astral-sh/uv/issues/10079).

---

## Getting Started

```bash
hermes              # Interactive CLI — start a conversation
hermes model        # Choose your LLM provider and model
hermes tools        # Configure which tools are enabled
hermes config set   # Set individual config values
hermes config get   # Print individual config values
hermes gateway      # Start the messaging gateway (Telegram, Discord, etc.)
hermes setup        # Run the full setup wizard (configures everything at once)
hermes claw migrate # Migrate from OpenClaw (if coming from OpenClaw)
hermes update       # Update to the latest version
hermes doctor       # Diagnose any issues
```

📖 **[Full documentation →](https://hermes-agent.nousresearch.com/docs/)**

---

## Skip the API-key collection — Nous Portal

Hermes works with whatever provider you want — that's not changing. But if you'd rather not collect five separate API keys for the model, web search, image generation, TTS, and a cloud browser, **[Nous Portal](https://portal.nousresearch.com)** covers all of them under one subscription:

- **300+ models** — pick any of them with `/model <name>`
- **Tool Gateway** — web search (Firecrawl), image generation (FAL), text-to-speech (OpenAI), cloud browser (Browser Use), all routed through your sub. No extra accounts.

One command from a fresh install:

```bash
hermes setup --portal
```

That logs you in via OAuth, sets Nous as your provider, and turns on the Tool Gateway. Check what's wired up any time with `hermes portal info`. Full details on the [Tool Gateway docs page](https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-gateway).

You can still bring your own keys per-tool whenever you want — the gateway is per-backend, not all-or-nothing.

---

## CLI vs Messaging Quick Reference

Hermes has two entry points: start the terminal UI with `hermes`, or run the gateway and talk to it from Telegram, Discord, Slack, WhatsApp, Signal, or Email. Once you're in a conversation, many slash commands are shared across both interfaces.

| Action                         | CLI                                           | Messaging platforms                                                              |
| ------------------------------ | --------------------------------------------- | -------------------------------------------------------------------------------- |
| Start chatting                 | `hermes`                                      | Run `hermes gateway setup` + `hermes gateway start`, then send the bot a message |
| Start fresh conversation       | `/new` or `/reset`                            | `/new` or `/reset`                                                               |
| Change model                   | `/model [provider:model]`                     | `/model [provider:model]`                                                        |
| Set a personality              | `/personality [name]`                         | `/personality [name]`                                                            |
| Retry or undo the last turn    | `/retry`, `/undo`                             | `/retry`, `/undo`                                                                |
| Compress context / check usage | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]`                                        |
| Browse skills                  | `/skills` or `/<skill-name>`                  | `/<skill-name>`                                                                  |
| Interrupt current work         | `Ctrl+C` or send a new message                | `/stop` or send a new message                                                    |
| Platform-specific status       | `/platforms`                                  | `/status`, `/sethome`                                                            |

For the full command lists, see the [CLI guide](https://hermes-agent.nousresearch.com/docs/user-guide/cli) and the [Messaging Gateway guide](https://hermes-agent.nousresearch.com/docs/user-guide/messaging).

---

## Documentation

All documentation lives at **[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)**:

| Section                                                                                             | What's Covered                                             |
| --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| [Quickstart](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart)                 | Install → setup → first conversation in 2 minutes          |
| [CLI Usage](https://hermes-agent.nousresearch.com/docs/user-guide/cli)                              | Commands, keybindings, personalities, sessions             |
| [Configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration)                | Config file, providers, models, all options                |
| [Messaging Gateway](https://hermes-agent.nousresearch.com/docs/user-guide/messaging)                | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [Security](https://hermes-agent.nousresearch.com/docs/user-guide/security)                          | Command approval, DM pairing, container isolation          |
| [Tools & Toolsets](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools)            | 40+ tools, toolset system, terminal backends               |
| [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)              | Procedural memory, Skills Hub, creating skills             |
| [Memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)                     | Persistent memory, user profiles, best practices           |
| [MCP Integration](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)               | Connect any MCP server for extended capabilities           |
| [Cron Scheduling](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron)              | Scheduled tasks with platform delivery                     |
| [Context Files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files)       | Project context that shapes every conversation             |
| [Architecture](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture)             | Project structure, agent loop, key classes                 |
| [Contributing](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing)             | Development setup, PR process, code style                  |
| [CLI Reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands)                  | All commands and flags                                     |
| [Environment Variables](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) | Complete env var reference                                 |

---

## Migrating from OpenClaw

If you're coming from OpenClaw, Hermes can automatically import your settings, memories, skills, and API keys.

**During first-time setup:** The setup wizard (`hermes setup`) automatically detects `~/.openclaw` and offers to migrate before configuration begins.

**Anytime after install:**

```bash
hermes claw migrate              # Interactive migration (full preset)
hermes claw migrate --dry-run    # Preview what would be migrated
hermes claw migrate --preset user-data   # Migrate without secrets
hermes claw migrate --overwrite  # Overwrite existing conflicts
```

What gets imported:

- **SOUL.md** — persona file
- **Memories** — MEMORY.md and USER.md entries
- **Skills** — user-created skills → `~/.hermes/skills/openclaw-imports/`
- **Command allowlist** — approval patterns
- **Messaging settings** — platform configs, allowed users, working directory
- **API keys** — allowlisted secrets (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **TTS assets** — workspace audio files
- **Workspace instructions** — AGENTS.md (with `--workspace-target`)

See `hermes claw migrate --help` for all options, or use the `openclaw-migration` skill for an interactive agent-guided migration with dry-run previews.

---

## Contributing

We welcome contributions! See the [Contributing Guide](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing) for development setup, code style, and PR process.

Quick start for contributors — use the standard installer, then work from the
full git checkout it creates at `$HERMES_HOME/hermes-agent` (usually
`~/.hermes/hermes-agent`). This matches the layout used by `hermes update`, the
managed venv, lazy dependencies, gateway, and docs tooling.

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
cd "${HERMES_HOME:-$HOME/.hermes}/hermes-agent"
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

Manual clone fallback (for throwaway clones/CI where you intentionally do not
want the managed install layout):

Create the venv outside the cloned source tree — a venv inside the directory
the agent operates from can be wiped by a relative-path command the agent runs
against its own checkout, destroying the running runtime mid-session.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv ~/.hermes/venvs/hermes-dev --python 3.11
source ~/.hermes/venvs/hermes-dev/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## Community

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Issues](https://github.com/NousResearch/hermes-agent/issues)
- 🔌 [computer-use-linux](https://github.com/avifenesh/computer-use-linux) — Linux desktop-control MCP server for Hermes and other MCP hosts, with AT-SPI accessibility trees, Wayland/X11 input, screenshots, and compositor window targeting.
- 🔌 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) — Community WeChat bridge: Run Hermes Agent and OpenClaw on the same WeChat account.

---

## License

MIT — see [LICENSE](LICENSE).

Built by [Nous Research](https://nousresearch.com).
>>>>>>> upstream/main
