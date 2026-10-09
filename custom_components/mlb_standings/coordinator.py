from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from aiohttp import ClientError, ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE_URL, API_SCHEDULE_URL, DEFAULT_UPDATE_INTERVAL, DIVISIONS, LEAGUES, TEAM_LOGO_URL

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
class PostseasonSeries:
    league_id: int
    game_type: str
    away_team: str
    home_team: str
    away_wins: int
    home_wins: int
    games_played: int
    state: str
    winner: str | None


@dataclass(slots=True)
class MlbStandingsData:
    leagues: dict[int, LeagueStanding]
    postseason_series: tuple[PostseasonSeries, ...] = ()

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

    async def async_get_postseason_series(self) -> tuple[PostseasonSeries, ...]:
        try:
            async with self._session.get(
                API_SCHEDULE_URL,
                params={
                    "sportId": 1,
                    "season": datetime.now().year,
                    "gameType": "F,D,L,W",
                    "hydrate": "team",
                },
            ) as response:
                response.raise_for_status()
                payload = await response.json()
        except ClientError as err:
            _LOGGER.warning("Error retrieving MLB postseason schedule: %s", err)
            return ()

        grouped: dict[tuple[str, int, tuple[str, str]], dict[str, Any]] = {}
        for date in payload.get("dates", []):
            for game in date.get("games", []):
                game_type = str(game.get("gameType", ""))
                away = game.get("teams", {}).get("away", {})
                home = game.get("teams", {}).get("home", {})
                away_team = away.get("team", {})
                home_team = home.get("team", {})
                if not away_team or not home_team:
                    continue

                league_id = int(away_team.get("league", {}).get("id", 0))
                if league_id not in LEAGUES:
                    continue

                series_league_id = min(LEAGUES) if game_type == "W" else league_id
                away_name = str(away_team.get("teamName") or away_team.get("name", "Unknown team"))
                home_name = str(home_team.get("teamName") or home_team.get("name", "Unknown team"))
                away_key = str(away_team.get("id") or away_name)
                home_key = str(home_team.get("id") or home_name)
                pair = tuple(sorted((away_key, home_key)))
                series = grouped.setdefault(
                    (game_type, series_league_id, pair),
                    {
                        "away_key": away_key,
                        "home_key": home_key,
                        "away_team": away_name,
                        "home_team": home_name,
                        "away_wins": 0,
                        "home_wins": 0,
                        "games_played": 0,
                        "live": False,
                    },
                )

                status = game.get("status", {}).get("abstractGameState")
                if status == "Final":
                    series["games_played"] += 1
                    if away.get("isWinner") is True:
                        winning_team_key = away_key
                    elif home.get("isWinner") is True:
                        winning_team_key = home_key
                    else:
                        winning_team_key = None

                    if winning_team_key == series["away_key"]:
                        series["away_wins"] += 1
                    elif winning_team_key == series["home_key"]:
                        series["home_wins"] += 1
                elif status == "Live":
                    series["live"] = True

        series_list = []
        for (game_type, series_league_id, _), series in grouped.items():
            wins_needed = {"F": 2, "D": 3, "L": 4, "W": 4}.get(game_type, 99)
            winner = None
            if series["away_wins"] >= wins_needed:
                winner = series["away_team"]
            elif series["home_wins"] >= wins_needed:
                winner = series["home_team"]

            state = "Final" if winner else "In Progress" if series["live"] or series["games_played"] else "Scheduled"
            series_list.append(
                PostseasonSeries(
                    league_id=series_league_id,
                    game_type=game_type,
                    away_team=series["away_team"],
                    home_team=series["home_team"],
                    away_wins=series["away_wins"],
                    home_wins=series["home_wins"],
                    games_played=series["games_played"],
                    state=state,
                    winner=winner,
                )
            )

        return tuple(series_list)

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
            al_league, nl_league, postseason_series = await asyncio.gather(
                self._client.async_get_league(103),
                self._client.async_get_league(104),
                self._client.async_get_postseason_series(),
            )
        except Exception as err:
            _LOGGER.warning("Error communicating with MLB API: %s", err)
            return self.data or MlbStandingsData(leagues={})

        return MlbStandingsData(
            leagues={103: al_league, 104: nl_league},
            postseason_series=postseason_series,
        )
