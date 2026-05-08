"""
Envoltorio sobre el SDK x402 para el lado servidor.
Maneja la construccion de requisitos de pago y la verificacion/liquidacion via facilitator.
"""

import base64
import json
import logging
from typing import Any, Optional

from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.mechanisms.svm.exact import ExactSvmServerScheme
from x402.server import x402ResourceServer

logger = logging.getLogger(__name__)


class X402Gate:
    """
    Interfaz de alto nivel para operaciones x402 en el servidor.
    Centraliza la verificacion y liquidacion de pagos via facilitator.
    """

    def __init__(
        self,
        facilitator_url: str,
        wallet_address: str,
        network: str,
        min_amount_usdc: float = 0.001,
        _resource_server: Optional[Any] = None,
    ) -> None:
        """
        _resource_server permite inyectar un mock en tests.
        En produccion se construye automaticamente desde facilitator_url.
        """
        self._wallet_address = wallet_address
        self._network = network
        self._min_amount_usdc = min_amount_usdc

        if _resource_server is not None:
            self._server = _resource_server
        else:
            http_client = HTTPFacilitatorClient(FacilitatorConfig(url=facilitator_url))
            self._server = x402ResourceServer(http_client)
            self._server.register(network, ExactSvmServerScheme())

    def build_payment_requirements(self, price_usdc: float) -> list[dict[str, Any]]:
        """
        Construye la lista de opciones de pago para un recurso.
        Aplica el minimo configurado como proteccion contra errores de unidades.
        """
        price = max(price_usdc, self._min_amount_usdc)
        # Construye el dict de requisitos directamente en formato camelCase (protocolo x402 v2)
        return [{
            "scheme": "exact",
            "payTo": self._wallet_address,
            "price": f"${price:.6f}",
            "network": self._network,
        }]

    async def verify_and_settle(
        self,
        payment_header: str,
        price_usdc: float,
    ) -> tuple[bool, str]:
        """
        Verifica el pago con el facilitator y, si es valido, lo liquida on-chain.
        Devuelve (exito, tx_hash_o_mensaje_de_error).
        """
        try:
            payload = json.loads(base64.b64decode(payment_header))
            requirements = self.build_payment_requirements(price_usdc)

            # Verificacion: el facilitator comprueba firma y fondos
            verify_result = await self._server.verify(payload, requirements)
            if not verify_result.is_valid:
                logger.debug("Pago rechazado por el facilitator")
                return False, "Verificacion fallida"

            # Liquidacion: el facilitator transmite la transaccion a la red
            settle_result = await self._server.settle(payload, requirements)
            tx_hash = getattr(settle_result, "transaction", "") or getattr(settle_result, "txHash", "")
            logger.debug("Pago liquidado", extra={"tx": tx_hash})
            return True, tx_hash

        except Exception as exc:
            logger.warning("Error en verify_and_settle: %s", exc)
            return False, str(exc)
