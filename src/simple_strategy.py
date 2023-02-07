import asyncio
import functools
import threading
from asyncio import Future
from decimal import Decimal
from typing import List, Tuple

from aiohttp import ClientResponseError
from cryptofeed.defines import BUY, SELL
from cryptofeed.exchange import RestExchange
from cryptofeed.types import OrderInfo

from order import order_from_order_info, Order, cancel_order, send_order
from state import State, BookSide

SIZE = 0.01
PRICE_OFFSET = 10
EXPECTED_ORDERS_PER_SIDE = 2

class SimpleStrategy:
    def __init__(self, exchange: RestExchange, state: State, balance_limit: float):
        self._exchange = exchange
        self._state = state
        self._balance_limit = balance_limit
        self.__lock = threading.Lock()
        self.__pending_orders = []
        self.__pending_cancels = []
        self.__bid_enabled = True
        self.__ask_enabled = True

    def process_strategy(self) -> None:
        self.__update_orders()

    def remove_pending_order(self, order_info: OrderInfo) -> None:
        self.__lock.acquire()
        try:
            # Handle new order
            if order_info.status == "NEW":
                order = order_from_order_info(order_info)
                print(f"New OrderId({order.order_id}), Symbol({order.symbol}), Side({order.side}), "
                      f"Size({order.size}), Price({order.price})")
                try:
                    self.__pending_orders.remove(order)
                except ValueError:
                    pass

            # Handle cancelled order
            if order_info.status == "CANCELED":
                order = order_from_order_info(order_info)
                print(f"Cancelled OrderId({order.order_id}), Symbol({order.symbol}), Side({order.side}), "
                      f"Size({order.size}), Price({order.price})")
                try:
                    self.__pending_cancels.remove(order)
                except ValueError:
                    pass

            # Handle trade
            if order_info.status == "TRADE":
                order = order_from_order_info(order_info)
                print(f"Traded OrderId({order.order_id}), Symbol({order.symbol}), Side({order.side}), "
                      f"Size({order.size}), Price({order.price})")
                self.__pull_orders(self._state.open_orders)
        finally:
            self.__lock.release()

    def __update_orders(self) -> None:
        self.__lock.acquire()
        try:
            top_market = self._state.top_market
            best_bid = top_market[BookSide.BID]
            best_ask = top_market[BookSide.ASK]
            open_orders = self._state.open_orders
            bid_orders = [order for order in open_orders if order.side == BUY]
            ask_orders = [order for order in open_orders if order.side == SELL]

            if self.__should_orders_be_pulled(BUY, bid_orders, best_bid):
                print("Pulling bid orders.")
                self.__pull_orders(bid_orders)

            if self.__should_orders_be_pulled(SELL, ask_orders, best_ask):
                print("Pulling ask orders.")
                self.__pull_orders(ask_orders)

            # Do nothing if pending orders exists
            if len(self.__pending_orders) > 0:
                print("Has pending orders, doing nothing.")
                return

            if not bid_orders and self.__bid_enabled and self.__is_inventory_within_limit(BUY):
                print("Inserting new bid orders.")
                orders = self.__create_orders(BUY, best_bid[0])
                self.__insert_orders(orders)

            if not ask_orders and self.__ask_enabled and self.__is_inventory_within_limit(SELL):
                print("Inserting new ask orders.")
                orders = self.__create_orders(SELL, best_ask[0])
                self.__insert_orders(orders)

            self.__pull_if_order_count_inconsistent()
        finally:
            self.__lock.release()

    def __pull_if_order_count_inconsistent(self) -> None:
        # Pulls all orders if pending and live orders count is not consistent
        expected_count = 0
        if self.__bid_enabled:
            expected_count += 2
        if self.__ask_enabled:
            expected_count += 2

        if len(self.__pending_orders) + len(self._state.open_orders) != expected_count:
            self.__pull_orders(self._state.open_orders)

    def __insert_orders(self, orders: List[Order]) -> None:
        for order in orders:
            self.__pending_orders.append(order)
            task = asyncio.ensure_future(send_order(exchange=self._exchange, order=order))
            task.add_done_callback(functools.partial(self.__order_insert_callback, order))

    def __create_orders(self, side: str, best_price: Decimal) -> List[Order]:
        next_level_offset = PRICE_OFFSET if side == SELL else -PRICE_OFFSET

        top_market_order = Order(
            symbol=self._state.symbol,
            side=side,
            size=SIZE,
            price=best_price)

        next_level_order = Order(
            symbol=self._state.symbol,
            side=side,
            size=SIZE,
            price=best_price + next_level_offset)

        return [top_market_order, next_level_order]

    def __pull_orders(self, orders: List[Order]) -> None:
        for order in orders:
            if order not in self.__pending_cancels:
                self.__pending_cancels.append(order)
                task = asyncio.ensure_future(cancel_order(self._exchange, order))
                task.add_done_callback(functools.partial(self.__order_cancel_callback, order))

    def __should_orders_be_pulled(
            self,
            side: str,
            open_orders: List[Order],
            top_level: Tuple[Decimal, Decimal]) -> bool:
        if not open_orders:
            return False
        if not self.__is_inventory_within_limit(side):
            return True

        return not self.__order_exists_at_top_level_and_not_alone(open_orders, top_level)

    def __is_inventory_within_limit(self, side: str) -> bool:
        # Inventory management, pull orders on side if exceeded
        curr_balance = self._state.balance
        if side == BUY:
            self.__bid_enabled = curr_balance <= self._balance_limit
            return self.__bid_enabled
        else:
            self.__ask_enabled = curr_balance >= -self._balance_limit
            return self.__ask_enabled

    @staticmethod
    def __order_exists_at_top_level_and_not_alone(open_orders: List[Order], top_level: Tuple[Decimal, Decimal]) -> bool:
        # Checks if top level is empty
        if not top_level:
            return False

        order_at_top_level = False
        for order in open_orders:
            if top_level[0] == order.price:
                order_at_top_level = True
                if top_level[1] == order.size:
                    # Order alone at top level
                    return False

        return order_at_top_level

    def __order_insert_callback(self, order: Order, future: Future) -> None:
        # Gracefully handle failed order inserts
        try:
            future.result()
        except ClientResponseError:
            self.__pending_orders.remove(order)

    def __order_cancel_callback(self, order: Order, future: Future) -> None:
        # Gracefully handle failed order cancels
        try:
            future.result()
        except ClientResponseError:
            self.__pending_cancels.remove(order)
