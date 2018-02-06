#!python3

import abc
import decimal
import hmac
from hashlib import sha512
import json
import time
from urllib.error import URLError, HTTPError, ContentTooShortError
from urllib.parse import urlencode
import urllib.request


class Exchange(metaclass=abc.ABCMeta)

    @abc.abstractmethod
    def initialize(self):
        raise NotImplemented()

    @abc.abstractmethod
    def rate_limit(self, ):
        raise NotImplemented()

    @abc.abstractmethod
    def update_keys(self, api, secret, auto_init):
        raise NotImplemented()

    @abc.abstractmethod
    def chart_data(self):
        raise NotImplemented()

    @abc.abstractmethod
    def ticker_data(self):
        raise NotImplemented()

    @abc.abstractmethod
    def balances(self):
        raise NotImplemented()

    @abc.abstractmethod
    def buy(self, currency_pair, rate, amount):
        raise NotImplemented()

    @abc.abstractmethod
    def cancel_order(self, currency_pair, order_number):
        raise NotImplemented()

    @abc.abstractmethod
    def open_orders(self, currency_pair):
        raise NotImplemented()

    @abc.abstractmethod
    def sell(self, currency_pair, rate, amount):
        raise NotImplemented()

    @abc.abstractmethod
    def trade_history(self, currency_pair):
        raise NotImplemented()




class Poloniex(Exchange):
    """
        Hi! I am the Poloniex.com Cryptocurrency Exchange Class for Python >3.5! My life long goal
        and penultimate aspiration is to encapsulate all published interactions for Poloniex's
        trading API! Hopefully I will live long and prosper...

        Args:
            api (str): API Access Key from Poloniex for authorization
            secret_key (str): Secret Key from Poloniex for authentication
            auto_init (bool): Launches the initialize() method upon instance creation if True

        Attributes:
            api (str): Instance level storage for the API Access Key
            secret_key (str): Instance level storage for the Secret Key
            connection (bool): Instance level indicator of successful connection

    """
# Internal Class Methods

    def __init__(self, api: str, secret_key: str, auto_init=False):
        self.api_key = api
        self.secret_key = secret_key
        self.public_api = 'https://poloniex.com/public?command='
        self.trading_api = 'https://poloniex.com/tradingapi'
        self.rate_timer = []
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

    def post_processing(self, data) -> dict:
        pass

    def rate_limit(self) ->bool:
        self.rate_timer.append(time.time())
        if len(self.rate_timer) > 4:
            diff = self.rate_timer[4] - self.rate_timer[0]
            if diff <= 1:
                time.sleep(1-diff)
            self.rate_timer.pop(0)
        return True

    def public_query(self, req: str, retries: int = 2) -> dict:
        url = self.public_api+req
        request = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(request) as response:
                data = response.read()
        except (URLError, HTTPError, ContentTooShortError) as err:
            if retries > 0:
                if hasattr(err, 'code') and 500 <= err.code < 600:
                    return self.public_query(req, retries - 1)
                else:
                    return dict([])
            else:
                return dict([])
        return json.loads(data)

    def signed_query(self, req: dict, retries: int = 2) -> dict:
        req['nonce'] = int(time.time()*1000)
        data = urlencode(req)
        sign = hmac.new(self.secret_key, data, sha512).hexdigest()
        headers = dict(Sign=sign, Key=self.api_key)
        url_req = urllib.request.Request(self.trading_api, data, headers)
        try:
            with urllib.request.urlopen(url_req) as response:
                data = response.read()
        except (URLError, HTTPError, ContentTooShortError) as err:
            if retries > 0:
                if hasattr(err, 'code') and 500 <= err.code < 600:
                    return self.signed_query(req, retries - 1)
                else:
                    return dict([])
            else:
                return dict([])

        return json.loads(data)

    def initialize(self) -> bool:
        if self.balances():
            return True
        else:
            return False

    def update_keys(self, api: str, secret_key: str, auto_init: bool=False) -> bool:
        self.api_key = api
        self.secret_key = secret_key
        if auto_init:
            self.connection = self.initialize()
        else:
            self.connection = False
        return self.connection

    # Public API Methods

    # Trading Api Methods

    def balances(self) -> dict:
        request = dict(command='returnBalances')
        return self.signed_query(request)

    def buy(self, currency_pair: str, rate: decimal.Decimal, amount: decimal.Decimal) -> dict:
        request = dict(command='buy',
                       currencyPair=currency_pair,
                       rate=rate,
                       amount=amount)
        return self.signed_query(request)

    def sell(self, currency_pair: str, rate: decimal.Decimal, amount: decimal.Decimal) -> dict:
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

    def withdraw(self, currency: str, address: str, amount: decimal.Decimal) -> dict:
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
            self.balances = self.exchange.balances()
            self.trade_history = self.exchange.trade_history
            self.orders = self.exchange.open_orders()


class CurrencyPair:
    def __init__(self, base, target):
        self.base_ticker = base
        self.target_ticker = target
