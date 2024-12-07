from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .base import StockXBaseModel
from .currency import Currency
from ..format import iso


@dataclass(frozen=True, slots=True)
class BatchStatus(StockXBaseModel):
    batch_id: str
    status: str
    total_items: int
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    item_statuses: BatchItemStatuses | None = None


@dataclass(frozen=True, slots=True)
class BatchItemStatuses(StockXBaseModel):
    queued: int = 0
    completed: int = 0
    failed: int = 0


@dataclass(frozen=True, slots=True)
class BatchResultBase(StockXBaseModel):
    item_id: str
    status: str
    result: BatchItemResult | None = None
    error: str = ""

    @property
    def listing_id(self) -> str | None:
        if self.result.listing_id:
            return self.result.listing_id
        return None


@dataclass(frozen=True, slots=True)
class BatchCreateResult(BatchResultBase):
    listing_input: BatchCreateInput | None = None


@dataclass(frozen=True, slots=True)
class BatchDeleteResult(BatchResultBase):
    listing_input: BatchDeleteInput | None = None


@dataclass(frozen=True, slots=True)
class BatchUpdateResult(BatchResultBase):
    listing_input: BatchUpdateInput | None = None


@dataclass(frozen=True, slots=True)
class BatchCreateInput(StockXBaseModel):
    variant_id: str
    amount: float
    quantity: int | None = None
    active: bool = True
    currency_code: Currency | None = None
    expires_at: datetime | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "variantId": self.variant_id,
            "quantity": int(self.quantity),
            "amount": str(int(self.amount)),
            "expiresAt": iso(self.expires_at),
            "currencyCode": str(self.currency_code),
            "active": self.active,
        }


@dataclass(frozen=True, slots=True)
class BatchUpdateInput(StockXBaseModel):
    listing_id: str
    active: bool | None = None
    currency_code: Currency | None = None
    expires_at: datetime | None = None
    amount: float | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "listingId": self.listing_id,
            "amount": str(int(self.amount)),
            "expiresAt": iso(self.expires_at),
            "currencyCode": str(self.currency_code),
            "active": self.active,
        }


@dataclass(frozen=True, slots=True)
class BatchDeleteInput(StockXBaseModel):
    id: str

    @property
    def listing_id(self) -> str:
        return self.id


@dataclass(frozen=True, slots=True)
class BatchItemResult(StockXBaseModel):
    listing_id: str
    ask_id: str = ""
