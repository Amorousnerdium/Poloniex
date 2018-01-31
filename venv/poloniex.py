#! python3

import abc
import decimal
import hmac
from hashlib import sha512
import json
import time
from urllib.error import URLError, HTTPError, ContentTooShortError
from urllib.parse import urlencode
import urllib.request


class Exchange (metaclass=abc.ABCMeta):

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
    def initialize(self):
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

    @abc.abstractmethod
    def update_keys(self, api, secret, auto_init):
        raise NotImplemented()


class Poloniex (Exchange):
    """
        Hi! I am the Poloniex.com Cryptocurrency Exchange Class for Python >3.5! My life long goal
        and penultimate aspiration is to encapsulate all published interactions for Poloniex's
        trading API! Hopefully I will live long and prosper...

        Args:
            api (str): API Access Key from Poloniex for authorization
            secret (str): Secret Key from Poloniex for authentication
            auto_init (bool): Launches the initialize() method upon instance creation if True

        Attributes:
            api (str): Instance level storage for the API Access Key
            secret (str): Instance level storage for the Secret Key
            connection (bool): Instance level indicator of successful connection

    """

    def __init__(self, api: str, secret_key: str, auto_init=False):
        self.api_key = api
        self.secret_key = secret_key
        self.publicapi = 'https://poloniex.com/public?command='
        self.tradingapi = 'https://poloniex.com/tradingapi'
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

    def balances(self):
        request = dict(command='returnBalances',
                       nonce=int(time.time() * 1000),)
        return self.signed_query(self.tradingapi, request)

    def buy(self, currency_pair: str, rate: Decimal.decimal, amount: Decimal.decimal)->dict:
        request = dict(command='buy',
                       nonce=int(time.time() * 1000),
                       currencyPair=currency_pair,
                       rate=rate,
                       amount=amount)
        return self.signed_query(self.tradingapi, request)

    def sell(self, currency_pair: str, rate: Decimal.decimal, amount: Decimal.decimal)->dict:
        request = dict(command='sell',
                       nonce=int(time.time() * 1000),
                       currencyPair=currency_pair,
                       rate=rate,
                       amount=amount)
        return self.signed_query(self.tradingapi, request)

    def cancel_order(self, currency_pair: str, order_number: str):
        request = dict(command='cancelOrder',
                       nonce=int(time.time() * 1000),
                       currencyPair=currency_pair,
                       orderNumber=order_number)
        return self.signed_query(self.tradingapi, request)

    def initialize(self) -> bool:
        if self.balance():
            return True
        else:
            return False

    def open_orders(self, currency_pair: str):
        request = dict(command='returnOpenOrders',
                       nonce=int(time.time() * 1000),
                       currencyPair=currency_pair)
        return self.signed_query(self.tradingapi, request)

    def post_processing(self, data):
        pass
    
    def public_query(self, url: str, retries: int = 2):
        req = urllib.request.Request(url)
        try:
            response = urllib.request.urlopen(req).read()
        except (URLError, HTTPError, ContentTooShortError) as err:
            response = None
            if retries > 0:
                if hasattr(err, 'code') and 500 <= err.code < 600:
                    return self.public.query(url, retries-1)
                else:
                    return None
            else:
                return None
        return json.loads(response)

    def signed_query(self, url: str, req={}, retries: int = 2):
        data = urllib.parse.urlencode(req)
        sign = hmac.new(self.secret_key, data, hashlib.sha512).hexdigest()
        headers = dict(Sign=sign, Key=self.api_key)
        request = urllib.request.Request(self.tradingapi, data, headers)
        try:
            response = urllib.request.urlopen(request).read()
        except (URLError, HTTPError, ContentToShortError) as err:
            response = None
            if retries > 0:
                if hasattr(err, 'code') and 500 <= err.code < 600:
                    return self.signed.query(url, req, retries-1)
                else:
                    return None
            else:
                return None
        resp = json.loads(response.read())
        return self.post_processing(resp)

    def trade_history(self, currency_pair: str):
        request = dict(command='returnTradeHistory',
                       nonce=int(time.time() * 1000),
                       currencyPair=currency_pair)
        return self.signed_query(self.tradingapi, request)

    def update_keys(self, api: str, secret_key: str, auto_init=False):
        self.api_key = api
        self.secret_key = secret_key
        if auto_init:
            self.connection = self.initialize()
        else:
            self.connection = False

    def withdraw(self, currency: str, address: str) -> dict:
        request = dict(command='withdraw',
                       nonce=int(time.time() * 1000),
                       currency=currency,
                       amount=amount,
                       address=address)
        return self.signed_query(self.tradingapi, request)


class Account:

        def __init__(self, api, secret, exchange: str='Poloniex', auto_init=False):
            if exchange == "Poloniex" or "poloniex:":
                self.exchange = Poloniex(api, secret, auto_init)
            if self.exchange:
                self.balances = self.exchange.balance()
                self.trade_history = self.exchange.trade_history
                self.orders = self.exchange.openorders()


class CurrencyPair:
    def __init__(self, base, target, **kwargs):
        self.base_ticker = base
        self.target_ticker = target
