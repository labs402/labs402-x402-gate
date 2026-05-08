# Diagrama de flujo — x402-scraper-gate

Flujo completo de una consulta pagada, desde el cliente hasta Solana mainnet.

```
CLIENTE                         SERVIDOR                        BLOCKCHAIN
(cliente_demo.py)               (servidor.py)                   (Solana mainnet)

    |                               |                               |
    |-- GET /wikipedia/Solana... -->|                               |
    |                               |                               |
    |<-- 402 Payment Required ------|                               |
    |    {                          |                               |
    |      scheme: "exact",         |                               |
    |      payTo: <wallet>,         |                               |
    |      price: "$0.001",         |                               |
    |      network: "solana:..."    |                               |
    |    }                          |                               |
    |                               |                               |
    |-- Firma tx USDC SPL --------->|                               |
    |   con KeypairSigner           |-- Verifica pago on-chain ---->|
    |                               |   (via facilitator)           |
    |                               |                               |-- Confirma tx
    |                               |<-- Pago confirmado -----------|
    |                               |    {txHash: "4QGE5..."}       |
    |                               |                               |
    |                               |-- scraper.py ----------------->
    |                               |   GET /api/rest_v1/page/summary/Solana
    |                               |<-- { titulo, resumen, url } --
    |                               |
    |<-- 200 OK --------------------|
    |    {                          |
    |      titulo: "Solana",        |
    |      resumen: "...",          |
    |      url: "..."               |
    |    }                          |
    |                               |
```

## Actores

| Actor | Rol |
|---|---|
| `cliente_demo.py` | Hace la peticion, detecta el 402, firma el pago, reintenta |
| `servidor.py` | Recibe peticiones, exige pago via middleware, llama al scraper |
| `PaymentMiddlewareASGI` | Intercepta peticiones, valida el pago, deja pasar o rechaza |
| Facilitator | Verifica la transaccion on-chain antes de confirmarla al servidor |
| Solana mainnet | Registra la transferencia de USDC de forma permanente |
| `scraper.py` | Llama a la API de Wikipedia y devuelve el resumen |

## Costos por consulta

| Concepto | Costo |
|---|---|
| Precio cobrado al cliente | $0.001 USDC |
| Fee de red Solana | ~$0.000025 (fraccion de centavo) |
| Facilitator Coinbase CDP | $0 (hasta 1,000 tx/mes), luego $0.001/tx |
| Wikipedia API | Gratis |

## Por que Solana

- Fees de red casi cero: cobrar $0.001 es viable porque el fee no se come el margen
- Confirmacion en ~400ms: la espera es imperceptible para el usuario
- USDC SPL: token nativo, sin bridges, sin wrapped tokens
