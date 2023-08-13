"""
Module that gets and converts currency rates
Referenced from https://github.com/MicroPyramid/forex-python/blob/master/forex_python/converter.py
"""
import os
from decimal import Decimal

import requests
import simplejson as json

from dotenv import load_dotenv
load_dotenv()

class RatesNotAvailableError(Exception):
    """
    Custom exception when https://www.exchangerate-api.com/
    is down and not available for currency rates
    """


class DecimalFloatMismatchError(Exception):
    """
    A float has been supplied when force_decimal was set to True
    """

class APIKeyNotFoundError(Exception):
    """
    API Key not found
    """

class Common:
    """Base class with common functions"""

    def __init__(self, force_decimal=False):
        self._force_decimal = force_decimal
        self._api_key = os.getenv("EXCHANGE_RATE_API_KEY")

        if self._api_key is None:
            raise APIKeyNotFoundError("API Key not found")

    def _source_url(self):
        return f"https://v6.exchangerate-api.com/v6/{self._api_key}"

    def _get_date_string(self, date_obj):
        if date_obj is None:
            return 'latest'
        date_str = date_obj.strftime('%Y-%m-%d')
        return date_str

    def _get_decoded_data(self, response, key, use_decimal=False):
        if self._force_decimal or use_decimal:
            decoded_data = json.loads(response.text, use_decimal=True)
        else:
            decoded_data = response.json()

        return decoded_data.get(key, {})


class CurrencyRates(Common):
    """Class that gets and responds currency rates"""

    def get_rates(self, base_cur):
        """Gets conversion rates from base_cur to all other currencies"""
        source_url = f"{self._source_url()}/latest/{base_cur}"
        response = requests.get(source_url, timeout=5)

        if response.status_code == 200:
            rates = self._get_decoded_data(response, "conversion_rates")
            return rates

        raise RatesNotAvailableError("Currency Rates Source Not Ready")


    def get_rate(self, base_cur, dest_cur):
        """Gets conversion rate from base_cur to dest_cur"""
        if base_cur == dest_cur:
            if self._force_decimal:
                return Decimal(1)
            return 1.

        source_url = f"{self._source_url()}/pair/{base_cur}/{dest_cur}"

        response = requests.get(source_url, timeout=5)

        if response.status_code == 200:
            rate = self._get_decoded_data(response, "conversion_rate")
            if not rate:
                raise RatesNotAvailableError(f"Currency Rate {base_cur} => {dest_cur} not available")
            return rate
        raise RatesNotAvailableError("Currency Rates Source Not Ready")


    def convert(self, base_cur, dest_cur, amount):
        """Converts base currency to destination currency"""
        if isinstance(amount, Decimal):
            use_decimal = True
        else:
            use_decimal = self._force_decimal

        if base_cur == dest_cur:  # Return same amount if both base_cur, dest_cur are same
            if use_decimal:
                return Decimal(amount)
            return float(amount)

        source_url = f"{self._source_url()}/pair/{base_cur}/{dest_cur}"

        response = requests.get(source_url, timeout=5)

        if response.status_code == 200:
            rate = self._get_decoded_data(response, "conversion_rate", use_decimal=use_decimal)
            if not rate:
                raise RatesNotAvailableError(f"Currency {base_cur} => {dest_cur} rate not available.")
            try:
                converted_amount = rate * amount
                return converted_amount
            except TypeError as t_e:
                raise DecimalFloatMismatchError(
                    "convert requires amount parameter is of type Decimal when force_decimal=True") \
                    from t_e

        raise RatesNotAvailableError("Currency Rates Source Not Ready")


_CURRENCY_FORMATTER = CurrencyRates()

get_rates = _CURRENCY_FORMATTER.get_rates
get_rate = _CURRENCY_FORMATTER.get_rate
convert = _CURRENCY_FORMATTER.convert


class CurrencyCodes:
    """Class that reads and returns currency codes"""
    def __init__(self):
        self.__currency_data = None

    @property
    def _currency_data(self):
        if self.__currency_data is None:
            file_path = os.path.dirname(os.path.abspath(__file__))
            with open(file_path + '/raw_data/currencies.json', encoding="utf-8") as f:
                self.__currency_data = json.loads(f.read())
        return self.__currency_data

    def _get_data(self, currency_code):
        currency_dict = next((item for item in self._currency_data \
                              if item["cc"] == currency_code), None)
        return currency_dict

    def _get_data_from_symbol(self, symbol):
        currency_dict = next((item for item in self._currency_data if item["symbol"] == symbol), None)
        return currency_dict

    def get_symbol(self, currency_code):
        """Gets symbol from currency code"""
        currency_dict = self._get_data(currency_code)
        if currency_dict:
            return currency_dict.get('symbol')
        return None

    def get_currency_name(self, currency_code):
        """Gets name from currency code"""
        currency_dict = self._get_data(currency_code)
        if currency_dict:
            return currency_dict.get('name')
        return None

    def get_currency_code_from_symbol(self, symbol):
        """Gets currency code from symbol"""
        currency_dict = self._get_data_from_symbol(symbol)
        if currency_dict:
            return currency_dict.get('cc')
        return None


_CURRENCY_CODES = CurrencyCodes()

get_symbol = _CURRENCY_CODES.get_symbol
get_currency_name = _CURRENCY_CODES.get_currency_name
get_currency_code_from_symbol = _CURRENCY_CODES.get_currency_code_from_symbol
