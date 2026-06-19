# ADR-0008 — No in-product AI/LLM

**Status:** Accepted (2026-06-19)

## Context

Nexus is a **deterministic automation control plane**. Some forward-looking experience proposals
(ADR-0007 and the `specs/05_experience/` drafts) carried an *optional local-model assist* — a Theme
Studio "describe in words" helper and an "Optional Assistant" for explain-failure / suggest-
remediation / draft-change / describe→workflow-scaffold. The operator has directed that **no LLM or
AI of any kind be implemented in this system**; that material was carry-over from a different
project and does not belong here.

## Decision

**Nexus contains no in-product AI/LLM, model, agent, persona, or assistant — anywhere.**

- The **Theme Studio** is purely deterministic (form + color pickers + a deterministic validator).
  There is no model in the theme pipeline.
- There is **no assistant surface** and no `area:ai` work. The `--area-persona` token and any
  "persona/assistant hue" are removed; area overrides are `--area-accent` + `--area-tint` only.
- "Smart"-feeling features (e.g. **similar-past-failures**, **suggested remediations**,
  **success-rate/MTTR insights**, **needs-attention** ranking) are computed from **historical
  run/incident data, the CMDB, and explicit rules** — never a model.
- This supersedes the AI-assist provisions of **ADR-0007** (the Theme Studio "optional local-model
  assist" and the "Optional Assistant"). The rest of ADR-0007 (the token contract, layered
  resolvers, themes-as-data with server-side deterministic validation, protected status semantics,
  accessibility-as-top-layer) stands unchanged.

Backlog effect: roadmap items **B15** and **L48** are withdrawn; the `area:ai` label is retired.

## Consequences

**Good:** the product stays deterministic, auditable, and reproducible — appropriate for an
automation control plane operators trust with production-affecting actions; no model hosting,
prompt-safety, or non-determinism surface area; aligns with the local-first / no-paid-services
guardrails.

**Bad / costs:** features that might otherwise lean on generation (e.g. natural-language → workflow
scaffold) are out of scope; "suggestion"-style helpers must be built from data + rules, which is
more explicit engineering than calling a model.

## Alternatives considered

- **Optional, off-by-default local model behind an adapter:** rejected by directive — even optional
  AI is unwanted in this system.
- **AI only for non-critical surfaces (theming copy, summaries):** rejected — the constraint is
  categorical (no AI anywhere), which also keeps the codebase and threat model simple.
