"""Tests del store de recursos."""

import pytest
from pathlib import Path

from labs402_x402_gate.store import ResourceStore
from labs402_x402_gate.types import Resource


@pytest.fixture
def recurso() -> Resource:
    return Resource(
        resource_id="r1",
        name="Test",
        description="Desc",
        content="Contenido",
        price_usdc=0.001,
        pay_to="WalletXYZ",
        network="solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
    )


def test_get_recurso_inexistente(tmp_path):
    store = ResourceStore(path=tmp_path / "store.json")
    assert store.get("no_existe") is None


def test_agregar_y_recuperar(tmp_path, recurso):
    store = ResourceStore(path=tmp_path / "store.json")
    store.add(recurso)
    recuperado = store.get("r1")
    assert recuperado is not None
    assert recuperado.resource_id == "r1"
    assert recuperado.content == "Contenido"
    assert recuperado.price_usdc == 0.001


def test_persistencia_entre_instancias(tmp_path, recurso):
    """El store debe sobrevivir a una nueva instancia leyendo el mismo archivo."""
    path = tmp_path / "store.json"
    store1 = ResourceStore(path=path)
    store1.add(recurso)

    store2 = ResourceStore(path=path)
    assert store2.get("r1") is not None
    assert store2.get("r1").name == "Test"


def test_remove_existente(tmp_path, recurso):
    store = ResourceStore(path=tmp_path / "store.json")
    store.add(recurso)
    assert store.remove("r1") is True
    assert store.get("r1") is None


def test_remove_inexistente(tmp_path):
    store = ResourceStore(path=tmp_path / "store.json")
    assert store.remove("no_existe") is False


def test_list_all(tmp_path):
    store = ResourceStore(path=tmp_path / "store.json")
    r1 = Resource("id1", "N1", "D1", "C1", 0.001, "W1", "NET")
    r2 = Resource("id2", "N2", "D2", "C2", 0.002, "W2", "NET")
    store.add(r1)
    store.add(r2)
    todos = store.list_all()
    assert len(todos) == 2
    ids = {r.resource_id for r in todos}
    assert ids == {"id1", "id2"}


def test_len(tmp_path, recurso):
    store = ResourceStore(path=tmp_path / "store.json")
    assert len(store) == 0
    store.add(recurso)
    assert len(store) == 1
