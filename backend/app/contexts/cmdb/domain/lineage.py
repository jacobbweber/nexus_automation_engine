"""CI lineage domain models + pure validators.

Lineage is *what makes a CI whole*: the typed relationships (with direction + cardinality) a CI of
a given type must resolve. Distinct from a CI's own fields (those live in CITypeSchema). The health
checker (24.3) consumes both. Validation is deterministic (ADR-0008).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Direction(StrEnum):
    UP = "up"  # a dependency / parent (the CI depends on the target — e.g. vm -> host)
    DOWN = "down"  # a dependent / child (the target depends on the CI — e.g. application -> vm)


class Cardinality(StrEnum):
    ONE = "one"
    MANY = "many"


class LineageRelationship(BaseModel):
    name: str  # relationship label, unique within a spec (e.g. "host", "datastores")
    target_type: str  # the related CI type (must be a known CI type)
    direction: Direction = Direction.UP
    cardinality: Cardinality = Cardinality.ONE
    required: bool = True


class LineageSpec(BaseModel):
    type: str
    relationships: list[LineageRelationship] = Field(default_factory=list)


def validate_lineage(spec: LineageSpec, known_types: set[str]) -> list[str]:
    """Validate a single lineage spec against the set of known CI types. Returns errors."""
    errors: list[str] = []
    if not spec.type.strip():
        errors.append("lineage 'type' must be non-empty")
    seen: set[str] = set()
    for r in spec.relationships:
        if not r.name.strip():
            errors.append("a relationship has an empty name")
            continue
        if r.name in seen:
            errors.append(f"duplicate relationship name: '{r.name}'")
        seen.add(r.name)
        if r.target_type not in known_types:
            errors.append(f"relationship '{r.name}' targets unknown CI type '{r.target_type}'")
    return errors


def validate_lineage_set(specs: list[LineageSpec]) -> list[str]:
    """Validate a whole set: each spec well-formed against the others, and no cycle in the
    required *up* (dependency) graph (which would make a CI impossible to ever fully resolve)."""
    known = {s.type for s in specs}
    errors: list[str] = []
    for s in specs:
        errors.extend(validate_lineage(s, known))

    # required-up dependency graph: type -> {target_types it must depend on}
    deps: dict[str, set[str]] = {
        s.type: {
            r.target_type
            for r in s.relationships
            if r.direction == Direction.UP and r.required and r.target_type in known
        }
        for s in specs
    }
    cycle = _find_cycle(deps)
    if cycle:
        errors.append(f"required-dependency cycle in lineage: {' -> '.join(cycle)}")
    return errors


def _find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    """Return a cycle path if the directed graph has one, else None (DFS with colors)."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in graph}
    path: list[str] = []

    def visit(node: str) -> list[str] | None:
        color[node] = GRAY
        path.append(node)
        for nxt in graph.get(node, set()):
            if nxt not in color:  # target outside graph keys — no outgoing edges
                continue
            if color[nxt] == GRAY:
                return [*path[path.index(nxt) :], nxt]
            if color[nxt] == WHITE:
                found = visit(nxt)
                if found:
                    return found
        path.pop()
        color[node] = BLACK
        return None

    for n in graph:
        if color[n] == WHITE:
            found = visit(n)
            if found:
                return found
    return None
