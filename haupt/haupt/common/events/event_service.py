from typing import Any, Mapping, Optional

from haupt.common.events.event import Event
from haupt.common.service_interface import Service


class EventService(Service):
    __all__ = ("record",)

    event_manager = None

    def can_handle(self, event_type: str) -> bool:
        return isinstance(event_type, str) and self.event_manager.knows(event_type)

    def get_event(
        self,
        event_type: str,
        event_data: Mapping = None,
        instance: Any = None,
        **kwargs,
    ) -> Event:
        if instance or not event_data:
            return self.event_manager.get(event_type).from_instance(instance, **kwargs)
        return self.event_manager.get(event_type).from_event_data(
            event_data=event_data, **kwargs
        )

    def record(
        self,
        event_type: str,
        event_data: Mapping = None,
        instance: Any = None,
        **kwargs,
    ) -> Optional[Event]:
        """Validate and record an event.

        >>> record('event.action', object_instance)
        """
        if not self.is_setup:
            return
        if not self.can_handle(event_type=event_type):
            return

        event = self.get_event(
            event_type=event_type, event_data=event_data, instance=instance, **kwargs
        )
        self.record_event(event)
        return event

    @staticmethod
    def _preprocess_event_data(event: Event):
        if event.owner_name and event.owner_name in event.data:
            event.data["owner_name"] = event.data.pop(event.owner_name)
        elif "owner.name" in event.data:
            event.data["owner_name"] = event.data.pop("owner.name")
        if event.owner_id and event.owner_id in event.data:
            event.data["owner_id"] = event.data.pop(event.owner_id)
        elif "owner.id" in event.data:
            event.data["owner_id"] = event.data.pop("owner.id")
        # Fallback to getting owner_id from instance
        if "owner_id" not in event.data and event.instance:
            instance = event.instance
            if instance.__class__.__name__ == "Organization":
                event.data["owner_id"] = instance.id
            elif hasattr(instance, "organization_id") and instance.organization_id:
                event.data["owner_id"] = instance.organization_id
            elif hasattr(instance, "owner_id") and instance.owner_id:
                event.data["owner_id"] = instance.owner_id
            elif hasattr(instance, "project") and instance.project:
                event.data["owner_id"] = instance.project.owner_id
        return event

    @staticmethod
    def _get_event_uuid(event: Event):
        entity_uuid = None
        if event.entity_uuid:
            if event.entity_uuid == "uuid":
                entity_uuid = event.data.get(event.entity_uuid, event.instance_uuid)
            else:
                entity_uuid = event.data.get(event.entity_uuid)
        return entity_uuid

    def record_event(self, event: Event):
        """Record an event.

        >>> record_event(Event())
        """
