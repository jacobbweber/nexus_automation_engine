"""Bounded contexts — each subpackage is a full vertical slice.

Planned contexts (built milestone by milestone; see specs/00_foundation/roadmap.md):
``identity_access``, ``automation_catalog``, ``orchestration_canvas``, ``execution_engine``,
``connectors``, ``observability``. Each contains ``domain/ application/ infrastructure/ api/``
and is added to the app via the platform app factory.
"""
