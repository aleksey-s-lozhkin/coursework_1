import json
import logging
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Union

import pandas as pd
import requests
from dotenv import load_dotenv

logs_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'logs',
)
os.makedirs(logs_path, exist_ok=True)

logger = logging.getLogger('utils')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler(os.path.join(logs_path, 'utils.log'), encoding='utf-8', mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


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
def read_xlsx(path: str, sheet: Union[int, str] = 0) -> List[Dict[str, Any]]:
    """ "Функция читает данные из xlsx файла и возвращает список словарей с транзакциями"""

    try:
        logger.info(f"Начало чтения файла: {path}, лист: {sheet}")
        logger.info(f"Файл существует: {os.path.exists(path)}")

        df = pd.read_excel(
            path,
            sheet_name=sheet,
            usecols=['Дата операции', 'Номер карты', 'Сумма платежа', 'Категория', 'Описание', 'Кэшбэк'],
        )

        logger.info(f"Файл прочитан успешно. Размер данных: {len(df)} строк, {len(df.columns)} колонок")

        df = df.rename(
            columns={
                'Дата операции': 'date',
                'Номер карты': 'card',
                'Сумма платежа': 'amount',
                'Категория': 'category',
                'Описание': 'description',
                'Кэшбэк': 'cashback',
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
def sorted_by_date(data: List[Dict[str, Any]], date: datetime) -> List[Dict[str, Any]]:
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

    formatted_result = []
    for transaction in result:
        formatted_transaction = {}
        for key in ['date', 'amount', 'category', 'description']:
            if key in transaction:
                if key == 'date':
                    formatted_transaction[key] = transaction[key].split()[0]
                else:
                    formatted_transaction[key] = transaction[key]
        formatted_result.append(formatted_transaction)

    return formatted_result


@log_function
def exchange_rate(currency: List[str]) -> List[Dict[str, Any]] | None:
    """Функция получает на вход словарь с перечнем валют, по которым надо получить текущий курс и возвращает словарь,
    где ключи - код валюты, а значения - текущий курс"""

    currency_value: List[Dict[str, Any]] = []

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
                currency_value.append({'currency': item, 'rate': float(get_convert['rate'])})
                logger.info(f'Успешно извлеченный курс для {item}: {get_convert["rate"]}')
            else:
                logger.warning(f"Не найден курс обмена валюты {item} в ответе: {get_convert}")
                currency_value.append({'currency': item, 'rate': None})

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

    stock_prices: List[Dict[str, Any]] = []

    load_dotenv()
    api_key = os.getenv('API_KEY')

    if not api_key:
        logger.error('API_KEY не найден в переменных окружения')
        return None

    if not data:
        logger.warning('Получен пустой список акций')
        return None

    symbol = ','.join(data)

    url = f'https://api.twelvedata.com/price?symbol={symbol}&interval=1day&apikey={api_key}'

    try:
        logger.info(f'Отправка GET-request для {symbol} на https://api.twelvedata.com...')
        response = requests.get(url, timeout=10)
        logger.info(f'Запрос выполнен успешно. Код состояния: {response.status_code}')

        if response.status_code != 200:
            logger.error(f'API вернул код состояния: {response.status_code} для валюты {symbol}')
            return None

        get_convert = response.json()

        for stock_symbol in data:
            if stock_symbol in get_convert:
                stock_data = get_convert[stock_symbol]
                if 'price' in stock_data and stock_data['price'] is not None:
                    try:
                        stock_prices.append({'stock': stock_symbol, 'price': float(stock_data['price'])})
                        logger.info(f'Успешно извлечена цена для {stock_symbol}: {stock_data["price"]}')
                    except (ValueError, TypeError) as e:
                        logger.error(f"Ошибка преобразования цены для {stock_symbol}: {stock_data['price']} - {e}")
                        stock_prices.append({'stock': stock_symbol, 'price': None})
                else:
                    logger.warning(f"Не найдена цена акции {stock_symbol} в ответе: {stock_data}")
                    stock_prices.append({'stock': stock_symbol, 'price': None})
            else:
                logger.warning(f"Акция {stock_symbol} не найдена в ответе API")
                stock_prices.append({'stock': stock_symbol, 'price': None})

        return stock_prices if stock_prices else None

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


@log_function
def sorted_by_range(data: List[Dict[str, Any]], date: datetime, date_range: str = 'M') -> List[Dict[str, Any]] | None:
    """ "Функция получает на вход список словарей с транзакциями и возвращает новый отфильтрованный список словарей
    на указанную дату с начала M - месяца, Y - года, ALL - все данные до указанной даты, W - недели"""

    if date_range == 'M':
        start_of_range = date.replace(day=1, hour=0, minute=0, second=0)

    elif date_range == 'Y':
        start_of_range = date.replace(day=1, month=1, hour=0, minute=0, second=0)

    elif date_range == 'ALL':
        start_of_range = datetime.min

    elif date_range == 'W':
        monday_number = (date - timedelta(days=date.weekday())).day
        start_of_range = date.replace(day=monday_number, hour=0, minute=0, second=0)

    else:
        logger.error(f'Ошибка при обработке временного диапазона "{date_range}"')
        raise ValueError

    logger.debug(f'range from {start_of_range} to {date}')

    filtered_data = list(
        filter(
            lambda x: (
                'date' in x
                and (lambda d: start_of_range <= d <= date if d else False)(
                    datetime.strptime(x['date'], '%d.%m.%Y %H:%M:%S')
                )
            ),
            data,
        )
    )

    logger.debug(filtered_data)
    return filtered_data


@log_function
def get_expense_by_category(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """Функция возвращает отсортированный список по категориям"""

    if not data:
        return None

    df = pd.DataFrame(data)

    expenses = df[df['amount'] < 0].groupby('category')['amount'].sum().round(0).sort_values(ascending=False)

    return [{"category": category, "amount": int(total_amount)} for category, total_amount in expenses.items()]


@log_function
def get_top_seven_category(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """ """

    if not data:
        return None

    df = pd.DataFrame(data)

    exclude_values = ['Переводы', 'Бонусы', 'Наличные', 'Пополнения']

    result_df = (
        df[(~df['category'].isin(exclude_values)) & (df['amount'] < 0)]
        .sort_values('amount', ascending=True)  # ascending=True для отрицательных чисел
        .head(7)
    )

    result = [{**record, 'amount': abs(record['amount'])} for record in result_df.to_dict('records')]

    logger.debug(result)
    return result


@log_function
def get_other_category(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """Получить категории кроме исключенных, пропуская первые 7 наибольших по модулю"""

    if not data:
        return None

    df = pd.DataFrame(data)

    exclude_values = ['Переводы', 'Бонусы', 'Наличные', 'Пополнения']

    result_df = (
        df[~df['category'].isin(exclude_values) & (df['amount'] < 0)].sort_values('amount', ascending=True).iloc[7:]
    )

    total_amount = result_df['amount'].abs().sum()

    result = [{"category": "Остальное", "amount": int(total_amount)}]

    logger.debug(result)
    return result


@log_function
def get_transfer_and_cash(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """ """

    if not data:
        return None

    df = pd.DataFrame(data)

    include_values = ['Переводы', 'Наличные']

    mask = df['category'].str.contains('|'.join(include_values), case=False, na=False)

    logger.debug(f"Найдено категорий по маске: {df[mask]['category'].unique().tolist()}")
    logger.debug(f"Отрицательные суммы: {df[df['amount'] < 0].shape[0]} транзакций")

    filtered_df = df[mask & (df['amount'] < 0)].copy()

    logger.debug(f"После фильтрации: {filtered_df.shape[0]} транзакций")

    result_series = filtered_df.groupby('category')['amount'].sum().abs().round(0).sort_values(ascending=False)

    result = [{'category': category, 'amount': int(amount)} for category, amount in result_series.items()]

    logger.debug(result)
    return result


@log_function
def get_income(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """ """

    if not data:
        return None

    df = pd.DataFrame(data)

    result_series = df[(df['amount'] > 0)].groupby('description')['amount'].sum().round(0).sort_values(ascending=False)

    result = [{'category': description, 'amount': int(amount)} for description, amount in result_series.items()]

    logger.debug(result)
    return result


@log_function
def get_total_amount(data: List[Dict[str, Any]]) -> int | None:
    """ """

    if not data:
        return None

    df = pd.DataFrame(data)

    total_expense = df[df['amount'] < 0]['amount'].sum().round(0)

    result = int(abs(total_expense))

    logger.debug(result)
    return result


@log_function
def get_total_amount_income(data: List[Dict[str, Any]]) -> int | None:
    """ """

    if not data:
        return None

    df = pd.DataFrame(data)

    total_expense = df[df['amount'] > 0]['amount'].sum().round(0)

    result = int(abs(total_expense))

    logger.debug(result)
    return result


def get_cashback(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """ """

    if not data:
        return None

    df = pd.DataFrame(data)

    cashback = df['cashback'].sum().round(0)

    cashback_value = int(abs(cashback))

    logger.debug(cashback_value)
    result_dict = [{"category": "Кэшбэк", "amount": cashback_value}]
    return result_dict
