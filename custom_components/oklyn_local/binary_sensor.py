"""Binary sensors Oklyn Local (depuis /api/info).

  - service_granted : connecté/autorisé au service Oklyn (granted)
  - key_valid       : clef de sécurité valide (key)
  - config_valid    : configuration valide (valid)
"""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import OklynLocalCoordinator
from .entity import OklynLocalEntity


@dataclass(frozen=True, kw_only=True)
class OklynBinaryDescription(BinarySensorEntityDescription):
    """Description d'un binary_sensor Oklyn (toujours depuis /api/info)."""

    field: str = ""


BINARY_SENSORS: tuple[OklynBinaryDescription, ...] = (
    OklynBinaryDescription(
        key="service_granted",
        translation_key="service_granted",
        field="granted",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    OklynBinaryDescription(
        key="key_valid",
        translation_key="key_valid",
        field="key",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    OklynBinaryDescription(
        key="config_valid",
        translation_key="config_valid",
        field="valid",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: OklynLocalCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OklynLocalBinarySensor(coordinator, desc) for desc in BINARY_SENSORS
    )


class OklynLocalBinarySensor(OklynLocalEntity, BinarySensorEntity):
    """Binary sensor générique basé sur un booléen de /api/info."""

    entity_description: OklynBinaryDescription

    def __init__(
        self,
        coordinator: OklynLocalCoordinator,
        description: OklynBinaryDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = next(iter(self._attr_device_info["identifiers"]))[1]
        self._attr_unique_id = f"{serial}_{description.key}"

    @property
    def _info(self) -> dict | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("info")

    @property
    def available(self) -> bool:
        info = self._info
        return (
            super().available
            and info is not None
            and self.entity_description.field in info
        )

    @property
    def is_on(self) -> bool | None:
        info = self._info
        if info is None:
            return None
        return bool(info.get(self.entity_description.field))
