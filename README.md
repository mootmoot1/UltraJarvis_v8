# UltraJarvis v8

UltraJarvis v8 is a Python CLI with production-grade developer agent capabilities.

## Installation

```bash
pip install -e .
```

## Commands

- `uj tools` - List available tools
- `uj status` - Show roadmap status
- `uj seed` - Seed roadmap from markdown
- `uj run` - Execute roadmap tasks
- `uj add <item>` - Add item to roadmap
- `uj expand` - Expand roadmap with AI
- `uj phase` - Show current phase
- `uj validate` - Validate roadmap
- `uj health [action]` - Health advisor (status/scan/plan/fix)
- `uj track list/add` - Track management
- `uj-jarvis` - Interactive conversational loop
- `uj devin "<task>"` - Production developer agent

## Devin Agent (Production)

UltraJarvis v8 includes a production-grade developer agent that can take natural language tasks and reliably plan → patch → lint/test → commit → PR.

### Modes

- **Fake Mode**: `UJ_DEVIN_FAKE=1` - Safe testing mode that simulates operations
- **Real Mode**: Default when `UJ_DEVIN_FAKE` is unset - Actually applies changes
- **Sandbox Mode**: `UJ_DEVIN_SANDBOX=1` - Uses git worktree for safe testing

### Environment Variables

- `UJ_DEVIN_ENABLED=1` - Enable the devin agent (required)
- `UJ_DEVIN_FAKE=1` - Run in fake/simulation mode
- `UJ_DEVIN_SANDBOX=1` - Use sandbox worktree mode
- `UJ_DEVIN_MAX_FILES=5` - Maximum files to modify per task
- `UJ_DEVIN_MAX_LINES=400` - Maximum lines to modify per task
- `UJ_DEVIN_RETRIES=1` - Number of retries on failure
- `UJ_DEVIN_OPEN_PR=1` - Automatically open PR after successful commit

#### Cloud AI Configuration

- `MODEL_PROVIDER=openai` - Use OpenAI (default)
- `MODEL_PROVIDER=lmstudio` - Use LM Studio/Ollama
- `OPENAI_API_KEY` - OpenAI API key (required for OpenAI)
- `MODEL_NAME` - Model name (e.g., gpt-4o-mini, llama-3.2-3b-instruct)
- `LMSTUDIO_BASE` - LM Studio base URL (default: http://localhost:1234)

### Safety Features

- **Protected Paths**: Blocks changes to .github/workflows/*, pyproject.toml, setup.py, etc.
- **File/Line Budgets**: Enforces limits on scope of changes
- **Pre-apply Backups**: Creates backups/ directory before applying changes
- **Sandbox Worktree**: Optional isolated testing environment

### Usage Examples

```bash
# Basic usage
uj devin "Add a test to ensure 'uj --help' works"

# Create new tool
uj devin "Create a beat-tool skeleton under tools/beat_tool.py and wire it in registry"

# Refactoring
uj devin "Refactor cloud_bridge to add retries and LM Studio provider"
```

### Troubleshooting

- **Missing diff header**: Check that patches are properly formatted
- **Merge conflicts**: Use sandbox mode to test changes safely
- **Provider errors**: Verify API keys and model names are correct
- **Protected path errors**: Review PROTECTED_PATHS configuration
