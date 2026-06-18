"""Simulation adapters — stateful, realistic stand-ins for real backends.

They stream genuine-looking Terraform/Ansible/script output with ANSI colors and timing jitter,
honor check/diff mode, and (for systems of record) return believable inventory, leases,
approvals, and telemetry. They satisfy exactly the same ports as real adapters will.
"""
