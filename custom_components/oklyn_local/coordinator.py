"""DataUpdateCoordinator pour Oklyn Local.

Interroge /api/info et /api/data en parallèle et fusionne le résultat dans un
seul dict :

    {
        "info": {... ou None si l'appel a échoué ...},
        "data": {... ou None si l'appel a échoué ...},
    }

Stratégie de cache (v0.1.9b1) :
- Si un endpoint répond → on met à jour la portion correspondante du cache.
- Si un endpoint échoue mais qu'on a une valeur récente (< CACHE_TTL_FACTOR ×
  scan_interval) → on la conserve (entités disponibles avec la dernière valeur
  connue).
- Au-delà du TTL → cache expiré, on renvoie None pour que les entités passent
  en unavailable plutôt que de servir un état périmé.
- Si les DEUX échouent ET qu'on n'a jamais eu de données → UpdateFailed.
- L'âge de la donnée est visible via le champ TIM exposé en sensor horodatage.

Améliorations de réactivité :
- Re-poll immédiat (1 s) après sortie d'une coupure HTTP — évite de servir
  le cache périmé pendant tout un cycle de 15 s.
- HTTP_RETRY_DELAY réduit à 0.3 s — moins de dead time pendant les corps vides.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OklynLocalClient, OklynLocalError
from .const import CACHE_TTL_FACTOR, DEFAULT_SCAN_INTERVAL, DOMAIN, OPT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

_REPOLL_DELAY = 1.0  # secondes après sortie de coupure


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
        self._last_good_ts: float = 0.0   # timestamp monotone du dernier poll réussi
        self._was_degraded: bool = False   # True si le dernier poll avait échoué
        scan_interval = entry.options.get(OPT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self._cache_ttl = scan_interval * CACHE_TTL_FACTOR
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

        now = time.monotonic()
        poll_ok = info is not None or data is not None

        if poll_ok:
            # Mise à jour du cache uniquement si l'endpoint a répondu.
            if info is not None:
                self._last_good["info"] = info
            if data is not None:
                self._last_good["data"] = data
            self._last_good_ts = now

            # Sortie de coupure → re-poll immédiat pour effacer le cache périmé.
            if self._was_degraded:
                _LOGGER.debug("Oklyn local : sortie de coupure — re-poll dans %.0f s", _REPOLL_DELAY)
                self.hass.loop.call_later(
                    _REPOLL_DELAY,
                    lambda: self.hass.async_create_task(self.async_request_refresh()),
                )
            self._was_degraded = False
        else:
            self._was_degraded = True

        # Cache expiré : ne pas servir un état trop vieux.
        cache_age = now - self._last_good_ts if self._last_good_ts else float("inf")
        cache_valid = cache_age < self._cache_ttl

        # Premier démarrage sans aucune donnée → échec normal.
        if not poll_ok and (
            self._last_good["info"] is None and self._last_good["data"] is None
        ):
            raise UpdateFailed("Boîtier Oklyn injoignable (info + data en échec)")

        if not poll_ok:
            if cache_valid:
                _LOGGER.warning(
                    "Oklyn local injoignable — cache conservé (âge=%.0fs, TIM=%s)",
                    cache_age,
                    (self._last_good.get("data") or {}).get("TIM"),
                )
            else:
                _LOGGER.warning(
                    "Oklyn local injoignable — cache expiré (âge=%.0fs > TTL=%.0fs) "
                    "→ entités unavailable",
                    cache_age,
                    self._cache_ttl,
                )
                return {"info": None, "data": None}

        return {
            "info": info if info is not None else (self._last_good["info"] if cache_valid else None),
            "data": data if data is not None else (self._last_good["data"] if cache_valid else None),
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
