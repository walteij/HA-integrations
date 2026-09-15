from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return redacted diagnostics for an ARR config entry."""
    data: dict[str, Any] = {
        "application": entry.data.get("application"),
        "instance_name": entry.data.get("instance_name"),
        "base_url": entry.data.get("base_url"),
        "verify_ssl": entry.data.get("verify_ssl"),
        "timeout": entry.data.get("timeout"),
        "options": dict(entry.options),
    }
    if "api_key" in entry.data:
        data["api_key"] = "REDACTED"
    return data
