.PHONY: system-deps setup run clean

system-deps:
	brew install libsndfile

setup: system-deps
	uv sync

run:
	uv run python main.py --minutes $(MINUTES) --voice $(or $(VOICE),female)

clean:
	rm -rf .venv *.wav
