from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_DIVISION_ID,
    CONF_FAVORITE_TEAM,
    CONF_LEAGUE_ID,
    CONF_SHOW_LOGOS,
    CONF_VIEW_MODE,
    DEFAULT_DIVISION_ID,
    DEFAULT_FAVORITE_TEAM,
    DEFAULT_LEAGUE_ID,
    DEFAULT_SHOW_LOGOS,
    DEFAULT_VIEW_MODE,
    DOMAIN,
    DIVISION_OPTIONS,
    LEAGUE_OPTIONS,
    TEAM_NAMES,
    VIEW_MODE_LABELS,
    VIEW_MODES,
)


def _data_schema(defaults: dict[str, object]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_VIEW_MODE, default=defaults[CONF_VIEW_MODE]): vol.In(
                VIEW_MODES
            ),
            vol.Required(CONF_LEAGUE_ID, default=defaults[CONF_LEAGUE_ID]): vol.In(
                [league_id for league_id, _league_name in LEAGUE_OPTIONS]
            ),
            vol.Required(CONF_DIVISION_ID, default=defaults[CONF_DIVISION_ID]): vol.In(
                [division_id for division_id, _division_name in DIVISION_OPTIONS]
            ),
            vol.Optional(CONF_FAVORITE_TEAM, default=defaults[CONF_FAVORITE_TEAM]): vol.In(
                TEAM_NAMES + ("",)
            ),
            vol.Required(CONF_SHOW_LOGOS, default=defaults[CONF_SHOW_LOGOS]): bool,
        }
    )


class MlbStandingsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return MlbStandingsOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, object] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="MLB Standings", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_data_schema(
                {
                    CONF_VIEW_MODE: DEFAULT_VIEW_MODE,
                    CONF_LEAGUE_ID: DEFAULT_LEAGUE_ID,
                    CONF_DIVISION_ID: DEFAULT_DIVISION_ID,
                    CONF_FAVORITE_TEAM: DEFAULT_FAVORITE_TEAM,
                    CONF_SHOW_LOGOS: DEFAULT_SHOW_LOGOS,
                }
            ),
        )


class MlbStandingsOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, object] | None = None):
        defaults = {
            CONF_VIEW_MODE: self.config_entry.options.get(CONF_VIEW_MODE, self.config_entry.data.get(CONF_VIEW_MODE, DEFAULT_VIEW_MODE)),
            CONF_LEAGUE_ID: self.config_entry.options.get(CONF_LEAGUE_ID, self.config_entry.data.get(CONF_LEAGUE_ID, DEFAULT_LEAGUE_ID)),
            CONF_DIVISION_ID: self.config_entry.options.get(CONF_DIVISION_ID, self.config_entry.data.get(CONF_DIVISION_ID, DEFAULT_DIVISION_ID)),
            CONF_FAVORITE_TEAM: self.config_entry.options.get(CONF_FAVORITE_TEAM, self.config_entry.data.get(CONF_FAVORITE_TEAM, DEFAULT_FAVORITE_TEAM)),
            CONF_SHOW_LOGOS: self.config_entry.options.get(CONF_SHOW_LOGOS, self.config_entry.data.get(CONF_SHOW_LOGOS, DEFAULT_SHOW_LOGOS)),
        }

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=_data_schema(defaults))
