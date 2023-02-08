from decimal import Decimal

import pytest
from unittest.mock import Mock, patch, AsyncMock, ANY

from cryptofeed.defines import BUY, SELL
from simple_strategy import SimpleStrategy
from state import State, BookSide


@pytest.fixture
def state():
    return Mock()


@pytest.fixture
def simple_strategy(state):
    return SimpleStrategy(exchange=Mock(), state=state, balance_limit=1)


@patch('simple_strategy.cancel_all_orders')
def test_no_top_market_cancels_all_orders(
        mock_cancel_all: AsyncMock,
        simple_strategy: SimpleStrategy,
        state: State) -> None:
    state.balance = 0
    state.top_market = {}

    state.open_orders = []
    simple_strategy.process_strategy()
    mock_cancel_all.assert_called()


@patch('simple_strategy.cancel_order')
@patch('simple_strategy.send_order')
def test_best_bid_only_has_our_open_order(
        mock_insert: Mock,
        mock_cancel: Mock,
        simple_strategy: SimpleStrategy,
        state: State) -> None:
    state.balance = 10
    state.top_market = {
        BookSide.BID: (Decimal(1), Decimal(1)),
        BookSide.ASK: (Decimal(2), Decimal(1)),
    }

    order_1 = Mock()
    order_1.side = BUY
    order_1.price = 1
    order_1.size = 1

    state.open_orders = [order_1]
    simple_strategy.process_strategy()
    mock_cancel.assert_called_once_with(exchange=ANY, order=order_1, callback=ANY)


@patch('simple_strategy.cancel_order')
@patch('simple_strategy.send_order')
def test_best_ask_only_has_our_open_order(
        mock_insert: Mock,
        mock_cancel: Mock,
        simple_strategy: SimpleStrategy,
        state: State) -> None:
    state.balance = -10
    state.top_market = {
        BookSide.BID: (Decimal(1), Decimal(1)),
        BookSide.ASK: (Decimal(2), Decimal(1)),
    }

    order_1 = Mock()
    order_1.side = SELL
    order_1.price = 2
    order_1.size = 2

    state.open_orders = [order_1]
    simple_strategy.process_strategy()
    mock_cancel.assert_called_once_with(exchange=ANY, order=order_1, callback=ANY)


@patch('simple_strategy.send_order')
def test_no_orders_inserts_orders(
        mock_insert: Mock,
        simple_strategy: SimpleStrategy,
        state: State) -> None:
    state.balance = 0
    state.top_market = {
        BookSide.BID: (Decimal(1), Decimal(1)),
        BookSide.ASK: (Decimal(2), Decimal(1)),
    }

    state.open_orders = []
    simple_strategy.process_strategy()
    assert mock_insert.call_count == 4


@patch('simple_strategy.cancel_order')
@patch('simple_strategy.send_order')
def test_position_exceeds_positive_limit_pull_all_bid_orders(
        mock_insert: Mock,
        mock_cancel: Mock,
        simple_strategy: SimpleStrategy,
        state: State) -> None:
    state.balance = 10
    state.top_market = {
        BookSide.BID: (Decimal(1), Decimal(1)),
        BookSide.ASK: (Decimal(2), Decimal(1)),
    }

    order_1 = Mock()
    order_1.side = BUY
    order_2 = Mock()
    order_2.side = BUY

    state.open_orders = [order_1, order_2]
    simple_strategy.process_strategy()
    assert mock_cancel.call_count == 2
    assert mock_insert.call_count == 2


@patch('simple_strategy.cancel_order')
@patch('simple_strategy.send_order')
def test_position_exceeds_positive_limit_pull_all_ask_orders(
        mock_insert: Mock,
        mock_cancel: Mock,
        simple_strategy: SimpleStrategy,
        state: State) -> None:
    state.balance = -10
    state.top_market = {
        BookSide.BID: (Decimal(1), Decimal(1)),
        BookSide.ASK: (Decimal(2), Decimal(1)),
    }

    order_1 = Mock()
    order_1.side = SELL
    order_2 = Mock()
    order_2.side = SELL

    state.open_orders = [order_1, order_2]
    simple_strategy.process_strategy()
    assert mock_cancel.call_count == 2
    assert mock_insert.call_count == 2


@patch('simple_strategy.send_order')
def test_has_pending_orders_do_nothing(
        mock_insert: Mock,
        simple_strategy: SimpleStrategy,
        state: State) -> None:
    state.balance = 0
    state.top_market = {
        BookSide.BID: (Decimal(1), Decimal(1)),
        BookSide.ASK: (Decimal(2), Decimal(1)),
    }

    state.open_orders = []

    simple_strategy.process_strategy()
    simple_strategy.process_strategy()


@patch('simple_strategy.cancel_order')
@patch('simple_strategy.send_order')
def test_pull_orders_if_count_is_inconsistent(
        mock_insert: Mock,
        mock_cancel: Mock,
        simple_strategy: SimpleStrategy,
        state: State) -> None:
    state.balance = 10
    state.top_market = {
        BookSide.BID: (Decimal(1), Decimal(1)),
        BookSide.ASK: (Decimal(2), Decimal(1)),
    }

    order_1 = Mock()
    order_1.side = SELL

    state.open_orders = [order_1]

    simple_strategy.process_strategy()
    assert mock_cancel.call_count == 1


@patch('simple_strategy.order_from_order_info')
@patch('simple_strategy.cancel_order')
def test_handle_trade_order_pull_all(
        mock_cancel: Mock,
        mock_converter: Mock,
        simple_strategy: SimpleStrategy,
        state: State) -> None:
    order_1 = Mock()
    order_2 = Mock()
    state.open_orders = [order_1, order_2]

    order_info = Mock()
    order_info.status = "TRADE"
    simple_strategy.handle_order_info(order_info)
    assert mock_cancel.call_count == 2
