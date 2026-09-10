from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any

from aiohttp import ClientError, ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE_URL, DEFAULT_UPDATE_INTERVAL, DIVISIONS, LEAGUES, TEAM_LOGO_URL

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class TeamStanding:
    team_id: int
    team_name: str
    league_id: int
    league_name: str
    division_id: int
    division_name: str
    wins: int
    losses: int
    winning_percentage: float
    games_back: str
    division_rank: int | None
    league_rank: int | None
    wild_card_rank: int | None
    streak_code: str | None
    streak_number: int | None
    division_leader: bool
    league_leader: bool
    wild_card_leader: bool
    clinched: bool
    runs_scored: int | None
    runs_allowed: int | None
    run_differential: int | None
    last_updated: str | None
    logo_url: str

    @property
    def record(self) -> str:
        return f"{self.wins}-{self.losses}"


@dataclass(slots=True)
class DivisionStanding:
    league_id: int
    league_name: str
    division_id: int
    division_name: str
    last_updated: str | None
    team_records: tuple[TeamStanding, ...]

    @property
    def leader(self) -> TeamStanding:
        return self.team_records[0]


@dataclass(slots=True)
class LeagueStanding:
    league_id: int
    league_name: str
    divisions: tuple[DivisionStanding, ...]

    @property
    def teams(self) -> tuple[TeamStanding, ...]:
        return tuple(team for division in self.divisions for team in division.team_records)

    @property
    def postseason_teams(self) -> tuple[TeamStanding, ...]:
        teams = sorted(
            self.teams,
            key=lambda team: (
                -(team.wins - team.losses),
                -team.wins,
                team.losses,
                team.division_rank or 999,
                team.team_name,
            ),
        )
        return tuple(teams[:6])


@dataclass(slots=True)
class MlbStandingsData:
    leagues: dict[int, LeagueStanding]

    @property
    def divisions(self) -> tuple[DivisionStanding, ...]:
        return tuple(division for league in self.leagues.values() for division in league.divisions)

    @property
    def teams(self) -> tuple[TeamStanding, ...]:
        return tuple(team for league in self.leagues.values() for team in league.teams)

    def league(self, league_id: int) -> LeagueStanding | None:
        return self.leagues.get(league_id)

    def division(self, division_id: int) -> DivisionStanding | None:
        for division in self.divisions:
            if division.division_id == division_id:
                return division
        return None

    def team(self, team_name: str) -> TeamStanding | None:
        normalized = team_name.casefold()
        for team in self.teams:
            if team.team_name.casefold() == normalized:
                return team
        return None


class MlbApiClient:
    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def async_get_league(self, league_id: int) -> LeagueStanding:
        try:
            async with self._session.get(f"{API_BASE_URL}?leagueId={league_id}") as response:
                response.raise_for_status()
                payload = await response.json()
        except ClientError as err:
            raise UpdateFailed(f"Error communicating with MLB API: {err}") from err

        records = payload.get("records", [])
        divisions: list[DivisionStanding] = []

        for record in records:
            division = record.get("division", {})
            league = record.get("league", {})
            team_records = [
                self._parse_team_record(record_item, league, division, record.get("lastUpdated"))
                for record_item in record.get("teamRecords", [])
            ]
            team_records.sort(key=lambda item: item.division_rank or 999)

            divisions.append(
                DivisionStanding(
                    league_id=int(league.get("id", league_id)),
                    league_name=str(league.get("name", LEAGUES.get(league_id, "MLB"))),
                    division_id=int(division.get("id")),
                    division_name=str(division.get("name", "Unknown Division")),
                    last_updated=record.get("lastUpdated"),
                    team_records=tuple(team_records),
                )
            )

        divisions.sort(key=lambda item: item.division_id)
        return LeagueStanding(
            league_id=league_id,
            league_name=LEAGUES.get(league_id, "MLB"),
            divisions=tuple(divisions),
        )

    @staticmethod
    def _parse_team_record(
        record: dict[str, Any],
        league: dict[str, Any],
        division: dict[str, Any],
        fallback_last_updated: str | None,
    ) -> TeamStanding:
        team = record.get("team", {})
        streak = record.get("streak", {})
        team_id = int(team.get("id"))
        division_id = int(division.get("id"))
        league_id = int(league.get("id"))

        return TeamStanding(
            team_id=team_id,
            team_name=str(team.get("name", "Unknown Team")),
            league_id=league_id,
            league_name=str(league.get("name", LEAGUES.get(league_id, "MLB"))),
            division_id=division_id,
            division_name=str(division.get("name") or DIVISIONS.get(division_id, (league_id, "Unknown Division"))[1]),
            wins=int(record.get("wins", 0)),
            losses=int(record.get("losses", 0)),
            winning_percentage=float(record.get("winningPercentage", 0.0)),
            games_back=str(record.get("gamesBack", "-")),
            division_rank=_safe_int(record.get("divisionRank")),
            league_rank=_safe_int(record.get("leagueRank")),
            wild_card_rank=_safe_int(record.get("wildCardRank")),
            streak_code=streak.get("streakCode"),
            streak_number=_safe_int(streak.get("streakNumber")),
            division_leader=bool(record.get("divisionLeader")),
            league_leader=bool(record.get("leagueLeader")),
            wild_card_leader=bool(record.get("wildCardLeader")),
            clinched=bool(record.get("clinched")),
            runs_scored=_safe_int(record.get("runsScored")),
            runs_allowed=_safe_int(record.get("runsAllowed")),
            run_differential=_safe_int(record.get("runDifferential")),
            last_updated=record.get("lastUpdated") or fallback_last_updated,
            logo_url=TEAM_LOGO_URL.format(team_id=team_id),
        )


def _safe_int(value: Any) -> int | None:
    try:
        if value in (None, "", "-"):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


class MlbStandingsCoordinator(DataUpdateCoordinator[MlbStandingsData]):
    def __init__(self, hass: HomeAssistant, client: MlbApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="MLB standings",
            update_interval=DEFAULT_UPDATE_INTERVAL,
            always_update=False,
        )
        self._client = client

    async def _async_update_data(self) -> MlbStandingsData:
        try:
            al_league, nl_league = await asyncio.gather(
                self._client.async_get_league(103),
                self._client.async_get_league(104),
            )
        except Exception as err:
            _LOGGER.warning("Error communicating with MLB API: %s", err)
            return self.data or MlbStandingsData(leagues={})

        return MlbStandingsData(
            leagues={103: al_league, 104: nl_league},
        )
