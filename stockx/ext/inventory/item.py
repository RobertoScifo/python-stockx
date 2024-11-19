from __future__ import annotations

from collections.abc import AsyncIterable, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .inventory import Inventory

from ...models import Listing


class Item:

    __slots__ = 'product_id', 'variant_id', 'price', 'quantity'

    def __init__(
            self,
            product_id: str,
            variant_id: str,
            price: float,
            quantity: int = 1,
    ) -> None:
        self.product_id = product_id
        self.variant_id = variant_id
        self.price = price
        self.quantity = quantity

    @property
    def price(self) -> float:
        return self.__price
    
    @price.setter
    def price(self, value: float) -> None:
        if value < 0:
            raise ValueError('Price must be greater than 0.')
        self.__price = value

    @property
    def quantity(self) -> int:
        return self.__quantity
    
    @quantity.setter
    def quantity(self, value: int) -> None:
        if value < 0:
            raise ValueError('Quantity must be greater than 0.') 
        if int(value) != value:
            raise ValueError('Quantity must be an integer.')   
        self.__quantity = value

    
class ListedItem:
    
    __slots__ = '_size', '_style_id', '_inventory', '_item',  'listing_ids'

    def __init__(
            self,
            item: Item,
            inventory: Inventory,
            listing_ids: Iterable[str],
    ) -> None:
        self._item = item
        self._inventory = inventory
        self.listing_ids = list(listing_ids)
        self.quantity = len(listing_ids)

        self._style_id = None
        self._size = None

    @classmethod
    async def from_inventory_listings(
            cls, 
            inventory: Inventory,
            listings: AsyncIterable[Listing]
    ) -> list[ListedItem]:
        items: dict[str, dict[float, ListedItem]] = {}

        async for listing in listings:
            amounts_dict = items.setdefault(listing.variant.id, {})
            
            if listing.amount in amounts_dict:
                amounts_dict[listing.amount].quantity += 1
                amounts_dict[listing.amount].listing_ids.append(listing.id)
            else:
                item = ListedItem(
                    item=Item(
                        product_id=listing.product.id, 
                        variant_id=listing.variant.id, 
                        price=listing.amount, 
                    ),
                    inventory=inventory,
                    listing_ids=[listing.id]
                )
                item._style_id = listing.style_id
                item._size = listing.variant_value

                amounts_dict[listing.amount] = item

        return [item for amount in items.values() for item in amount.values()]
    
    @property
    def product_id(self) -> str:
        return self._item.product_id

    @property
    def variant_id(self) -> str:
        return self._item.variant_id
    
    @property
    def price(self) -> float:
        return self._item.price
    
    @price.setter
    def price(self, value: float) -> None:
        if value != self.price:
            self._item.price = value
            self._inventory.register_price_change(self)
    
    @property
    def quantity(self) -> int:
        return self._item.quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if value != self.quantity:
            self._item.quantity = value
            self._inventory.register_quantity_change(self)

    @property
    def style_id(self) -> str | None:
        return self._style_id
    
    @property
    def size(self) -> str | None:
        return self._size
    
    def quantity_to_sync(self) -> int:
        return self.quantity - len(self.listing_ids)
    
    def payout(self) -> float: # TODO: compute payout based on active orders
        transaction_fee = max(
            self._inventory.transaction_fee * self.price, 
            self._inventory.minimum_transaction_fee
        )
        payment_fee = self._inventory.payment_fee * self.price
        shipping_fee = self._inventory.shipping_fee
        return self.price - transaction_fee - payment_fee - shipping_fee
    
    