# BinanceTestTrading
Simple trading strategy that will place orders in an event-driven way on BTCUSDT perpetual futures.

This strategy is event-based driven from on websocket feed messages to track order book, positions and open orders.
The strategy always sets up 2 bid and 2 ask orders of size 0.1 BTC, the bids are placed at the best available bid and at the best available bid minus 10 dollars.  

Bids orders are only placed if the current BTC position is <= 1 BTC while asks orders are only placed if the current BTC position is >= -1 BTC. Orders and cancels are inserted via RESTful POST API endpoints. 

Note: Some functions from crytofeed for the POST API do not work for the Sandbox environment, a few workarounds were added to bypass this.

The strategy listens to the feed and updates its quotes based on new information. It maintains an internal expectation of the state of its orders to prevent duplication but is able to reconciles with the feed gracefully if there is a discrepancy.

Potential drawbacks include:
- The open order internal state is only a best guess estimate by tracking post orders and is reconciled only on as it only updated on feed updates
- Order updates are only sent on book updates, if this feed is delayed the orders may be incorrect
- This pulls all orders on a trade, hence orders lose priority if re-inserted on the same level

### Running the strategy
- Requires Python 3.8
- Use `pipenv shell` to enter the virtual environment
- Run `pipenv sync` to install dependencies
- Run `python main.py` to run the strategy


### For development and testing
- Use `pipenv shell` to enter the virtual environment.
- Run `pipenv sync --dev` to install dependencies
- To run the tests, use `pipenv run test`
- Coding linting is available via `Black` and `isort`
  - To run linter, use `pipenv run fmt`
