import json
import logging
import os
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv

logs_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'logs',
)
os.makedirs(logs_path, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_path, 'utils.log'), encoding='utf-8', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f'Вызов функции {func.__name__}')
        try:
            result = func(*args, **kwargs)
            logger.info(f'Функция {func.__name__} успешно завершилась')
            return result
        except Exception as err:
            logger.error(f"Ошибка в функции {func.__name__}: {str(err)}")
    return wrapper


@log_function
def greeting() -> str | None:
    """Функция возвращает приветствие в зависимости от текущего времени пользователя"""

    cur_hour = datetime.now().hour

    greet_message = ['Доброй ночи', 'Доброго утра', 'Доброго дня', 'Доброго вечера']
    time_of_day = cur_hour // 6
    return greet_message[time_of_day]


@log_function
def read_user_setting(setting: str) -> List[str] | None:
    """Функция считывает настройки пользователя из файла ../data/user_setting.json"""

    user_setting_config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
    )
    user_setting_config = os.path.join(user_setting_config_path, 'user_setting.json')

    try:
        logger.info(f'Чтение пользовательских настроек: {setting}')
        with open(user_setting_config, 'r', encoding='utf-8') as user_setting:
            data = json.load(user_setting)
            if setting == 'user_currencies':
                result = data.get('user_currencies')
                logger.info(f'Валюта пользователя: {result}')
                return result
            elif setting == 'user_stocks':
                result = data.get('user_stocks')
                logger.info(f'Акции пользователя: {result}')
                return result
            else:
                return None

    except FileNotFoundError:
        logger.error(f"Файл {user_setting_config} не найден")
        raise

    except json.JSONDecodeError:
        logger.error(f"Ошибка при работе с JSON в файле {user_setting_config}")
        raise


@log_function
def read_xlsx(path: str, sheet: int | str) -> List[Dict[str, Any]]:
    """ "Функция читает данные из xlsx файла и возвращает список словарей с транзакциями"""

    try:
        logger.info(f"Начало чтения файла: {path}, лист: {sheet}")
        logger.info(f"Файл существует: {os.path.exists(path)}")

        df = pd.read_excel(
            path, sheet, usecols=['Дата операции', 'Номер карты', 'Сумма платежа', 'Категория', 'Описание']
        )

        logger.info(f"Файл прочитан успешно. Размер данных: {len(df)} строк, {len(df.columns)} колонок")

        df = df.rename(
            columns={
                'Дата операции': 'date',
                'Номер карты': 'card',
                'Сумма платежа': 'amount',
                'Категория': 'category',
                'Описание': 'description',
            }
        )

        logger.info("Колонки переименованы")

        return df.to_dict('records')

    except FileNotFoundError:
        logger.error(f"Файл не найден: {path}")
        logger.error(f"Текущая рабочая директория: {os.getcwd()}")
        raise FileNotFoundError(f"Excel file not found: {path}")

    except Exception as err:
        logger.error(f"Ошибка при чтении Excel файла: {err}")
        logger.error(f"Тип ошибки: {type(err).__name__}")
        raise ValueError(f"Error while reading excel file: {err}")


@log_function
def sorted_by_date(data: List[Dict[str, Any]], date: datetime):
    """ "Функция получает на вход список словарей с транзакциями и возвращает новый отфильтрованный список словарей
    на указанную дату с начала месяца"""

    start_of_month = date.replace(day=1, hour=0, minute=0, second=0)

    filtered_data = list(
        filter(
            lambda x: (
                'date' in x
                and (lambda d: start_of_month <= d <= date if d else False)(
                    datetime.strptime(x['date'], '%d.%m.%Y %H:%M:%S')
                )
            ),
            data,
        )
    )

    return filtered_data


@log_function
def top_five(data: list[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """Функция получает на вход список словарей с транзакциями и возвращает ТОП 5 транзакций по сумме платежа"""

    if not data:
        return None

    result = sorted(data, key=lambda transaction: abs(transaction.get('amount', 0)), reverse=True)[:5]

    return [
        {key: transaction[key] for key in ['date', 'amount', 'category', 'description'] if key in transaction}
        for transaction in result
    ]


@log_function
def exchange_rate(currency: List[str]) -> List[Dict[str, Any]] | None:
    """Функция получает на вход словарь с перечнем валют, по которым надо получить текущий курс и возвращает словарь,
    где ключи - код валюты, а значения - текущий курс"""

    currency_value: Dict[str, Any] = {}

    load_dotenv()
    api_key = os.getenv('API_KEY')

    if not api_key:
        logger.error('API_KEY не найден в переменных окружения')

    for item in currency:
        url = f'https://api.twelvedata.com/currency_conversion?symbol={item}/RUB&amount=100&apikey={api_key}'

        try:
            logger.info(f'Отправка GET-request для {currency} на https://api.twelvedata.com...')
            response = requests.get(url, timeout=10)
            logger.info(f'Запрос выполнен успешно. Код состояния: {response.status_code}')

            if response.status_code != 200:
                logger.error(f'API вернул код состояния: {response.status_code} для валюты {item}')

                continue

            get_convert = response.json()
            logger.info(f'Полученные данные: {get_convert}')

            if 'rate' in get_convert and get_convert['rate'] is not None:
                currency_value[item] = {'price': str(get_convert['rate'])}
                logger.info(f'Успешно извлеченный курс для {item}: {get_convert["rate"]}')
            else:
                logger.warning(f"Не найден курс обмена валюты {item} в ответе: {get_convert}")
                currency_value[item] = {'price': None}

        except requests.exceptions.RequestException as err:
            logger.error(f"При выполнении запроса произошла ошибка: {err}")
            continue

        except (KeyError, ValueError, TypeError) as err:
            logger.error(f"Ошибка при обработке данных для валюты {item}: {err}")
            continue

    return currency_value if currency_value else None


@log_function
def stock_price(data: List[str]) -> List[Dict[str, Any]] | None:
    """Функция получает на вход список акций и возвращает список словарей, где ключи - код акций, а значение -
    стоимость акций"""

    load_dotenv()
    api_key = os.getenv('API_KEY')

    if not api_key:
        logger.error('API_KEY не найден в переменных окружения')

    symbol = ', '.join(data)

    url = f'https://api.twelvedata.com/price?symbol={symbol}&interval=1day&apikey={api_key}'

    try:
        logger.info(f'Отправка GET-request для {symbol} на https://api.twelvedata.com...')
        response = requests.get(url, timeout=10)
        logger.info(f'Запрос выполнен успешно. Код состояния: {response.status_code}')

        if response.status_code != 200:
            logger.error(f'API вернул код состояния: {response.status_code} для валюты {symbol}')
            return None

        get_convert = response.json()
        logger.info(f'Полученные данные: {get_convert}')
        return get_convert if get_convert else None

    except requests.exceptions.RequestException as err:
        logger.error(f"При выполнении запроса произошла ошибка: {err}")
        return None

    except (KeyError, ValueError, TypeError) as err:
        logger.error(f"Ошибка при обработке данных для акций {symbol}: {err}")
        return None


@log_function
def get_expense(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Функция для получения суммы трат по картам"""

    data_frame = pd.DataFrame(data)

    expenses = data_frame[data_frame['amount'] < 0].groupby('card')['amount'].sum().abs().round(2)

    result = []
    for card, total_amount in expenses.items():
        cashback = round(total_amount * 0.01, 2)
        result.append({"last_digits": card[1:], "total_spent": float(total_amount), "cashback": float(cashback)})

    return result
