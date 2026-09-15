from __future__ import annotations

from typing import Any

from .base_adapter import BaseARRAdapter


class SonarrAdapter(BaseARRAdapter):
    """Adapter for Sonarr API behavior."""

    application = "sonarr"
    api_version = "/api/v3"
    lookup_endpoint = "/api/v3/series/lookup"
    library_endpoint = "/api/v3/series"
    queue_endpoint = "/api/v3/queue"
    health_endpoint = "/api/v3/health"
    disk_space_endpoint = "/api/v3/diskspace"
    quality_profile_endpoint = "/api/v3/qualityprofile"
    root_folder_endpoint = "/api/v3/rootfolder"
    command_endpoint = "/api/v3/command"

    @property
    def supported_actions(self) -> set[str]:
        return {
            "rss_sync",
            "refresh_library",
            "rescan_folders",
            "refresh_quality_profiles",
            "refresh_root_folders",
            "refresh_all_series",
            "search_monitored_episodes",
        }

    @property
    def monitoring_options(self) -> dict[str, str]:
        return {
            "all": "All episodes",
            "future": "Future episodes",
            "missing": "Missing episodes",
            "existing": "Existing episodes",
            "first": "First season",
            "latest": "Latest season",
            "none": "None",
        }

    def build_media_payload(
        self,
        lookup_result: dict[str, Any],
        *,
        root_folder: str | None = None,
        quality_profile: str | int | None = None,
        monitoring_mode: str | None = None,
        search_after_add: bool = False,
    ) -> dict[str, Any]:
        profile_id = quality_profile if isinstance(quality_profile, int) else None
        payload: dict[str, Any] = {
            "title": lookup_result.get("title") or lookup_result.get("name"),
            "images": lookup_result.get("images", []),
            "monitored": True,
            "addOptions": {
                "searchForMissingEpisodes": search_after_add,
                "ignoreEpisodesWithFiles": False,
                "ignoreEpisodesWithoutFiles": False,
            },
        }
        if root_folder:
            payload["rootFolderPath"] = root_folder
        if profile_id is not None:
            payload["qualityProfileId"] = profile_id
        if monitoring_mode:
            payload["monitor"] = monitoring_mode
        if lookup_result.get("tvdbId") is not None:
            payload["tvdbId"] = int(lookup_result["tvdbId"])
        if lookup_result.get("imdbId") is not None:
            payload["imdbId"] = lookup_result["imdbId"]
        return payload

    async def async_search_monitored_episodes(self) -> dict[str, Any]:
        return await self.async_trigger_command("MissingEpisodeSearch")

    async def async_refresh_all_series(self) -> dict[str, Any]:
        return await self.async_trigger_command("RefreshSeries")

    async def async_delete_media(self, media_id: str | int, *, delete_files: bool = False, add_import_exclusion: bool = False) -> dict[str, Any]:
        return await self.async_trigger_command("DeleteSeries", seriesId=int(media_id), deleteFiles=delete_files, addImportExclusion=add_import_exclusion)
