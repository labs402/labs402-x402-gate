"""Tipos compartidos del servidor x402 MCP."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Resource:
    """Recurso protegido registrado en el store."""
    resource_id: str
    name: str
    description: str
    content: str
    price_usdc: float
    pay_to: str
    network: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "price_usdc": self.price_usdc,
            "pay_to": self.pay_to,
            "network": self.network,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Resource":
        return cls(**{k: data[k] for k in cls.__dataclass_fields__})


@dataclass
class PaymentChallenge:
    """Respuesta cuando no hay pago — indica al cliente lo que debe pagar."""
    status: str = "payment_required"
    resource_id: str = ""
    payment_requirements: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "resource_id": self.resource_id,
            "payment_requirements": self.payment_requirements,
            "message": self.message,
        }


@dataclass
class PaymentResult:
    """Respuesta exitosa con el contenido del recurso."""
    status: str = "success"
    resource_id: str = ""
    content: str = ""
    transaction: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "resource_id": self.resource_id,
            "content": self.content,
            "transaction": self.transaction,
        }
