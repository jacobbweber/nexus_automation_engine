"""Determinism context — deterministic policy & workflow pinning (v4.0 Pillar D).

Pinning rules guarantee a workflow for matching CIs (management-by-invariant). A reconciler turns
rules into action — assert (compliance), enforce (review-gated reconcile), or gate (block the
triggering change) — and a coverage preview answers "what is guaranteed, and where does reality not
match?" Composes M24 (selectors over schema), M25 (compliance), M26 (review), M11/M16.
"""
