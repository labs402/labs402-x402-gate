"""Logica de negocio de charge_and_serve y rate limiter."""

import logging
import time
from collections import defaultdict
from typing import Any, Optional

from .store import ResourceStore
from .types import PaymentChallenge, PaymentResult
from .x402_client import X402Gate

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter en memoria por wallet pagadora.
    No persiste entre reinicios del servidor.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self._max = max_requests
        self._window = window_seconds
        # wallet -> lista de timestamps de peticiones recientes
        self._requests: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        """
        Devuelve True si la peticion esta dentro del limite.
        Devuelve False si se supero el maximo para esa clave en la ventana de tiempo.
        """
        now = time.monotonic()
        cutoff = now - self._window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= self._max:
            return False
        self._requests[key].append(now)
        return True

    def reset(self, key: str) -> None:
        """Limpia el historial de un key (util en tests)."""
        self._requests.pop(key, None)


async def charge_and_serve(
    resource_id: str,
    payment_header: Optional[str],
    payer_wallet: Optional[str],
    store: ResourceStore,
    gate: X402Gate,
    rate_limiter: RateLimiter,
) -> dict[str, Any]:
    """
    Logica central del MCP server x402.

    Flujo:
    1. Verifica que el recurso existe.
    2. Aplica rate limiting por wallet pagadora (si se proporciona).
    3. Sin payment_header -> devuelve el challenge de pago.
    4. Con payment_header -> verifica via facilitator y entrega el contenido.
    """
    # Paso 1: buscar el recurso en el store
    resource = store.get(resource_id)
    if resource is None:
        raise ValueError(f"Recurso no encontrado: '{resource_id}'")

    # Paso 2: rate limiting (solo si se conoce la wallet del pagador)
    if payer_wallet:
        if not rate_limiter.allow(payer_wallet):
            raise ValueError(
                f"Limite de peticiones excedido para {payer_wallet}. "
                f"Maximo {rate_limiter._max} peticiones por {rate_limiter._window} segundos."
            )

    # Paso 3: sin pago -> devolver challenge
    if not payment_header:
        requirements = gate.build_payment_requirements(resource.price_usdc)
        challenge = PaymentChallenge(
            resource_id=resource_id,
            payment_requirements=requirements,
            message=(
                f"Se requieren ${resource.price_usdc:.6f} USDC en {resource.network} "
                f"para acceder a '{resource.name}'. "
                "Incluye el pago firmado en el campo payment_header y reintenta."
            ),
        )
        logger.debug("Challenge emitido", extra={"resource_id": resource_id})
        return challenge.to_dict()

    # Paso 4: verificar y liquidar el pago
    success, tx_hash = await gate.verify_and_settle(payment_header, resource.price_usdc)
    if not success:
        raise ValueError(f"Pago invalido o rechazado por el facilitator: {tx_hash}")

    result = PaymentResult(
        resource_id=resource_id,
        content=resource.content,
        transaction=tx_hash,
    )
    logger.debug("Contenido entregado", extra={"resource_id": resource_id, "tx": tx_hash})
    return result.to_dict()
