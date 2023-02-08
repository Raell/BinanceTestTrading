import threading
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Tuple

from cryptofeed.types import OrderBook, OrderInfo, Position

from order import Order, order_from_order_info


class BookSide:
    BID = "bid"
    ASK = "ask"


class BookKeys:
    BOOK = "book"


@dataclass
class State:
    symbol: str
    asset: str
    balance: float
    open_orders: List[Order]
    top_market: Dict[str, Tuple[Decimal, Decimal]]

    def __init__(self, symbol, asset):
        self._symbol = symbol
        self._asset = asset
        self._balance = 0
        self._open_orders = []
        self._top_market = {}
        self.__lock = threading.Lock()

    @property
    def symbol(self) -> str:
        self.__lock.acquire()
        try:
            return self._symbol
        finally:
            self.__lock.release()

    @property
    def asset(self) -> str:
        self.__lock.acquire()
        try:
            return self._asset
        finally:
            self.__lock.release()

    @property
    def balance(self) -> float:
        self.__lock.acquire()
        try:
            return self._balance
        finally:
            self.__lock.release()

    @property
    def open_orders(self) -> List[Order]:
        self.__lock.acquire()
        try:
            return self._open_orders
        finally:
            self.__lock.release()

    @property
    def top_market(self) -> Dict[str, Tuple[Decimal, Decimal]]:
        self.__lock.acquire()
        try:
            return self._top_market
        finally:
            self.__lock.release()

    def handle_book(self, book: OrderBook) -> None:
        self.__lock.acquire()
        try:
            if book.symbol == self._symbol:
                book_dict = book.to_dict()
                self.__update_top_book(book_dict)
        finally:
            self.__lock.release()

    def __update_top_book(self, book_dict: Dict[str, Dict]):
        if BookKeys.BOOK not in book_dict:
            self._top_market = {}
            return

        if BookSide.BID in book_dict[BookKeys.BOOK]:
            bids = book_dict[BookKeys.BOOK][BookSide.BID]
            if bids:
                self._top_market[BookSide.BID] = list(bids.items())[0]

        if BookSide.ASK in book_dict[BookKeys.BOOK]:
            asks = book_dict[BookKeys.BOOK][BookSide.ASK]
            if asks:
                self._top_market[BookSide.ASK] = list(asks.items())[0]

    def initialize_balance(self, balance: float) -> None:
        self._balance = balance

    def handle_positions(self, positions: Position) -> None:
        self.__lock.acquire()
        try:
            self._balance = float(positions.position)
        finally:
            self.__lock.release()

    def handle_order_info(self, order_info: OrderInfo) -> None:
        self.__lock.acquire()
        try:
            order = order_from_order_info(order_info)
            if order_info.status == "NEW":
                self._open_orders.append(order)
            if order_info.status == "TRADE" or order_info.status == "CANCELED":
                try:
                    self._open_orders.remove(order)
                except ValueError:
                    pass
        finally:
            self.__lock.release()
