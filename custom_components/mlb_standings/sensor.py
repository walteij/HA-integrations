from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DIVISION_ID, CONF_FAVORITE_TEAM, CONF_LEAGUE_ID, CONF_SHOW_LOGOS, CONF_VIEW_MODE, DOMAIN, LEAGUES
from .coordinator import DivisionStanding, LeagueStanding, MlbStandingsData, TeamStanding
from . import RuntimeData


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    runtime: RuntimeData = hass.data[DOMAIN][entry.entry_id]
    data = runtime.coordinator.data
    settings = {
        CONF_VIEW_MODE: entry.options.get(CONF_VIEW_MODE, entry.data.get(CONF_VIEW_MODE, "all")),
        CONF_LEAGUE_ID: int(entry.options.get(CONF_LEAGUE_ID, entry.data.get(CONF_LEAGUE_ID, 103))),
        CONF_DIVISION_ID: int(entry.options.get(CONF_DIVISION_ID, entry.data.get(CONF_DIVISION_ID, 201))),
        CONF_FAVORITE_TEAM: str(entry.options.get(CONF_FAVORITE_TEAM, entry.data.get(CONF_FAVORITE_TEAM, ""))).strip(),
        CONF_SHOW_LOGOS: bool(entry.options.get(CONF_SHOW_LOGOS, entry.data.get(CONF_SHOW_LOGOS, True))),
    }

    entities: list[SensorEntity] = []
    selected_leagues, selected_divisions = _select_scope(
        data,
        settings[CONF_VIEW_MODE],
        settings[CONF_LEAGUE_ID],
        settings[CONF_DIVISION_ID],
    )

    for league in selected_leagues:
        entities.append(MlbPostseasonSummarySensor(entry.entry_id, runtime.coordinator, league))
        entities.append(MlbLeagueSensor(entry.entry_id, runtime.coordinator, league, settings[CONF_SHOW_LOGOS]))

    for division in selected_divisions:
        entities.append(MlbDivisionSummarySensor(entry.entry_id, runtime.coordinator, division))
        entities.append(MlbDivisionSensor(entry.entry_id, runtime.coordinator, division, settings[CONF_SHOW_LOGOS]))
        for team in division.team_records:
            entities.append(MlbTeamSensor(entry.entry_id, runtime.coordinator, team, settings[CONF_SHOW_LOGOS]))

    if settings[CONF_FAVORITE_TEAM]:
        favorite = data.team(settings[CONF_FAVORITE_TEAM])
        if favorite is not None:
            entities.append(MlbFavoriteTeamSensor(entry.entry_id, runtime.coordinator, favorite, settings[CONF_SHOW_LOGOS]))

    async_add_entities(entities)


def _select_scope(
    data: MlbStandingsData,
    view_mode: str,
    league_id: int,
    division_id: int,
) -> tuple[tuple[LeagueStanding, ...], tuple[DivisionStanding, ...]]:
    if view_mode == "league":
        league = data.league(league_id)
        return ((league,) if league is not None else (), league.divisions if league is not None else ())

    if view_mode == "division":
        division = data.division(division_id)
        if division is None:
            return (), ()

        league = data.league(division.league_id)
        return ((league,) if league is not None else (), (division,))

    leagues = tuple(data.leagues[league_key] for league_key in sorted(data.leagues))
    divisions = tuple(division for league in leagues for division in league.divisions)
    return leagues, divisions


class MlbBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:baseball"

    def __init__(self, entry_id: str, coordinator, show_logos: bool) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._show_logos = show_logos

    @property
    def entity_picture(self):
        return None

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data is not None


class MlbLeagueSensor(MlbBaseSensor):
    _attr_native_unit_of_measurement = None
    _attr_suggested_display_precision = 3
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry_id: str, coordinator, league: LeagueStanding, show_logos: bool) -> None:
        super().__init__(entry_id, coordinator, show_logos)
        self._league = league
        self._attr_unique_id = f"{self._entry_id}_league_{league.league_id}"
        self._attr_name = f"{league.league_name} standings leader"

    @property
    def native_value(self):
        return self._league.divisions[0].leader.winning_percentage if self._league.divisions else None

    @property
    def entity_picture(self):
        if not self._show_logos or not self._league.divisions:
            return None
        return self._league.divisions[0].leader.logo_url

    @property
    def extra_state_attributes(self):
        if not self._league.divisions:
            return {}

        leader = self._league.divisions[0].leader
        return {
            "league": self._league.league_name,
            "leader": leader.team_name,
            "wins": leader.wins,
            "losses": leader.losses,
            "record": leader.record,
            "division_count": len(self._league.divisions),
        }

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"league_{self._league.league_id}")},
            name=self._league.league_name,
            manufacturer="MLB",
            model="League standings",
        )


