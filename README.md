# MLB Standings

This repository is structured as a Home Assistant integration collection.

The active HACS-facing integration is MLB Standings, and the repository is ready for HACS as a custom repository of type `Integration`, because each installable integration lives under `custom_components/<domain>`.

## Current Integrations

### MLB Standings

The active integration is [`custom_components/mlb_standings`](custom_components/mlb_standings), which exposes MLB standings as sensor entities.

It provides:

- League leader sensors for the American League and National League
- League postseason summary sensors with the current playoff bracket for AL and NL
- Division summary sensors with the full standings table for a selected division
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
- [`custom_components/mlb_standings/brand`](custom_components/mlb_standings/brand): local brand assets used by Home Assistant
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

## Lovelace Card Example

Use the division summary sensor in a Markdown card to show the full table for one selected division.

```yaml
type: markdown
title: MLB Standings
content: >
	{% set s = states.sensor['sensor.al_east_standings'] %}
	{% if s %}
	### {{ s.attributes.division }}

	| Team | W | L | GB | PCT |
	| --- | ---: | ---: | ---: | ---: |
	{% for row in s.attributes.standings %}
	| {{ row.team }} | {{ row.wins }} | {{ row.losses }} | {{ row.games_back }} | {{ '%.3f' | format(row.winning_percentage) }} |
	{% endfor %}
	{% else %}
	No standings available.
	{% endif %}
```

Replace `sensor.al_east_standings` with the entity id for the division you selected in the integration options.

Use the postseason summary sensor in a second Markdown card to show the current playoff bracket.

```yaml
type: markdown
title: MLB Postseason
content: >
	{% set s = states.sensor['sensor.american_league_postseason'] %}
	{% if s %}
	### {{ s.attributes.league }}

	| Seed | Team | Division | W | L | PCT | Clinched |
	| --- | --- | --- | ---: | ---: | ---: | --- |
	{% for row in s.attributes.bracket %}
	| {{ row.seed }} | {{ row.team }} | {{ row.division }} | {{ row.wins }} | {{ row.losses }} | {{ '%.3f' | format(row.winning_percentage) }} | {{ 'Yes' if row.clinched else 'No' }} |
	{% endfor %}
	{% else %}
	No postseason data available.
	{% endif %}
```

Replace `sensor.american_league_postseason` with the AL or NL postseason entity id you want to display.

## Custom Lovelace Card

The repository now also includes a custom Lovelace card at [`www/mlb-standings-card.js`](www/mlb-standings-card.js).

The card includes live buttons in the header so you can switch AL/NL and divisions directly on the dashboard.

Add it to Home Assistant as a Lovelace resource with this URL:

```text
https://raw.githubusercontent.com/walteij/HA-integrations/main/www/mlb-standings-card.js
```

After adding the resource, use this card type in your dashboard:

```yaml
type: custom:mlb-standings-card
mode: division
league: AL
division: East
title: AL East Standings
```

For postseason brackets, switch the mode:

```yaml
type: custom:mlb-standings-card
mode: postseason
league: NL
title: NL Postseason
```

## Notes

- The integration polls the MLB Stats API directly.
- The old add-on/dashboard files are no longer the primary implementation.
- Local brand images in `custom_components/mlb_standings/brand` are supported by Home Assistant 2026.3 and newer; on 2026.1 the logo still needs to come from the Home Assistant brands repository.
