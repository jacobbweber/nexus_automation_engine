"""Seed a realistic set of CI type schemas so the CMDB-as-contract has substance out of the box.

Idempotent: only seeds when the registry is empty. Schemas are the *definitions*; lineage (24.2)
and the health checker (24.3) consume them. Field/tag choices mirror a believable enterprise CMDB
(VMware/Pure/Cohesity/ServiceNow estate).
"""

from __future__ import annotations

from app.contexts.cmdb.domain.lineage import (
    Cardinality,
    Direction,
    LineageRelationship,
    LineageSpec,
)
from app.contexts.cmdb.domain.models import CITypeSchema, FieldDef, FieldType
from app.contexts.cmdb.infrastructure.repository import (
    CITypeSchemaRepository,
    LineageSpecRepository,
)

_ENVS = ["Production", "Staging", "Development"]
_LIFECYCLE = ["operational", "maintenance", "retired"]

# Tags every managed CI is expected to carry (the deterministic tagging discipline).
_COMMON_TAGS = ["owner", "team", "environment", "cost_center"]


def _schemas() -> list[CITypeSchema]:
    return [
        CITypeSchema(
            type="vm",
            label="Virtual Machine",
            description="A virtual machine (compute) — the workhorse compute CI.",
            naming_pattern=r"^[a-z][a-z0-9-]{2,40}$",
            required_tags=[*_COMMON_TAGS, "backup_tier"],
            fields=[
                FieldDef(name="name", label="Name", required=True),
                FieldDef(name="fqdn", label="FQDN", required=True),
                FieldDef(
                    name="env",
                    label="Environment",
                    datatype=FieldType.ENUM,
                    allowed_values=_ENVS,
                    required=True,
                ),
                FieldDef(
                    name="lifecycle_state",
                    label="Lifecycle state",
                    datatype=FieldType.ENUM,
                    allowed_values=_LIFECYCLE,
                    required=True,
                    default="operational",
                ),
                FieldDef(name="os", label="Operating system", required=True),
                FieldDef(name="cpu", label="vCPU", datatype=FieldType.INTEGER, required=True),
                FieldDef(
                    name="memory_gb", label="Memory (GB)", datatype=FieldType.INTEGER, required=True
                ),
            ],
        ),
        CITypeSchema(
            type="host",
            label="Hypervisor Host",
            description="An ESXi / hypervisor host that runs VMs.",
            naming_pattern=r"^[a-z][a-z0-9.-]{2,60}$",
            required_tags=[*_COMMON_TAGS],
            fields=[
                FieldDef(name="name", label="Name", required=True),
                FieldDef(
                    name="env",
                    label="Environment",
                    datatype=FieldType.ENUM,
                    allowed_values=_ENVS,
                    required=True,
                ),
                FieldDef(
                    name="lifecycle_state",
                    label="Lifecycle state",
                    datatype=FieldType.ENUM,
                    allowed_values=_LIFECYCLE,
                    required=True,
                    default="operational",
                ),
                FieldDef(name="model", label="Hardware model", required=True),
            ],
        ),
        CITypeSchema(
            type="cluster",
            label="Compute Cluster",
            description="A vSphere/compute cluster grouping hosts.",
            naming_pattern=r"^[a-z][a-z0-9-]{2,40}$",
            required_tags=[*_COMMON_TAGS],
            fields=[
                FieldDef(name="name", label="Name", required=True),
                FieldDef(
                    name="env",
                    label="Environment",
                    datatype=FieldType.ENUM,
                    allowed_values=_ENVS,
                    required=True,
                ),
                FieldDef(
                    name="ha_enabled", label="HA enabled", datatype=FieldType.BOOLEAN, required=True
                ),
            ],
        ),
        CITypeSchema(
            type="datastore",
            label="Datastore",
            description="A VMware datastore backed by a storage volume.",
            naming_pattern=r"^[a-z][a-z0-9-]{2,40}$",
            required_tags=[*_COMMON_TAGS],
            fields=[
                FieldDef(name="name", label="Name", required=True),
                FieldDef(
                    name="env",
                    label="Environment",
                    datatype=FieldType.ENUM,
                    allowed_values=_ENVS,
                    required=True,
                ),
                FieldDef(
                    name="lifecycle_state",
                    label="Lifecycle state",
                    datatype=FieldType.ENUM,
                    allowed_values=_LIFECYCLE,
                    required=True,
                    default="operational",
                ),
                FieldDef(
                    name="capacity_gb",
                    label="Capacity (GB)",
                    datatype=FieldType.INTEGER,
                    required=True,
                ),
            ],
        ),
        CITypeSchema(
            type="volume",
            label="Storage Volume",
            description="A backing storage volume (e.g. Pure FlashArray).",
            naming_pattern=r"^[a-z][a-z0-9-]{2,40}$",
            required_tags=[*_COMMON_TAGS],
            fields=[
                FieldDef(name="name", label="Name", required=True),
                FieldDef(name="array", label="Storage array", required=True),
                FieldDef(
                    name="size_gb", label="Size (GB)", datatype=FieldType.INTEGER, required=True
                ),
                FieldDef(name="protection_group", label="Protection group", required=False),
            ],
        ),
        CITypeSchema(
            type="backup_policy",
            label="Backup Policy",
            description="A data-protection policy (e.g. Cohesity protection job).",
            required_tags=["owner", "team"],
            fields=[
                FieldDef(name="name", label="Name", required=True),
                FieldDef(
                    name="rpo_hours", label="RPO (hours)", datatype=FieldType.INTEGER, required=True
                ),
                FieldDef(
                    name="retention_days",
                    label="Retention (days)",
                    datatype=FieldType.INTEGER,
                    required=True,
                ),
            ],
        ),
        CITypeSchema(
            type="application",
            label="Business Application",
            description="A logical business application composed of underlying CIs.",
            required_tags=[*_COMMON_TAGS, "criticality"],
            fields=[
                FieldDef(name="name", label="Name", required=True),
                FieldDef(
                    name="criticality",
                    label="Criticality",
                    datatype=FieldType.ENUM,
                    allowed_values=["tier-1", "tier-2", "tier-3"],
                    required=True,
                ),
                FieldDef(
                    name="env",
                    label="Environment",
                    datatype=FieldType.ENUM,
                    allowed_values=_ENVS,
                    required=True,
                ),
            ],
        ),
    ]


