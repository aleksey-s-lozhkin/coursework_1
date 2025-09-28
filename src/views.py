import json
import os
import requests
import logging
from datetime import datetime
from typing import Any, Dict, List
from dotenv import load_dotenv


def greeting() -> str | None:
    """Функция возвращает приветствие в зависимости от текущего времени пользователя"""

    cur_hour = datetime.now().hour

    greet_message = ['Доброй ночи', 'Доброго утра', 'Доброго дня', 'Доброго вечера']
    time_of_day = cur_hour // 6
    return greet_message[time_of_day]


def read_user_setting(setting: str) -> List[str] | None:
    """Функция считывает настройки пользователя из файла ../data/user_setting.json"""

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    user_setting_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    user_setting_config = os.path.join(user_setting_config_path, 'user_setting.json')

    try:
        logger.info(f'Reading user settings for: {setting}')
        with open(user_setting_config, 'r', encoding='utf-8') as user_setting:
            data = json.load(user_setting)
            if setting == 'user_currencies':
                result = data.get('user_currencies')
                logger.info(f'User currency: {result}')
                return result
            elif setting == 'user_stocks':
                result = data.get('user_stocks')
                logger.info(f'User stock: {result}')
                return result
            else:
                return None

    except FileNotFoundError:
        print(f"File {user_setting_config} not found")
        raise

    except json.JSONDecodeError:
        print(f"Error parsing JSON in a file {user_setting_config}")
        raise


def exchange_rate(currency: List[str]) -> List[Dict[str, Any]] | None:
    """Функция получает на вход словарь с перечнем валют, по которым надо получить текущий курс и возвращает словарь,
    где ключи - код валюты, а значения - текущий курс"""

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    currency_value: Dict[str, Any] = {}

    load_dotenv()
    api_key = os.getenv('API_KEY')

    if not api_key:
        logger.error('API_KEY not found in environment variables')

    for item in currency:
        url = f'https://api.twelvedata.com/currency_conversion?symbol={item}/RUB&amount=100&apikey={api_key}'

        try:
            logger.info(f'Send GET-request for {currency} to https://api.twelvedata.com...')
            response = requests.get(url, timeout=10)
            logger.info(f'Request is successful. Status code: {response.status_code}')

            if response.status_code != 200:
                logger.error(f'API returned status code: {response.status_code} for currency {item}')

                continue

            get_convert = response.json()
            logger.info(f'Received data: {get_convert}')

            if 'rate' in get_convert and get_convert['rate'] is not None:
                currency_value[item] = {'price':str(get_convert['rate'])}
                logger.info(f'Successfully extracted rate for {item}: {get_convert["rate"]}')
            else:
                logger.warning(f"No rate found for currency {item} in response: {get_convert}")
                currency_value[item] = {'price': None}

        except requests.exceptions.RequestException as err:
            logger.error(f"An error occurred when executing the request: {err}")
            continue

        except (KeyError, ValueError, TypeError) as err:
            logger.error(f"Error processing data for currency {item}: {err}")
            continue

    return currency_value if currency_value else None


def top_five(data: list[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Функция получает на вход список словарей с транзакциями и возвращает ТОП 5 транзакций по сумме платежа"""

    pass


def stock_price(data: List[str]) -> List[Dict[str, Any]] | None:
    """Функция получает на вход список акций и возвращает список словарей, где ключи - код акций, а значение -
    стоимость акций"""

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    load_dotenv()
    api_key = os.getenv('API_KEY')

    if not api_key:
        logger.error('API_KEY not found in environment variables')

    symbol = ', '.join(data)

    url = f'https://api.twelvedata.com/price?symbol={symbol}&interval=1day&apikey={api_key}'

    try:
        logger.info(f'Send GET-request for {symbol} to https://api.twelvedata.com...')
        response = requests.get(url, timeout=10)
        logger.info(f'Request is successful. Status code: {response.status_code}')

        if response.status_code != 200:
            logger.error(f'API returned status code: {response.status_code} for currency {symbol}')
            return None

        get_convert = response.json()
        logger.info(f'Received data: {get_convert}')
        return get_convert if get_convert else None

    except requests.exceptions.RequestException as err:
        logger.error(f"An error occurred when executing the request: {err}")
        return None

    except (KeyError, ValueError, TypeError) as err:
        logger.error(f"Error processing data for stocks {symbol}: {err}")
        return None


def general(data: List[Dict[str, Any]], date: str) -> json:
    pass
