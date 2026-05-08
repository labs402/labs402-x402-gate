# labs402-x402-gate

> **Alpha** — en desarrollo activo. No usar en produccion con fondos significativos.

MCP server y templates para proteger endpoints con pagos x402 sobre Solana.
Un agente paga, el endpoint responde. Sin cuentas de usuario, sin suscripciones, sin intermediarios.

Parte del proyecto [Labs402](https://github.com/labs402) — el stack hispano para monetizar agentes IA con x402 sobre Solana.

---

## Que es x402

x402 es un protocolo de pagos HTTP para agentes IA. Cuando un cliente hace una peticion a un endpoint protegido:

1. El servidor responde `402 Payment Required` con los detalles del pago (precio, wallet, red)
2. El cliente firma el pago con su wallet y reintenta la peticion con el header `Payment`
3. El servidor verifica el pago on-chain y entrega el contenido

Todo ocurre en milisegundos, sin redireccion, sin sesion, sin tarjeta de credito.
El pago es en USDC sobre Solana mainnet. El fee de red es una fraccion de centavo.

---

## Componentes

| Componente | Descripcion |
|---|---|
| `labs402_x402_gate/` | MCP server con herramienta `charge_and_serve` para Claude Code y otros agentes MCP |
| `examples/hola_x402/` | Ejemplo minimo: servidor FastAPI + cliente httpx con una transaccion real en mainnet |

---

## Requisitos

- Python 3.12+
- Una wallet Solana con USDC y SOL (SOL para fees de red: fracciones de centavo por tx)
- Cuenta en [Coinbase Developer Platform](https://portal.cdp.coinbase.com/access/api) para el facilitator de mainnet (free tier: 1,000 tx/mes)

---

## Instalacion

```bash
git clone https://github.com/labs402/labs402-x402-gate.git
cd labs402-x402-gate

python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux / Mac

pip install -e .
```

---

## Ejemplo rapido: hola_x402

El ejemplo minimo que demuestra una transaccion x402 completa en Solana mainnet.

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu wallet y facilitator (ver seccion Variables de entorno)

# 2. Iniciar el servidor (terminal 1)
python examples/hola_x402/servidor.py

# 3. Ejecutar el cliente (terminal 2)
python examples/hola_x402/cliente.py
```

El cliente paga $0.001 USDC, el servidor verifica el pago on-chain y responde con el contenido.
Ver `examples/hola_x402/README.md` para el flujo completo paso a paso.

---

## MCP Server: charge_and_serve

El MCP server expone la herramienta `charge_and_serve` para agentes que soporten el protocolo MCP
(Claude Code, Cursor, y otros).

### Conectar a Claude Code

```bash
claude mcp add labs402-x402-gate -- python -m labs402_x402_gate
```

### Herramienta disponible

**`charge_and_serve(resource_id, payment_header, payer_wallet)`**

Protege el acceso a un recurso registrado en el store local. El flujo:

1. El agente llama `charge_and_serve` sin `payment_header` — recibe el challenge de pago (precio, wallet, red)
2. El agente firma el pago con la wallet del usuario
3. El agente llama `charge_and_serve` de nuevo con el `payment_header` firmado — recibe el contenido

```python
# Respuesta cuando no hay pago (paso 1)
{
    "status": "payment_required",
    "price_usdc": 0.01,
    "pay_to": "...",
    "network": "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
    "message": "Paga 0.010000 USDC para acceder a este recurso"
}

# Respuesta con pago valido (paso 2)
{
    "status": "ok",
    "resource_id": "...",
    "content": "...",
    "tx": "..."
}
```

### Registrar un recurso

```python
from labs402_x402_gate.store import ResourceStore
from labs402_x402_gate.types import Resource

store = ResourceStore()
store.add(Resource(
    id="mi-recurso",
    content="El contenido que se entrega tras el pago",
    price_usdc=0.01,
    description="Descripcion publica del recurso"
))
```

---

## Variables de entorno

Copiar `.env.example` como `.env` y completar:

| Variable | Descripcion | Requerida |
|---|---|---|
| `SOLANA_WALLET_ADDRESS` | Direccion publica de la wallet que recibe los pagos | Si |
| `SOLANA_PRIVATE_KEY` | Clave privada de la wallet que paga (base58 o array JSON de 64 bytes) | Si |
| `FACILITATOR_URL` | URL del facilitator que verifica los pagos on-chain | Si |
| `PORT` | Puerto del servidor HTTP (default: 8000) | No |
| `SERVIDOR_URL` | URL del servidor al que conecta el cliente de ejemplo | No |

**Facilitators disponibles:**

| Facilitator | URL | Notas |
|---|---|---|
| Coinbase CDP | `https://api.cdp.coinbase.com/platform/v2/x402` | Recomendado para mainnet. 1,000 tx/mes gratis |
| PayAI | `https://facilitator.payai.network` | Publico, sin cuenta, para pruebas |
| x402.org | `https://x402.org/facilitator` | Solo Solana devnet |

**Advertencia:** `SOLANA_PRIVATE_KEY` da control total sobre los fondos de esa wallet.
Usar una wallet dedicada para desarrollo con saldo minimo ($1-5 USDC). Nunca la wallet principal.

---

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Los tests cubren el flujo completo de `charge_and_serve`: challenge sin pago, entrega con pago valido,
rechazo de pago invalido, recurso no encontrado, rate limiting por wallet, y validacion de config.

---

## Roadmap

- [x] Ejemplo `hola_x402` funcionando en Solana mainnet
- [x] MCP server con `charge_and_serve` y rate limiting
- [x] Store local de recursos (`~/.labs402/store.json`)
- [ ] Template `x402-scraper-gate` (proteger resultados de scraping)
- [ ] Template `x402-llm-gate` (proteger llamadas a modelos de lenguaje)
- [ ] Soporte Base mainnet (USDC ERC-20)
- [ ] CLI para registrar y gestionar recursos desde la terminal

---

## Licencia

MIT — ver `LICENSE`.

---

*Labs402 — construye agentes IA que se pagan solos.*
