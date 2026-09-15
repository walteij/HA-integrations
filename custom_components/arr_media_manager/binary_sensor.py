from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity

from .entity import ARRMediaManagerEntity


class ARRBinarySensor(ARRMediaManagerEntity, BinarySensorEntity):
    """Generic binary sensor."""

    def __init__(self, coordinator: Any, config_entry: Any, key: str, name: str, state: bool) -> None:
        super().__init__(coordinator, config_entry, key)
        self._attr_name = name
        self._state = state

    @property
    def is_on(self) -> bool:
        return self._state
