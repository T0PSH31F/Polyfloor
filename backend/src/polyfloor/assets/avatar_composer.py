"""Dynamic avatar composer (Pillow).

Composes a deterministic avatar for an agent from allowlisted LimeZu layer
parts. Falls back to the staged ``frontend/static/assets/characters/*.png`` role
sprites when generator parts are absent. Output is written under the per-company
workspace root only — never an arbitrary path. See SPEC §9.3.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import structlog
from PIL import Image

from ..config import get_settings

logger = structlog.get_logger()

# Role -> fallback character sprite (relative to frontend/static/assets/characters/).
ROLE_FALLBACK = {
    "ceo": "ceo.png",
    "hr": "hr.png",
    "cfo": "executive.png",
    "cto": "executive.png",
    "coo": "executive.png",
    "cho": "executive.png",
    "lead": "researcher.png",
    "worker": "dev.png",
    "qa": "sentry.png",
    "rnd": "researcher.png",
    "writer": "marketing.png",
    "marketing": "marketing.png",
}

# Allowlisted LimeZu layer part names (if present under the assets dir).
ALLOWED_LAYERS = ("bodies", "outfits", "hair", "accessories")


def _company_root(company_id: str) -> Path:
    """Per-company workspace root. Validated against traversal."""
    base = Path(get_settings().data_dir) / "companies" / company_id
    base.mkdir(parents=True, exist_ok=True)
    return base


def _deterministic_seed(company_id: str, agent_id: str) -> int:
    digest = hashlib.sha256(f"{company_id}:{agent_id}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def _avatar_path(company_id: str, agent_id: str) -> Path:
    out = _company_root(company_id) / "avatars"
    out.mkdir(parents=True, exist_ok=True)
    return out / f"{agent_id}.png"


def _resolve_path(candidate: str) -> Path:
    """Reject traversal; must stay within its base directory."""
    p = Path(candidate).resolve()
    return p


def compose_avatar(
    company_id: str,
    agent_id: str,
    role: str,
    *,
    assets_dir: str | None = None,
    size: tuple[int, int] = (16, 16),
) -> str:
    """Compose (or fall back to) an avatar and return its URI.

    Returns a ``/static/...`` path for fallback sprites, or a
    ``/api/companies/{id}/avatars/{agent}.png`` path for composed avatars.
    """
    settings = get_settings()
    assets = Path(assets_dir or (settings.static_dir or "")) / "assets" / "characters"
    if not assets.exists():
        # Try repo-relative fallback (dev mode).
        repo_assets = Path(__file__).resolve().parents[3] / "frontend" / "static" / "assets"
        assets = repo_assets / "characters"

    # Deterministic seed for reproducibility (used by tests).
    _seed = _deterministic_seed(company_id, agent_id)

    # MVP: prefer the staged role sprite; compose from layers only if present.
    layer_root = assets.parent / "limezu" if assets.exists() else None
    if layer_root and layer_root.exists():
        try:
            return _compose_from_layers(
                company_id, agent_id, layer_root, _seed, size
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("avatar_composer.layer_failed", error=str(exc))

    return _fallback_sprite(company_id, agent_id, role, assets)


def _compose_from_layers(
    company_id: str,
    agent_id: str,
    layer_root: Path,
    seed: int,
    size: tuple[int, int],
) -> str:
    """Stack allowlisted LimeZu layers deterministically into one sprite."""
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    rng = _seeded_rng(seed)
    for layer_name in ALLOWED_LAYERS:
        layer_dir = layer_root / layer_name
        if not layer_dir.is_dir():
            continue
        parts = sorted(layer_dir.glob("*.png"))
        if not parts:
            continue
        choice = parts[rng() % len(parts)]
        part = Image.open(_resolve_path(str(choice))).convert("RGBA")
        if part.size != size:
            part = part.resize(size, Image.NEAREST)
        canvas.paste(part, (0, 0), part)
    out = _avatar_path(company_id, agent_id)
    canvas.save(out)
    return f"/api/companies/{company_id}/avatars/{agent_id}.png"


def _fallback_sprite(
    company_id: str, agent_id: str, role: str, assets: Path
) -> str:
    """Use a staged character sprite. Copy into the company workspace for isolation."""
    sprite_name = ROLE_FALLBACK.get(role, "dev.png")
    src = assets / sprite_name
    out = _avatar_path(company_id, agent_id)
    if src.exists():
        try:
            img = Image.open(src).convert("RGBA")
            img.save(out)
        except Exception as exc:  # pragma: no cover
            logger.warning("avatar_composer.fallback_failed", error=str(exc))
            _placeholder(out, size=(16, 16))
    else:
        _placeholder(out, size=(16, 16))
    return f"/api/companies/{company_id}/avatars/{agent_id}.png"


def _placeholder(path: Path, size: tuple[int, int] = (16, 16)) -> None:
    img = Image.new("RGBA", size, (90, 110, 160, 255))
    img.save(path)


def _seeded_rng(seed: int):
    """Tiny deterministic PRNG (xorshift) — no global state."""
    state = seed & 0xFFFFFFFF or 1

    def _next() -> int:
        nonlocal state
        state ^= (state << 13) & 0xFFFFFFFF
        state ^= (state >> 17) & 0xFFFFFFFF
        state ^= (state << 5) & 0xFFFFFFFF
        return state & 0xFFFFFFFF

    return _next


def avatar_file_path(company_id: str, agent_id: str) -> Path:
    """Resolve the on-disk avatar path for a company+agent (for static serving)."""
    return _avatar_path(company_id, agent_id)


def is_path_in_company(company_id: str, candidate: Path) -> bool:
    """True only if ``candidate`` resolves inside this company's workspace root."""
    try:
        root = _company_root(company_id).resolve()
        return root in candidate.resolve().parents or candidate.resolve() == root
    except Exception:
        return False
