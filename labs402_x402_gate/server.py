"""
MCP server principal de labs402-x402-gate.
Expone la tool charge_and_serve sobre stdio para Claude Code, Cursor y OpenClaw.
"""

import json
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from mcp.server.fastmcp import FastMCP

from .config import load_config
from .handlers import RateLimiter
from .handlers import charge_and_serve as _charge_and_serve
from .store import ResourceStore
from .x402_client import X402Gate


def setup_logging(level: str = "INFO") -> None:
    """
    Configura logging estructurado en JSON hacia stderr.
    stderr se usa para no contaminar el canal stdio del protocolo MCP.
    """
    class _JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            entry: dict[str, Any] = {
                "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "msg": record.getMessage(),
            }
            if record.exc_info:
                entry["exc"] = self.formatException(record.exc_info)
            # Incluye campos extra si los hay (nunca loguear private_key)
            for key, val in record.__dict__.get("extra", {}).items():
                if key not in ("private_key", "seed", "mnemonic"):
                    entry[key] = val
            return json.dumps(entry, ensure_ascii=False)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler], force=True)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Inicializa los recursos compartidos al arrancar el servidor MCP."""
    config = load_config()
    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Iniciando labs402-x402-gate", extra={"network": config.network})

    store = ResourceStore()
    gate = X402Gate(
        facilitator_url=config.facilitator_url,
        wallet_address=config.solana_wallet_address,
        network=config.network,
        min_amount_usdc=config.min_amount_usdc,
    )
    rate_limiter = RateLimiter(max_requests=config.rate_limit_per_minute, window_seconds=60)

    yield {
        "config": config,
        "store": store,
        "gate": gate,
        "rate_limiter": rate_limiter,
    }

    logger.info("Servidor MCP detenido")


mcp = FastMCP("labs402-x402-gate", lifespan=lifespan)


@mcp.tool()
async def charge_and_serve(
    resource_id: str,
    payment_header: Optional[str] = None,
    payer_wallet: Optional[str] = None,
) -> dict[str, Any]:
    """
    Accede a un recurso protegido por pago x402 en Solana.

    Flujo de dos pasos:
    1. Llamar sin payment_header -> el servidor devuelve los requisitos de pago (challenge).
    2. Firmar el pago con la wallet y llamar de nuevo con payment_header -> el servidor
       verifica via facilitator y entrega el contenido.

    Args:
        resource_id: Identificador del recurso a acceder.
        payment_header: Pago firmado en base64 (obtenido del paso 1).
        payer_wallet: Direccion publica de la wallet que paga (para rate limiting).

    Returns:
        Con status "payment_required": incluye payment_requirements para firmar.
        Con status "success": incluye el content del recurso y el tx hash.
    """
    # El lifespan_context lo provee FastMCP automaticamente
    # Acceso via atributo del server singleton para compatibilidad con MCP SDK 1.x
    from mcp.server.fastmcp import Context
    ctx = mcp.get_context()
    lc = ctx.request_context.lifespan_context

    return await _charge_and_serve(
        resource_id=resource_id,
        payment_header=payment_header,
        payer_wallet=payer_wallet,
        store=lc["store"],
        gate=lc["gate"],
        rate_limiter=lc["rate_limiter"],
    )
