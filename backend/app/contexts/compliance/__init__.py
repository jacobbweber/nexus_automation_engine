"""Compliance context — continuous posture from scheduled drift sweeps (v4.0 Pillar B, M25.4).

Periodically evaluates published workflows in compliance mode (no mutation), snapshots the estate's
posture, and opens incidents on drift. Consumes connectors' DriftReport + the canvas compliance use
case; never owns drift evaluation itself.
"""
