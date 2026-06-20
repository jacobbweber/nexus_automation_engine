"""GitOps context — config-as-code backbone (v4.0 Pillar E).

Serializes all config artifacts to a canonical, deterministic layout and versions them in a local
Git repo (system-of-record + DR backup + history/diff/restore + optional pull/reconcile). Local git
only (no remote/paid); audit commit messages carry the actor, never secrets. Deterministic.
"""
