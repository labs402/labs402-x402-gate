"""
Cliente de ejemplo: paga automaticamente el endpoint /premium usando x402 sobre Solana mainnet.

Flujo:
  1. Solicita /premium sin pago -> recibe 402 con requisitos de pago
  2. Firma la transaccion SPL con la wallet del cliente
  3. Reintenta con el header X-Payment -> recibe 200 con el contenido
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

# Clave privada de la wallet que realiza el pago (nunca hardcodear)
SOLANA_PRIVATE_KEY = os.environ["SOLANA_PRIVATE_KEY"]

# URL del servidor a pagar
SERVIDOR_URL = os.getenv("SERVIDOR_URL", "http://localhost:8000")


def cargar_signer(clave_privada: str) -> KeypairSigner:
    """
    Acepta la clave privada en dos formatos:
    - Base58: lo que muestra Phantom en Configuracion > Mostrar clave privada
    - Array JSON de 64 bytes: formato de solana-keygen (archivo .json)
    """
    clave = clave_privada.strip()
    if clave.startswith("["):
        # Formato: [1, 2, 3, ..., 64]
        return KeypairSigner.from_bytes(bytes(json.loads(clave)))
    # Formato base58
    return KeypairSigner.from_base58(clave)


async def main() -> None:
    signer = cargar_signer(SOLANA_PRIVATE_KEY)
    print(f"Wallet del cliente: {signer.address}")

    # x402Client orquesta el flujo 402: detecta el rechazo, crea el pago, reintenta
    cliente_x402 = x402Client()
    # register_exact_svm_client vincula el signer al esquema exact-SVM para cualquier red Solana
    register_exact_svm_client(cliente_x402, signer)

    async with x402HttpxClient(cliente_x402) as http:
        print(f"\nSolicitando {SERVIDOR_URL}/premium ...")
        print("(Si el servidor responde 402, el cliente paga y reintenta automaticamente)")

        respuesta = await http.get(f"{SERVIDOR_URL}/premium")
        # aread() asegura que el cuerpo de la respuesta este completamente cargado
        await respuesta.aread()

        if respuesta.status_code == 200:
            datos = respuesta.json()
            print("\nContenido premium recibido:")
            print(json.dumps(datos, indent=2, ensure_ascii=False))

            # Intenta extraer el hash de la transaccion del header de respuesta
            # El nombre exacto del header depende de la version del SDK y el facilitator
            for nombre_header in ("x-payment-response", "x-transaction-id", "x-receipt"):
                recibo_raw = respuesta.headers.get(nombre_header, "")
                if recibo_raw:
                    try:
                        import base64
                        recibo = json.loads(base64.b64decode(recibo_raw))
                        tx_hash = (
                            recibo.get("txHash")
                            or recibo.get("transaction")
                            or recibo.get("signature", "")
                        )
                        if tx_hash:
                            print(f"\nTransaccion confirmada: {tx_hash}")
                            print(f"Explorador: https://explorer.solana.com/tx/{tx_hash}")
                    except Exception:
                        pass
                    break

            print("\nVerificar pagos recibidos en:")
            print(f"https://explorer.solana.com/address/{os.getenv('SOLANA_WALLET_ADDRESS', '<SOLANA_WALLET_ADDRESS>')}/tokens")

        else:
            print(f"\nError inesperado: HTTP {respuesta.status_code}")
            print(respuesta.text)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
