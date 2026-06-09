.PHONY: install lint build run compose-up compose-down logs test-compose

# Install Node dependencies for Prism/Spectral/Newman
install:
	npm install

# Lint OpenAPI contracts with Spectral
lint:
	npm run lint

# Build all images used by the Compose stack
build:
	docker compose build

# Run the full stack. The API depends on DB and AI, so standalone API mode is not used.
run: compose-up

# Compose commands
compose-up:
	docker compose up -d --build

compose-down:
	docker compose down

logs:
	docker compose logs -f

# Run Newman tests on compose stack
test-compose:
	npm run test:compose
