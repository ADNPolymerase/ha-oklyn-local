"""Diagnostics pour Oklyn Local."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import OklynLocalCoordinator

# Champs potentiellement sensibles à masquer dans /api/info
TO_REDACT = {"mac", "ssid", "serial", "ip_adress", "ip_address"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator: OklynLocalCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    return {
        "entry": {
            "host": entry.data.get("host"),
            "options": dict(entry.options),
        },
        "info": async_redact_data(data.get("info") or {}, TO_REDACT),
        "data": data.get("data") or {},
        "last_update_success": coordinator.last_update_success,
    }
