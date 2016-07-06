"""Super Simple Stocks assignment for JPMorgan application

Aleksei Smyshliaev, 06.07.2016

Written for Python 2.7. Script does not rely on any third-party libraries
and can be rewritten to Python 3.x at any moment. Python 2.7 was chosen,
because it is the version author was the most proficient with
at the time of creation.

Docstrings are written according to Epytext format.

Script is supposed to be run from command line, e.g.
    $ python2.7 stocks.py
    or
    > python2.7.exe stocks.py
Command line interface should guide you from there.

"""

# Fix integer/integer division
from __future__ import division

from datetime import datetime, timedelta
import operator


class Trade(object):
    """This class holds data of a single trade for a given stock"""

    #: Time when the trade was held
    timestamp = None
    #: Quantity of shares traded
    quantity = 0
    #: Buy/sell indicator
    direction = ""
    #: Price per one share
    price = 0

    def __init__(self, **kw):
        """Initialize attributes from kwargs"""

        for (_attr, _value) in kw.iteritems():
            # Use C{hasattr()} to avoid setting unknown attributes
            if hasattr(self, _attr):
                setattr(self, _attr, _value)


class Stock(object):
    """This class holds data for a single stock symbol"""

    # Constant values for C{Stock.type}
    COMMON = "Common"
    PREFERRED = "Preferred"

    #: Fixed Dividend (real number in [0.0 .. 1.0] representing percent)
    fixed_dividend = 0.0
    #: Last Dividend in pennies
    last_dividend = 0
    #: Par value in pennies
    par_value = 0
    #: Symbol name
    symbol = ""
    #: Stock type, either L{Stock.COMMON} or L{Stock.PREFERRED}
    type = ""
    #: List of made transactions for this stock
    trades = None

    def __init__(self, **kw):
        """Initialize list of recorded trades"""

        self.trades = list()
        for (_attr, _value) in kw.iteritems():
            # Use C{hasattr()} to avoid setting unknown attributes
            if hasattr(self, _attr):
                setattr(self, _attr, _value)
        assert self.type in (Stock.COMMON, Stock.PREFERRED), \
            "Stock type must be '{}' or '{}'".format(
                Stock.COMMON, Stock.PREFERRED)

    @property
    def dividend_yield(self):
        """Calculate dividend yield for a given stock"""

        if self.type == Stock.COMMON:
            return self.last_dividend / self.price
        elif self.type == Stock.PREFERRED:
            return (self.fixed_dividend * self.par_value) / self.price

    @property
    def PE_ratio(self):
        """Calculate P/E Ratio for a given stock"""

        return self.dividend_yield / self.price

    @property
    def price(self):
        """Calculate stock price based on trades in past 15 minutes"""

        _recent_trades = self.recent_trades
        # Calculate the stock price
        _total_quantity = sum(_trade.quantity for _trade in _recent_trades)
        _total_price = 0.0
        for _trade in _recent_trades:
            _total_price += (_trade.quantity * _trade.price)
        if _total_price == 0:
            # Escape division by zero
            return 0
        return (_total_price / _total_quantity)

    @property
    def recent_trades(self):
        """Filter trades recorded in last 15 minutes

        @return: L{Trade} instances with timestamp in last 15 minutes
        @rtype: C{list}

        """
        _threshold = datetime.now() - timedelta(minutes=15)

        def _key(_trade):
            return (_trade.timestamp >= _threshold)
        return filter(_key, self.trades)

    def trade(self, **kw):
        """Shortcut function: record a trade for a given stock"""

        self.trades.append(Trade(**kw))


class Stocks(list):
    """This class holds list of all known stocks"""

    def add(self, **kw):
        """Add a stock to the list

        @param kw: keyword arguments for L{Stock} initialization
        @type kw: C{dict}

        """
        self.append(Stock(**kw))

    @property
    def GBCE_share_index(self):
        """Calculate GBCE share index

        Use geometric mean of prices for all stocks for calculation

        """
        _nn = len(self)
        # Calculate product of all prices
        _product = reduce(operator.mul, tuple(_stock.price for _stock in self))
        # Calculate n-th root of the product
        return (_product ** (1 / _nn))

    def get(self, symbol):
        """Get a L{Stock} object referenced by its symbol

        @param symbol: symbol of a stock
        @type symbol: C{str}
        @retrun: stock instance
        @rtype: L{Stock}

        """
        for _stock in self:
            if _stock.symbol == symbol:
                return _stock
        raise ValueError("Stock symbol '{}' is not registered".format(symbol))


