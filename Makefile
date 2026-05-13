.PHONY: system-deps setup run clean

system-deps:
	brew install espeak-ng libsndfile

setup: system-deps
	uv sync

run:
	uv run python main.py --minutes $(MINUTES) --voice $(or $(VOICE),af_heart)

clean:
	rm -rf .venv *.wav
