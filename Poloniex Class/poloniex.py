#!python3

import hmac
import json
import time
import urllib.request
from decimal import Decimal
from hashlib import sha512
from urllib.error import URLError, HTTPError, ContentTooShortError
from urllib.parse import urlencode

from numpy import exp, linspace, convolve


class Poloniex:
    """
        Hi! I am the Poloniex.com Cryptocurrency Exchange Class for Python >3.5! My life long goal and penultimate
        aspiration is to encapsulate all published interactions for Poloniex's trading API! Hopefully I will live long
        and prosper...

        Args:
            api_key (str): API Access Key from Poloniex for authorization
            secret_key (str): Secret Key from Poloniex for authentication
            auto_init (bool): Launches the initialize() method upon instance creation if True

        Attributes:
            api_key (str): Instance level storage for the API Access Key
            secret_key (str): Instance level storage for the Secret Key
            connection (bool): Instance level indicator of successful initialization

    """
    rate_timer = []

    __slots__ = ["api_key", "secret_key", "public_api", "trading_api", "connection"]

# Internal Class Methods

    def __init__(self, api_key: str, secret_key: str, auto_init=False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.public_api = 'https://poloniex.com/public?command='
        self.trading_api = 'https://poloniex.com/tradingapi'
        if auto_init:
            self.connection = self.initialize()
        else:
            self.connection = False

    def __repr__(self):
        c = self.__class__.__name__
        a = self.api_key
        s = self.secret_key
        con = self.connection
        return "{c} (Key: {a}, Secret: {s}, Connected: {con})".format(c=c, a=a, s=s, con=con)

    def __bool__(self):
        return self.connection

    def initialize(self) -> bool:
        """
        Initiates a connection to the Poloniex API to verify correct API & Secret keys. Utilizes the balances() method's
        return for determination.

        Returns:
            bool
        """
        if self.balances:
            self.connection = True
            return True
        else:
            self.connection = False
            return False

    def rate_limit(self) ->bool:
        """
        Rate limiting method to prevent violation of Poloniex's policy for the number of requests per second. While
        Poloniex has set the rate at 6 requests per second, this function limits the number of requests to 5 per second.

        Returns:
            bool
        """
        Poloniex.rate_timer.append(time.time())
        if len(Poloniex.rate_timer) > 4:
            diff = Poloniex.rate_timer[4] - Poloniex.rate_timer[0]
            if diff <= 1:
                time.sleep(1-diff)
            Poloniex.rate_timer.pop(0)
        return True

    def public_query(self, req: str, retries: int = 2) -> dict:
        """
        Builds and passes the actual request to Poloniex's public API. In the event of a 500 series http error, the
        request is retried after 3 seconds up the maximum number of times defined by the 'retries' argument.
        Args:
            req (str): The actual request to be appended to the public API's url.
            retries (int): Maximum number of retries in the event of a 500 series HTTP error. Default = 2

        Returns:
            dict
        """
        url = self.public_api+req
        request = urllib.request.Request(url)
        self.rate_limit()
        try:
            with urllib.request.urlopen(request) as response:
                data = response.read()
        except (URLError, HTTPError, ContentTooShortError) as err:
            if retries > 0:
                if hasattr(err, 'code') and 500 <= err.code < 600:
                    time.sleep(3)
                    return self.public_query(req, retries - 1)
                else:
                    return dict([])
            else:
                return dict([])
        return json.loads(data)

    def signed_query(self, req: dict, retries: int = 2) -> dict:
        """
        Builds and passes the actual request to Poloniex's trading API. In the event of a 500 series http error, the
        request is retried after 3 seconds up the maximum number of times defined by the 'retries' argument.
        Args:
            req (dict): The actual request in JSON format.
            retries (int): Maximum number of retries in the event of a 500 series HTTP error. Default = 2

        Returns:
            dict
        """
        req['nonce'] = int(time.time()*1000)
        data = urlencode(req)
        sign = hmac.new(self.secret_key, data, sha512).hexdigest()
        headers = dict(Sign=sign, Key=self.api_key)
        url_req = urllib.request.Request(self.trading_api, data, headers)
        self.rate_limit()
        try:
            with urllib.request.urlopen(url_req) as response:
                data = response.read()
        except (URLError, HTTPError, ContentTooShortError) as err:
            if retries > 0:
                if hasattr(err, 'code') and 500 <= err.code < 600:
                    time.sleep(3)
                    return self.signed_query(req, retries - 1)
                else:
                    return dict([])
            else:
                return dict([])

        return json.loads(data)

    def update_keys(self, api: str, secret_key: str, auto_init: bool=False) -> bool:
        """
        Updates the API and Secret keys for the instance.

        Args:
            api (str): Poloniex Account API key
            secret_key (str): Poloniex Account Secret key
            auto_init (bool): Automatically launch the initialize() method to verify keys.

        Returns:
            bool
        """
        self.api_key = api
        self.secret_key = secret_key
        if auto_init:
            self.connection = self.initialize()
        else:
            self.connection = False
        return self.connection

    # Class Properties - Public API

    @property
    def ticker_data(self) -> dict:
        """
        Returns the ticker for all markets.

        Returns:
            dict: Sample output:
                    {"BTC_LTC":
                        {   "last":"0.0251",
                            "lowestAsk":"0.02589999",
                            "highestBid":"0.0251",
                            "percentChange":"0.02390438",
                            "baseVolume":"6.16485315",
                            "quoteVolume":"245.82513926"
                        }
                    ,"BTC_NXT":
                        {   "last":"0.00005730",
                            "lowestAsk":"0.00005710",
                            "highestBid":"0.00004903",
                            "percentChange":"0.16701570",
                            "baseVolume":"0.45347489",
                            "quoteVolume":"9094"
                        },
                    ... }
        """
        return self.public_query('returnTicker')

    # Class Properties - Trading API

    @property
    def balances(self) -> dict:
        request = dict(command='returnBalances')
        return self.signed_query(request)

    # Public API Methods

    def chart_data(self, currency_pair: str, period: int, start: str, end: str) -> dict:
        """
        Returns candlestick chart data. Required GET parameters are "currencyPair", "period" (candlestick period in
        seconds; valid values are 300, 900, 1800, 7200, 14400, and 86400), "start", and "end". "Start" and "end" are
        given in UNIX timestamp format and used to specify the date range for the data returned.

        Returns:
            dict: Sample output:
                    [
                        {   "date":1405699200,
                            "high":0.0045388,
                            "low":0.00403001,
                            "open":0.00404545,
                            "close":0.00427592,
                            "volume":44.11655644,
                            "quoteVolume":10259.29079097,
                            "weightedAverage":0.00430015},
                    ...]
        """
        request = 'returnChartData&currencyPair='+currency_pair
        request.join('&start='+start)
        request.join('&end='+end)
        request.join('&period='+str(period))
        return self.public_query(request)

    # Trading Api Methods

    def buy(self, currency_pair: str, rate: Decimal, amount: Decimal) -> dict:
        request = dict(command='buy',
                       currencyPair=currency_pair,
                       rate=rate,
                       amount=amount)
        return self.signed_query(request)

    def sell(self, currency_pair: str, rate: Decimal, amount: Decimal) -> dict:
        request = dict(command='sell',
                       currencyPair=currency_pair,
                       rate=rate,
                       amount=amount)
        return self.signed_query(request)

    def cancel_order(self, order_number: str) -> dict:
        request = dict(command='cancelOrder',
                       orderNumber=order_number)
        return self.signed_query(request)

    def open_orders(self, currency_pair: str) -> dict:
        request = dict(command='returnOpenOrders',
                       currencyPair=currency_pair)
        return self.signed_query(request)

    def trade_history(self, currency_pair: str) -> dict:
        request = dict(command='returnTradeHistory',
                       currencyPair=currency_pair)
        return self.signed_query(request)

    def withdraw(self, currency: str, address: str, amount: Decimal) -> dict:
        request = dict(command='withdraw',
                       currency=currency,
                       amount=amount,
                       address=address)
        return self.signed_query(request)


class Account:

    def __init__(self, api, secret, exchange: str = 'Poloniex', auto_init=False):
        if exchange == "Poloniex" or "poloniex:":
            self.exchange = Poloniex(api, secret, auto_init)
        if self.exchange:
            self.balances = self.exchange.balances
            self.trade_history = self.exchange.trade_history
            self.orders = self.exchange.open_orders(currency_pair='all')

    def ema_calc(self, closings, period: int):
        weights = exp(linspace(-1., 0., period))
        weights /= weights.sum()
        y = convolve(closings, weights, mode='full')[:len(closings)]
        y[:period] = y[period]
        return y

    def ema(self, currency_pair: str, length: int, period: int, start: int = None):
        if start is None:
            end = int(time.time())
            start = int(end-length*3600)
        else:
            end = int(start+length*3600)
        data = self.exchange.chart_data(currency_pair, period, str(start), str(end))
        closings = list()
        for x in data:
            for key, value in x.items():
                closings.append(x['close'])
        return self.ema_calc(closings, period)

#For Future Use...
    # class CurrencyPair:
    # def __init__(self, base, target):
    #   self.base_ticker = base
    #    self.target_ticker = target
    #    self.base_name
    #    self.target_name
    #    self.string
    #    self.price
