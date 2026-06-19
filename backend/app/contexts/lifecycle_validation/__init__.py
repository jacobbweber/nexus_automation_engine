"""Lifecycle Validation bounded context (3.0) — "origin-story validation".

The elegant single gate: no automation is *valid & approved* unless it carries required metadata
(authored_by, approved_date, last_updated, last_reviewed, CI type + heritage) AND passes a CMDB
CI-lifecycle consistency check. Validation runs at **build/save** and again **pre-launch**; a run
is rejected if its target contradicts the CMDB lifecycle (e.g. a datastore that's a cluster
member, or a retired CI). The check is governed by one **admin-editable ValidationPolicy** that
every execution path consults — so all automation stays stable and true.

See specs/00_foundation/vision_operator_experience.md and the operator backlog.
"""
