from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity

from .entity import ARRMediaManagerEntity


class ARRSelect(ARRMediaManagerEntity, SelectEntity):
    """Generic select entity."""

    def __init__(self, coordinator: Any, config_entry: Any, key: str, name: str, options: list[str], current: str | None) -> None:
        super().__init__(coordinator, config_entry, key)
        self._attr_name = name
        self._attr_options = options
        self._current = current

    @property
    def current_option(self) -> str | None:
        return self._current

    async def async_select_option(self, option: str) -> None:
        self._current = option
