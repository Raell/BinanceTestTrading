from dataclasses import dataclass
from decimal import Decimal

from cryptofeed.defines import GOOD_TIL_CANCELED, LIMIT
from cryptofeed.exchange import RestExchange
from cryptofeed.types import OrderInfo


@dataclass
class Order:
    symbol: str
    side: str
    size: float
    price: Decimal
    order_id: str

    def __init__(
            self,
            symbol: str,
            side: str,
            size: float,
            price: Decimal,
            order_id: str = None):
        self._symbol = symbol
        self._side = side
        self._size = size
        self._price = price
        self._order_id = order_id

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def side(self) -> str:
        return self._side

    @property
    def size(self) -> float:
        return self._size

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def order_id(self) -> str:
        return self._order_id

    def __eq__(self, other):
        if not isinstance(other, Order):
            return NotImplemented

        return self.symbol == other.symbol and \
               self.side == other.side and \
               self.size == other.size and \
               self.price == other.price


def order_from_order_info(order_info: OrderInfo) -> Order:
    return Order(
        symbol=order_info.symbol,
        side=order_info.side,
        size=float(order_info.amount),
        price=Decimal(order_info.raw["o"]["p"]),
        order_id=order_info.id)


async def send_order(
        exchange: RestExchange,
        order: Order) -> None:
    print(f"Sending order for Symbol({order.symbol}), Side({order.side}), "
          f"Size({float(order.size)}), Price({order.price}).")
    await exchange.place_order(
        symbol=order.symbol,
        side=order.side,
        order_type=LIMIT,
        amount=float(order.size),
        price=order.price,
        time_in_force=GOOD_TIL_CANCELED)


async def cancel_order(
        exchange: RestExchange,
        order: Order,
) -> None:
    print(f"Sending cancel for order Id({order.order_id}), Symbol({order.symbol}), Side({order.side}), "
          f"Size({order.size}), Price({order.price}).")
    await exchange.cancel_order(
        symbol=order.symbol,
        order_id=order.order_id)
