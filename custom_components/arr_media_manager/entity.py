from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class ARRMediaManagerEntity(Entity):
    """Base entity for ARR media manager devices."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: Any, config_entry: Any, key: str) -> None:
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.entity_key = key
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.data.get("instance_name", "ARR Media Manager"),
            manufacturer="ARR",
            model=config_entry.data.get("application", "arr"),
            configuration_url=config_entry.data.get("base_url"),
            sw_version=self.coordinator.data.get("status", {}).get("version") if self.coordinator.data else None,
        )

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success
