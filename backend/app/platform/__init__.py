"""Platform — the composition root and cross-cutting infrastructure.

Wires the FastAPI application, async database (SQLite WAL), configuration, and security
middleware. Contexts plug their api routers into the app here; no business rules live in this
package.
"""
