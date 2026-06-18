"""Execution engine bounded context.

Owns the job lifecycle state machine (PENDING -> RUNNING -> SUCCESS/FAILED/CANCELLED), persists
runs and their log streams, broadcasts live logs over WebSocket, and exposes run telemetry. It
drives work by asking the ``connectors`` registry for the right adapter — it never speaks a
vendor's protocol directly.
"""
