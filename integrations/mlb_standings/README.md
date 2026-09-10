# MLB Standings Integration

This folder documents the MLB Standings integration that is implemented in `custom_components/mlb_standings`.

## Purpose

Show MLB standings in Home Assistant as sensor entities with selectable scope and an optional favorite team.

## Install Location

The actual Home Assistant integration code lives in:

- `custom_components/mlb_standings`

## Why This Folder Exists

This repository is set up to host multiple Home Assistant integrations over time.

Keeping a separate documentation folder per integration makes it easier to:

- explain what each integration does
- add notes or usage examples
- keep future integrations organized
- preserve HACS compatibility by leaving installable code in `custom_components/`

## Current Status

The MLB Standings integration is ready as a custom integration with:

- config flow selectors
- options flow support
- sensor entities backed by a shared data coordinator
- local brand images for newer Home Assistant versions; on 2026.1 the logo must still be provided through the Home Assistant brands repository
