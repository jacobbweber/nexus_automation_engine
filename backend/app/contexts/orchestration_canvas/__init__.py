"""Orchestration Canvas bounded context — the product centerpiece.

A visual DAG engine (ported from the Ava-POC Foundry, re-targeted to backend orchestration):
operators wire nodes into governed, versioned workflows where each actionable node binds to a
backend via the connectors ports. The engine resolves the graph topologically, runs independent
branches in parallel, propagates skips from condition/switch routing, retries with error
branches, and pauses on human/approval gates — streaming step state over WebSocket and
persisting runs/steps. See specs/02_canvas_orchestration/canvas_orchestration.md.
"""
