"""Identifier helpers. All entities use opaque string ids (UUID4 hex)."""

from __future__ import annotations

import uuid


def new_id(prefix: str = "") -> str:
    """Return a fresh opaque id, optionally namespaced with a short prefix.

    Examples: ``new_id()`` -> ``"3f2c..."``; ``new_id("wf")`` -> ``"wf_3f2c..."``.
    The prefix is a readability aid only; ids are compared as whole strings.
    """
    raw = uuid.uuid4().hex
    return f"{prefix}_{raw}" if prefix else raw
