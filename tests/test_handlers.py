"""Tests de la logica principal: charge_and_serve y RateLimiter."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock

from labs402_x402_gate.handlers import RateLimiter, charge_and_serve


class TestChargeAndServe:

    @pytest.mark.asyncio
    async def test_challenge_sin_payment_header(self, store_con_recurso, mock_gate):
        """Sin payment_header el servidor debe devolver el challenge de pago."""
        resultado = await charge_and_serve(
            resource_id="recurso_prueba",
            payment_header=None,
            payer_wallet=None,
            store=store_con_recurso,
            gate=mock_gate,
            rate_limiter=RateLimiter(),
        )
        assert resultado["status"] == "payment_required"
        assert resultado["resource_id"] == "recurso_prueba"
        assert len(resultado["payment_requirements"]) > 0
        assert "message" in resultado

    @pytest.mark.asyncio
    async def test_contenido_con_pago_valido(self, store_con_recurso, mock_gate):
        """Con pago valido el servidor entrega el contenido del recurso."""
        import base64, json
        # Header de pago simulado (base64 de JSON valido)
        payload = json.dumps({"x402Version": 2, "scheme": "exact", "payload": {}})
        header = base64.b64encode(payload.encode()).decode()

        resultado = await charge_and_serve(
            resource_id="recurso_prueba",
            payment_header=header,
            payer_wallet="PayerWallet123",
            store=store_con_recurso,
            gate=mock_gate,
            rate_limiter=RateLimiter(),
        )
        assert resultado["status"] == "success"
        assert resultado["content"] == "Contenido premium de prueba"
        assert resultado["resource_id"] == "recurso_prueba"

    @pytest.mark.asyncio
    async def test_rechazo_pago_invalido(self, store_con_recurso, mock_gate):
        """Un pago invalido debe lanzar ValueError con mensaje claro."""
        import base64, json

        # Configurar el gate para que rechace el pago
        mock_gate._server.verify = AsyncMock(
            return_value=MagicMock(is_valid=False, payer="")
        )

        payload = json.dumps({"x402Version": 2, "scheme": "exact", "payload": {}})
        header = base64.b64encode(payload.encode()).decode()

        with pytest.raises(ValueError, match="Pago invalido"):
            await charge_and_serve(
                resource_id="recurso_prueba",
                payment_header=header,
                payer_wallet="PayerWallet123",
                store=store_con_recurso,
                gate=mock_gate,
                rate_limiter=RateLimiter(),
            )

    @pytest.mark.asyncio
    async def test_recurso_inexistente(self, store_vacio, mock_gate):
        """Si el resource_id no existe debe lanzar ValueError."""
        with pytest.raises(ValueError, match="no encontrado"):
            await charge_and_serve(
                resource_id="no_existe",
                payment_header=None,
                payer_wallet=None,
                store=store_vacio,
                gate=mock_gate,
                rate_limiter=RateLimiter(),
            )

    @pytest.mark.asyncio
    async def test_config_rechaza_sin_private_key(self):
        """load_config debe fallar si falta SOLANA_PRIVATE_KEY."""
        from unittest.mock import patch
        from labs402_x402_gate.config import load_config

        env_backup = os.environ.copy()
        os.environ.pop("SOLANA_PRIVATE_KEY", None)
        os.environ["SOLANA_WALLET_ADDRESS"] = "TestWallet"
        try:
            # patch load_dotenv para que no recargue el .env real durante el test
            with patch("labs402_x402_gate.config.load_dotenv"):
                with pytest.raises(ValueError, match="SOLANA_PRIVATE_KEY"):
                    load_config()
        finally:
            os.environ.clear()
            os.environ.update(env_backup)


class TestConfig:

    def _set_env(self, overrides: dict) -> None:
        os.environ["SOLANA_PRIVATE_KEY"] = overrides.get("SOLANA_PRIVATE_KEY", "fake_key_base58")
        os.environ["SOLANA_WALLET_ADDRESS"] = overrides.get("SOLANA_WALLET_ADDRESS", "FakeWallet111")
        os.environ["LABS402_NETWORK"] = overrides.get("LABS402_NETWORK", "mainnet-beta")
        os.environ["FACILITATOR_URL"] = overrides.get("FACILITATOR_URL", "https://fake.facilitator")

    def _clean_env(self) -> None:
        for k in ("SOLANA_PRIVATE_KEY", "SOLANA_WALLET_ADDRESS", "LABS402_NETWORK",
                  "FACILITATOR_URL", "LABS402_MIN_AMOUNT_USDC", "LABS402_RATE_LIMIT_PER_MINUTE"):
            os.environ.pop(k, None)

    def test_carga_correcta(self):
        from labs402_x402_gate.config import load_config
        self._clean_env()
        self._set_env({})
        try:
            cfg = load_config()
            assert cfg.solana_wallet_address == "FakeWallet111"
            assert cfg.network == "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"
            assert cfg.min_amount_usdc == 0.001
            assert cfg.rate_limit_per_minute == 10
        finally:
            self._clean_env()

    def test_rechaza_wallet_vacia(self):
        from labs402_x402_gate.config import load_config
        self._clean_env()
        self._set_env({"SOLANA_WALLET_ADDRESS": ""})
        try:
            with pytest.raises(ValueError, match="SOLANA_WALLET_ADDRESS"):
                load_config()
        finally:
            self._clean_env()

    def test_rechaza_red_invalida(self):
        from labs402_x402_gate.config import load_config
        self._clean_env()
        self._set_env({"LABS402_NETWORK": "red_inexistente"})
        try:
            with pytest.raises(ValueError, match="LABS402_NETWORK"):
                load_config()
        finally:
            self._clean_env()

    def test_acepta_devnet(self):
        from labs402_x402_gate.config import load_config
        self._clean_env()
        self._set_env({"LABS402_NETWORK": "devnet"})
        try:
            cfg = load_config()
            assert "devnet" in cfg.network or "EtWTRABZ" in cfg.network
        finally:
            self._clean_env()


class TestRateLimiter:

    def test_permite_dentro_del_limite(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.allow("wallet_a") is True

    def test_bloquea_al_superar_limite(self):
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        for _ in range(10):
            limiter.allow("wallet_b")
        assert limiter.allow("wallet_b") is False

    def test_wallets_independientes(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.allow("wallet_x")
        # wallet_x llego al limite, wallet_y no
        assert limiter.allow("wallet_x") is False
        assert limiter.allow("wallet_y") is True

    def test_reset_limpia_historial(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.allow("wallet_z")
        assert limiter.allow("wallet_z") is False
        limiter.reset("wallet_z")
        assert limiter.allow("wallet_z") is True
