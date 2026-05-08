"""Carga y validacion de configuracion desde variables de entorno."""

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Mint USDC en Solana mainnet-beta
USDC_MINT_MAINNET = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# Identificadores CAIP-2 por red
NETWORKS = {
    "mainnet-beta": "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
    "devnet": "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1",
}


@dataclass(frozen=True)
class Config:
    """Configuracion inmutable del servidor."""
    solana_wallet_address: str
    solana_private_key: str     # nunca se registra en logs
    facilitator_url: str
    network: str                # identificador CAIP-2
    usdc_mint: str
    min_amount_usdc: float
    rate_limit_per_minute: int
    log_level: str


def load_config() -> Config:
    """
    Carga la configuracion desde variables de entorno.
    Lanza ValueError si falta alguna variable obligatoria.
    """
    load_dotenv()
    private_key = os.environ.get("SOLANA_PRIVATE_KEY", "").strip()
    if not private_key:
        raise ValueError(
            "SOLANA_PRIVATE_KEY es obligatoria. "
            "Exportala desde Phantom: Configuracion > Mostrar clave privada."
        )

    wallet_address = os.environ.get("SOLANA_WALLET_ADDRESS", "").strip()
    if not wallet_address:
        raise ValueError(
            "SOLANA_WALLET_ADDRESS es obligatoria. "
            "Es la direccion publica de la wallet que recibe los pagos."
        )

    network_name = os.environ.get("LABS402_NETWORK", "mainnet-beta").strip()
    network_caip2 = NETWORKS.get(network_name)
    if not network_caip2:
        raise ValueError(
            f"LABS402_NETWORK invalida: '{network_name}'. "
            f"Valores aceptados: {list(NETWORKS.keys())}"
        )

    facilitator_url = os.environ.get(
        "FACILITATOR_URL",
        "https://api.cdp.coinbase.com/platform/v2/x402",
    ).strip()

    try:
        min_amount = float(os.environ.get("LABS402_MIN_AMOUNT_USDC", "0.001"))
    except ValueError:
        raise ValueError("LABS402_MIN_AMOUNT_USDC debe ser un numero decimal (ej: 0.001)")

    try:
        rate_limit = int(os.environ.get("LABS402_RATE_LIMIT_PER_MINUTE", "10"))
    except ValueError:
        raise ValueError("LABS402_RATE_LIMIT_PER_MINUTE debe ser un entero")

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Solo confirma que la configuracion cargó; nunca loguea claves ni seeds
    logger.debug("Configuracion cargada", extra={"network": network_caip2, "facilitator": facilitator_url})

    return Config(
        solana_wallet_address=wallet_address,
        solana_private_key=private_key,
        facilitator_url=facilitator_url,
        network=network_caip2,
        usdc_mint=USDC_MINT_MAINNET,
        min_amount_usdc=min_amount,
        rate_limit_per_minute=rate_limit,
        log_level=log_level,
    )
