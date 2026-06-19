"""Regression: leased secrets reach the pool for downstream use but are never persisted (S4)."""

from __future__ import annotations

from app.contexts.orchestration_canvas.application.node_actions import _secret_lease
from app.shared_kernel.variable_pool import VariablePool


async def test_secret_lease_masks_persisted_output_but_exposes_to_pool():
    pool = VariablePool()
    out = await _secret_lease(
        {"safe": "prod", "object_name": "db_admin", "bind_as": "cred"}, pool
    )
    # The returned/persisted output never carries the real secret.
    assert out["secret"] == "***masked***"
    assert out["username"]
    assert out["lease_id"]

    # Downstream nodes can still use the real secret via the pool binding.
    real = pool.resolve("{{cred.secret}}")
    assert real and real != "***masked***"
    # And the masked output value is not the real secret.
    assert real != out["secret"]
