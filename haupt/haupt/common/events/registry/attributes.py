from haupt.common.events.event import Attribute

OWNER_ATTRIBUTES = (Attribute("id"), Attribute("name"))

OWNER_RESOURCE_ATTRIBUTES = (
    Attribute("uuid", is_uuid=True),
    Attribute("name"),
    Attribute("owner.name"),
    Attribute("owner_id"),
)

AGENT_RESOURCE_ATTRIBUTES = (
    Attribute("uuid", is_uuid=True),
    Attribute("name"),
    Attribute("owner.name"),
    Attribute("owner_id"),
    Attribute("agent_name"),
    Attribute("agent_uuid"),
    Attribute("agent_id"),
)

SERVICE_ACCOUNT_RESOURCE_ATTRIBUTES = (
    Attribute("uuid", is_uuid=True),
    Attribute("name"),
    Attribute("owner.name"),
    Attribute("owner_id"),
    Attribute("sa_name"),
    Attribute("sa_uuid"),
    Attribute("sa_id"),
)

PROJECT_OWNER_ATTRIBUTES = (
    Attribute("name"),
    Attribute("owner.name"),
    Attribute("owner_id"),
)

PROJECT_RESOURCE_ATTRIBUTES = (
    Attribute("uuid", is_uuid=True),
    Attribute("project.uuid", is_uuid=True),
    Attribute("project.name"),
    Attribute("project.owner.name"),
    Attribute("name", is_required=False),
)

PROJECT_RESOURCE_OWNER_ATTRIBUTES = (
    Attribute("uuid", is_uuid=True),
    Attribute("project.uuid", is_uuid=True),
    Attribute("project.name"),
    Attribute("project.owner.name"),
    Attribute("owner_id"),
    Attribute("name", is_required=False),
)

PROJECT_RUN_EXECUTOR_ATTRIBUTES = (
    Attribute("uuid", is_uuid=True),
    Attribute("project.uuid", is_uuid=True),
    Attribute("project.name"),
    Attribute("project.owner.name"),
    Attribute("name", is_required=False),
    Attribute("is_managed", attr_type=bool, is_required=False),
    Attribute("managed_by", attr_type=str, is_required=False),
    Attribute("pipeline_id", attr_type=int, is_required=False),
)

PROJECT_RUN_EXECUTOR_OWNER_ATTRIBUTES = (
    Attribute("uuid", is_uuid=True),
    Attribute("project.uuid", is_uuid=True),
    Attribute("project.name"),
    Attribute("owner_id"),
    Attribute("project.owner.name"),
    Attribute("name", is_required=False),
    Attribute("is_managed", attr_type=bool, is_required=False),
    Attribute("managed_by", attr_type=str, is_required=False),
    Attribute("pipeline_id", attr_type=int, is_required=False),
)
