from __future__ import annotations

from typing import Any

from .base_adapter import BaseARRAdapter


class LidarrAdapter(BaseARRAdapter):
    """Adapter for Lidarr API behavior."""

    application = "lidarr"
    api_version = "/api/v1"
    lookup_endpoint = "/api/v1/artist/lookup"
    library_endpoint = "/api/v1/artist"
    queue_endpoint = "/api/v1/queue"
    health_endpoint = "/api/v1/health"
    disk_space_endpoint = "/api/v1/diskspace"
    quality_profile_endpoint = "/api/v1/qualityprofile"
    root_folder_endpoint = "/api/v1/rootfolder"
    command_endpoint = "/api/v1/command"

    @property
    def supported_actions(self) -> set[str]:
        return {
            "rss_sync",
            "refresh_library",
            "rescan_folders",
            "refresh_quality_profiles",
            "refresh_root_folders",
            "refresh_all_artists",
            "search_monitored_albums",
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
        payload: dict[str, Any] = {
            "artistName": lookup_result.get("title") or lookup_result.get("name"),
            "foreignArtistId": lookup_result.get("foreignId"),
            "monitored": True,
            "addOptions": {
                "searchForMissingAlbums": search_after_add,
            },
        }
        if root_folder:
            payload["rootFolderPath"] = root_folder
        if quality_profile is not None:
            payload["qualityProfileId"] = int(quality_profile) if isinstance(quality_profile, str) and quality_profile.isdigit() else quality_profile
        if monitoring_mode:
            payload["monitor"] = monitoring_mode
        return payload

    async def async_search_monitored_albums(self) -> dict[str, Any]:
        return await self.async_trigger_command("MoviesSearch")

    async def async_refresh_all_artists(self) -> dict[str, Any]:
        return await self.async_trigger_command("RefreshArtist")

    async def async_delete_media(self, media_id: str | int, *, delete_files: bool = False, add_import_exclusion: bool = False) -> dict[str, Any]:
        return await self.async_trigger_command("DeleteArtist", artistId=int(media_id), deleteFiles=delete_files, addImportExclusion=add_import_exclusion)
