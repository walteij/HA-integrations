from __future__ import annotations

from typing import Final

DOMAIN: Final = "arr_media_manager"
PLATFORMS: Final[tuple[str, ...]] = ("sensor", "binary_sensor", "button", "select")

APPLICATION_SONARR: Final = "sonarr"
APPLICATION_RADARR: Final = "radarr"
APPLICATION_LIDARR: Final = "lidarr"
SUPPORTED_APPLICATIONS: Final[dict[str, str]] = {
    APPLICATION_SONARR: "Sonarr",
    APPLICATION_RADARR: "Radarr",
    APPLICATION_LIDARR: "Lidarr",
}

API_VERSIONS: Final[dict[str, str]] = {
    APPLICATION_SONARR: "/api/v3",
    APPLICATION_RADARR: "/api/v3",
    APPLICATION_LIDARR: "/api/v1",
}

DEFAULT_TIMEOUT: Final = 30
DEFAULT_UPDATE_INTERVAL: Final = 300
DEFAULT_DISK_SPACE_THRESHOLD: Final = 15
DEFAULT_MONITORING_MODE: Final = "all"
MAX_LOOKUP_RESULTS: Final = 10

CONF_APPLICATION: Final = "application"
CONF_INSTANCE_NAME: Final = "instance_name"
CONF_BASE_URL: Final = "base_url"
CONF_API_KEY: Final = "api_key"
CONF_VERIFY_SSL: Final = "verify_ssl"
CONF_TIMEOUT: Final = "timeout"
CONF_DEFAULT_ROOT_FOLDER: Final = "default_root_folder"
CONF_DEFAULT_QUALITY_PROFILE: Final = "default_quality_profile"
CONF_DEFAULT_MONITORING_MODE: Final = "default_monitoring_mode"
CONF_AUTO_SEARCH: Final = "auto_start_search"
CONF_CREATE_MONITORING_SENSORS: Final = "create_monitoring_sensors"
CONF_CREATE_COMMAND_BUTTONS: Final = "create_command_buttons"
CONF_MAX_LOOKUP_RESULTS: Final = "max_lookup_results"
CONF_INCLUDE_POSTER_URLS: Final = "include_poster_urls"
CONF_INCLUDE_EXTENDED_QUEUE: Final = "include_extended_queue"
CONF_DISK_SPACE_THRESHOLD: Final = "disk_space_low_threshold"

ATTR_CONFIG_ENTRY_ID: Final = "config_entry_id"
ATTR_QUERY: Final = "query"
ATTR_MEDIA_ID: Final = "media_id"
ATTR_LOOKUP_ID: Final = "lookup_id"
ATTR_ROOT_FOLDER: Final = "root_folder"
ATTR_QUALITY_PROFILE: Final = "quality_profile"
ATTR_MONITORING_MODE: Final = "monitoring_mode"
ATTR_SEARCH_AFTER_ADD: Final = "search_after_add"
ATTR_CONFIRM: Final = "confirm"
ATTR_DELETE_FILES: Final = "delete_files"
ATTR_ADD_IMPORT_EXCLUSION: Final = "add_import_exclusion"
ATTR_YEAR: Final = "year"
ATTR_FOREIGN_ID: Final = "foreign_id"
ATTR_EXACT_MATCH: Final = "exact_match"
ATTR_SEASON_NUMBER: Final = "season_number"
ATTR_MEDIA_SUBTYPE: Final = "media_subtype"

SERVICE_LOOKUP: Final = "lookup"
SERVICE_ADD_MEDIA: Final = "add_media"
SERVICE_SEARCH_AND_ADD: Final = "search_and_add"
SERVICE_TRIGGER_SEARCH: Final = "trigger_search"
SERVICE_REFRESH: Final = "refresh"
SERVICE_DELETE_MEDIA: Final = "delete_media"

DATA_COORDINATOR: Final = "coordinator"
DATA_ADAPTER: Final = "adapter"
DATA_CLIENT: Final = "client"
