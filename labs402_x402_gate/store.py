"""Registro local de recursos protegidos. v0.1: JSON en ~/.labs402/store.json."""

import json
import logging
from pathlib import Path
from typing import Optional

from .types import Resource

logger = logging.getLogger(__name__)

DEFAULT_STORE_PATH = Path.home() / ".labs402" / "store.json"


class ResourceStore:
    """
    Registro persistente de recursos protegidos con x402.
    Cada entrada asocia un resource_id con su contenido y precio.
    """

    def __init__(self, path: Path = DEFAULT_STORE_PATH) -> None:
        self._path = path
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
                logger.debug("Store cargado", extra={"path": str(self._path), "recursos": len(self._data)})
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("No se pudo leer el store, iniciando vacio: %s", exc)
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get(self, resource_id: str) -> Optional[Resource]:
        """Devuelve el recurso o None si no existe."""
        raw = self._data.get(resource_id)
        if raw is None:
            return None
        return Resource.from_dict(raw)

    def add(self, resource: Resource) -> None:
        """Agrega o reemplaza un recurso en el store."""
        self._data[resource.resource_id] = resource.to_dict()
        self._save()
        logger.debug("Recurso registrado", extra={"resource_id": resource.resource_id})

    def remove(self, resource_id: str) -> bool:
        """Elimina un recurso. Devuelve True si existia."""
        if resource_id not in self._data:
            return False
        del self._data[resource_id]
        self._save()
        return True

    def list_all(self) -> list[Resource]:
        """Devuelve todos los recursos registrados."""
        return [Resource.from_dict(v) for v in self._data.values()]

    def __len__(self) -> int:
        return len(self._data)
