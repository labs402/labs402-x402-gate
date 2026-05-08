"""
Servidor FastAPI que cobra 0.001 USDC por consulta al scraper de Wikipedia.

Flujo de pago:
  1. Cliente solicita GET /wikipedia/{titulo} sin pago
  2. PaymentMiddlewareASGI responde 402 con los requisitos (wallet, precio, red)
  3. Cliente firma y reintenta con el header X-Payment
  4. Middleware verifica el pago via facilitator on-chain
  5. El endpoint ejecuta el scraper y devuelve el resultado

La configuracion (wallet, facilitator, network) se carga desde labs402_x402_gate.
"""

import sys

import uvicorn
from fastapi import FastAPI
from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.svm.exact import ExactSvmServerScheme
from x402.server import x402ResourceServer

# load_config carga y valida las variables de entorno desde .env
from labs402_x402_gate.config import load_config

from scraper import obtener_resumen

# --- Configuracion -------------------------------------------------------

try:
    config = load_config()
except ValueError as e:
    print(f"Error de configuracion: {e}", file=sys.stderr)
    print("Copia .env.example como .env y rellena los valores.", file=sys.stderr)
    sys.exit(1)

PRECIO_USDC = "$0.001"

# --- Servidor x402 -------------------------------------------------------

app = FastAPI(
    title="x402-scraper-gate",
    description="Scraper de Wikipedia protegido con pagos x402 sobre Solana.",
)

facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=config.facilitator_url))
server = x402ResourceServer(facilitator)
server.register(config.network, ExactSvmServerScheme())

rutas: dict[str, RouteConfig] = {
    "GET /wikipedia/{titulo}": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                pay_to=config.solana_wallet_address,
                price=PRECIO_USDC,
                network=config.network,
            )
        ],
    ),
}

app.add_middleware(PaymentMiddlewareASGI, routes=rutas, server=server)

# --- Endpoints -----------------------------------------------------------


@app.get("/wikipedia/{titulo}")
async def wikipedia(titulo: str):
    """Devuelve el resumen de Wikipedia para el titulo dado, tras verificar el pago."""
    try:
        return obtener_resumen(titulo)
    except Exception as e:
        return {"error": str(e), "titulo": titulo}


@app.get("/salud")
async def salud():
    """Health check. No requiere pago."""
    return {"estado": "activo", "precio_por_consulta": PRECIO_USDC}


# --- Arranque ------------------------------------------------------------

if __name__ == "__main__":
    print(f"Servidor iniciando en http://0.0.0.0:8000")
    print(f"Wallet receptora: {config.solana_wallet_address}")
    print(f"Facilitator: {config.facilitator_url}")
    print(f"Red: {config.network}")
    print(f"Precio por consulta: {PRECIO_USDC} USDC")
    uvicorn.run(app, host="0.0.0.0", port=8000)
