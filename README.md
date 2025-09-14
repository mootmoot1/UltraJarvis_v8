# UltraJarvis v8

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
pytest --cov=tools --cov=advisors --cov=core --cov-report=term-missing
ruff check .
black --check .
```

### CI Status
[![CI](https://github.com/mootmoot1/UltraJarvis_v8/actions/workflows/ci.yml/badge.svg)](https://github.com/mootmoot1/UltraJarvis_v8/actions/workflows/ci.yml)
