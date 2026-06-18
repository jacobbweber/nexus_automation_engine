"""VariablePool — the typed, expression-capable reference resolver for the canvas engine.

Ported and cleaned from the Ava-POC Foundry. It maps ``node_id -> output`` (plus arbitrary
keys) and resolves ``{{ ... }}`` references inside any string / nested structure with three
behaviors (see specs/02_canvas_orchestration/canvas_orchestration.md §"Typed VariablePool"):

1. **Typed exact-replacement** — a string that is exactly one ``{{ expr }}`` returns the
   resolved *value* (preserving its Python type: dict, list, int, ...), not a string.
2. **Safe expression evaluation** — dot-notation, indexing, and simple math/logic are evaluated
   against the pool with a restricted builtins set (never arbitrary code / no imports).
3. **Jinja2-lite templating** — strings with surrounding text are rendered as Jinja2 templates,
   supporting loops/conditionals over the same nested pool.

Flat dot-notation keys (``"a.b"``) are also exposed as nested structures (``a.b``) so both
``{{a.b}}`` and templating ``{{ a.b }}`` resolve.
"""

from __future__ import annotations

import logging
from typing import Any

import jinja2

log = logging.getLogger("nexus.variable_pool")

_SAFE_BUILTINS: dict[str, Any] = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "bool": bool,
    "range": range,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "sorted": sorted,
    "True": True,
    "False": False,
    "None": None,
}


class _AttrDict:
    """Wraps a dict so expressions can use both attribute and item access (``a.b`` / ``a['b']``)."""

    __slots__ = ("_d",)

    def __init__(self, d: dict[str, Any]) -> None:
        self._d = d

    def __getattr__(self, name: str) -> Any:
        if name in self._d:
            return _wrap(self._d[name])
        raise AttributeError(name)

    def __getitem__(self, key: Any) -> Any:
        return _wrap(self._d[key])

    def __len__(self) -> int:
        return len(self._d)

    def __iter__(self):
        return iter(self._d)

    def __contains__(self, key: Any) -> bool:
        return key in self._d

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return repr(self._d)


def _wrap(val: Any) -> Any:
    if isinstance(val, dict):
        return _AttrDict(val)
    if isinstance(val, list):
        return [_wrap(x) for x in val]
    if isinstance(val, tuple):
        return tuple(_wrap(x) for x in val)
    return val


def _unwrap(val: Any) -> Any:
    if isinstance(val, _AttrDict):
        return val._d
    if isinstance(val, list):
        return [_unwrap(x) for x in val]
    if isinstance(val, tuple):
        return tuple(_unwrap(x) for x in val)
    return val


class VariablePool:
    def __init__(self, initial_vars: dict[str, Any] | None = None) -> None:
        self.pool: dict[str, Any] = {}
        if initial_vars:
            self.pool.update(initial_vars)

    def set(self, path: str, value: Any) -> None:
        """Store a value under a (possibly dot-notation) key."""
        self.pool[path] = value

    def get(self, path: str, default: Any = None) -> Any:
        if path in self.pool:
            return self.pool[path]
        try:
            return self.evaluate(path)
        except Exception:
            return default

    def resolve(self, expression: Any) -> Any:
        """Resolve a template string, or recurse through a dict/list of them."""
        if isinstance(expression, str):
            stripped = expression.strip()
            # Typed exact-replacement fast path: a lone {{ expr }}.
            if (
                stripped.startswith("{{")
                and stripped.endswith("}}")
                and stripped.count("{{") == 1
                and stripped.count("}}") == 1
            ):
                inner = stripped[2:-2].strip()
                try:
                    return self.evaluate(inner)
                except Exception:
                    pass  # fall through to template rendering
            # Otherwise render as a Jinja2 template against the nested pool.
            try:
                env = jinja2.Environment(autoescape=False, undefined=jinja2.ChainableUndefined)
                template = env.from_string(expression)
                return template.render(**self._nested())
            except Exception as exc:  # noqa: BLE001 - rendering must never crash resolution
                log.warning("Jinja2 render failed for %r: %s", expression, exc)
                return expression
        if isinstance(expression, dict):
            return {k: self.resolve(v) for k, v in expression.items()}
        if isinstance(expression, list):
            return [self.resolve(x) for x in expression]
        return expression

    def evaluate(self, expr: str) -> Any:
        """Evaluate a single expression against the pool (restricted; no imports/builtins)."""
        nested = self._nested()
        scope = {k: _wrap(v) for k, v in nested.items()}
        scope["__builtins__"] = _SAFE_BUILTINS
        try:
            return _unwrap(eval(expr, scope, {}))  # noqa: S307 - restricted builtins, no imports
        except Exception:
            # Fallback: treat as a literal key or a manual dotted lookup.
            if expr in self.pool:
                return self.pool[expr]
            curr: Any = nested
            for part in expr.split("."):
                if isinstance(curr, dict) and part in curr:
                    curr = curr[part]
                else:
                    raise KeyError(f"Could not resolve {expr!r} in pool") from None
            return curr

    def _nested(self) -> dict[str, Any]:
        """Expand flat dot-notation keys into a nested dict structure."""
        nested: dict[str, Any] = {}
        for key, value in self.pool.items():
            if "." in key:
                parts = key.split(".")
                curr = nested
                for part in parts[:-1]:
                    if not isinstance(curr.get(part), dict):
                        curr[part] = {}
                    curr = curr[part]
                curr[parts[-1]] = value
            else:
                nested[key] = value
        return nested
