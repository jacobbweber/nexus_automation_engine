"""Review context — multi-audience human review & run-level approval (v4.0 Pillar C).

Deterministically classifies a change (standard/normal/emergency), builds audience-tailored Change
Review Packets (technical / non-technical / executive + flowchart) from building blocks' plain
summaries, and gates approval-required runs. No AI (ADR-0008) — composition + rules only.
"""
