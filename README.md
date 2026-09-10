# HA Integrations

This repository is structured as a Home Assistant integration collection.

It is ready for HACS as a custom repository of type `Integration`, because each installable integration lives under `custom_components/<domain>`.

## Current Integrations

### MLB Standings

The active integration is [`custom_components/mlb_standings`](custom_components/mlb_standings), which exposes MLB standings as sensor entities.

It provides:

- League leader sensors for the American League and National League
- Division leader sensors for all six MLB divisions
- Team sensors for the selected league or division scope
- An optional favorite team sensor
- Team logos through `entity_picture` when enabled

Configuration is handled through the Home Assistant config flow with selectors for:

- `view_mode`: `all`, `league`, or `division`
- `league_id`: `103` for AL or `104` for NL
- `division_id`: one of `200`, `201`, `202`, `203`, `204`, `205`
- `favorite_team`: a selectable MLB team name
- `show_logos`: `true` or `false`

## Repository Layout

The repository is split into two layers:

- `custom_components/` contains the Home Assistant code that HACS installs.
- `integrations/` contains human-friendly documentation for each integration and a place to add future integrations cleanly.

Current layout:

- [`custom_components/mlb_standings`](custom_components/mlb_standings): installable Home Assistant integration
- [`integrations/mlb_standings`](integrations/mlb_standings): documentation and integration notes

## Add Another Integration Later

When you add a new integration, use the same pattern:

- `custom_components/<new_domain>` for the code
- `integrations/<new_domain>` for documentation

That keeps the repository HACS-friendly while still giving each integration its own folder and explanation.

## Install Locally

1. Copy `custom_components/mlb_standings` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration from Settings > Devices & services > Add integration.
4. Adjust the options if you want to track just one league or one division.

## Notes

- The integration polls the MLB Stats API directly.
- The old add-on/dashboard files are no longer the primary implementation.
