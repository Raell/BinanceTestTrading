from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from state import BookKeys, BookSide, State


@pytest.fixture
def symbol():
    return "BTCUSDT"


@pytest.fixture
def state(symbol):
    return State(symbol, "BTC")


def test_book_update(symbol: str, state: State) -> None:
    book = Mock()
    book.symbol = symbol
    book.to_dict = Mock()
    book.to_dict.return_value = {
        BookKeys.BOOK: {
            BookSide.BID: {Decimal(1): Decimal(1)},
            BookSide.ASK: {Decimal(2): Decimal(1)},
        }
    }

    state.handle_book(book)
    print(state.top_market)
    assert state.top_market[BookSide.BID] == (Decimal(1), Decimal(1))
    assert state.top_market[BookSide.ASK] == (Decimal(2), Decimal(1))


def test_balance_initialization(symbol: str, state: State) -> None:
    assert state.balance == 0
    state.initialize_balance(1)
    assert state.balance == 1


def test_balance_initialization(symbol: str, state: State) -> None:
    assert state.balance == 0
    state.initialize_balance(1)
    assert state.balance == 1


def test_handle_positions(symbol: str, state: State) -> None:
    positions = Mock()
    positions.position = 1
    assert state.balance == 0
    state.handle_positions(positions)
    assert state.balance == 1


@patch("state.order_from_order_info")
def test_handle_new_order_info(mock_converter: Mock, symbol: str, state: State) -> None:
    order = Mock()
    order_info = Mock()
    order_info.status = "NEW"
    mock_converter.return_value = order

    state.handle_order_info(order_info)
    assert order in state.open_orders


@patch("state.order_from_order_info")
def test_handle_trade_order_info(
    mock_converter: Mock, symbol: str, state: State
) -> None:
    order = Mock()
    order_info_1 = Mock()
    order_info_1.status = "NEW"
    mock_converter.return_value = order

    state.handle_order_info(order_info_1)
    assert order in state.open_orders

    order_info_2 = Mock()
    order_info_2.status = "TRADE"
    state.handle_order_info(order_info_2)
    assert order not in state.open_orders


@patch("state.order_from_order_info")
def test_handle_cancel_order_info(
    mock_converter: Mock, symbol: str, state: State
) -> None:
    order = Mock()
    order_info_1 = Mock()
    order_info_1.status = "NEW"
    mock_converter.return_value = order

    state.handle_order_info(order_info_1)
    assert order in state.open_orders

    order_info_2 = Mock()
    order_info_2.status = "CANCELED"
    state.handle_order_info(order_info_2)
    assert order not in state.open_orders
