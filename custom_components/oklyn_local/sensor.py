"""Capteurs Oklyn Local (lecture seule).

Trois familles :
  - mesures principales (depuis /api/data, valeurs converties)
  - diagnostic boîtier (depuis /api/info)
  - capteurs bruts pour analyse (depuis /api/data, valeurs telles quelles)
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfInformation,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_DIVIDE, DOMAIN
from .coordinator import OklynLocalCoordinator
from .entity import OklynLocalEntity

# "source" indique de quel endpoint vient la valeur : "data" ou "info".


@dataclass(frozen=True, kw_only=True)
class OklynSensorDescription(SensorEntityDescription):
    """Description d'un capteur Oklyn local."""

    source: str = "data"          # "data" (/api/data) ou "info" (/api/info)
    field: str = ""               # clé JSON dans la réponse (sert aussi à la dispo)
    divide: float | None = None   # diviseur de conversion (None = brut)
    value_fn: Callable[[Any], Any] | None = None
    # payload_fn reçoit TOUT le dict de l'endpoint (pour combiner 2 champs,
    # ex. mesure corrigée = brut + correction). Prioritaire sur value_fn/divide.
    payload_fn: Callable[[dict[str, Any]], Any] | None = None


def _num(payload: dict[str, Any], field: str) -> float | None:
    """Lit un champ numérique du payload, ou None s'il manque/invalide."""
    raw = payload.get(field)
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _ph_corrige(payload: dict[str, Any]) -> float | None:
    """pH corrigé = (PH1 + APH) / 100."""
    brut, corr = _num(payload, "PH1"), _num(payload, "APH")
    if brut is None or corr is None:
        return None
    return (brut + corr) / DATA_DIVIDE["PH1"]


def _redox_corrige(payload: dict[str, Any]) -> float | None:
    """Redox corrigé = (ORP + ARX) / 10."""
    brut, corr = _num(payload, "ORP"), _num(payload, "ARX")
    if brut is None or corr is None:
        return None
    return (brut + corr) / DATA_DIVIDE["ORP"]


# --- Mesures principales (converties) --------------------------------------
MEASURE_SENSORS: tuple[OklynSensorDescription, ...] = (
    OklynSensorDescription(
        key="temperature_eau",
        translation_key="temperature_eau",
        source="data",
        field="EAU",
        divide=DATA_DIVIDE["EAU"],
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    OklynSensorDescription(
        key="temperature_air",
        translation_key="temperature_air",
        source="data",
        field="AIR",
        divide=DATA_DIVIDE["AIR"],
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    # --- pH : valeur corrigée (principale) + valeur brute sonde ------------
    OklynSensorDescription(
        key="ph",
        translation_key="ph",
        source="data",
        field="PH1",                 # champ requis pour la disponibilité
        payload_fn=_ph_corrige,      # (PH1 + APH) / 100
        native_unit_of_measurement="pH",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    OklynSensorDescription(
        key="ph_sonde",
        translation_key="ph_sonde",
        source="data",
        field="PH1",
        divide=DATA_DIVIDE["PH1"],   # PH1 / 100 (lecture sonde, sans correction)
        native_unit_of_measurement="pH",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    # --- Redox : valeur corrigée (principale) + valeur brute sonde ---------
    OklynSensorDescription(
        key="redox",
        translation_key="redox",
        source="data",
        field="ORP",
        payload_fn=_redox_corrige,   # (ORP + ARX) / 10
        native_unit_of_measurement="mV",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    OklynSensorDescription(
        key="redox_sonde",
        translation_key="redox_sonde",
        source="data",
        field="ORP",
        divide=DATA_DIVIDE["ORP"],   # ORP / 10 (lecture sonde, sans correction)
        native_unit_of_measurement="mV",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    # --- Corrections appliquées (APH/ARX), diagnostic ---------------------
    OklynSensorDescription(
        key="offset_ph",
        translation_key="offset_ph",
        source="data",
        field="APH",
        divide=DATA_DIVIDE["APH"],
        native_unit_of_measurement="pH",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        entity_registry_enabled_default=False,
    ),
    OklynSensorDescription(
        key="offset_redox",
        translation_key="offset_redox",
        source="data",
        field="ARX",
        divide=DATA_DIVIDE["ARX"],
        native_unit_of_measurement="mV",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
    ),
)

# --- Diagnostic boîtier (depuis /api/info) ---------------------------------
INFO_SENSORS: tuple[OklynSensorDescription, ...] = (
    OklynSensorDescription(
        key="wifi_signal",
        translation_key="wifi_signal",
        source="info",
        field="wifilevel",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    OklynSensorDescription(
        key="memory_free",
        translation_key="memory_free",
        source="info",
        field="memory_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    OklynSensorDescription(
        key="version",
        translation_key="version",
        source="info",
        field="version",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    OklynSensorDescription(
        key="core_version",
        translation_key="core_version",
        source="info",
        field="core_version",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    OklynSensorDescription(
        key="sdk_version",
        translation_key="sdk_version",
        source="info",
        field="sdk_version",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

# --- Capteurs bruts pour analyse (depuis /api/data) ------------------------
# Exposés tels quels, désactivés par défaut pour ne pas polluer l'UI.
RAW_DATA_FIELDS = (
    "HSN", "TIM", "SC1", "BOX", "OQT", "PQT", "HPN",
    "SPN", "SC2", "ECM", "APH", "ARX", "AMG", "ATA", "ATE",
)

RAW_SENSORS: tuple[OklynSensorDescription, ...] = tuple(
    OklynSensorDescription(
        key=f"raw_{field.lower()}",
        translation_key="raw_field",
        source="data",
        field=field,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    )
    for field in RAW_DATA_FIELDS
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: OklynLocalCoordinator = hass.data[DOMAIN][entry.entry_id]
    descriptions = (*MEASURE_SENSORS, *INFO_SENSORS, *RAW_SENSORS)
    async_add_entities(
        OklynLocalSensor(coordinator, desc) for desc in descriptions
    )


class OklynLocalSensor(OklynLocalEntity, SensorEntity):
    """Un capteur générique Oklyn local."""

    entity_description: OklynSensorDescription

    def __init__(
        self,
        coordinator: OklynLocalCoordinator,
        description: OklynSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = next(iter(self._attr_device_info["identifiers"]))[1]
        self._attr_unique_id = f"{serial}_{description.key}"
        # Le translation_key "raw_field" est partagé : on personnalise le nom
        if description.translation_key == "raw_field":
            self._attr_translation_placeholders = {"field": description.field}

    @property
    def _payload(self) -> dict[str, Any] | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.source)

    @property
    def available(self) -> bool:
        # Disponible uniquement si l'endpoint source a répondu et le champ existe.
        payload = self._payload
        return (
            super().available
            and payload is not None
            and self.entity_description.field in payload
        )

    @property
    def native_value(self) -> Any:
        payload = self._payload
        if payload is None:
            return None

        desc = self.entity_description
        if desc.payload_fn is not None:
            return desc.payload_fn(payload)

        raw = payload.get(desc.field)
        if raw is None:
            return None

        if desc.value_fn is not None:
            return desc.value_fn(raw)
        if desc.divide is not None:
            try:
                return float(raw) / desc.divide
            except (TypeError, ValueError):
                return None
        return raw