def seed_cmdb_schemas(repo: CITypeSchemaRepository | None = None) -> int:
    """Seed default CI type schemas. Returns the number created (0 if already populated)."""
    repo = repo or CITypeSchemaRepository()
    if repo.count() > 0:
        return 0
    created = 0
    for schema in _schemas():
        repo.upsert(schema)
        created += 1
    return created


def _up(name: str, target: str, card: Cardinality = Cardinality.ONE, required: bool = True):
    return LineageRelationship(
        name=name, target_type=target, direction=Direction.UP, cardinality=card, required=required
    )


def _lineage() -> list[LineageSpec]:
    """The required relationships that make each CI type 'whole' (only references seeded types).

    Forms a DAG: application -> vm -> {host -> cluster, datastore -> volume -> backup_policy,
    backup_policy}. No cycle in the required-up graph.
    """
    return [
        LineageSpec(
            type="vm",
            relationships=[
                _up("host", "host"),
                _up("datastores", "datastore", Cardinality.MANY),
                _up("backup_policy", "backup_policy"),
            ],
        ),
        LineageSpec(type="host", relationships=[_up("cluster", "cluster")]),
        LineageSpec(type="cluster", relationships=[]),  # top-level grouping
        LineageSpec(type="datastore", relationships=[_up("volume", "volume")]),
        LineageSpec(type="volume", relationships=[_up("backup_policy", "backup_policy")]),
        LineageSpec(type="backup_policy", relationships=[]),
        LineageSpec(
            type="application",
            relationships=[
                LineageRelationship(
                    name="members",
                    target_type="vm",
                    direction=Direction.DOWN,
                    cardinality=Cardinality.MANY,
                    required=True,
                )
            ],
        ),
    ]


def seed_cmdb_lineage(repo: LineageSpecRepository | None = None) -> int:
    """Seed default lineage specs. Returns the number created (0 if already populated)."""
    repo = repo or LineageSpecRepository()
    if repo.count() > 0:
        return 0
    created = 0
    for spec in _lineage():
        repo.upsert(spec)
        created += 1
    return created
