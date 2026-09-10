# MLB Standings Home Assistant Integration

This repository now contains a proper Home Assistant custom integration that exposes MLB standings as sensor entities.

## What it provides

- League leader sensors for the American League and National League
- Division leader sensors for all six MLB divisions
- Team sensors for the selected league or division scope
- An optional favorite team sensor
- Team logos through `entity_picture` when enabled

## Integration options

- `view_mode`: `all`, `league`, or `division`
- `league_id`: `103` for AL or `104` for NL
- `division_id`: one of `200`, `201`, `202`, `203`, `204`, `205`
- `favorite_team`: team name, for example `Yankees` or `Phillies`
- `show_logos`: `true` or `false`

## Install locally

1. Copy `custom_components/mlb_standings` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration from Settings > Devices & services > Add integration.
4. Adjust the options if you want to track just one league or one division.

## Notes

- The integration polls the MLB Stats API directly.
- The old add-on/dashboard files are no longer the primary implementation.
