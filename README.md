# Guided Meditation

Generate guided meditation audio using [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) TTS.

## Setup

```bash
make setup
```

## Usage

```bash
# 20-minute meditation with default female voice
make run MINUTES=20

# Male voice, slower pace
uv run python main.py --minutes 20 --voice male --pace slow

# Use any Kokoro voice ID
uv run python main.py --minutes 15 --voice af_nicole

# Random anchor intervals
uv run python main.py --minutes 20 --anchor-interval -1
```

## Design Choices

### Voices
- **Female default: `af_bella`** — Grade A-, warm tone, trained on 10-100hrs of high-quality data. Produces natural, soothing speech ideal for meditation.
- **Male default: `am_fenrir`** — Grade C+, deeper and calmer quality. Best male voice for measured, deliberate delivery.

### Pace & Pauses
Meditation requires space for the listener to follow instructions and settle into each sensation.

| Parameter | Default | Why |
|-----------|---------|-----|
| Speech speed | 0.7x | Slow enough to feel unhurried, fast enough to stay engaging |
| Intro pause | 12s | Time to adjust posture after each instruction |
| Body scan pause | 18s | Allows awareness to settle into each body part |
| Anchor pause | 15s | Space to reconnect with breath before silence resumes |
| Closing pause | 15s | Gentle transition back without rushing |

Use `--pace slow` (0.65x, longer pauses) or `--pace medium` (0.75x, shorter pauses) to adjust.

## Structure

1. **Intro** (extra) — posture correction, spine alignment, breath slowing
2. **Body** (your `--minutes`) — full body scan + silence with periodic breath anchors
3. **Closing** (extra) — staying with the feeling, gentle return

## Available Voices

All 54 [Kokoro voices](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) bundled locally. Shortcuts: `female` → `af_bella`, `male` → `am_fenrir`.
