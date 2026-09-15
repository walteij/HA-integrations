from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from aiohttp import ClientSession
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .api import (
    ArrApiClient,
    ArrAuthenticationError,
    ArrConnectionError,
    ArrInvalidResponseError,
    ArrSslError,
    ArrTimeoutError,
    ArrUnsupportedOperationError,
)
from .const import (
    API_VERSIONS,
    APPLICATION_LIDARR,
    APPLICATION_RADARR,
    APPLICATION_SONARR,
    CONF_API_KEY,
    CONF_APPLICATION,
    CONF_BASE_URL,
    CONF_INSTANCE_NAME,
    CONF_TIMEOUT,
    CONF_VERIFY_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def validate_base_url(raw_url: str) -> str:
    value = raw_url.strip()
    if not value:
        raise ValueError("URL is required")
    if value.endswith("/"):
        value = value.rstrip("/")
    if "://" not in value:
        raise ValueError("Invalid URL")
    scheme = value.split("://", 1)[0].lower()
    if scheme not in {"http", "https"}:
        raise ValueError("Unsupported URL scheme")
    return value


async def _validate_connection(app_type: str, base_url: str, api_key: str, verify_ssl: bool, timeout: int) -> tuple[str, str]:
    session = ClientSession()
    try:
        client = ArrApiClient(session, base_url, api_key, verify_ssl=verify_ssl, timeout=timeout)
        endpoint = f"{API_VERSIONS[app_type]}/system/status"
        payload = await client.get(endpoint)
        status = payload if isinstance(payload, dict) else {}
        app_name = str(status.get("appName") or status.get("application") or "").lower()
        if not app_name:
            app_name = str(status.get("instanceName") or "")
        if app_type == APPLICATION_SONARR and "sonarr" not in app_name:
            raise ArrUnsupportedOperationError("Wrong ARR application selected")
        if app_type == APPLICATION_RADARR and "radarr" not in app_name:
            raise ArrUnsupportedOperationError("Wrong ARR application selected")
        if app_type == APPLICATION_LIDARR and "lidarr" not in app_name:
            raise ArrUnsupportedOperationError("Wrong ARR application selected")
        version = str(status.get("version") or status.get("appVersion") or "unknown")
        instance_identifier = str(status.get("instanceId") or status.get("instanceName") or f"{app_type}:{base_url}")
        return instance_identifier, version
    except ArrAuthenticationError as err:
        raise err
    except ArrTimeoutError as err:
        raise err
    except ArrSslError as err:
        raise err
    except ArrConnectionError as err:
        raise err
    except ArrInvalidResponseError as err:
        raise err
    finally:
        await session.close()


class ARRMediaManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._application: str | None = None
        self._instance_name: str | None = None
        self._base_url: str | None = None
        self._api_key: str | None = None
        self._verify_ssl: bool = True
        self._timeout: int = 30

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._application = user_input[CONF_APPLICATION]
                self._instance_name = user_input[CONF_INSTANCE_NAME]
                self._base_url = validate_base_url(user_input[CONF_BASE_URL])
                self._api_key = user_input[CONF_API_KEY].strip()
                self._verify_ssl = user_input[CONF_VERIFY_SSL]
                self._timeout = int(user_input[CONF_TIMEOUT])
                uid, version = await _validate_connection(
                    self._application,
                    self._base_url,
                    self._api_key,
                    self._verify_ssl,
                    self._timeout,
                )
                await self.async_set_unique_id(f"{self._application}:{uid}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=self._instance_name,
                    data={
                        CONF_APPLICATION: self._application,
                        CONF_BASE_URL: self._base_url,
                        CONF_API_KEY: self._api_key,
                        CONF_VERIFY_SSL: self._verify_ssl,
                        CONF_TIMEOUT: self._timeout,
                        CONF_INSTANCE_NAME: self._instance_name,
                        "version": version,
                    },
                )
            except ValueError:
                errors["base_url"] = "invalid_url"
            except ArrAuthenticationError:
                errors["api_key"] = "invalid_auth"
            except ArrTimeoutError:
                errors["base_url"] = "timeout"
            except ArrSslError:
                errors["base_url"] = "ssl_error"
            except ArrConnectionError:
                errors["base_url"] = "cannot_connect"
            except ArrInvalidResponseError:
                errors["base_url"] = "unexpected_response"
            except ArrUnsupportedOperationError:
                errors["base_url"] = "wrong_application"
        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(),
            errors=errors,
        )

    def _get_schema(self) -> selector.ConfigEntrySelector:
        return selector.ConfigEntrySelector(
            selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": APPLICATION_SONARR, "label": "Sonarr"},
                        {"value": APPLICATION_RADARR, "label": "Radarr"},
                        {"value": APPLICATION_LIDARR, "label": "Lidarr"},
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        return await self.async_step_user()

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self.async_step_user(user_input)
