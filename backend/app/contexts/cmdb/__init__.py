"""CMDB bounded context — CI type schemas, lineage specs, and the deterministic health checker.

See specs/07_cmdb/cmdb.md and ADR-0009. The ServiceNow connector remains the ACL that fetches raw
CI data; this context owns what a "healthy / correct" CI means and checks CIs against it.
"""
