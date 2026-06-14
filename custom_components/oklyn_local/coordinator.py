"""DataUpdateCoordinator pour Oklyn Local.

Interroge /api/info et /api/data en parallèle et fusionne le résultat dans un
seul dict :

    {
        "info": {... ou None si l'appel a échoué ...},
        "data": {... ou None si l'appel a échoué ...},
    }

- Si /api/data échoue → les capteurs de mesure deviennent indisponibles.
- Si /api/info échoue → les capteurs diagnostic deviennent indisponibles.
- Si les DEUX échouent → UpdateFailed (toutes les entités indisponibles).
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

        if info is None and data is None:
            raise UpdateFailed("Boîtier Oklyn injoignable (info + data en échec)")

        return {"info": info, "data": data}

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
