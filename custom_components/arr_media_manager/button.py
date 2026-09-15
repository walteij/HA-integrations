from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity

from .entity import ARRMediaManagerEntity


class ARRButton(ARRMediaManagerEntity, ButtonEntity):
    """Generic button entity."""

    def __init__(self, coordinator: Any, config_entry: Any, key: str, name: str, command: str) -> None:
        super().__init__(coordinator, config_entry, key)
        self._attr_name = name
        self._command = command

    async def async_press(self) -> None:
        """Handle button press."""
        return None
