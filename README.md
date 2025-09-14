# UltraJarvis v8

[![CI](https://github.com/mootmoot1/UltraJarvis_v8/actions/workflows/ci.yml/badge.svg)](https://github.com/mootmoot1/UltraJarvis_v8/actions/workflows/ci.yml)

UltraJarvis v8 is a Python CLI tool for building an AI empire across multiple markets. It provides roadmap management, health monitoring, and a conversational AI loop with various tools and advisors.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/mootmoot1/UltraJarvis_v8.git
cd UltraJarvis_v8

# Install in development mode
pip install -e .
```

### Basic Usage

```bash
# List available tools
uj tools

# Check roadmap status
uj status

# Seed tasks from roadmap
uj seed --limit 10

# Run tasks in batch
uj run --batch 25

# Health scan
uj health scan

# Start interactive Jarvis loop
uj-jarvis
```

## Commands

### `uj` Command

The main CLI provides these subcommands:

- `uj tools` - List all available tools
- `uj status` - Show roadmap queue status
- `uj seed [--limit N] [--section NAME]` - Seed tasks from roadmap.md to queue
- `uj run [--batch N]` - Process tasks from queue (default batch: 50)
- `uj add ITEM [--section NAME]` - Add item to roadmap section
- `uj expand [--goal GOAL] [--phases N] [--items-per-phase N]` - Expand roadmap with phases
- `uj phase` - Show phase summary
- `uj validate` - Validate roadmap and queue files
- `uj health [status|scan|plan|fix]` - Health advisor operations
- `uj track list` - List available tracks
- `uj track add NAME` - Add a track
- `uj jarvis` - Start interactive Jarvis loop

### Global Options

- `--log-file PATH` - Specify log file path (default: logs/uj.log)
- `--help` - Show help message

### `uj-jarvis` Interactive Loop

Start the conversational AI loop:

```bash
uj-jarvis
```

Available commands in the loop:
- `set goal <description>` - Set current goal
- `expand phases` - Add phase tasks to roadmap
- `health scan` - Run health diagnostics
- `seed` - Seed tasks from roadmap
- `run --batch N` - Process N tasks
- `status` - Show queue status
- `list tracks` - List available tracks
- `add track NAME` - Add a track
- `remember <note>` - Save a note to memory
- `show memory` - Display saved notes and goal
- `quit` or `exit` - Exit the loop

## Tools & Advisors

### Tools
- **roadmap** - Manage project roadmap and task queue
- **files** - Safe file read/write operations
- **websearch** - Web search functionality (stub implementation)
- **browser** - Browser automation
- **email** - Email operations
- **os_control** - Operating system controls
- **automation** - Task automation

### Advisors
- **health_advisor** - System health monitoring and diagnostics
- **phase_advisor** - Project phase management
- **track_loader** - Track management system

## Development Setup

### Prerequisites
- Python 3.9 or higher
- pip

### Development Installation

```bash
# Clone and enter directory
git clone https://github.com/mootmoot1/UltraJarvis_v8.git
cd UltraJarvis_v8

# Install development dependencies
pip install -r requirements.txt

# Install in editable mode
pip install -e .
```

### Running Tests

```bash
# Run all tests with coverage
pytest --cov=tools --cov=advisors --cov-report=term-missing

# Run specific test file
pytest tests/test_tools_sanity.py -v

# Quick test run
pytest -q
```

### Code Quality

```bash
# Lint code
ruff check .

# Format code
black .

# Check formatting
black --check .
```

### Project Structure

```
UltraJarvis_v8/
├── advisors/           # AI advisors for health, phases, tracks
├── tools/              # Core tools (roadmap, files, etc.)
├── tests/              # Test suite
├── data/               # Runtime data (memory, health state)
├── logs/               # Log files
├── project/            # Project files (roadmap.md)
├── uc.py              # Main CLI entry point
├── jarvis.py          # Interactive loop
├── registry.py        # Tool discovery system
└── pyproject.toml     # Package configuration
```

## Configuration

The system uses several configuration files:

- `project/roadmap.md` - Main project roadmap
- `data/memory.json` - Jarvis conversation memory
- `data/health_state.json` - Health monitoring state
- `tasks.txt` - Current task queue
- `logs/` - Various log files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### CI/CD

The project uses GitHub Actions for continuous integration:
- Tests on Python 3.9 and 3.10
- Code linting with ruff
- Code formatting with black
- Test coverage reporting

## License

This project is part of the UltraJarvis AI empire building initiative.
