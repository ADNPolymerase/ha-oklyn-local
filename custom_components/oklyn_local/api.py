"""Local HTTP client for the Oklyn pool controller (read-only).

Interroge uniquement deux endpoints en GET :
    GET http://<host>/api/info
    GET http://<host>/api/data

Aucune écriture (PUT/POST) n'est implémentée — c'est volontaire.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from .const import (
    DEFAULT_TIMEOUT,
    ENDPOINT_DATA,
    ENDPOINT_INFO,
    HTTP_RETRIES,
    HTTP_RETRY_DELAY,
)

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

    async def _async_get_once(self, endpoint: str) -> dict[str, Any]:
        """Une seule tentative GET (lève en cas d'échec)."""
        url = f"{self._base_url}{endpoint}"
        try:
            async with self._session.get(url, timeout=self._timeout) as resp:
                if resp.status != 200:
                    raise OklynLocalResponseError(
                        f"HTTP {resp.status} sur {endpoint}"
                    )
                body = (await resp.text()).strip()
        except OklynLocalError:
            raise
        except asyncio.TimeoutError as exc:
            raise OklynLocalConnectionError(
                f"Timeout en interrogeant {url}"
            ) from exc
        except aiohttp.ClientError as exc:
            raise OklynLocalConnectionError(f"Erreur réseau: {exc}") from exc

        # Le boîtier renvoie parfois un corps VIDE avec un HTTP 200.
        if not body:
            raise OklynLocalResponseError(f"Corps vide sur {endpoint}")
        try:
            data = json.loads(body)
        except ValueError as exc:
            raise OklynLocalResponseError(
                f"JSON invalide depuis {endpoint}"
            ) from exc
        if not isinstance(data, dict):
            raise OklynLocalResponseError(
                f"Réponse inattendue (pas un objet JSON) sur {endpoint}"
            )
        return data

    async def _async_get(
        self, endpoint: str, retries: int = HTTP_RETRIES
    ) -> dict[str, Any]:
        """GET avec retries — le boîtier renvoie souvent un corps vide en HTTP 200.

        On réessaie sur réponse vide / JSON invalide / erreur réseau, espacés
        de HTTP_RETRY_DELAY, dans le même cycle de polling.
        """
        last_exc: OklynLocalError | None = None
        for attempt in range(1, retries + 1):
            try:
                data = await self._async_get_once(endpoint)
                if attempt > 1:
                    _LOGGER.debug(
                        "GET %s OK après %d tentatives", endpoint, attempt
                    )
                else:
                    _LOGGER.debug("GET %s -> %d champs", endpoint, len(data))
                return data
            except OklynLocalError as exc:
                last_exc = exc
                if attempt < retries:
                    _LOGGER.debug(
                        "GET %s tentative %d/%d échouée (%s), retry dans %.1fs",
                        endpoint, attempt, retries, exc, HTTP_RETRY_DELAY,
                    )
                    await asyncio.sleep(HTTP_RETRY_DELAY)
        assert last_exc is not None
        raise last_exc

    async def async_get_info(self) -> dict[str, Any]:
        """GET /api/info — informations techniques du boîtier."""
        return await self._async_get(ENDPOINT_INFO)

    async def async_get_data(self) -> dict[str, Any]:
        """GET /api/data — mesures brutes."""
        return await self._async_get(ENDPOINT_DATA)
