from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ArrApiError, ArrAuthenticationError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ARRMediaManagerCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator for ARR app status and library metadata."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, adapter: object) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(minutes=5),
        )
        self.entry = entry
        self.adapter = adapter

    async def _async_update_data(self) -> dict:
        try:
            status = await self.adapter.async_get_system_status()
            queue = await self.adapter.async_get_queue()
            health = await self.adapter.async_get_health_issues()
            disk = await self.adapter.async_get_disk_space()
            library = await self.adapter.async_get_library_summary()
            return {
                "status": status,
                "queue": queue,
                "health": health,
                "disk": disk,
                "library": library,
            }
        except ArrAuthenticationError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except ArrApiError as err:
            raise UpdateFailed(f"ARR update failed: {err}") from err
