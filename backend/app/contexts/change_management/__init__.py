"""Change Management bounded context (2.0).

Wraps execution in governed change: reusable **change templates** (standard ITSM fields),
per-resource **change-control policies** (auto change control + require-approved-change), and
**change records** opened/closed around runs. This is what turns ad-hoc automation into audited,
CAB-aware change so operators can self-serve against production safely. See
specs/00_foundation/vision_2_0.md and ADR-0005.
"""
