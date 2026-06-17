"""Base entity partagée pour Oklyn Local."""
from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import OklynLocalCoordinator


class OklynLocalEntity(CoordinatorEntity[OklynLocalCoordinator]):
    """Base : rattache toutes les entités au même device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: OklynLocalCoordinator) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        info = (coordinator.data or {}).get("info") or {}
        serial = str(info.get("serial") or entry.unique_id or entry.entry_id)
        mac = info.get("mac")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            connections={(CONNECTION_NETWORK_MAC, mac)} if mac else set(),
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=info.get("hostname") or "Oklyn Local",
            sw_version=str(info.get("core_version") or info.get("version") or ""),
            configuration_url=f"http://{entry.data.get('host')}",
        )
