from typing import Dict

from cryptofeed.defines import DELETE, GET
from cryptofeed.exchanges.mixins.binance_rest import BinanceRestMixin

SANDBOX_REST_API = "https://testnet.binancefuture.com"
SANDBOX_REST_ORDER = "/fapi/v1/"
SANDBOX_REST_ACCOUNT = "/fapi/v2/"
ACCOUNT = "account"
ALL_OPEN_ORDER = "allOpenOrders"


async def get_account_info(exchange: BinanceRestMixin) -> Dict[str, str]:
    # Manual implementation of GET for Sandbox API
    data = await exchange._request(
        GET, ACCOUNT, auth=True, api=SANDBOX_REST_API + SANDBOX_REST_ACCOUNT
    )
    return data


async def cancel_all_orders(exchange: BinanceRestMixin, symbol: str) -> None:
    # Manual implementation of CANCEL ALL for Sandbox API
    await exchange._request(
        DELETE,
        ALL_OPEN_ORDER,
        auth=True,
        api=SANDBOX_REST_API + SANDBOX_REST_ORDER,
        payload={"symbol": symbol},
    )
