"""Deterministic theme validator (Python port of the frontend `theme-schema.ts` gate).

Same contract: a theme may only set an allow-listed set of semantic color tokens for light + dark,
all valid hex, complete, and meeting WCAG-AA contrast on the legibility-critical pairs. This is the
server-side gate — a theme is only stored/served if it passes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

THEME_SCHEMA = "nexus-theme/v1"

ALLOWED_TOKEN_KEYS: set[str] = {
    "--bg",
    "--surface",
    "--surface-2",
    "--surface-3",
    "--overlay",
    "--text",
    "--text-muted",
    "--text-subtle",
    "--text-onAccent",
    "--border",
    "--border-strong",
    "--divider",
    "--accent",
    "--accent-hover",
    "--accent-active",
    "--accent-contrast",
    "--accent-soft",
    "--success",
    "--warn",
    "--danger",
    "--info",
    "--run-running",
    "--run-ok",
    "--run-warn",
    "--run-failed",
    "--run-skipped",
    "--focus",
    "--selection",
    "--link",
}

REQUIRED_TOKEN_KEYS: tuple[str, ...] = (
    "--bg",
    "--surface",
    "--surface-2",
    "--text",
    "--text-muted",
    "--border",
    "--accent",
    "--accent-hover",
    "--accent-contrast",
    "--success",
    "--warn",
    "--danger",
    "--info",
    "--run-running",
    "--run-ok",
    "--run-warn",
    "--run-failed",
    "--run-skipped",
    "--focus",
)

_RUN_KEYS = ("--run-running", "--run-ok", "--run-warn", "--run-failed", "--run-skipped")
_HEX = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

AA_NORMAL = 4.5
AA_LARGE = 3.0


def is_hex(v: object) -> bool:
    return isinstance(v, str) and bool(_HEX.match(v.strip()))


def _expand(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _chan(c: int) -> float:
    s = c / 255
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4


def luminance(hex_str: str) -> float:
    r, g, b = _expand(hex_str)
    return 0.2126 * _chan(r) + 0.7152 * _chan(g) + 0.0722 * _chan(b)


def contrast_ratio(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = (la, lb) if la >= lb else (lb, la)
    return (hi + 0.05) / (lo + 0.05)


@dataclass
class ValidationResult:
    ok: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _validate_mode(mode: str, tokens: dict, out: ValidationResult) -> None:
    for k, v in tokens.items():
        if k not in ALLOWED_TOKEN_KEYS:
            out.errors.append(
                f"{mode}: disallowed token '{k}' (themes set only semantic color tokens)"
            )
            continue
        if not is_hex(v):
            out.errors.append(f"{mode}: '{k}' is not a valid hex color ('{v}')")
    for k in REQUIRED_TOKEN_KEYS:
        if k not in tokens:
            out.errors.append(f"{mode}: missing required token '{k}'")

    def ok(k: str) -> bool:
        return is_hex(tokens.get(k))

    if ok("--text") and ok("--bg") and contrast_ratio(tokens["--text"], tokens["--bg"]) < AA_NORMAL:
        out.errors.append(f"{mode}: body text fails AA on bg")
    if (
        ok("--text")
        and ok("--surface")
        and contrast_ratio(tokens["--text"], tokens["--surface"]) < AA_NORMAL
    ):
        out.errors.append(f"{mode}: body text fails AA on surface")
    if (
        ok("--text-muted")
        and ok("--bg")
        and contrast_ratio(tokens["--text-muted"], tokens["--bg"]) < AA_NORMAL
    ):
        out.errors.append(f"{mode}: muted text fails AA on bg")
    if (
        ok("--accent-contrast")
        and ok("--accent")
        and contrast_ratio(tokens["--accent-contrast"], tokens["--accent"]) < AA_NORMAL
    ):
        out.errors.append(f"{mode}: accent-contrast fails AA on accent")
    for k in _RUN_KEYS:
        if ok(k) and ok("--bg") and contrast_ratio(tokens[k], tokens["--bg"]) < AA_LARGE:
            out.errors.append(f"{mode}: {k} fails AA-large on bg")


def validate_theme(candidate: object) -> ValidationResult:
    out = ValidationResult()
    if not isinstance(candidate, dict):
        out.errors.append("theme must be an object")
        return out
    if candidate.get("$schema") != THEME_SCHEMA:
        out.errors.append(f"$schema must be '{THEME_SCHEMA}'")
    if not isinstance(candidate.get("id"), str) or not candidate.get("id"):
        out.errors.append("missing id")
    if not isinstance(candidate.get("name"), str) or not candidate.get("name"):
        out.errors.append("missing name")
    if candidate.get("base") not in ("light", "dark"):
        out.errors.append("base must be 'light' or 'dark'")
    tokens = candidate.get("tokens")
    if not isinstance(tokens, dict):
        out.errors.append("missing tokens")
        return out
    if not isinstance(tokens.get("light"), dict):
        out.errors.append("missing tokens.light")
    else:
        _validate_mode("light", tokens["light"], out)
    if not isinstance(tokens.get("dark"), dict):
        out.errors.append("missing tokens.dark")
    else:
        _validate_mode("dark", tokens["dark"], out)
    out.ok = len(out.errors) == 0
    return out
