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

from .const import DATA_DIVIDE, DOMAIN, SC1_MANUAL_OFF, SC1_MANUAL_ON
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
    # attrs_fn reçoit TOUT le dict de l'endpoint et retourne des attributs
    # supplémentaires (ex. valeur brute sonde + offset) pour les capteurs
    # "corrigés", afin de garder la traçabilité brut → correction → corrigé.
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


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


def _temp_eau_corrigee(payload: dict[str, Any]) -> float | None:
    """Température eau corrigée = (EAU + ATE) / 100."""
    brut, corr = _num(payload, "EAU"), _num(payload, "ATE")
    if brut is None or corr is None:
        return None
    return (brut + corr) / DATA_DIVIDE["EAU"]


def _temp_air_corrigee(payload: dict[str, Any]) -> float | None:
    """Température air corrigée = (AIR + ATA) / 100."""
    brut, corr = _num(payload, "AIR"), _num(payload, "ATA")
    if brut is None or corr is None:
        return None
    return (brut + corr) / DATA_DIVIDE["AIR"]


def _raw_corrected_attrs(
    raw_field: str, offset_field: str, divide: float
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Construit un attrs_fn exposant raw / offset / corrigé sur un capteur "corrigé".

    Garde la traçabilité du calcul sans dupliquer d'entités : la valeur brute
    sonde et l'offset restent disponibles en attribut du capteur principal.
    """

    def _attrs(payload: dict[str, Any]) -> dict[str, Any]:
        brut, off = _num(payload, raw_field), _num(payload, offset_field)
        attrs: dict[str, Any] = {}
        if brut is not None:
            attrs[f"raw_{raw_field.lower()}"] = brut / divide
        if off is not None:
            attrs[f"offset_{offset_field.lower()}"] = off / divide
        if brut is not None and off is not None:
            attrs["corrected"] = (brut + off) / divide
        return attrs

    return _attrs


# --- Mesures principales (converties) --------------------------------------
MEASURE_SENSORS: tuple[OklynSensorDescription, ...] = (
    # --- Température eau : corrigée (principale) + sonde brute -------------
    OklynSensorDescription(
        key="temperature_eau",
        translation_key="temperature_eau",
        source="data",
        field="EAU",
        payload_fn=_temp_eau_corrigee,   # (EAU + ATE) / 100 — confirmé 2026-06-15
        attrs_fn=_raw_corrected_attrs("EAU", "ATE", DATA_DIVIDE["EAU"]),
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    OklynSensorDescription(
        key="temperature_eau_sonde",
        translation_key="temperature_eau_sonde",
        source="data",
        field="EAU",
        divide=DATA_DIVIDE["EAU"],       # EAU / 100 (sonde brute)
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
    ),
    # --- Température air : corrigée (principale) + sonde brute -------------
    OklynSensorDescription(
        key="temperature_air",
        translation_key="temperature_air",
        source="data",
        field="AIR",
        payload_fn=_temp_air_corrigee,   # (AIR + ATA) / 100 — confirmé 2026-06-15
        attrs_fn=_raw_corrected_attrs("AIR", "ATA", DATA_DIVIDE["AIR"]),
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    OklynSensorDescription(
        key="temperature_air_sonde",
        translation_key="temperature_air_sonde",
        source="data",
        field="AIR",
        divide=DATA_DIVIDE["AIR"],       # AIR / 100 (sonde brute)
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
    ),
    # --- Température boîtier -----------------------------------------------
    OklynSensorDescription(
        key="temperature_boitier",
        translation_key="temperature_boitier",
        source="data",
        field="BOX",
        divide=DATA_DIVIDE["BOX"],       # BOX en °C entier (probable)
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    # --- pH : valeur corrigée (principale) + valeur brute sonde ------------
    OklynSensorDescription(
        key="ph",
        translation_key="ph",
        source="data",
        field="PH1",                 # champ requis pour la disponibilité
        payload_fn=_ph_corrige,      # (PH1 + APH) / 100
        attrs_fn=_raw_corrected_attrs("PH1", "APH", DATA_DIVIDE["PH1"]),
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
        attrs_fn=_raw_corrected_attrs("ORP", "ARX", DATA_DIVIDE["ORP"]),
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
    OklynSensorDescription(
        key="offset_temp_eau",
        translation_key="offset_temp_eau",
        source="data",
        field="ATE",
        divide=DATA_DIVIDE["ATE"],
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
    ),
    OklynSensorDescription(
        key="offset_temp_air",
        translation_key="offset_temp_air",
        source="data",
        field="ATA",
        divide=DATA_DIVIDE["ATA"],
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
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
    entities: list[SensorEntity] = [
        OklynLocalSensor(coordinator, desc) for desc in descriptions
    ]
    entities.append(OklynPumpModeSensor(coordinator))
    async_add_entities(entities)


class OklynPumpModeSensor(OklynLocalEntity, SensorEntity):
    """Mode de la pompe déduit de SC1 : auto / manuel (sinon arrêt = auto)."""

    _attr_translation_key = "pompe_mode"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["auto", "manuel"]
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: OklynLocalCoordinator) -> None:
        super().__init__(coordinator)
        serial = next(iter(self._attr_device_info["identifiers"]))[1]
        self._attr_unique_id = f"{serial}_pompe_mode"

    def _sc1(self) -> int | None:
        data = (self.coordinator.data or {}).get("data")
        if not data or "SC1" not in data:
            return None
        try:
            return int(data["SC1"])
        except (TypeError, ValueError):
            return None

    @property
    def available(self) -> bool:
        return super().available and self._sc1() is not None

    @property
    def native_value(self) -> str | None:
        sc1 = self._sc1()
        if sc1 is None:
            return None
        if (sc1 >> SC1_MANUAL_ON) & 1 or (sc1 >> SC1_MANUAL_OFF) & 1:
            return "manuel"
        return "auto"


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

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        desc = self.entity_description
        if desc.attrs_fn is None:
            return None
        payload = self._payload
        if payload is None:
            return None
        return desc.attrs_fn(payload) or None