class Interface(object):
    """Handler for all command-line interaction with user"""

    TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M:%S"

    def __init__(self):
        """Initialize stocks storage"""

        self.stocks = Stocks()

    def run(self):
        """Print prompt and wait for user actions"""
        _prompt_short = "Please, choose an action to perform [r/d/e]: "
        _prompt = ("r) Record a trade\n"
            "d) Display stocks data\n"
            "e) Exit\n"
            "\n"
            + _prompt_short)

        print "Greetings!\n"
        _answer = raw_input(_prompt)
        while _answer != "e":
            if _answer == "r":
                self.trade()
                _answer = raw_input(_prompt)
            elif _answer == "d":
                self.show_market()
                _answer = raw_input(_prompt)
            else:
                _answer = raw_input("Incorrect option '{}'\n{}".format(
                    _answer, _prompt_short))
        print "\nGood bye!"

    def show_market(self):
        """Display market data"""

        _divider = (
            "+------+---------+--------+--------+-----+--------+-----+------+")
        _header = (
            "|Stock | Type    |Last    |Fixed   |Par  |Dividend|P/E  |Ticker|"
            "\n"
            "|symbol|         |divident|dividend|value|yield   |ratio|price |")
        _common_data = "|{:6}|{:9}|{:8}|{:>8}|{:5}|"
        _no_trades = "  No trade data yet  |"
        _with_trades = "{:8.3f}|{:5.3f}|{:6.3f}|"

        print _divider
        print _header
        print _divider

        for _stock in self.stocks:
            # Hide "0%" for L{Stock.COMMON} stocks
            if _stock.type == Stock.COMMON:
                _fixed_dividend = ""
            elif _stock.type == Stock.PREFERRED:
                _fixed_dividend = "{:1.0%}".format(_stock.fixed_dividend)
            # Fill in common data
            _data = _common_data.format(_stock.symbol, _stock.type,
                _stock.last_dividend, _fixed_dividend, _stock.par_value)

            if len(_stock.recent_trades) < 1:
                # If there were no trades it is unable to calculate data
                # Show placeholder
                _data += _no_trades
            else:
                _data += _with_trades.format(_stock.dividend_yield,
                    _stock.PE_ratio, _stock.price)

            print _data
            print _divider

        print "\nGCBE All Share Index: {:4.3f}\n".format(
            self.stocks.GBCE_share_index)

    def trade(self):
        """Prompt user for trade data"""

        # Input stock
        _names = tuple(_stock.symbol for _stock in self.stocks)
        _available = "Available stocks: [{}]\n".format(",".join(_names))
        _select_stock = "Please, select a stock: "
        _answer = raw_input(_available + _select_stock)
        # Validate stock symbol
        while _answer not in _names:
            _answer = raw_input(("Incorrect stock symbol '{}'\n".format(_answer))
                + _available + _select_stock)
        _symbol = _answer

        # Input timestamp
        _now = datetime.now()
        _prompt = ("Default timestamp: {}\n"
            "Press ENTER to accept or enter your own: ".format(
                _now.strftime(self.TIMESTAMP_FORMAT)))
        _answer = raw_input(_prompt)
        _timestamp = None
        # Validate timestamp
        while _timestamp is None:
            if not _answer:
                _timestamp = _now
                break
            try:
                _timestamp = datetime.strptime(_answer, self.TIMESTAMP_FORMAT)
            except ValueError:
                _answer = raw_input(("Incorrect string '{}'\n".format(answer))
                    + _prompt)

        # Input buy or sell
        _prompt = "Please, choose to buy or sell [b/s]: "
        _answer = raw_input(_prompt)
        # Validate buy or sell choice
        while _answer not in ("b", "s"):
            _answer = raw_input(("Incorrect option '{}'\n".format(_answer))
                + _prompt)
        _buy = (_answer == "b")

        # Input quantity
        _verb = "BUY" if _buy else "SELL"
        _prompt = "Please, input quantity to {} (pcs): ".format(_verb)
        _answer = raw_input(_prompt)
        # Validate quantity number
        while not _answer.isdigit():
            _answer = raw_input(("Incorrect amount '{}'\n".format(_answer))
                + _prompt)
        _quantity = int(_answer)

        # Input price
        _prompt = "Please, input one share price (pennies): "
        _answer = raw_input(_prompt)
        _price = None
        while _price is None:
            try:
                _price = float(_answer)
            except ValueError:
                _answer = raw_input(("Incorrect price '{}'\n".format(_answer))
                    + _prompt)

        # Record trade in stock
        _stock = self.stocks.get(_symbol)
        _args = dict(timestamp=_timestamp, quantity=_quantity, direction=_verb,
            price=_price)
        _stock.trade(**_args)
        # Notify user
        _output = ("\nRecorded trade: [{timestamp}] {direction} {quantity}"
            " {stock} shares for {price} apiece.\n")
        print _output.format(stock=_symbol, **_args)


if __name__ == "__main__":
    # Initialize stock market
    _interface = Interface()
    _interface.stocks.add(symbol="TEA", type=Stock.COMMON, last_dividend=0,
        par_value=100)
    _interface.stocks.add(symbol="POP", type=Stock.COMMON, last_dividend=8,
        par_value=100)
    _interface.stocks.add(symbol="ALE", type=Stock.COMMON, last_dividend=23,
        par_value=100)
    _interface.stocks.add(symbol="GIN", type=Stock.PREFERRED, last_dividend=8,
        fixed_dividend=0.02, par_value=100)
    _interface.stocks.add(symbol="JOE", type=Stock.COMMON, last_dividend=13,
        par_value=100)

    # Run user interface (command-line)
    _interface.run()
