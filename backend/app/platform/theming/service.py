"""Theme storage over a writable directory (mounted as a Docker volume). Only validated themes are
served or saved; a revision (max mtime) powers the change stream."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.platform.config import get_settings
from app.platform.theming.validation import ValidationResult, validate_theme

_SLUG = re.compile(r"[^a-z0-9-]")


def _dir() -> Path:
    d = Path(get_settings().themes_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def slug(theme_id: str) -> str:
    s = _SLUG.sub("-", theme_id.strip().lower()).strip("-")
    return s or "theme"


def list_themes() -> list[dict]:
    """Return all *valid* user themes from the volume (invalid files are skipped, not served)."""
    themes: list[dict] = []
    for path in sorted(_dir().glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if validate_theme(doc).ok:
            themes.append(doc)
    return themes


def revision() -> float:
    """Max mtime across theme files — changes whenever a theme is added/edited/removed."""
    mtimes = [p.stat().st_mtime for p in _dir().glob("*.json")]
    return max(mtimes, default=0.0)


def save_theme(doc: object) -> ValidationResult:
    """Validate then persist a user theme. Returns the validation result (caller maps to HTTP)."""
    result = validate_theme(doc)
    if not result.ok or not isinstance(doc, dict):
        return result
    path = _dir() / f"{slug(str(doc['id']))}.json"
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return result


def delete_theme(theme_id: str) -> bool:
    path = _dir() / f"{slug(theme_id)}.json"
    if path.exists():
        path.unlink()
        return True
    return False
