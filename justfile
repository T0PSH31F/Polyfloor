# Polyfloor — task runner

# Format all code (requires Nix)
fmt:
	nix fmt

format: fmt

# Lint backend + frontend (no Nix required)
lint:
	cd backend && ruff check src/ tests/
	cd frontend && npx svelte-check --tsconfig ./tsconfig.json

# Run all tests (no Nix required)
test: backend-test frontend-test

# Run backend tests
backend-test:
	cd backend && uv run python -m pytest tests/ -v --tb=short

# Run frontend tests
frontend-test:
	cd frontend && npx vitest run

# Full check WITHOUT nix (sandbox/CI-friendly): lint + tests + svelte-check
check-local:
	cd backend && ruff check src/ tests/
	cd backend && uv run python -m pytest tests/ -v --tb=short -x
	cd frontend && npx svelte-check --tsconfig ./tsconfig.json
	cd frontend && npm run build

# Full check WITH nix (format check + lint + tests + nix flake check)
check:
	nix fmt -- --check
	cd backend && ruff check src/ tests/
	cd backend && uv run python -m pytest tests/ -v --tb=short -x
	cd frontend && npx svelte-check --tsconfig ./tsconfig.json
	nix flake check --no-build

# Nix flake check only
nix-check:
	nix flake check --no-build

# Run dev servers (backend :8001 + frontend :5173, proxied)
dev:
	@echo "Starting backend (http://127.0.0.1:8001) and frontend (http://127.0.0.1:5173)..."
	@cd backend && uv run uvicorn polyfloor.main:app --reload --host 127.0.0.1 --port 8001 &
	@cd frontend && npm run dev

# Run backend dev server only
dev-backend:
	cd backend && uv run uvicorn polyfloor.main:app --reload --host 127.0.0.1 --port 8001

# Run frontend dev server only
dev-frontend:
	cd frontend && npm run dev

# Install frontend dependencies
frontend-install:
	cd frontend && npm install

# Install backend dependencies
backend-install:
	cd backend && uv sync --extra dev
