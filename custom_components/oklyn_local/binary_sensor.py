"""Binary sensors Oklyn Local.

Depuis /api/info :
  - service_granted : connecté/autorisé au service Oklyn (granted)
  - key_valid       : clef de sécurité valide (key)
  - config_valid    : configuration valide (valid)

Décodés depuis /api/data (champ SC1, bitfield d'état) :
  - pompe           : pompe en marche (bit 14)
  - aux1            : sortie relais AUX1 (bit 22), nom/type configurables

AUX2 n'est PAS exposé par le boîtier en local → pas de capteur AUX2 ici.
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

from .const import (
    AUX1_TYPE_ELECTROLYZER,
    AUX1_TYPE_HEATING,
    AUX1_TYPE_LIGHT,
    DEFAULT_AUX1_NAME,
    DEFAULT_AUX1_TYPE,
    DOMAIN,
    OPT_AUX1_NAME,
    OPT_AUX1_TYPE,
    SC1_AUX1,
    SC1_PUMP_RUNNING,
)
from .coordinator import OklynLocalCoordinator
from .entity import OklynLocalEntity


def _sc1(coordinator: OklynLocalCoordinator) -> int | None:
    """Retourne la valeur SC1 du dernier /api/data, ou None si indispo."""
    data = (coordinator.data or {}).get("data")
    if not data or "SC1" not in data:
        return None
    try:
        return int(data["SC1"])
    except (TypeError, ValueError):
        return None


# Type AUX1 -> (device_class, icône)
AUX1_TYPE_PRESENTATION = {
    AUX1_TYPE_LIGHT: (BinarySensorDeviceClass.LIGHT, "mdi:lightbulb"),
    AUX1_TYPE_HEATING: (BinarySensorDeviceClass.HEAT, "mdi:radiator"),
    AUX1_TYPE_ELECTROLYZER: (BinarySensorDeviceClass.RUNNING, "mdi:atom"),
}


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
    entities: list[BinarySensorEntity] = [
        OklynLocalBinarySensor(coordinator, desc) for desc in BINARY_SENSORS
    ]
    entities.append(OklynPumpRunningBinarySensor(coordinator))
    entities.append(OklynAux1BinarySensor(coordinator, entry))
    async_add_entities(entities)


class _OklynSc1BitBinarySensor(OklynLocalEntity, BinarySensorEntity):
    """Base : binary_sensor lisant un bit du champ SC1 (/api/data)."""

    _bit: int

    @property
    def available(self) -> bool:
        return super().available and _sc1(self.coordinator) is not None

    @property
    def is_on(self) -> bool | None:
        sc1 = _sc1(self.coordinator)
        if sc1 is None:
            return None
        return bool((sc1 >> self._bit) & 1)


class OklynPumpRunningBinarySensor(_OklynSc1BitBinarySensor):
    """Pompe en marche (SC1 bit 14)."""

    _bit = SC1_PUMP_RUNNING
    _attr_translation_key = "pompe"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: OklynLocalCoordinator) -> None:
        super().__init__(coordinator)
        serial = next(iter(self._attr_device_info["identifiers"]))[1]
        self._attr_unique_id = f"{serial}_pompe"


class OklynAux1BinarySensor(_OklynSc1BitBinarySensor):
    """Sortie AUX1 (SC1 bit 22). Nom/type configurables via les options."""

    _bit = SC1_AUX1
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: OklynLocalCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        serial = next(iter(self._attr_device_info["identifiers"]))[1]
        self._attr_unique_id = f"{serial}_aux1"
        # Nom libre choisi par l'utilisateur (ex. "Lumière").
        self._attr_name = entry.options.get(OPT_AUX1_NAME, DEFAULT_AUX1_NAME)
        aux_type = entry.options.get(OPT_AUX1_TYPE, DEFAULT_AUX1_TYPE)
        presentation = AUX1_TYPE_PRESENTATION.get(aux_type)
        if presentation:
            self._attr_device_class, self._attr_icon = presentation
        else:  # custom
            self._attr_device_class = BinarySensorDeviceClass.POWER


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
