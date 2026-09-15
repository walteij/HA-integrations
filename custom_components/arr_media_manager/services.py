from __future__ import annotations

import logging
from functools import partial
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _get_entry_runtime(hass: HomeAssistant, call: ServiceCall) -> tuple[Any, Any]:
    entry_id = call.data.get("config_entry_id")
    if not entry_id:
        raise ValueError("config_entry_id is required")
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None:
        raise ValueError(f"Unknown config entry: {entry_id}")
    runtime = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if runtime is None:
        raise ValueError(f"ARR integration not initialized for {entry_id}")
    return entry, runtime["adapter"]


async def async_register_services(hass: HomeAssistant) -> None:
    """Register integration services when at least one config entry is loaded."""
    for service_name, handler in {
        "lookup": async_handle_lookup,
        "add_media": async_handle_add_media,
        "search_and_add": async_handle_search_and_add,
        "trigger_search": async_handle_trigger_search,
        "refresh": async_handle_refresh,
        "delete_media": async_handle_delete_media,
    }.items():
        if hass.services.has_service(DOMAIN, service_name):
            continue
        hass.services.async_register(DOMAIN, service_name, partial(handler, hass), schema=None)


async def async_unregister_services(hass: HomeAssistant) -> None:
    """Remove registered services when the final entry unloads."""
    for service_name in [
        "lookup",
        "add_media",
        "search_and_add",
        "trigger_search",
        "refresh",
        "delete_media",
    ]:
        if hass.services.has_service(DOMAIN, service_name):
            hass.services.async_remove(DOMAIN, service_name)


async def async_handle_lookup(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    _, adapter = _get_entry_runtime(hass, call)
    query = str(call.data.get("query") or "")
    max_results = int(call.data.get("max_results", 10))
    if not query:
        raise ValueError("query is required")
    results = await adapter.async_lookup(query, max_results=max_results)
    return {"count": len(results), "results": results}


async def async_handle_add_media(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    _, adapter = _get_entry_runtime(hass, call)
    lookup_id = call.data.get("lookup_id")
    if lookup_id is None:
        raise ValueError("lookup_id is required")
    payload = adapter.build_media_payload(
        {"title": call.data.get("title") or str(lookup_id), "id": lookup_id},
        root_folder=call.data.get("root_folder"),
        quality_profile=call.data.get("quality_profile"),
        monitoring_mode=call.data.get("monitoring_mode"),
        search_after_add=bool(call.data.get("search_after_add", False)),
    )
    result = await adapter.async_add_media(payload)
    return {"status": "ok", "result": result}


async def async_handle_search_and_add(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    _, adapter = _get_entry_runtime(hass, call)
    query = str(call.data.get("query") or "")
    if not query:
        raise ValueError("query is required")
    lookup_results = await adapter.async_lookup(query, max_results=10)
    result = await adapter.async_search_and_add(
        query,
        lookup_results=lookup_results,
        root_folder=call.data.get("root_folder"),
        quality_profile=call.data.get("quality_profile"),
        monitoring_mode=call.data.get("monitoring_mode"),
        search_after_add=bool(call.data.get("search_after_add", False)),
        exact_match=bool(call.data.get("exact_match", False)),
        year=call.data.get("year"),
        foreign_id=call.data.get("foreign_id"),
    )
    return {"status": "ok", "result": result}


async def async_handle_trigger_search(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    _, adapter = _get_entry_runtime(hass, call)
    media_id = call.data.get("media_id")
    if media_id is None:
        raise ValueError("media_id is required")

    if adapter.application == "sonarr":
        command = "MissingEpisodeSearch"
        payload = {"seriesId": int(media_id)}
    elif adapter.application == "radarr":
        command = "MoviesSearch"
        payload = {"movieId": int(media_id)}
    elif adapter.application == "lidarr":
        command = "MissingAlbumSearch"
        payload = {"artistId": int(media_id)}
    else:
        command = "Search"
        payload = {"mediaId": int(media_id)}

    if call.data.get("season_number") is not None:
        payload["seasonNumber"] = int(call.data.get("season_number"))
    if call.data.get("media_subtype"):
        payload["mediaType"] = call.data.get("media_subtype")
    result = await adapter.async_trigger_command(command, **payload)
    return {"status": "ok", "result": result}


async def async_handle_refresh(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    _, adapter = _get_entry_runtime(hass, call)
    action = str(call.data.get("action") or "library").lower()

    if action in {"library", "refresh_library"}:
        result = await adapter.async_refresh_library()
    elif action in {"rss", "rss_sync"}:
        result = await adapter.async_trigger_command("RssSync")
    elif action in {"rescan", "rescan_folders"}:
        result = await adapter.async_trigger_command("RescanFolders")
    elif adapter.application == "sonarr" and action in {"series", "refresh_series"}:
        result = await adapter.async_refresh_all_series()
    elif adapter.application == "radarr" and action in {"movies", "refresh_movies"}:
        result = await adapter.async_refresh_all_movies()
    elif adapter.application == "lidarr" and action in {"artists", "refresh_artists"}:
        result = await adapter.async_refresh_all_artists()
    else:
        result = await adapter.async_trigger_command(action)
    return {"status": "ok", "result": result}


async def async_handle_delete_media(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    _, adapter = _get_entry_runtime(hass, call)
    media_id = call.data.get("media_id")
    if media_id is None:
        raise ValueError("media_id is required")
    if not bool(call.data.get("confirm", False)):
        raise ValueError("Deletion requires confirm=True")
    result = await adapter.async_delete_media(
        media_id,
        delete_files=bool(call.data.get("delete_files", False)),
        add_import_exclusion=bool(call.data.get("add_import_exclusion", False)),
    )
    return {"status": "ok", "result": result}