class MlbPostseasonSummarySensor(MlbBaseSensor):
    _attr_native_unit_of_measurement = None

    def __init__(self, entry_id: str, coordinator, league: LeagueStanding) -> None:
        super().__init__(entry_id, coordinator, show_logos=False)
        self._league = league
        self._attr_unique_id = f"{self._entry_id}_postseason_{league.league_id}"
        self._attr_name = f"{league.league_name} postseason"

    @property
    def native_value(self):
        return self._league.league_name

    @property
    def extra_state_attributes(self):
        return {
            "league": self._league.league_name,
            "postseason_team_count": len(self._league.postseason_teams),
            "bracket": [
                {
                    "seed": index,
                    "team": team.team_name,
                    "division": team.division_name,
                    "record": team.record,
                    "wins": team.wins,
                    "losses": team.losses,
                    "winning_percentage": team.winning_percentage,
                    "clinched": team.clinched,
                    "division_leader": team.division_leader,
                    "wild_card_rank": team.wild_card_rank,
                }
                for index, team in enumerate(self._league.postseason_teams, start=1)
            ],
        }

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"postseason_{self._league.league_id}")},
            name=f"{self._league.league_name} postseason",
            manufacturer="MLB",
            model="Postseason standings summary",
        )


class MlbDivisionSensor(MlbBaseSensor):
    _attr_native_unit_of_measurement = None

    def __init__(self, entry_id: str, coordinator, division: DivisionStanding, show_logos: bool) -> None:
        super().__init__(entry_id, coordinator, show_logos)
        self._division = division
        self._attr_unique_id = f"{self._entry_id}_division_{division.division_id}"
        self._attr_name = f"{division.division_name} standings leader"

    @property
    def native_value(self):
        return self._division.leader.team_name if self._division.team_records else None

    @property
    def entity_picture(self):
        if not self._show_logos or not self._division.team_records:
            return None
        return self._division.leader.logo_url

    @property
    def extra_state_attributes(self):
        if not self._division.team_records:
            return {}

        leader = self._division.leader
        return {
            "league": self._division.league_name,
            "division": self._division.division_name,
            "leader": leader.team_name,
            "wins": leader.wins,
            "losses": leader.losses,
            "record": leader.record,
            "winning_percentage": leader.winning_percentage,
        }

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"division_{self._division.division_id}")},
            name=self._division.division_name,
            manufacturer="MLB",
            model="Division standings",
        )


class MlbDivisionSummarySensor(MlbBaseSensor):
    _attr_native_unit_of_measurement = None

    def __init__(self, entry_id: str, coordinator, division: DivisionStanding) -> None:
        super().__init__(entry_id, coordinator, show_logos=False)
        self._division = division
        self._attr_unique_id = f"{self._entry_id}_division_summary_{division.division_id}"
        self._attr_name = f"{division.division_name} standings"

    @property
    def native_value(self):
        return self._division.division_name

    @property
    def extra_state_attributes(self):
        return {
            "league": self._division.league_name,
            "division": self._division.division_name,
            "last_updated": self._division.last_updated,
            "standings": [
                {
                    "rank": team.division_rank,
                    "team": team.team_name,
                    "record": team.record,
                    "wins": team.wins,
                    "losses": team.losses,
                    "games_back": team.games_back,
                    "winning_percentage": team.winning_percentage,
                    "streak": f"{team.streak_code or ''}{team.streak_number or ''}".strip(),
                    "runs_scored": team.runs_scored,
                    "runs_allowed": team.runs_allowed,
                    "run_differential": team.run_differential,
                    "leader": team.division_leader,
                }
                for team in self._division.team_records
            ],
        }

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"division_summary_{self._division.division_id}")},
            name=self._division.division_name,
            manufacturer="MLB",
            model="Division standings summary",
        )


class MlbTeamSensor(MlbBaseSensor):
    _attr_native_unit_of_measurement = None
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, entry_id: str, coordinator, team: TeamStanding, show_logos: bool) -> None:
        super().__init__(entry_id, coordinator, show_logos)
        self._team = team
        self._attr_unique_id = f"{self._entry_id}_team_{team.team_id}"
        self._attr_name = f"{team.team_name} standings"

    @property
    def native_value(self):
        return self._team.winning_percentage

    @property
    def entity_picture(self):
        if not self._show_logos:
            return None
        return self._team.logo_url

    @property
    def extra_state_attributes(self):
        return {
            "record": self._team.record,
            "wins": self._team.wins,
            "losses": self._team.losses,
            "games_back": self._team.games_back,
            "division": self._team.division_name,
            "league": self._team.league_name,
            "division_rank": self._team.division_rank,
            "league_rank": self._team.league_rank,
            "wild_card_rank": self._team.wild_card_rank,
            "streak": f"{self._team.streak_code or ''}{self._team.streak_number or ''}".strip(),
            "runs_scored": self._team.runs_scored,
            "runs_allowed": self._team.runs_allowed,
            "run_differential": self._team.run_differential,
        }

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"team_{self._team.team_id}")},
            name=self._team.team_name,
            manufacturer="MLB",
            model="Team standings",
        )


class MlbFavoriteTeamSensor(MlbTeamSensor):
    def __init__(self, entry_id: str, coordinator, team: TeamStanding, show_logos: bool) -> None:
        super().__init__(entry_id, coordinator, team, show_logos)
        self._attr_unique_id = f"{self._entry_id}_favorite_team"
        self._attr_name = f"Favorite team ({team.team_name})"
