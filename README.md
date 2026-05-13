# Guided Meditation

Generate guided meditation audio using StyleTTS2 voice cloning.

## Setup

```bash
make setup
```

This installs:
- **System**: `libsndfile` (via Homebrew, for WAV I/O)
- **Python**: `styletts2`, `soundfile`, `numpy` (via uv)

## Usage

```bash
# 20-minute meditation with female voice
make run MINUTES=20

# Male voice
make run MINUTES=15 VOICE=male

# Custom anchor interval (every 3 min)
uv run python main.py --minutes 15 --voice male --anchor-interval 3

# Random anchor intervals (3-7 min)
uv run python main.py --minutes 20 --voice female --anchor-interval -1

# Custom voice sample
uv run python main.py --minutes 10 --voice /path/to/your_voice.wav
```

## Structure

The generated audio:

1. **Intro** (extra) — posture correction, spine alignment, breath slowing
2. **Body** (your `--minutes`) — full body scan + silence with periodic breath anchors
3. **Closing** (extra) — staying with the feeling, gentle return

## Voice Samples

Built-in voices in `voices/` (male/female). Pass any WAV path with `--voice` for custom cloning.
