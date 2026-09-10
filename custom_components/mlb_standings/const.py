from __future__ import annotations

from datetime import timedelta

DOMAIN = "mlb_standings"
NAME = "MLB Standings"

API_BASE_URL = "https://statsapi.mlb.com/api/v1/standings"
TEAM_LOGO_URL = "https://www.mlbstatic.com/team-logos/team-cap-on-light/{team_id}.svg"

DEFAULT_VIEW_MODE = "all"
DEFAULT_LEAGUE_ID = 103
DEFAULT_DIVISION_ID = 201
DEFAULT_FAVORITE_TEAM = ""
DEFAULT_SHOW_LOGOS = True
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=15)

VIEW_MODES = ("all", "league", "division")
VIEW_MODE_LABELS = {
    "all": "All leagues",
    "league": "One league",
    "division": "One division",
}
LEAGUES = {
    103: "American League",
    104: "National League",
}
LEAGUE_OPTIONS = (
    (103, "American League"),
    (104, "National League"),
)
TEAM_NAMES = (
    "Brewers",
    "Cubs",
    "Pirates",
    "Cardinals",
    "Reds",
    "Dodgers",
    "Padres",
    "Giants",
    "D-backs",
    "Rockies",
    "Phillies",
    "Mets",
    "Marlins",
    "Braves",
    "Nationals",
    "Yankees",
    "Red Sox",
    "Rays",
    "Blue Jays",
    "Orioles",
    "Guardians",
    "Twins",
    "Tigers",
    "Royals",
    "White Sox",
    "Astros",
    "Mariners",
    "Rangers",
    "Athletics",
    "Angels",
)
DIVISIONS = {
    200: (103, "American League West"),
    201: (103, "American League East"),
    202: (103, "American League Central"),
    203: (104, "National League West"),
    204: (104, "National League East"),
    205: (104, "National League Central"),
}
DIVISION_OPTIONS = (
    (200, "American League West"),
    (201, "American League East"),
    (202, "American League Central"),
    (203, "National League West"),
    (204, "National League East"),
    (205, "National League Central"),
)

CONF_VIEW_MODE = "view_mode"
CONF_LEAGUE_ID = "league_id"
CONF_DIVISION_ID = "division_id"
CONF_FAVORITE_TEAM = "favorite_team"
CONF_SHOW_LOGOS = "show_logos"
