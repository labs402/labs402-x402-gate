# x402-scraper-gate — Monetiza un scraper en 5 minutos

Template que muestra como proteger un scraper con pagos x402 sobre Solana.
Cada consulta cuesta 0.001 USDC (~$0.001). El pago se verifica on-chain antes de entregar el resultado.

Parte de [labs402-x402-gate](https://github.com/labs402/labs402-x402-gate).

---

## Que hace este template

Un servidor FastAPI expone el endpoint `GET /wikipedia/{titulo}`.
Cuando un cliente lo invoca:

1. El servidor responde `402 Payment Required` con los datos de pago (wallet, precio, red).
2. El cliente firma una transferencia de 0.001 USDC en Solana y reintenta.
3. El servidor verifica el pago on-chain via el facilitator.
4. Si el pago es valido, el servidor llama a la API de Wikipedia y devuelve el resumen.

Todo el flujo ocurre en menos de 2 segundos. Sin cuentas de usuario. Sin tarjetas.

---

## Requisitos

- Python 3.12+
- Una wallet Solana con USDC y algo de SOL (para los fees de red: fracciones de centavo)
- Cuenta en [Coinbase Developer Platform](https://portal.cdp.coinbase.com/access/api) para mainnet
  (alternativa sin cuenta para pruebas: `https://facilitator.payai.network`)

---

## Instalacion

```bash
# Desde la raiz del repo labs402-x402-gate
pip install -e .

# Entra al directorio del template
cd templates/x402-scraper-gate

# Configura las variables de entorno
cp .env.example .env
# Edita .env con tu wallet y facilitator
```

---

## Paso a paso

### 1. Configura tu .env

Abre `.env` y completa:

```
SOLANA_WALLET_ADDRESS=<tu wallet publica que recibe los pagos>
SOLANA_PRIVATE_KEY=<clave privada de la wallet que paga en la demo>
FACILITATOR_URL=https://api.cdp.coinbase.com/platform/v2/x402
```

**Usa una wallet de desarrollo con saldo minimo ($1-5 USDC).** No uses tu wallet principal.

La clave privada la exportas desde Phantom:
`Configuracion > Seguridad y privacidad > Mostrar clave privada`

### 2. Arranca el servidor (terminal 1)

```bash
python servidor.py
```

Deberia aparecer:
```
Servidor iniciando en http://0.0.0.0:8000
Wallet receptora: <tu wallet>
Precio por consulta: $0.001 USDC
```

### 3. Ejecuta el cliente demo (terminal 2)

```bash
python cliente_demo.py
```

El cliente consulta el articulo `Solana_(blockchain_platform)`, paga 0.001 USDC y muestra el resultado:

```
Wallet del cliente: <tu wallet>
Solicitando http://localhost:8000/wikipedia/Solana_(blockchain_platform) ...

Contenido entregado tras verificar el pago:

Titulo : Solana (blockchain platform)
URL    : https://en.wikipedia.org/wiki/Solana_(blockchain_platform)

Resumen:
Solana is a blockchain platform designed to host decentralized applications...

Transaccion on-chain: 4QGE5bK...
Explorador: https://explorer.solana.com/tx/4QGE5bK...
```

---

## Estructura del template

| Archivo | Descripcion |
|---|---|
| `scraper.py` | Llama a la API REST de Wikipedia y devuelve el resumen |
| `servidor.py` | FastAPI con middleware x402 que protege el endpoint |
| `cliente_demo.py` | Cliente que paga y consulta automaticamente |
| `.env.example` | Variables de entorno necesarias |
| `diagrama.md` | Diagrama ASCII del flujo completo |

---

## Adaptar a tu propio scraper

Para monetizar tu propio scraper:

1. Modifica `scraper.py` con tu logica de extraccion de datos.
2. Cambia el precio en `servidor.py`:
   ```python
   PRECIO_USDC = "$0.01"  # o lo que corresponda a tu caso de uso
   ```
3. Ajusta la ruta del endpoint segun tu API.

---

## Diagrama del flujo

Ver `diagrama.md` para el flujo completo paso a paso con costos.

---

## Nota sobre la API de Wikipedia

Este template usa la API REST oficial de Wikipedia (`/api/rest_v1/page/summary/{titulo}`),
no scraping de HTML. Es gratuita, no requiere autenticacion y devuelve JSON directamente.
Solo exige un `User-Agent` identificando al cliente, que ya esta incluido en `scraper.py`.

---

## Licencia

MIT — ver `LICENSE` en la raiz del repo.
