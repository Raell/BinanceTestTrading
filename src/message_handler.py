import threading

from cryptofeed.types import OrderBook, OrderInfo, Position

from simple_strategy import SimpleStrategy
from state import State


class MessageHandler:
    def __init__(self, state: State):
        self._state = state
        self._strategy = None
        self.__lock = threading.Lock()

    async def order_book_handler(self, book: OrderBook, receipt_timestamp) -> None:
        self.__lock.acquire()
        try:
            self._state.handle_book(book)
            if self._strategy is not None:
                self._strategy.process_strategy()
        finally:
            self.__lock.release()

    async def positions_handler(self, positions: Position, receipt_timestamp) -> None:
        self.__lock.acquire()
        try:
            self._state.handle_positions(positions)
        finally:
            self.__lock.release()

    async def order_info_handler(
        self, order_info: OrderInfo, receipt_timestamp
    ) -> None:
        self.__lock.acquire()
        try:
            self._state.handle_order_info(order_info)
            if self._strategy is not None:
                self._strategy.handle_order_info(order_info)
        finally:
            self.__lock.release()

    def set_strategy(self, strategy: SimpleStrategy) -> None:
        if self._strategy is None:
            self._strategy = strategy
