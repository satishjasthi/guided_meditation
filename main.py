import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from kokoro import KPipeline
from kokoro.model import KModel

SCRIPT_PATH = Path(__file__).parent / "meditation_script.json"
MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "kokoro-v1_0.pth"
CONFIG_PATH = MODEL_DIR / "config.json"
VOICES_DIR = MODEL_DIR / "voices"
SAMPLE_RATE = 24000
DEFAULT_ANCHOR_INTERVAL = 5

# Known safe SHA256 from https://huggingface.co/hexgrad/Kokoro-82M
EXPECTED_MODEL_HASH = "496dba118d1a58f5f3db2efc88dbdc216e0483fc89fe6e47ee1f2c53f18ad1e4"

VOICE_MAP = {
    "female": "af_heart",
    "male": "am_michael",
}


def validate_model(path: Path) -> bool:
    """Validate model checkpoint integrity and safety before loading."""
    if not path.exists():
        print(f"ERROR: Model file not found at {path}")
        return False

    print("Validating model checkpoint integrity...")
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual_hash = sha256.hexdigest()

    if actual_hash != EXPECTED_MODEL_HASH:
        print(f"ERROR: Model hash mismatch!")
        print(f"  Expected: {EXPECTED_MODEL_HASH}")
        print(f"  Got:      {actual_hash}")
        return False

    # Verify safe deserialization (no arbitrary code execution)
    print("Verifying safe deserialization (weights_only=True)...")
    try:
        torch.load(path, map_location="cpu", weights_only=True)
    except Exception as e:
        print(f"ERROR: Unsafe checkpoint: {e}")
        return False

    print("Model validation passed ✓")
    return True


def load_script() -> dict:
    with open(SCRIPT_PATH) as f:
        return json.load(f)


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(SAMPLE_RATE * seconds))


def speak(pipeline, text: str, voice: str) -> np.ndarray:
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
    voice_id = VOICE_MAP.get(voice, voice)
    lang_code = voice_id[0]

    if not validate_model(MODEL_PATH):
        sys.exit(1)

    # Load model from local path only
    print("Loading model from local checkpoint...")
    model = KModel(repo_id="hexgrad/Kokoro-82M", config=str(CONFIG_PATH), model=str(MODEL_PATH)).eval()
    pipeline = KPipeline(lang_code=lang_code, repo_id="hexgrad/Kokoro-82M", model=model)

    # Override voice loading to use local files
    voice_path = VOICES_DIR / f"{voice_id}.pt"
    if not voice_path.exists():
        print(f"ERROR: Voice file not found: {voice_path}")
        print(f"Available voices: {[p.stem for p in VOICES_DIR.glob('*.pt')]}")
        sys.exit(1)
    pipeline.voices[voice_id] = torch.load(voice_path, map_location="cpu", weights_only=True)

    print("Generating intro...")
    intro_audio = build_section(pipeline, script["intro"], voice_id, pause=6.0)

    print("Generating closing...")
    closing_audio = build_section(pipeline, script["closing"], voice_id, pause=10.0)

    target_samples = minutes * 60 * SAMPLE_RATE
    middle_chunks = []

    print("Generating body scan...")
    body_scan_audio = build_section(pipeline, script["body_scan"], voice_id, pause=10.0)
    middle_chunks.append(body_scan_audio)

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
