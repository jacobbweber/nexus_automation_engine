"""Scheduling bounded context (2.0).

Schedule workflows to run automatically — interval or daily triggers, with optional maintenance
windows (run only inside an allowed hour range). A background ticker claims due schedules and
dispatches them through the canvas. See specs/00_foundation/vision_2_0.md (theme B).
"""
