"""Fixtures compartidos para los tests del MCP server."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from labs402_x402_gate.store import ResourceStore
from labs402_x402_gate.types import Resource
from labs402_x402_gate.x402_client import X402Gate


@pytest.fixture
def recurso_ejemplo() -> Resource:
    return Resource(
        resource_id="recurso_prueba",
        name="Recurso de prueba",
        description="Descripcion para tests",
        content="Contenido premium de prueba",
        price_usdc=0.001,
        pay_to="FakeWalletServer111",
        network="solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
    )


@pytest.fixture
def store_con_recurso(tmp_path, recurso_ejemplo) -> ResourceStore:
    """Store temporal con un recurso pre-cargado."""
    store = ResourceStore(path=tmp_path / "store.json")
    store.add(recurso_ejemplo)
    return store


@pytest.fixture
def store_vacio(tmp_path) -> ResourceStore:
    return ResourceStore(path=tmp_path / "store.json")


@pytest.fixture
def mock_gate() -> X402Gate:
    """Gate con facilitator mockeado para no hacer llamadas reales."""
    mock_server = MagicMock()
    mock_server.verify = AsyncMock(return_value=MagicMock(is_valid=True, payer="FakePayerWallet"))
    mock_server.settle = AsyncMock(return_value=MagicMock(success=True, transaction="txhash_fake_123"))

    gate = X402Gate(
        facilitator_url="https://fake.facilitator",
        wallet_address="FakeWalletServer111",
        network="solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
        min_amount_usdc=0.001,
        _resource_server=mock_server,
    )
    return gate
