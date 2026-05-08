"""
Cliente demo: paga automaticamente el scraper de Wikipedia con x402 sobre Solana mainnet.

Consulta de ejemplo: articulo "Solana_(blockchain_platform)" por 0.001 USDC.

El cliente detecta el 402, firma el pago con la wallet configurada en .env,
y reintenta la peticion. Todo el flujo es automatico.
"""

import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from x402 import x402Client
from x402.http.clients import x402HttpxClient
from x402.mechanisms.svm import KeypairSigner
from x402.mechanisms.svm.exact.register import register_exact_svm_client

load_dotenv()

SOLANA_PRIVATE_KEY = os.environ.get("SOLANA_PRIVATE_KEY", "")
SERVIDOR_URL = os.getenv("SERVIDOR_URL", "http://localhost:8000")

# Articulo de Wikipedia a consultar en la demo
ARTICULO_DEMO = "Solana_(blockchain_platform)"


def cargar_signer(clave_privada: str) -> KeypairSigner:
    """
    Acepta la clave privada en dos formatos:
    - Base58: exportada desde Phantom (Configuracion > Seguridad > Mostrar clave privada)
    - Array JSON de 64 bytes: generada con solana-keygen
    """
    clave = clave_privada.strip()
    if not clave:
        print("Error: SOLANA_PRIVATE_KEY no esta configurada en .env", file=sys.stderr)
        sys.exit(1)
    if clave.startswith("["):
        return KeypairSigner.from_bytes(bytes(json.loads(clave)))
    return KeypairSigner.from_base58(clave)


async def main() -> None:
    signer = cargar_signer(SOLANA_PRIVATE_KEY)
    print(f"Wallet del cliente: {signer.address}")
    print(f"Servidor: {SERVIDOR_URL}")
    print(f"Articulo: {ARTICULO_DEMO}")
    print(f"Precio: 0.001 USDC\n")

    cliente_x402 = x402Client()
    register_exact_svm_client(cliente_x402, signer)

    async with x402HttpxClient(cliente_x402) as http:
        url = f"{SERVIDOR_URL}/wikipedia/{ARTICULO_DEMO}"
        print(f"Solicitando {url} ...")
        print("Si el servidor responde 402, el cliente paga y reintenta automaticamente.\n")

        respuesta = await http.get(url)
        await respuesta.aread()

        if respuesta.status_code == 200:
            datos = respuesta.json()

            if "error" in datos:
                print(f"Error del scraper: {datos['error']}")
                sys.exit(1)

            print("Contenido entregado tras verificar el pago:\n")
            print(f"Titulo : {datos['titulo']}")
            print(f"URL    : {datos['url']}")
            print(f"\nResumen:\n{datos['resumen']}")

            # Intenta mostrar el hash de la transaccion si el facilitator lo devuelve
            for nombre in ("x-payment-response", "x-transaction-id", "x-receipt"):
                recibo_raw = respuesta.headers.get(nombre, "")
                if recibo_raw:
                    try:
                        import base64
                        recibo = json.loads(base64.b64decode(recibo_raw))
                        tx = (
                            recibo.get("txHash")
                            or recibo.get("transaction")
                            or recibo.get("signature", "")
                        )
                        if tx:
                            print(f"\nTransaccion on-chain: {tx}")
                            print(f"Explorador: https://explorer.solana.com/tx/{tx}")
                    except Exception:
                        pass
                    break

            print("\nVerificar pagos recibidos en:")
            print(f"https://explorer.solana.com/address/{os.getenv('SOLANA_WALLET_ADDRESS', '<SOLANA_WALLET_ADDRESS>')}/tokens")

        else:
            print(f"Error inesperado: HTTP {respuesta.status_code}")
            print(respuesta.text)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
