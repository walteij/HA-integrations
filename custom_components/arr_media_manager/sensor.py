from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity

from .entity import ARRMediaManagerEntity


class ARRStatusSensor(ARRMediaManagerEntity, SensorEntity):
    """Generic status sensor."""

    _attr_icon = "mdi:information-outline"

    def __init__(self, coordinator: Any, config_entry: Any, key: str, name: str, value: Any) -> None:
        super().__init__(coordinator, config_entry, key)
        self._attr_name = name
        self._state = value

    @property
    def native_value(self) -> Any:
        return self._state
