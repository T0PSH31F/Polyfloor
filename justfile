# Polyfloor — Task runner

# Format all code
format:
    nix fmt
    cd backend && ruff format src/ tests/
    cd frontend && npx prettier --write .

# Lint all code
lint:
    cd backend && ruff check src/ tests/
    cd backend && mypy src/polyfloor
    cd frontend && npx svelte-check --tsconfig ./tsconfig.json

# Run all tests
test: backend-test frontend-test

# Run backend tests
backend-test:
    cd backend && python -m pytest tests/ -v --tb=short

# Run frontend tests
frontend-test:
    cd frontend && npx vitest run

# Run all checks (format check + lint + test + nix eval)
check:
    nix fmt -- --check
    cd backend && ruff check src/ tests/
    cd backend && python -m pytest tests/ -v --tb=short -x
    cd frontend && npx svelte-check --tsconfig ./tsconfig.json
    nix flake check --no-build

# Nix flake check
nix-check:
    nix flake check --no-build

# Run backend dev server
dev-backend:
    cd backend && uv run uvicorn polyfloor.main:app --reload --host 127.0.0.1 --port 8001

# Run frontend dev server
dev-frontend:
    cd frontend && npm run dev

# Run database migration
db-migrate:
    psql "${POLYFLOOR_DATABASE_DSN:-postgresql://polyfloor@localhost:5432/polyfloor}" -f db/migrations/001_tower_core.sql

# Install frontend dependencies
frontend-install:
    cd frontend && npm install

# Install backend dependencies
backend-install:
    cd backend && uv sync
