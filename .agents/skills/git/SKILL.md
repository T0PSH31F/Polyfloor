---

## name: git description: Fast automated Git workflow to stage changes, run pre-commit checks, generate conventional commit messages, push to GitHub, and sync/merge with main. Triggers on /git or when user requests git sync/commit/push.

# Fast Git Sync & Merge Workflow (/git)

Automates the fast git commit, push, and merge workflow for Polyfloor and general repositories.

## Trigger Instructions

When the user types `/git`, "git sync", "git commit and push", or invokes this skill:

1. **Pre-Commit Checks**:

   - Run `just check` (or `nix flake check` if `just` unavailable).
   - Ensure tests, linting, and Nix flake evaluations pass cleanly.

1. **Secrets & Safety Audit**:

   - Run `git status -s` and inspect diff.
   - Verify no secrets, API keys, passwords, `.env` files, or temporary build artifacts are present.

1. **Stage & Commit**:

   - Stage changes: `git add .`
   - Formulate a clean Conventional Commit message (`feat(...)`, `fix(...)`, `docs(...)`, `refactor(...)`).

1. **Push & Merge**:

   - If on `main`: execute `git push origin main`.
   - If on feature branch:
     - Push branch: `git push origin <branch>`
     - Merge to main: `git checkout main && git merge <branch> && git push origin main`

1. **Report**:

   - Provide terse summary of committed files, commit hash, and push status.
