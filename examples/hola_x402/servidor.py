"""
Servidor de ejemplo: endpoint /premium protegido con x402 sobre Solana mainnet.
Cobra 0.001 USDC por llamada. El facilitator verifica y liquida el pago on-chain.
"""

import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.svm.exact import ExactSvmServerScheme
from x402.server import x402ResourceServer

load_dotenv()

# Wallet que recibe los pagos USDC (clave publica, no secreta)
SOLANA_WALLET_ADDRESS = os.environ["SOLANA_WALLET_ADDRESS"]

# URL del facilitator (verifica y liquida pagos on-chain)
FACILITATOR_URL = os.getenv(
    "FACILITATOR_URL", "https://api.cdp.coinbase.com/platform/v2/x402"
)

PORT = int(os.getenv("PORT", "8000"))

# Identificador CAIP-2 de Solana mainnet-beta (genesis hash como discriminador de red)
SOLANA_MAINNET = "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"

app = FastAPI(title="labs402-x402-gate hola_x402")

# El facilitator recibe el pago firmado del cliente, lo verifica contra la red
# y confirma la liquidacion antes de que el servidor libere el contenido
facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=FACILITATOR_URL))

server = x402ResourceServer(facilitator)
# Registra el esquema "exact" para Solana mainnet
# ExactSvmServerScheme valida que el pago sea una transferencia SPL exacta al wallet correcto
server.register(SOLANA_MAINNET, ExactSvmServerScheme())

# Cada entrada del diccionario define que rutas requieren pago y en que condiciones
rutas: dict[str, RouteConfig] = {
    "GET /premium": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                pay_to=SOLANA_WALLET_ADDRESS,
                price="$0.001",
                network=SOLANA_MAINNET,
            )
        ],
    ),
}

# El middleware intercepta las peticiones entrantes:
# - Sin pago -> devuelve 402 con los requisitos de pago
# - Con pago valido -> deja pasar la peticion al endpoint
app.add_middleware(PaymentMiddlewareASGI, routes=rutas, server=server)


@app.get("/premium")
async def endpoint_premium():
    return {
        "mensaje": "Pago verificado. Contenido premium entregado.",
        "red": SOLANA_MAINNET,
        "monto_cobrado": "$0.001 USDC",
    }


@app.get("/salud")
async def health_check():
    return {"estado": "activo"}


if __name__ == "__main__":
    print(f"Servidor iniciando en http://0.0.0.0:{PORT}")
    print(f"Wallet receptora: {SOLANA_WALLET_ADDRESS}")
    print(f"Facilitator: {FACILITATOR_URL}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
