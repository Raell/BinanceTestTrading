from decimal import Decimal
from typing import Dict, List

from order import Order

POSITION_AMOUNT_KEY = "positionAmt"
SYMBOL_KEY = "symbol"
POSITION_KEY = "positions"
SIDE_KEY = "side"
PRICE_KEY = "price"
ORDER_ID_KEY = "orderId"
ORIGINAL_QTY_KEY = "origQty"
EXECUTED_QTY_KEY = "executedQty"


def get_balance_for_asset(account_info: Dict, asset: str) -> float:
    positions = account_info[POSITION_KEY]
    return float(next((item[POSITION_AMOUNT_KEY] for item in positions if item[SYMBOL_KEY] == asset), 0))


def get_open_orders_from_info(open_orders_info: Dict, asset: str, symbol: str) -> List[Order]:
    open_orders = []
    for order_info in open_orders_info:
        if not order_info[SYMBOL_KEY] == asset:
            continue
        size = Decimal(order_info[ORIGINAL_QTY_KEY]) - Decimal(order_info[EXECUTED_QTY_KEY])
        order = Order(
            symbol=symbol,
            side=order_info[SIDE_KEY],
            size=size,
            price=Decimal(order_info[PRICE_KEY]),
            order_id=order_info[ORDER_ID_KEY])
        open_orders.append(order)
    return open_orders
