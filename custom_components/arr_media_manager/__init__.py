from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ArrApiClient
from .const import DOMAIN, PLATFORMS
from .coordinator import ARRMediaManagerCoordinator
from .lidarr import LidarrAdapter
from .radarr import RadarrAdapter
from .services import async_register_services, async_unregister_services
from .sonarr import SonarrAdapter

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from YAML configuration."""
    return True


def _build_adapter_for_entry(entry: ConfigEntry, client: ArrApiClient):
    app = entry.data["application"]
    if app == "sonarr":
        return SonarrAdapter(client)
    if app == "radarr":
        return RadarrAdapter(client)
    if app == "lidarr":
        return LidarrAdapter(client)
    raise ValueError(f"Unsupported application type: {app}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry for an ARR instance."""
    session = async_get_clientsession(hass)
    client = ArrApiClient(
        session,
        entry.data["base_url"],
        entry.data["api_key"],
        verify_ssl=entry.data.get("verify_ssl", True),
        timeout=entry.data.get("timeout", 30),
    )
    adapter = _build_adapter_for_entry(entry, client)
    coordinator = ARRMediaManagerCoordinator(hass, entry, adapter)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "adapter": adapter,
        "client": client,
        "coordinator": coordinator,
    }
    await async_register_services(hass)
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and its platforms."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await async_unregister_services(hass)
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
