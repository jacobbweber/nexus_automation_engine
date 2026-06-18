"""Identity & Access bounded context.

Owns who you are and what you may touch: users, organizations, teams, asset groups, and the
RBAC entitlement evaluation that runs Organization -> Team -> AssetGroup. A global role
(admin/engineer/operator/consumer) is the baseline; explicit resource permissions refine it.
"""
