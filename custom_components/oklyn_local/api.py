"""Local HTTP client for the Oklyn pool controller (read-only).

Interroge uniquement deux endpoints en GET :
    GET http://<host>/api/info
    GET http://<host>/api/data

Aucune écriture (PUT/POST) n'est implémentée — c'est volontaire.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import DEFAULT_TIMEOUT, ENDPOINT_DATA, ENDPOINT_INFO

_LOGGER = logging.getLogger(__name__)


class OklynLocalError(Exception):
    """Base error for the local client."""


class OklynLocalConnectionError(OklynLocalError):
    """Connexion / réseau / timeout."""


class OklynLocalResponseError(OklynLocalError):
    """Réponse HTTP inattendue ou JSON invalide."""


class OklynLocalClient:
    """Async client interrogeant le boîtier Oklyn en local."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self._session = session
        # Accepte une IP nue, un host, ou une URL complète
        host = host.strip().rstrip("/")
        if not host.startswith(("http://", "https://")):
            host = f"http://{host}"
        self._base_url = host
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def _async_get(self, endpoint: str) -> dict[str, Any]:
        url = f"{self._base_url}{endpoint}"
        try:
            async with self._session.get(url, timeout=self._timeout) as resp:
                if resp.status != 200:
                    raise OklynLocalResponseError(
                        f"HTTP {resp.status} sur {endpoint}"
                    )
                try:
                    data = await resp.json(content_type=None)
                except Exception as exc:  # noqa: BLE001
                    raise OklynLocalResponseError(
                        f"JSON invalide depuis {endpoint}"
                    ) from exc
        except OklynLocalError:
            raise
        except asyncio.TimeoutError as exc:
            raise OklynLocalConnectionError(
                f"Timeout en interrogeant {url}"
            ) from exc
        except aiohttp.ClientError as exc:
            raise OklynLocalConnectionError(f"Erreur réseau: {exc}") from exc

        if not isinstance(data, dict):
            raise OklynLocalResponseError(
                f"Réponse inattendue (pas un objet JSON) sur {endpoint}"
            )
        _LOGGER.debug("GET %s -> %d champs", endpoint, len(data))
        return data

    async def async_get_info(self) -> dict[str, Any]:
        """GET /api/info — informations techniques du boîtier."""
        return await self._async_get(ENDPOINT_INFO)

    async def async_get_data(self) -> dict[str, Any]:
        """GET /api/data — mesures brutes."""
        return await self._async_get(ENDPOINT_DATA)
