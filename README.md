UltraJarvis

[![CI](https://github.com/mootmoot1/UltraJarvis_v8/actions/workflows/ci.yml/badge.svg)](https://github.com/mootmoot1/UltraJarvis_v8/actions/workflows/ci.yml)

UltraJarvis v8 is a Python CLI with production-grade developer-agent capabilities plus AI-powered task management, automation, observability, and persistent memory. It includes a conversational loop, tools/advisors, runtime hardening, and a “Devin”-style developer agent that can plan → patch → lint/test → commit → PR.

Installation

Clone the repo and install in editable/dev mode:

$ git clone https://github.com/mootmoot1/UltraJarvis_v8.git
$ cd UltraJarvis_v8
$ pip install -e .

(Optionally) install dev dependencies:

$ pip install -r requirements.txt
$ pip install pytest pytest-cov ruff black

Quick start

List tools:
$ uj tools

Check status:
$ uj status

Seed tasks:
$ uj seed –limit 10

Run tasks:
$ uj run –batch 25

Health scan:
$ uj health scan

Start interactive mode:
$ uj-jarvis

View metrics:
$ uj metrics

View memory:
$ uj memory view –limit 20

CLI commands (uj)
	•	uj tools — list available tools
	•	uj status — show roadmap queue status
	•	uj seed [–limit N] [–section NAME] — seed tasks from roadmap
	•	uj run [–batch N] — process queued tasks
	•	uj add  [–section NAME] — add item to roadmap
	•	uj expand [–goal GOAL] [–phases N] [–items-per-phase N] — expand roadmap with phases
	•	uj phase — show phase summary
	•	uj validate — validate roadmap and queue files
	•	uj health [status|scan|plan|fix] — health advisor
	•	uj track list / uj track add NAME — track management
	•	uj metrics — performance metrics and tool usage
	•	uj memory view / uj memory forget-last N / uj memory clear-session — memory ops
	•	uj-jarvis — interactive conversational loop
	•	uj devin “” — production developer agent

Devin agent (production)

The built-in developer agent can take natural language tasks and execute them end-to-end (plan → patch → lint/test → commit → PR).

Modes
	•	Fake mode (simulate safely): set UJ_DEVIN_FAKE=1
	•	Real mode (default when UJ_DEVIN_FAKE is unset)
	•	Sandbox mode (safe git worktree): set UJ_DEVIN_SANDBOX=1

Environment variables
	•	UJ_DEVIN_ENABLED=1 (required to enable the agent)
	•	UJ_DEVIN_FAKE=1 (simulate)
	•	UJ_DEVIN_SANDBOX=1 (use worktree sandbox)
	•	UJ_DEVIN_MAX_FILES=5
	•	UJ_DEVIN_MAX_LINES=400
	•	UJ_DEVIN_RETRIES=1
	•	UJ_DEVIN_OPEN_PR=1
	•	MODEL_PROVIDER=openai | lmstudio
	•	OPENAI_API_KEY=… (required for OpenAI)
	•	MODEL_NAME=gpt-4o-mini | llama-3.2-…
	•	LMSTUDIO_BASE=http://localhost:1234 (when using LM Studio/Ollama)

Safety features
	•	Protected paths (blocks critical files)
	•	File/line budgets to limit change scope
	•	Pre-apply backups (backs up changed files)
	•	Optional sandbox worktree isolation

Examples
	•	Basic: uj devin “Add a test to ensure ‘uj –help’ works”
	•	Create tool: uj devin “Create tools/beat_tool.py and wire it in registry”
	•	Refactor: uj devin “Refactor cloud_bridge with retries and LM Studio provider”

Features
	•	CLI tools and advisors (roadmap, files, browser, email, os_control, automation; health_advisor, phase_advisor, track_loader)
	•	Interactive mode with optional speech synthesis
	•	Runtime hardening (timeouts, retries, fallbacks)
	•	Watchdog (auto-disables flaky tools)
	•	Smart memory (short-term buffer + persistent SQLite)
	•	Caching and profiling for performance
	•	Structured logging and metrics (observability)

Project structure

UltraJarvis_v8/
	•	uc.py (main CLI)
	•	jarvis.py (interactive loop)
	•	registry.py (tool discovery/execution)
	•	tools/ (tool implementations)
	•	advisors/ (advisors)
	•	core/ (runtime, cache, persistence, watchdog)
	•	tests/
	•	data/ (memory files/db)
	•	logs/
	•	project/ (roadmap.md)

Development

Setup:
$ pip install -e .

Run tests:
$ pytest -q
$ pytest –cov=tools –cov=advisors –cov-report=term-missing

Lint/format:
$ ruff check .
$ black –check .

CI/CD

GitHub Actions runs lint (ruff), format check (black), and tests (pytest with coverage) on Python versions in the matrix. Badge: see top of this file.

License

MIT License.