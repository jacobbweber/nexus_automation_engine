"""Shared helpers for simulation adapters: ANSI coloring and realistic timing jitter."""

from __future__ import annotations

import asyncio
import random

from app.platform.config import get_settings

# ANSI escape codes — the frontend terminal renders these (mimics a real operator console).
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
GREY = "\033[90m"


def color(text: str, code: str, bold: bool = False) -> str:
    prefix = (BOLD if bold else "") + code
    return f"{prefix}{text}{RESET}"


async def jitter() -> None:
    """Sleep a realistic, randomized amount between log lines (disabled in tests)."""
    settings = get_settings()
    if not settings.sim_jitter:
        return
    await asyncio.sleep(random.uniform(0.1, settings.sim_jitter_max_seconds))
