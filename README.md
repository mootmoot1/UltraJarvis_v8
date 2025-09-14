# UltraJarvis v8

A Python CLI package for AI-powered task management and automation with performance optimization and persistent memory.

## Features

- **CLI Tools**: `uj` command with subcommands for tools, seed, run, status, health
- **Interactive Mode**: `uj-jarvis` conversational loop with speech synthesis
- **Runtime Hardening**: Timeout/retry/fallback system for all tool operations
- **Watchdog System**: Auto-disables flaky tools after repeated failures
- **Smart Memory**: Short-term context buffer and persistent SQLite storage
- **Performance Optimization**: Caching layer and profiling for tool operations
- **Speech Queue**: Async bounded queue with drop-oldest behavior and timeouts
- **Health Monitoring**: Built-in health advisor for system diagnostics
- **Extensible**: Plugin-based tool and advisor system

## Quick Start

```bash
# Install in development mode
pip install -e .

# List available tools
uj tools

# Check system status
uj status

# Start interactive mode
uj-jarvis

# Interactive mode with performance profiling
uj-jarvis --profile --speech-off --log-file custom.log
```

## Commands

### CLI Commands (`uj`)

- `uj tools` - List all available tools
- `uj status` - Show roadmap queue status
- `uj seed [--limit N] [--section NAME]` - Seed tasks from roadmap
- `uj run [--batch N]` - Process queued tasks
- `uj health [scan|plan|fix]` - Health diagnostics
- `uj track list` - List available tracks
- `uj track add NAME` - Add track to roadmap

### Interactive Mode (`uj-jarvis`)

Available flags:
- `--speech-off` - Disable text-to-speech
- `--no-watchdog` - Disable watchdog for debugging  
- `--log-file PATH` - Custom log file path
- `--profile` - Enable per-tool execution time profiling
- `--forget-last` - Clear last conversation from persistent memory
- `--clear-memory` - Clear all persistent memory

Interactive commands:
- `set goal <text>` - Set current goal
- `expand phases` - Add phase tasks to roadmap
- `run <tool> <action> key=val` - Execute tool action
- `note <text>` - Add note to persistent memory
- `remember <text>` - Remember information in persistent storage
- `show memory` - Display memory summary (both JSON and SQLite)
- `search <query>` - Search through persistent notes
- `health scan` - Run health diagnostics
- `quit` / `exit` - Exit interactive mode

## Performance Features

### Caching System
- **LRU Cache**: Tool outputs cached with 5-minute TTL
- **Smart Keys**: MD5 hash of tool+action+arguments
- **Cache Hits**: Repeat calls return instantly from cache
- **Automatic Eviction**: Oldest entries removed when cache is full

### Profiling System
- **Per-Tool Timing**: Track execution time for each tool action
- **Statistics**: Calls, total time, average, min/max times
- **Profile Summary**: Displayed on exit when `--profile` flag used
- **Performance Insights**: Identify slow operations and optimization opportunities

### Parallel Execution
- **Safe Operations**: Read-only tools can run concurrently
- **Async Support**: Background processing for compatible operations
- **Resource Management**: Controlled concurrency to prevent overload

## Persistent Memory

### SQLite Storage (`data/memory.db`)
- **Notes Table**: Timestamped notes with tags and full-text search
- **Conversations Table**: Complete conversation history with session tracking
- **Persistence**: Data survives application restarts
- **Search**: Query notes by content with `search <query>` command

### Memory Management
- **Dual Storage**: JSON for session data, SQLite for persistence
- **Automatic Backup**: Conversations and notes saved automatically
- **Memory Commands**: 
  - `--forget-last` - Remove last conversation
  - `--clear-memory` - Wipe all persistent data

### Example Session (Memory Persistence)

```bash
# Session 1
$ uj-jarvis
Jarvis: Online. Goal: (none) | try: set goal <..>, note <text>, search <query>...
You: note My focus niche this week is fitness creators
Jarvis: Noted: My focus niche this week is fitness creators
You: quit

# Session 2 (after restart)
$ uj-jarvis  
Jarvis: Online. Goal: (none) | try: set goal <..>, note <text>, search <query>...
You: search fitness
Jarvis: Found 1 notes: [2025-09-14] My focus niche this week is fitness creators...
You: show memory
Jarvis: {"goal": null, "persistent_notes": 1, "recent_notes": [...], "persistent_conversations": 2, ...}
```

## Runtime Features (Sprint 2)

### Speech Queue
- Asynchronous speech with bounded queue (max 8 items)
- Automatic drop-oldest behavior when queue is full
- 10-second timeout per TTS call
- Use `--speech-off` to disable TTS completely

### Tool Hardening
- All tools wrapped with 15-second timeout
- Automatic retry (2 attempts) with exponential backoff
- Graceful fallback responses on failure
- Never crashes the Jarvis loop

