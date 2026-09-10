# Integrations

This folder is a documentation hub for all integrations in this repository.

Each integration should get its own subfolder here so the repository can grow without becoming flat or confusing.

Recommended pattern:

- `custom_components/<domain>` for the actual Home Assistant integration code
- `integrations/<domain>` for documentation, notes, and future expansion details

This repository is intended to stay HACS-friendly, so the code that Home Assistant installs must remain under `custom_components/`.