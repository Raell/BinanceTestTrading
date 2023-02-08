import asyncio

from cryptofeed import FeedHandler
from cryptofeed.defines import L2_BOOK, ORDER_INFO, POSITIONS
from cryptofeed.exchanges import BinanceFutures
from cryptofeed.exchanges.mixins.binance_rest import BinanceRestMixin

from message_handler import MessageHandler
from post_parsing_utils import get_balance_for_asset, get_open_orders_from_info
from sandbox_get_override import (SANDBOX_REST_API, SANDBOX_REST_ORDER,
                                  cancel_all_orders, get_account_info)
from simple_strategy import SimpleStrategy
from state import State


def main():
    path_to_config = "config.yaml"
    symbol = "BTC-USDT-PERP"
    asset = "BTCUSDT"

    state = State(symbol, asset)
    message_handler = MessageHandler(state)

    binance_futures_public = BinanceFutures(
        config=path_to_config,
        sandbox=True,
        symbols=[symbol],
        channels=[L2_BOOK],
        callbacks={L2_BOOK: message_handler.order_book_handler},
    )
    binance_futures_private = BinanceFutures(
        config=path_to_config,
        sandbox=True,
        symbols=[symbol],
        channels=[POSITIONS, ORDER_INFO],
        callbacks={
            POSITIONS: message_handler.positions_handler,
            ORDER_INFO: message_handler.order_info_handler,
        },
    )

    # Manually override REST API for orders, as current implementation
    # does not support using sandbox REST API
    binance_futures_public.api = SANDBOX_REST_API + SANDBOX_REST_ORDER
    binance_futures_private.api = SANDBOX_REST_API + SANDBOX_REST_ORDER

    strategy = SimpleStrategy(
        exchange=binance_futures_public, state=state, balance_limit=1
    )
    message_handler.set_strategy(strategy)

    initialize_account_info(binance_futures_private, state)

    f = FeedHandler()
    f.add_feed(binance_futures_public)
    f.add_feed(binance_futures_private)
    f.run()


def initialize_account_info(exchange: BinanceRestMixin, state: State) -> None:
    loop = asyncio.get_event_loop()

    # Get starting balance
    account_info = loop.run_until_complete(get_account_info(exchange))
    balance = get_balance_for_asset(account_info, state.asset)

    # Cancels all open orders
    cancel_all_orders(exchange, state.asset)

    # Initialize balance
    state.initialize_balance(balance)


if __name__ == "__main__":
    main()
