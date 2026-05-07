# hola_x402 — ejemplo minimo en Solana mainnet

Un servidor FastAPI con un endpoint protegido por x402 y un cliente Python que
detecta el 402, firma el pago en Solana, y obtiene la respuesta. Costo del test:
0.001 USDC (una milesima de dolar).

---

## Que necesitas antes de empezar

1. **Python 3.12+** instalado
2. **Una wallet Solana** con:
   - Al menos 0.01 USDC (para el test + margen)
   - Al menos 0.001 SOL (para fees de la red, son fracciones de centavo)
3. **Cuenta en Coinbase Developer Platform** para el facilitator de mainnet:
   - Crear en: https://portal.cdp.coinbase.com/access/api
   - Free tier: 1,000 transacciones/mes sin costo

> Para una prueba inicial sin crear cuenta CDP, puedes usar el facilitator publico
> de PayAI: `FACILITATOR_URL=https://facilitator.payai.network`

---

## Paso 1: instalar dependencias

Desde la raiz del repositorio (`labs402-x402-gate/`):

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
# source .venv/bin/activate

pip install -e .
```

---

## Paso 2: configurar variables de entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` con estos valores:

| Variable | Donde obtenerla |
|---|---|
| `SOLANA_WALLET_ADDRESS` | La direccion publica de tu wallet (la que recibe los pagos) |
| `SOLANA_PRIVATE_KEY` | Phantom: Configuracion > Seguridad y privacidad > Mostrar clave privada |
| `FACILITATOR_URL` | Dejar el default de CDP, o usar `https://facilitator.payai.network` para prueba sin cuenta |

**Usa una wallet de desarrollo** con saldo minimo. Nunca la wallet principal.

---

## Paso 3: correr el servidor

En una terminal:

```bash
python examples/hola_x402/servidor.py
```

Deberias ver:

```
Servidor iniciando en http://0.0.0.0:8000
Wallet receptora: <tu_wallet>
Facilitator: https://api.cdp.coinbase.com/platform/v2/x402
```

Verifica que el servidor responde con un 402 (sin pago):

```bash
curl http://localhost:8000/premium
```

Respuesta esperada: HTTP 402 con los requisitos de pago en el header `PAYMENT-REQUIRED`.

---

## Paso 4: correr el cliente

En otra terminal (con el mismo `.venv` activado):

```bash
python examples/hola_x402/cliente.py
```

El cliente:
1. Solicita `/premium` -> recibe 402
2. Firma la transaccion SPL con tu wallet
3. Reintenta con el header `X-Payment`
4. Recibe 200 con el contenido premium

Salida esperada:

```
Wallet del cliente: <tu_pubkey>

Solicitando http://localhost:8000/premium ...
(Si el servidor responde 402, el cliente paga y reintenta automaticamente)

Contenido premium recibido:
{
  "mensaje": "Pago verificado. Contenido premium entregado.",
  "red": "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
  "monto_cobrado": "$0.001 USDC"
}

Transaccion confirmada: <tx_hash>
Explorador: https://explorer.solana.com/tx/<tx_hash>
```

---

## Paso 5: verificar en el explorador

Abre el link del explorador que imprime el cliente. Deberias ver:

- Una transferencia SPL de 0.001 USDC desde tu wallet al servidor
- Estado: confirmada (Finalized)
- Fee pagada por el facilitator (no por tu wallet de cliente)

Si el link no aparece en el output, busca tu wallet en:
https://explorer.solana.com/address/<SOLANA_WALLET_ADDRESS>/tokens

---

## Soluciones a problemas comunes

**Error: `SOLANA_WALLET_ADDRESS` no definida**
Asegurate de haber copiado `.env.example` a `.env` y rellenado los valores.

**Error de autenticacion con CDP**
CDP puede requerir autenticacion adicional. Para el primer test usa:
`FACILITATOR_URL=https://facilitator.payai.network` en tu `.env`.

**Error: fondos insuficientes**
Verifica que tu wallet tiene USDC en Solana mainnet (no en otra red).
El USDC de Ethereum o Base no sirve — debe ser USDC SPL en Solana.

**El cliente imprime 402 en lugar de 200**
El facilitator rechazo el pago. Revisa que `FACILITATOR_URL` sea correcto
y que el servidor este corriendo con `SOLANA_MAINNET` como red.

---

## Constantes de referencia

| Dato | Valor |
|---|---|
| USDC mint Solana mainnet | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |
| Red Solana mainnet (CAIP-2) | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` |
| Red Solana devnet (CAIP-2) | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` |
| Facilitator mainnet (CDP) | `https://api.cdp.coinbase.com/platform/v2/x402` |
| Facilitator mainnet (PayAI) | `https://facilitator.payai.network` |
| Facilitator testnet | `https://x402.org/facilitator` |
