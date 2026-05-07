# labs402-x402-gate

> **Alpha** — en desarrollo activo. No usar en produccion con fondos significativos.

Templates para proteger endpoints con pagos x402 sobre Solana.
Un agente paga, el endpoint responde. Sin cuentas de usuario, sin suscripciones.

Parte del proyecto [Labs402](https://github.com/labs402) — el stack hispano para monetizar agentes IA con x402 sobre Solana.

---

## Contenido

| Carpeta | Descripcion |
|---|---|
| `examples/hola_x402/` | Ejemplo minimo: servidor FastAPI + cliente httpx en Solana mainnet |

---

## Requisitos

- Python 3.12+
- Una wallet Solana con USDC y SOL (para fees de la red, fracciones de centavo)
- Cuenta en [Coinbase Developer Platform](https://portal.cdp.coinbase.com) para el facilitator de mainnet

---

## Inicio rapido

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux / Mac

pip install -e .

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu wallet y facilitator

# 3. Correr el servidor (en una terminal)
python examples/hola_x402/servidor.py

# 4. Correr el cliente (en otra terminal)
python examples/hola_x402/cliente.py
```

Ver instrucciones detalladas en `examples/hola_x402/README.md`.

---

## Licencia

MIT — ver `LICENSE`.
