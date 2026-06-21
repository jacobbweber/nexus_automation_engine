"""In-app documentation API (M29.4/29.5).

Serves the authored markdown docs tree (so ``docs/`` stays the single canonical source) and a
**generated reference** built from the system's own live metadata (catalog plain summaries, CMDB
schemas + lineage, pinning rules) so reference docs can't drift from reality.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/docs-site", tags=["docs"])

# repo_root/docs — resolved from this file so it works regardless of CWD.
_DOCS_DIR = Path(__file__).resolve().parents[3] / "docs"


class DocPage(BaseModel):
    path: str  # relative to docs/, POSIX-style (e.g. "concepts/atomic-automation.md")
    title: str


def _title_of(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


@router.get("/pages", response_model=list[DocPage])
def list_pages() -> list[DocPage]:
    if not _DOCS_DIR.is_dir():
        return []
    pages: list[DocPage] = []
    for md in sorted(_DOCS_DIR.rglob("*.md")):
        rel = md.relative_to(_DOCS_DIR).as_posix()
        pages.append(DocPage(path=rel, title=_title_of(md.read_text(encoding="utf-8"), rel)))
    return pages


@router.get("/page")
def get_page(path: str) -> dict[str, str]:
    # Resolve + confine to the docs dir (no traversal outside it).
    target = (_DOCS_DIR / path).resolve()
    if not str(target).startswith(str(_DOCS_DIR.resolve())) or target.suffix != ".md":
        raise HTTPException(status_code=400, detail="invalid doc path")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="doc not found")
    return {"path": path, "content": target.read_text(encoding="utf-8")}


@router.get("/reference")
def reference() -> dict[str, object]:
    """Reference generated from live metadata so it can't drift from the running platform."""
    from app.contexts.automation_catalog.application.service import CatalogService
    from app.contexts.cmdb.application.service import CmdbLineageService, CmdbSchemaService
    from app.contexts.determinism.infrastructure.repository import PinningRuleRepository

    blocks = [
        {
            "name": t.name,
            "connector": str(t.connector),
            "action": t.action,
            "idempotency": str(t.idempotency),
            "risk": str(t.risk),
            "summary": (
                f"{t.plain_summary.action} {t.plain_summary.outcome}" if t.plain_summary else ""
            ),
        }
        for t in CatalogService().list_all()
    ]
    schemas = [
        {
            "type": s.type,
            "label": s.label,
            "required_fields": [f.name for f in s.fields if f.required],
            "required_tags": s.required_tags,
        }
        for s in CmdbSchemaService().list_schemas()
    ]
    lineage = [
        {"type": lin.type, "relationships": [r.name for r in lin.relationships]}
        for lin in CmdbLineageService().list_lineage()
    ]
    rules = [
        {
            "name": r.name,
            "selector": r.selector.model_dump(),
            "workflow": r.workflow,
            "trigger": str(r.trigger),
            "enforcement": str(r.enforcement),
        }
        for r in PinningRuleRepository().list_all()
    ]
    return {
        "building_blocks": blocks,
        "cmdb_schemas": schemas,
        "cmdb_lineage": lineage,
        "pinning_rules": rules,
    }
