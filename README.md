UltraJarvis v8

UltraJarvis v8 is a Python CLI with production-grade developer agent capabilities, AI-powered task management, automation, performance optimization, and persistent memory.

Features
	•	CLI Tools: uj command with subcommands for tools, seed, run, status, health
	•	Interactive Mode: uj-jarvis conversational loop with speech synthesis
	•	Runtime Hardening: Timeout/retry/fallback system for all tool operations
	•	Watchdog System: Auto-disables flaky tools after repeated failures
	•	Smart Memory: Short-term context buffer and persistent SQLite storage
	•	Performance Optimization: Caching layer and profiling for tool operations
	•	Speech Queue: Async bounded queue with drop-oldest behavior and timeouts
	•	Health Monitoring: Built-in health advisor for system diagnostics
	•	Extensible: Plugin-based tool and advisor system
	•	Production Developer Agent: Natural language → plan → patch → lint/test → commit → PR

Installation

pip install -e .

Quick Start

List available tools

uj tools

View performance metrics

uj metrics

View memory and notes

uj memory view –limit 20

Check system status

uj status

Start interactive mode

uj-jarvis

CLI Commands
	•	uj tools - List available tools
	•	uj status - Show roadmap status
	•	uj seed - Seed roadmap from markdown
	•	uj run - Execute roadmap tasks
	•	uj add  - Add item to roadmap
	•	uj expand - Expand roadmap with AI
	•	uj phase - Show current phase
	•	uj validate - Validate roadmap
	•	uj health [action] - Health advisor (status/scan/plan/fix)
	•	uj track list/add - Track management
	•	uj metrics - Show performance metrics
	•	uj memory view - View stored notes and conversations
	•	uj memory forget-last N - Remove last N conversations
	•	uj memory clear-session - Clear current session data
	•	uj-jarvis - Interactive conversational loop
	•	uj devin “” - Production developer agent

Devin Agent (Production)

UltraJarvis v8 includes a production-grade developer agent that can take natural language tasks and reliably plan → patch → lint/test → commit → PR.

Modes
	•	Fake Mode: UJ_DEVIN_FAKE=1 - Safe testing mode
	•	Real Mode: Default when unset
	•	Sandbox Mode: UJ_DEVIN_SANDBOX=1 - Uses git worktree for safe testing

Environment Variables
	•	UJ_DEVIN_ENABLED=1 - Enable the devin agent
	•	UJ_DEVIN_MAX_FILES=5 - Maximum files to modify per task
	•	UJ_DEVIN_MAX_LINES=400 - Maximum lines to modify per task
	•	UJ_DEVIN_RETRIES=1 - Number of retries on failure
	•	UJ_DEVIN_OPEN_PR=1 - Automatically open PR after commit
	•	MODEL_PROVIDER=openai or lmstudio
	•	OPENAI_API_KEY - Required for OpenAI
	•	MODEL_NAME - Model name (gpt-4o-mini, llama-3.2, etc.)

Safety Features
	•	Protected Paths: Blocks critical files
	•	File/Line Budgets: Limits scope of changes
	•	Pre-apply Backups: Creates backups/ directory
	•	Sandbox Worktree: Isolated testing

Usage Examples

Basic usage

uj devin “Add a test to ensure ‘uj –help’ works”

Create new tool

uj devin “Create a beat-tool skeleton under tools/beat_tool.py”

Refactoring

uj devin “Refactor cloud_bridge to add retries and LM Studio provider”