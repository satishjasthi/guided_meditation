import argparse
import json
import random
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import nltk
nltk.download('punkt_tab', quiet=True)

# Patch torch.load to allow loading StyleTTS2 checkpoints
_original_torch_load = torch.load
torch.load = lambda *args, **kwargs: _original_torch_load(*args, **{**kwargs, "weights_only": False})

from styletts2 import tts as styletts2_tts

SCRIPT_PATH = Path(__file__).parent / "meditation_script.json"
VOICES_DIR = Path(__file__).parent / "voices"
SAMPLE_RATE = 24000
DEFAULT_ANCHOR_INTERVAL = 5  # minutes


def load_script() -> dict:
    with open(SCRIPT_PATH) as f:
        return json.load(f)


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(SAMPLE_RATE * seconds))


def speak(engine, text: str, voice_path: str) -> np.ndarray:
    return engine.inference(text, target_voice_path=voice_path, output_sample_rate=SAMPLE_RATE)


def build_section(engine, lines: list[str], voice_path: str, pause: float = 8.0) -> np.ndarray:
    """Synthesize a list of lines with pauses between them."""
    chunks = []
    for line in lines:
        chunks.append(speak(engine, line, voice_path))
        chunks.append(silence(pause))
    return np.concatenate(chunks)


def build_meditation(minutes: int, voice: str, anchor_interval: int, output: str):
    script = load_script()

    # Resolve voice path
    if voice in ("male", "female"):
        voice_path = str(VOICES_DIR / f"{voice}.wav")
    else:
        voice_path = voice  # custom path

    engine = styletts2_tts.StyleTTS2()

    # Build intro (always included, extra)
    print("Generating intro...")
    intro_audio = build_section(engine, script["intro"], voice_path, pause=6.0)

    # Build closing (always included, extra ~2 min)
    print("Generating closing...")
    closing_audio = build_section(engine, script["closing"], voice_path, pause=10.0)

    # Build middle section to fill `minutes`
    target_samples = minutes * 60 * SAMPLE_RATE
    middle_chunks = []

    # Start with body scan
    print("Generating body scan...")
    body_scan_audio = build_section(engine, script["body_scan"], voice_path, pause=10.0)
    middle_chunks.append(body_scan_audio)

    # Fill remaining time with silence + anchors every anchor_interval minutes
    current_samples = len(body_scan_audio)
    anchor_samples = anchor_interval * 60 * SAMPLE_RATE
    anchor_lines = script["anchors"]
    anchor_idx = 0

    print("Filling meditation body with silence and anchors...")
    while current_samples < target_samples:
        # Add silence until next anchor (or end)
        remaining = target_samples - current_samples
        gap = min(anchor_samples, remaining)
        middle_chunks.append(silence(gap / SAMPLE_RATE))
        current_samples += gap

        if current_samples < target_samples:
            # Pick anchor line (random or sequential)
            if anchor_interval == -1:  # random mode handled at arg level
                line = random.choice(anchor_lines)
            else:
                line = anchor_lines[anchor_idx % len(anchor_lines)]
                anchor_idx += 1
            anchor_audio = speak(engine, line, voice_path)
            middle_chunks.append(anchor_audio)
            current_samples += len(anchor_audio)

    middle_audio = np.concatenate(middle_chunks)
    # Trim to exact target
    middle_audio = middle_audio[:target_samples]

    # Combine: intro + middle + closing
    full_audio = np.concatenate([intro_audio, middle_audio, closing_audio])

    sf.write(output, full_audio, SAMPLE_RATE)
    total_min = len(full_audio) / SAMPLE_RATE / 60
    print(f"Saved {output} ({total_min:.1f} min total: intro + {minutes} min body + closing)")


def main():
    parser = argparse.ArgumentParser(description="Generate guided meditation audio with StyleTTS2")
    parser.add_argument("--minutes", type=int, required=True, help="Duration of main meditation body (minutes)")
    parser.add_argument("--voice", default="female", help="Voice: 'male', 'female', or path to a WAV file")
    parser.add_argument("--anchor-interval", type=int, default=DEFAULT_ANCHOR_INTERVAL,
                        help="Minutes between breath anchors (default: 5, use -1 for random intervals)")
    parser.add_argument("--output", default="meditation.wav", help="Output file path")
    args = parser.parse_args()

    # Handle random anchor interval (1-7 min random gaps)
    anchor_interval = args.anchor_interval
    if anchor_interval == -1:
        anchor_interval = random.randint(3, 7)

    build_meditation(args.minutes, args.voice, anchor_interval, args.output)


if __name__ == "__main__":
    main()
