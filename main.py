import argparse
import json
import random
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

SCRIPT_PATH = Path(__file__).parent / "meditation_script.json"
SAMPLE_RATE = 24000
DEFAULT_ANCHOR_INTERVAL = 5

# Voice mapping: female/male shortcuts to Kokoro voice IDs
VOICE_MAP = {
    "female": "af_heart",
    "male": "am_michael",
}


def load_script() -> dict:
    with open(SCRIPT_PATH) as f:
        return json.load(f)


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(SAMPLE_RATE * seconds))


def speak(pipeline, text: str, voice: str) -> np.ndarray:
    """Generate audio for a single line using Kokoro."""
    chunks = []
    for _, _, audio in pipeline(text, voice=voice, speed=0.9):
        chunks.append(audio)
    return np.concatenate(chunks) if chunks else np.array([])


def build_section(pipeline, lines: list[str], voice: str, pause: float = 8.0) -> np.ndarray:
    chunks = []
    for line in lines:
        chunks.append(speak(pipeline, line, voice))
        chunks.append(silence(pause))
    return np.concatenate(chunks)


def build_meditation(minutes: int, voice: str, anchor_interval: int, output: str):
    script = load_script()

    # Resolve voice
    voice_id = VOICE_MAP.get(voice, voice)
    lang_code = voice_id[0]  # first char: a=American, b=British, etc.

    pipeline = KPipeline(lang_code=lang_code)

    # Build intro (extra)
    print("Generating intro...")
    intro_audio = build_section(pipeline, script["intro"], voice_id, pause=6.0)

    # Build closing (extra)
    print("Generating closing...")
    closing_audio = build_section(pipeline, script["closing"], voice_id, pause=10.0)

    # Build middle section to fill `minutes`
    target_samples = minutes * 60 * SAMPLE_RATE
    middle_chunks = []

    # Start with body scan
    print("Generating body scan...")
    body_scan_audio = build_section(pipeline, script["body_scan"], voice_id, pause=10.0)
    middle_chunks.append(body_scan_audio)

    # Fill remaining time with silence + anchors
    current_samples = len(body_scan_audio)
    anchor_samples = anchor_interval * 60 * SAMPLE_RATE
    anchor_lines = script["anchors"]
    anchor_idx = 0

    print("Filling meditation body with silence and anchors...")
    while current_samples < target_samples:
        remaining = target_samples - current_samples
        gap = min(anchor_samples, remaining)
        middle_chunks.append(silence(gap / SAMPLE_RATE))
        current_samples += gap

        if current_samples < target_samples:
            line = anchor_lines[anchor_idx % len(anchor_lines)]
            anchor_idx += 1
            anchor_audio = speak(pipeline, line, voice_id)
            middle_chunks.append(anchor_audio)
            current_samples += len(anchor_audio)

    middle_audio = np.concatenate(middle_chunks)[:target_samples]

    # Combine: intro + middle + closing
    full_audio = np.concatenate([intro_audio, middle_audio, closing_audio])
    sf.write(output, full_audio, SAMPLE_RATE)
    total_min = len(full_audio) / SAMPLE_RATE / 60
    print(f"Saved {output} ({total_min:.1f} min total: intro + {minutes} min body + closing)")


def main():
    parser = argparse.ArgumentParser(description="Generate guided meditation audio with Kokoro TTS")
    parser.add_argument("--minutes", type=int, required=True, help="Duration of main meditation body (minutes)")
    parser.add_argument("--voice", default="female",
                        help="Voice: 'male', 'female', or Kokoro voice ID (e.g. af_heart, am_michael)")
    parser.add_argument("--anchor-interval", type=int, default=DEFAULT_ANCHOR_INTERVAL,
                        help="Minutes between breath anchors (default: 5, use -1 for random)")
    parser.add_argument("--output", default="meditation.wav", help="Output file path")
    args = parser.parse_args()

    anchor_interval = args.anchor_interval
    if anchor_interval == -1:
        anchor_interval = random.randint(3, 7)

    build_meditation(args.minutes, args.voice, anchor_interval, args.output)


if __name__ == "__main__":
    main()