### Watchdog System
- Automatically disables tools after 3 failures in 60 seconds
- Session-scoped (resets on restart)
- Announces disabling via speech
- Use `--no-watchdog` for debugging

### Smart Memory
- Short-term buffer: last 10 user/assistant turns in `data/memory_runtime.json`
- Long-term memory: persistent notes in `data/memory.json`
- Use `note <text>` command to add manual notes
- Runtime buffer cleared on each session start

### CLI Flags
```bash
uj-jarvis --speech-off --log-file logs/debug.log  # Mute TTS, custom log
uj-jarvis --no-watchdog                           # Disable watchdog
```

## Development

### Setup
```bash
git clone https://github.com/mootmoot1/UltraJarvis_v8.git
cd UltraJarvis_v8
pip install -e .
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tools --cov=advisors --cov=core

# Run specific test file
pytest tests/test_runtime.py -v

# Test performance features
pytest tests/test_runtime.py::test_cache_hit_performance -v
pytest tests/test_runtime.py::test_sqlite_persistence_across_restart -v
```

### CI/CD
[![CI](https://github.com/mootmoot1/UltraJarvis_v8/actions/workflows/ci.yml/badge.svg)](https://github.com/mootmoot1/UltraJarvis_v8/actions/workflows/ci.yml)

The project uses GitHub Actions for continuous integration:
- Python 3.9 and 3.10 matrix testing
- Automated testing with pytest
- Code quality checks with ruff and black
- Pip dependency caching for faster builds

## Architecture

### Tools
- `roadmap` - Task queue management (cached)
- `websearch` - Web search functionality (cached)
- `files` - File operations
- `browser` - Browser automation
- `email` - Email operations
- `os_control` - System control
- `speech` - Text-to-speech with queuing

### Advisors
- `health_advisor` - System health monitoring
- `phase_advisor` - Goal and phase management
- `track_loader` - Predefined track management

### Core Modules
- `core/runtime.py` - Runtime memory management
- `core/watchdog.py` - Tool failure monitoring
- `core/persistence.py` - SQLite persistent memory
- `core/cache.py` - Tool output caching system
- `tools/speech.py` - Speech queue implementation

## File Structure

```
UltraJarvis_v8/
├── uc.py              # Main CLI entry point
├── jarvis.py          # Interactive conversational loop
├── registry.py        # Tool discovery, execution, and profiling
├── tools/             # Tool implementations
├── advisors/          # Advisor implementations  
├── core/              # Core runtime modules
│   ├── runtime.py     # Short-term memory management
│   ├── persistence.py # SQLite persistent storage
│   ├── cache.py       # Tool output caching
│   └── watchdog.py    # Tool failure monitoring
├── tests/             # Test suite
├── data/              # Runtime data storage
│   ├── memory.json    # Session memory
│   ├── memory.db      # Persistent SQLite database
│   └── memory_runtime.json # Short-term buffer
├── logs/              # Log files
└── project/           # Project files (roadmap.md)
```

## Runtime Features

### Watchdog System
- Automatically disables tools after 3 failures within 60 seconds
- Session-scoped (resets on restart)
- Provides user-friendly error messages
- Can be disabled with `--no-watchdog` flag

### Timeout & Retry System
- 15-second timeout per tool operation
- 2 retries with exponential backoff (0.5s, 1.5s)
- Structured fallback responses on final failure
- Never crashes the main Jarvis loop

### Smart Memory
- **Short-term buffer**: Last 10 user/assistant turns in `data/memory_runtime.json`
- **Long-term memory**: Persistent SQLite storage in `data/memory.db`
- **Note command**: `note My focus niche this week is fitness creators`
- **Search capability**: `search fitness` to find relevant notes
- **Memory consultation**: Runtime buffer checked first, then persistent storage

### Speech Queue
- Async bounded queue (maxsize=8) with background worker
- Drop-oldest behavior when queue is full
- 10-second timeout per TTS call
- Graceful muting with `--speech-off` flag

## Development

### Setup
```bash
# Clone and install
git clone <repo-url>
cd UltraJarvis_v8
pip install -e .

# Install development dependencies
pip install pytest pytest-cov ruff black

# Run tests
pytest -q

# Run linting
ruff check .
black --check .
```

## Performance Optimization

### Caching Benefits
- **Faster Responses**: Cached tool calls return in ~1ms vs original execution time
- **Reduced Load**: Prevents redundant expensive operations
- **Smart Invalidation**: 5-minute TTL ensures fresh data when needed

### Profiling Output Example
```
=== Tool Performance Profile ===
websearch.search:
  Calls: 5
  Total: 2.150s
  Avg: 0.430s
  Min: 0.001s (cached)
  Max: 0.850s
roadmap.status:
  Calls: 3
  Total: 0.045s
  Avg: 0.015s
  Min: 0.010s
  Max: 0.025s
================================
```

## License

MIT License
