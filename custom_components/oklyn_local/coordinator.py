"""DataUpdateCoordinator pour Oklyn Local.

Interroge /api/info et /api/data en parallèle et fusionne le résultat dans un
seul dict :

    {
        "info": {... ou None si l'appel a échoué ...},
        "data": {... ou None si l'appel a échoué ...},
    }

Stratégie de cache :
- Si un endpoint répond → on met à jour la portion correspondante du cache.
- Si un endpoint échoue mais qu'on a une valeur précédente → on la conserve
  (les entités restent disponibles avec la dernière valeur connue).
- Si les DEUX échouent ET qu'on n'a jamais eu de données → UpdateFailed.
- L'âge de la donnée est visible via le champ TIM (timestamp du boîtier)
  exposé en sensor horodatage.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OklynLocalClient, OklynLocalError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, OPT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class OklynLocalCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordonne le polling des endpoints locaux Oklyn."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: OklynLocalClient,
        entry: ConfigEntry,
    ) -> None:
        self._client = client
        self._last_good: dict[str, Any] = {"info": None, "data": None}
        scan_interval = entry.options.get(OPT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        info_res, data_res = await asyncio.gather(
            self._client.async_get_info(),
            self._client.async_get_data(),
            return_exceptions=True,
        )

        info = self._unwrap(info_res, "info")
        data = self._unwrap(data_res, "data")

        # Mise à jour du cache uniquement si l'endpoint a répondu.
        if info is not None:
            self._last_good["info"] = info
        if data is not None:
            self._last_good["data"] = data

        # Premier démarrage sans aucune donnée → échec normal.
        if info is None and data is None:
            if self._last_good["info"] is None and self._last_good["data"] is None:
                raise UpdateFailed("Boîtier Oklyn injoignable (info + data en échec)")
            _LOGGER.warning(
                "Oklyn local injoignable — données précédentes conservées (TIM=%s)",
                (self._last_good.get("data") or {}).get("TIM"),
            )

        return {
            "info": info if info is not None else self._last_good["info"],
            "data": data if data is not None else self._last_good["data"],
        }

    @staticmethod
    def _unwrap(result: Any, key: str) -> dict[str, Any] | None:
        if isinstance(result, dict):
            return result
        if isinstance(result, OklynLocalError):
            _LOGGER.debug("Endpoint %s indisponible: %s", key, result)
            return None
        if isinstance(result, Exception):
            _LOGGER.warning("Erreur inattendue sur %s: %s", key, result)
            return None
        return None
