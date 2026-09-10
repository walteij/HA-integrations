from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

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
            vol.Required(
                CONF_VIEW_MODE,
                default=defaults[CONF_VIEW_MODE],
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(label=VIEW_MODE_LABELS[view_mode], value=view_mode)
                        for view_mode in VIEW_MODES
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_LEAGUE_ID,
                default=defaults[CONF_LEAGUE_ID],
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(label=league_name, value=league_id)
                        for league_id, league_name in LEAGUE_OPTIONS
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_DIVISION_ID,
                default=defaults[CONF_DIVISION_ID],
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(label=division_name, value=division_id)
                        for division_id, division_name in DIVISION_OPTIONS
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_FAVORITE_TEAM,
                default=defaults[CONF_FAVORITE_TEAM],
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(label=team_name, value=team_name)
                        for team_name in TEAM_NAMES
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_SHOW_LOGOS, default=defaults[CONF_SHOW_LOGOS]): bool,
        }
    )


class MlbStandingsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

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


async def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    return MlbStandingsOptionsFlow(config_entry)


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
