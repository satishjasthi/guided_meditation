.PHONY: system-deps setup run clean docker-build docker-push docker-run

IMAGE := satishjasthi/guided-meditation:latest
PLATFORMS := linux/amd64,linux/arm64

system-deps:
	brew install espeak-ng libsndfile

setup: system-deps
	uv sync

run:
	uv run python main.py --minutes $(MINUTES) --voice $(or $(VOICE),female)

docker-build:
	docker buildx build --platform $(PLATFORMS) -t $(IMAGE) --push .

docker-run:
	docker run --rm -v $(PWD)/output:/app/output $(IMAGE) \
		--minutes $(or $(MINUTES),10) --voice $(or $(VOICE),female) --output output/meditation.wav

clean:
	rm -rf .venv *.wav output/
