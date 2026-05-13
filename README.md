# Guided Meditation

Generate guided meditation audio using [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) TTS.

## Setup

```bash
make setup
```

This installs:
- **System**: `espeak-ng`, `libsndfile` (via Homebrew)
- **Python**: `kokoro`, `soundfile`, `numpy` (via uv)

## Usage

```bash
# 20-minute meditation with female voice (af_heart)
make run MINUTES=20

# Male voice (am_michael)
make run MINUTES=15 VOICE=male

# Use any Kokoro voice ID directly
uv run python main.py --minutes 20 --voice af_bella

# Custom anchor interval (every 3 min)
uv run python main.py --minutes 15 --voice male --anchor-interval 3

# Random anchor intervals (3-7 min)
uv run python main.py --minutes 20 --anchor-interval -1
```

## Available Voices

Any [Kokoro voice](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) works. Shortcuts:
- `female` → `af_heart` (highest quality female)
- `male` → `am_michael` (high quality male)

## Structure

The generated audio:

1. **Intro** (extra) — posture correction, spine alignment, breath slowing
2. **Body** (your `--minutes`) — full body scan + silence with periodic breath anchors
3. **Closing** (extra) — staying with the feeling, gentle return
