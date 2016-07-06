"""Super Simple Stocks assignment for JPMorgan application

Aleksei Smyshliaev, 26.11.2015

Written for Python 2.7. Script does not rely on any third-party libraries
and can be rewritten to Python 3.x at any moment. Python 2.7 was chosen, because
it is the version author was the most proficient with at the time of creation.

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

# Constant values for C{Stock.type}
TYPE_COMMON = "Common"
TYPE_PREFERRED = "Preferred"

# Global list of stocks (initialized at run-time)
STOCKS = None


class ObjectWithAttributes(object):
    """Base class for stocks and stock trades"""

    __attributes__ = ()

    def __init__(self, **kw):
        """Update instance attributes if respective keyword values are passed"""

        for (_attr, _value) in kw.iteritems():
            if _attr in self.__attributes__:
                setattr(self, _attr, _value)


class Trade(ObjectWithAttributes):
    """This class holds data of a single trade for a given stock"""

    __attributes__ = ("timestamp", "quantity", "direction", "price")

    # Time when the trade was held
    timestamp = None
    # Quantity of shares traded
    quantity = 0
    # Buy/sell indicator
    direction = ""
    # Price per one share
    price = 0


class Stock(ObjectWithAttributes):
    """This class holds data for a single stock symbol"""

    # List of class attributes
    __attributes__ = ("symbol", "type", "last_dividend", "fixed_dividend",
        "par_value", "trades")

    # Fixed Dividend (real number in [0.0 .. 1.0] representing percent)
    fixed_dividend = 0.0
    # Last Dividend in pennies
    last_dividend = 0
    # Par value in pennies
    par_value = 0
    # Symbol name
    symbol = ""
    # Stock type, either C{TYPE_COMMON} or C{TYPE_PREFERRED}
    type = ""
    # List of made transactions for this stock
    trades = None

    def __init__(self, *args, **kw):
        """Initialize list of recorded trades"""

        self.trades = list()
        super(Stock, self).__init__(*args, **kw)

    @property
    def dividend_yield(self):
        """Calculate dividend yield for a given stock"""

        if self.type == TYPE_COMMON:
            return self.last_dividend / self.price
        elif self.type == TYPE_PREFERRED:
            return (self.fixed_dividend * self.par_value) / self.price
        else:
            raise ValueError("Unknown stock type: '%s'" % self.type)

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
        """FIlter trades recorded in last 15 minutes

        @return: C{Trade} instances with timestamp in last 15 minutes
        @rtype: C{list}

        """
        _threshold = datetime.now() - timedelta(minutes=15)

        def _key(_trade):
            return (_trade.timestamp >= _threshold)
        return filter(_key, self.trades)

    def trade(self, **kw):
        """Record a trade for a given stock"""

        self.trades.append(Trade(**kw))


class Stocks(list):
    """This class holds list of all known stocks"""

    def add(self, **kw):
        """Add a stock to the list

        @param kw: keyword arguments for C{Stock} initialization
        @type kw: C{dict}

        """
        self.append(Stock(**kw))

    @property
    def GBCE_share_index(self):
        """Calculate GBCE index using geometric mean of prices for all stocks"""

        _nn = len(self)
        _prices = tuple(_stock.price for _stock in self)
        # Calculate product of all prices
        _product = reduce(operator.mul, _prices)
        # Calculate n-th root of the product
        return (_product ** (1 / _nn))

    def get(self, symbol):
        """Get a stock referenced by its symbol

        @param symbol: symbol of a stock
        @type symbol: C{str}
        @retrun: stock instance
        @rtype: C{Stock}

        """
        for _stock in self:
            if _stock.symbol == symbol:
                return _stock
        raise ValueError("Invalid stock symbol '%s'" % symbol)


class Interface(object):
    """Handler for all command-line interaction with user"""

    @classmethod
    def run(cls):
        """Print prompt and wait for user actions"""
        _prompt_short = "Please, choose an action to perform [a/b/c]: "
        _prompt = ("a) Record a trade\n"
            "b) Display stocks data\n"
            "c) Exit\n"
            "\n"
            + _prompt_short)

        print "Greetings!\n"
        _answer = raw_input(_prompt)
        while _answer != "c":
            if _answer == "a":
                cls.trade()
                _answer = raw_input(_prompt)
            elif _answer == "b":
                cls.show_market()
                _answer = raw_input(_prompt)
            else:
                _answer = raw_input("Incorrect option '%s'\n" + _prompt_short
                    % _answer)
        print "\nGood bye!"

    @classmethod
    def show_market(cls):
        """Display market data"""

        _divider =  "+------+---------+--------+--------+-----+--------+-----+------+"
        _header = "|Stock | Type    |Last    |Fixed   |Par  |Dividend|P/E  |Ticker|\n" \
                  "|symbol|         |divident|dividend|value|yield   |ratio|price |"
        _no_trades = "|{:6}|{:9}|{:8}|{:>8}|{:5}|  No trade data yet  |"
        _with_trades = "|{:6}|{:9}|{:8}|{:>8}|{:5}|{:8.3f}|{:5.3f}|{:6.3f}|"

        print _divider
        print _header
        print _divider

        for _stock in STOCKS:
            # Hide "0%" for C{TPYE_COMMON} stocks
            _fixed_dividend = ("{:1.0%}".format(_stock.fixed_dividend)
                if _stock.type == TYPE_PREFERRED else "")
            # Fill in common data
            _data = (_stock.symbol, _stock.type, _stock.last_dividend,
                _fixed_dividend, _stock.par_value)

            if len(_stock.recent_trades) < 1:
                # If there were no trades it is unable to calculate data
                # Show placeholder
                print _no_trades.format(*_data)
            else:
                _data += (_stock.dividend_yield, _stock.PE_ratio, _stock.price)
                print _with_trades.format(*_data)
            print _divider

        print "\nGCBE All Share Index: {:4.3f}\n".format(STOCKS.GBCE_share_index)

    @classmethod
    def select_stock(cls):
        """Make user choose one of the available stocks

        @return: stock symbol
        @rtype: C{str}

        """
        _names = tuple(_stock.symbol for _stock in STOCKS)
        _available = "Available stocks: [%s]\n" % ",".join(_names)
        _select_stock = "Please, select a stock: "
        _answer = raw_input(_available + _select_stock)
        while _answer not in _names:
            _answer = raw_input(("Incorrect stock symbol '%s'\n" % _answer)
                + _available + _select_stock)
        return _answer

    @classmethod
    def trade(cls):
        """Prompt user for trade data"""

        # Select stock
        _symbol = cls.select_stock()

        # Select timestamp
        _now = datetime.now()
        _format = "%d/%m/%Y %H:%M:%S"
        _prompt = (("Default timestamp: %s\n" % _now.strftime(_format))
            + "Press ENTER to accept or enter your own: ")
        _answer = raw_input(_prompt)
        _timestamp = None
        while _timestamp is None:
            if not _answer:
                _timestamp = _now
                break
            try:
                _timestamp = datetime.strptime(_answer, _format)
            except ValueError:
                _answer = raw_input(("Incorrect string '%s'\n" % _answer)
                    + _prompt)

        # Select buy or sell
        _prompt = "Please, choose to buy or sell [b/s]: "
        _answer = raw_input(_prompt)
        while _answer not in ("b", "s"):
            _answer = raw_input(("Incorrect option '%s'\n" % _answer)
                + _prompt)
        _buy = (_answer == "b")

        # Select quantity
        _verb = "BUY" if _buy else "SELL"
        _prompt = "Please, input quantity to %s (pcs): " % _verb
        _answer = raw_input(_prompt)
        while not _answer.isdigit():
            _answer = raw_input(("Incorrect amount '%s'\n" % _answer)
                + _prompt)
        _quantity = int(_answer)

        # Select price
        _prompt = "Please, input one share price (pennies): "
        _answer = raw_input(_prompt)
        _price = None
        while _price is None:
            try:
                _price = float(_answer)
            except ValueError:
                _answer = raw_input(("Incorrect price '%s'\n" % _answer)
                    + _prompt)

        # Record trade in stock
        _stock = STOCKS.get(_symbol)
        _stock.trade(timestamp=_timestamp, quantity=_quantity, direction=_verb,
            price=_price)
        # Notify user
        print "\nRecorded trade: [%s] %s %i %s shares for %s apiece.\n" % (
            _timestamp.strftime(_format), _verb, _quantity, _symbol, _price)


if __name__ == "__main__":
    # Initialize stock market
    STOCKS = Stocks()
    STOCKS.add(symbol="TEA", type=TYPE_COMMON, last_dividend=0, par_value=100)
    STOCKS.add(symbol="POP", type=TYPE_COMMON, last_dividend=8, par_value=100)
    STOCKS.add(symbol="ALE", type=TYPE_COMMON, last_dividend=23, par_value=100)
    STOCKS.add(symbol="GIN", type=TYPE_PREFERRED, last_dividend=8,
        fixed_dividend=0.02, par_value=100)
    STOCKS.add(symbol="JOE", type=TYPE_COMMON, last_dividend=13, par_value=100)

    # Run user interface (command-line)
    Interface.run()
