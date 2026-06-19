"""Incident Management bounded context (3.0).

Every failed job or workflow run is auto-captured as an **incident card** on a triage kanban
board (New → Triage → Investigating → Resolved), linked to the failing run. Operators can convert
an incident into a draft **remediation workflow** on the canvas. See
specs/00_foundation/vision_operator_experience.md (pillar 4).
"""
