"""Tests del wrapper X402Gate con facilitator mockeado."""

import base64
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from labs402_x402_gate.x402_client import X402Gate


@pytest.fixture
def gate(mock_gate) -> X402Gate:
    return mock_gate


class TestBuildPaymentRequirements:

    def test_estructura_basica(self, gate):
        reqs = gate.build_payment_requirements(0.001)
        assert isinstance(reqs, list)
        assert len(reqs) == 1
        req = reqs[0]
        assert req["scheme"] == "exact"
        assert "payTo" in req or "pay_to" in req

    def test_minimo_aplicado(self, gate):
        """Si el precio pedido es menor al minimo, se usa el minimo."""
        reqs = gate.build_payment_requirements(0.0001)
        req = reqs[0]
        # El precio debe ser al menos 0.001 USDC
        price_str = req.get("price", "")
        price_value = float(price_str.replace("$", ""))
        assert price_value >= 0.001

    def test_precio_exacto(self, gate):
        reqs = gate.build_payment_requirements(0.005)
        req = reqs[0]
        price_str = req.get("price", "")
        price_value = float(price_str.replace("$", ""))
        assert abs(price_value - 0.005) < 1e-9


class TestVerifyAndSettle:

    @pytest.mark.asyncio
    async def test_pago_valido(self, gate):
        payload = json.dumps({"x402Version": 2, "scheme": "exact", "payload": {}})
        header = base64.b64encode(payload.encode()).decode()

        ok, tx = await gate.verify_and_settle(header, price_usdc=0.001)
        assert ok is True
        assert tx == "txhash_fake_123"

    @pytest.mark.asyncio
    async def test_pago_rechazado_por_facilitator(self, gate):
        gate._server.verify = AsyncMock(
            return_value=MagicMock(is_valid=False, payer="")
        )
        payload = json.dumps({"x402Version": 2, "scheme": "exact", "payload": {}})
        header = base64.b64encode(payload.encode()).decode()

        ok, mensaje = await gate.verify_and_settle(header, price_usdc=0.001)
        assert ok is False

    @pytest.mark.asyncio
    async def test_header_invalido(self, gate):
        """Un header que no es base64 JSON valido debe devolver False sin explotar."""
        ok, msg = await gate.verify_and_settle("no_es_base64_valido!!!!", price_usdc=0.001)
        assert ok is False
        assert len(msg) > 0
