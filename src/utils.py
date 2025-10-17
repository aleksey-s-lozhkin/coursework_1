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
            raise

    return wrapper


@log_function
def greeting() -> str | None:
    """Функция возвращает приветствие в зависимости от текущего времени пользователя"""

    # Получаем текущее время
    cur_hour = datetime.now().hour

    # Создаем список приветствий
    greet_message = ['Доброй ночи', 'Доброго утра', 'Доброго дня', 'Доброго вечера']

    # В зависимости от времени выбираем из списка
    time_of_day = cur_hour // 6

    return greet_message[time_of_day]


@log_function
def read_user_setting(setting: str) -> List[str] | None:
    """Функция считывает настройки пользователя из файла ../data/user_setting.json"""

    # Формируем путь к директории с настройками (папка data на уровень выше)
    user_setting_config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
    )
    # Формируем полный путь к файлу настроек
    user_setting_config = os.path.join(user_setting_config_path, 'user_setting.json')

    try:
        # Логируем попытку чтения настроек
        logger.info(f'Чтение пользовательских настроек: {setting}')

        # Открываем и читаем JSON файл с настройками
        with open(user_setting_config, 'r', encoding='utf-8') as user_setting:
            data: Dict[str, Any] = json.load(user_setting)

            # Возвращаем соответствующие настройки в зависимости от запроса
            if setting == 'user_currencies':
                result = data.get('user_currencies')
                if isinstance(result, list) and all(isinstance(item, str) for item in result):
                    logger.info(f'Валюта пользователя: {result}')
                    return result
                else:
                    logger.error(f"user_currencies не является списком строк: {type(result)}")
                    return None
            elif setting == 'user_stocks':
                result = data.get('user_stocks')
                if isinstance(result, list) and all(isinstance(item, str) for item in result):
                    logger.info(f'Акции пользователя: {result}')
                    return result
                else:
                    logger.error(f"user_stocks не является списком строк: {type(result)}")
                    return None
            else:
                # Возвращаем None для неизвестных настроек
                return None

    # Обрабатываем случай отсутствия файла
    except FileNotFoundError:
        logger.error(f"Файл {user_setting_config} не найден")
        raise

    # Обрабатываем ошибки формата JSON
    except json.JSONDecodeError:
        logger.error(f"Ошибка при работе с JSON в файле {user_setting_config}")
        raise


@log_function
def read_xlsx(path: str, sheet: Union[int, str] = 0) -> List[Dict[str, Any]]:
    """ "Функция читает данные из xlsx файла и возвращает список словарей с транзакциями"""

    try:
        # Логируем начало чтения файла и проверяем его существование
        logger.info(f"Начало чтения файла: {path}, лист: {sheet}")
        logger.info(f"Файл существует: {os.path.exists(path)}")

        # Читаем Excel файл, выбирая только нужные колонки
        df = pd.read_excel(
            path,
            sheet_name=sheet,
            usecols=['Дата операции', 'Номер карты', 'Сумма платежа', 'Категория', 'Описание', 'Кэшбэк'],
        )

        # Логируем успешное чтение и размер данных
        logger.info(f"Файл прочитан успешно. Размер данных: {len(df)} строк, {len(df.columns)} колонок")

        # Переименовываем колонки с русского на английский для удобства обработки
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

        # Конвертируем DataFrame в список словарей и возвращаем
        records = df.to_dict('records')
        # Преобразуем каждый словарь, чтобы ключи были строками
        result = []
        for record in records:
            new_record = {}
            for key, value in record.items():
                new_record[str(key)] = value
            result.append(new_record)
        return result

    # Обрабатываем случай отсутствия файла
    except FileNotFoundError:
        logger.error(f"Файл не найден: {path}")
        logger.error(f"Текущая рабочая директория: {os.getcwd()}")
        raise FileNotFoundError(f"Excel file not found: {path}")

    # Обрабатываем все остальные ошибки
    except Exception as err:
        logger.error(f"Ошибка при чтении Excel файла: {err}")
        logger.error(f"Тип ошибки: {type(err).__name__}")
        raise ValueError(f"Error while reading excel file: {err}")


@log_function
def sorted_by_date(data: List[Dict[str, Any]], date: datetime) -> List[Dict[str, Any]]:
    """ "Функция получает на вход список словарей с транзакциями и возвращает новый отфильтрованный список словарей
    на указанную дату с начала месяца"""

    # Вычисляем начало месяца от переданной даты (первый день в 00:00:00)
    start_of_month = date.replace(day=1, hour=0, minute=0, second=0)

    # Фильтруем данные: оставляем транзакции в диапазоне [начало месяца, переданная дата]
    filtered_data: List[Dict[str, Any]] = [
        transaction
        for transaction in data
        if 'date' in transaction
        and (lambda d: start_of_month <= d <= date if d else False)(
            datetime.strptime(transaction['date'], '%d.%m.%Y %H:%M:%S')
        )
    ]

    # Возвращаем отфильтрованный список транзакций
    return filtered_data


@log_function
def top_five(data: list[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """Функция получает на вход список словарей с транзакциями и возвращает ТОП 5 транзакций по сумме платежа"""

    # Проверяем, что входные данные не пустые
    if not data:
        return None

    # Сортируем транзакции по абсолютному значению суммы (по убыванию) и берем топ-5
    result = sorted(data, key=lambda transaction: abs(transaction.get('amount', 0)), reverse=True)[:5]

    # Форматируем результат для вывода
    formatted_result = []
    for transaction in result:
        formatted_transaction = {}
        # Для каждой транзакции оставляем только нужные поля
        for key in ['date', 'amount', 'category', 'description']:
            if key in transaction:
                if key == 'date':
                    # Для даты оставляем только часть до пробела (убираем время)
                    formatted_transaction[key] = transaction[key].split()[0]
                else:
                    # Для остальных полей копируем как есть
                    formatted_transaction[key] = transaction[key]
        formatted_result.append(formatted_transaction)

    # Возвращаем отформатированный список топ-5 транзакций
    return formatted_result


@log_function
def exchange_rate(currency: List[str]) -> List[Dict[str, Any]] | None:
    """Функция получает на вход словарь с перечнем валют, по которым надо получить текущий курс и возвращает словарь,
    где ключи - код валюты, а значения - текущий курс"""

    # Инициализируем список для хранения результатов
    currency_value: List[Dict[str, Any]] = []

    # Загружаем переменные окружения из .env файла
    load_dotenv()
    # Получаем API ключ из переменных окружения
    api_key = os.getenv('API_KEY')

    # Проверяем наличие API ключа
    if not api_key:
        logger.error('API_KEY не найден в переменных окружения')

    # Обрабатываем каждую валюту из списка
    for item in currency:
        # Формируем URL для запроса конвертации в рубли
        url = f'https://api.twelvedata.com/currency_conversion?symbol={item}/RUB&amount=100&apikey={api_key}'

        try:
            # Логируем начало запроса к API
            logger.info(f'Отправка GET-request для {currency} на https://api.twelvedata.com...')
            # Выполняем HTTP-запрос с таймаутом 10 секунд
            response = requests.get(url, timeout=10)
            logger.info(f'Запрос выполнен успешно. Код состояния: {response.status_code}')

            # Проверяем успешность HTTP-запроса
            if response.status_code != 200:
                logger.error(f'API вернул код состояния: {response.status_code} для валюты {item}')
                continue

            # Парсим JSON ответ от API
            get_convert = response.json()
            logger.info(f'Полученные данные: {get_convert}')

            # Проверяем наличие и валидность курса в ответе
            if 'rate' in get_convert and get_convert['rate'] is not None:
                # Добавляем валюту и курс в результат
                currency_value.append({'currency': item, 'rate': float(get_convert['rate'])})
                logger.info(f'Успешно извлеченный курс для {item}: {get_convert["rate"]}')
            else:
                # Логируем отсутствие курса в ответе
                logger.warning(f"Не найден курс обмена валюты {item} в ответе: {get_convert}")
                currency_value.append({'currency': item, 'rate': None})

        # Обрабатываем ошибки сетевого запроса
        except requests.exceptions.RequestException as err:
            logger.error(f"При выполнении запроса произошла ошибка: {err}")
            continue

        # Обрабатываем ошибки обработки данных
        except (KeyError, ValueError, TypeError) as err:
            logger.error(f"Ошибка при обработке данных для валюты {item}: {err}")
            continue

    # Возвращаем результат или None если список пустой
    return currency_value if currency_value else None


@log_function
def stock_price(data: List[str]) -> List[Dict[str, Any]] | None:
    """Функция получает на вход список акций и возвращает список словарей, где ключи - код акций, а значение -
    стоимость акций"""

    # Инициализируем список для хранения цен акций
    stock_prices: List[Dict[str, Any]] = []

    # Загружаем переменные окружения и получаем API ключ
    load_dotenv()
    api_key = os.getenv('API_KEY')

    # Проверяем наличие API ключа
    if not api_key:
        logger.error('API_KEY не найден в переменных окружения')
        return None

    # Проверяем, что передан непустой список акций
    if not data:
        logger.warning('Получен пустой список акций')
        return None

    # Объединяем коды акций в строку через запятую для API запроса
    symbol = ','.join(data)

    # Формируем URL для запроса цен акций
    url = f'https://api.twelvedata.com/price?symbol={symbol}&interval=1day&apikey={api_key}'

    try:
        # Логируем и выполняем HTTP-запрос к API
        logger.info(f'Отправка GET-request для {symbol} на https://api.twelvedata.com...')
        response = requests.get(url, timeout=10)
        logger.info(f'Запрос выполнен успешно. Код состояния: {response.status_code}')

        # Проверяем успешность HTTP-запроса
        if response.status_code != 200:
            logger.error(f'API вернул код состояния: {response.status_code} для валюты {symbol}')
            return None

        # Парсим JSON ответ от API
        get_convert = response.json()

        # Обрабатываем данные для каждой акции из исходного списка
        for stock_symbol in data:
            if stock_symbol in get_convert:
                stock_data = get_convert[stock_symbol]
                # Проверяем наличие и валидность цены в ответе
                if 'price' in stock_data and stock_data['price'] is not None:
                    try:
                        # Преобразуем цену в float и добавляем в результат
                        stock_prices.append({'stock': stock_symbol, 'price': float(stock_data['price'])})
                        logger.info(f'Успешно извлечена цена для {stock_symbol}: {stock_data["price"]}')
                    except (ValueError, TypeError) as e:
                        # Обрабатываем ошибки преобразования типа
                        logger.error(f"Ошибка преобразования цены для {stock_symbol}: {stock_data['price']} - {e}")
                        stock_prices.append({'stock': stock_symbol, 'price': None})
                else:
                    # Логируем отсутствие цены в ответе API
                    logger.warning(f"Не найдена цена акции {stock_symbol} в ответе: {stock_data}")
                    stock_prices.append({'stock': stock_symbol, 'price': None})
            else:
                # Логируем отсутствие акции в ответе API
                logger.warning(f"Акция {stock_symbol} не найдена в ответе API")
                stock_prices.append({'stock': stock_symbol, 'price': None})

        # Возвращаем результат или None если список пустой
        return stock_prices if stock_prices else None

    # Обрабатываем ошибки сетевого запроса
    except requests.exceptions.RequestException as err:
        logger.error(f"При выполнении запроса произошла ошибка: {err}")
        return None

    # Обрабатываем ошибки обработки данных
    except (KeyError, ValueError, TypeError) as err:
        logger.error(f"Ошибка при обработке данных для акций {symbol}: {err}")
        return None


@log_function
def get_expense(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Функция для получения суммы трат по картам"""

    # Создаем DataFrame из списка транзакций
    data_frame = pd.DataFrame(data)

    # Проверяем, что DataFrame не пустой и содержит необходимые колонки
    if data_frame.empty or 'amount' not in data_frame.columns or 'card' not in data_frame.columns:
        return []

    # Фильтруем траты (отрицательные суммы), группируем по карте и вычисляем сумму
    expenses = data_frame[data_frame['amount'] < 0].groupby('card')['amount'].sum().abs().round(2)

    # Формируем результат в нужном формате
    result: List[Dict[str, Any]] = []
    for card, total_amount in expenses.items():
        # Вычисляем кэшбэк 1% от суммы трат
        cashback = round(total_amount * 0.01, 2)
        # Добавляем информацию по карте (последние цифры, сумма трат, кэшбэк)
        result.append({"last_digits": str(card)[1:], "total_spent": float(total_amount), "cashback": float(cashback)})

    return result


@log_function
def sorted_by_range(data: List[Dict[str, Any]], date: datetime, date_range: str = 'M') -> List[Dict[str, Any]] | None:
    """ "Функция получает на вход список словарей с транзакциями и возвращает новый отфильтрованный список словарей
    на указанную дату с начала M - месяца, Y - года, ALL - все данные до указанной даты, W - недели"""

    # Определяем начальную дату диапазона в зависимости от параметра date_range
    if date_range == 'M':
        # Для месяца: начало месяца (первый день)
        start_of_range = date.replace(day=1, hour=0, minute=0, second=0)

    elif date_range == 'Y':
        # Для года: начало года (1 января)
        start_of_range = date.replace(day=1, month=1, hour=0, minute=0, second=0)

    elif date_range == 'ALL':
        # Для всего периода: минимальная дата (все данные до указанной даты)
        start_of_range = datetime.min

    elif date_range == 'W':
        # Для недели: понедельник текущей недели
        monday_number = (date - timedelta(days=date.weekday())).day
        start_of_range = date.replace(day=monday_number, hour=0, minute=0, second=0)

    else:
        # Обработка неизвестного диапазона
        logger.error(f'Ошибка при обработке временного диапазона "{date_range}"')
        raise ValueError

    # Логируем вычисленный диапазон дат
    logger.debug(f'Диапазон от {start_of_range} до {date}')

    # Фильтруем данные: оставляем транзакции в диапазоне [start_of_range, date]
    filtered_data: List[Dict[str, Any]] = [
        transaction
        for transaction in data
        if 'date' in transaction
        and (lambda d: start_of_range <= d <= date if d else False)(
            datetime.strptime(transaction['date'], '%d.%m.%Y %H:%M:%S')
        )
    ]

    # Логируем отфильтрованные данные и возвращаем результат
    logger.debug(f'Получено {filtered_data} транзакций')
    return filtered_data


@log_function
def get_expense_by_category(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """Функция возвращает отсортированный список по категориям"""

    # Проверка на пустые входные данные
    if not data:
        return None

    # Создание DataFrame из списка транзакций
    df = pd.DataFrame(data)

    # Фильтрация расходов (отрицательные суммы), группировка по категориям,
    # суммирование, округление и сортировка по убыванию
    expenses = df[df['amount'] < 0].groupby('category')['amount'].sum().round(0).sort_values(ascending=False)

    # Преобразование результата в список словарей с категориями и суммами
    result = []
    for category, total_amount in expenses.items():
        result.append({"category": str(category), "amount": int(total_amount)})
    return result


@log_function
def get_top_seven_category(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """Возвращает топ-7 категорий с наибольшими расходами, исключая служебные категории"""

    # Проверка на пустые входные данные
    if not data:
        return None

    # Создание DataFrame из списка транзакций
    df = pd.DataFrame(data)

    # Категории для исключения из топа (служебные операции)
    exclude_values = ['Переводы', 'Бонусы', 'Наличные', 'Пополнения']

    # Фильтрация и сортировка данных:
    # - Исключаем служебные категории, оставляем только расходы (отрицательные суммы), сортируем по сумме
    # (ascending=True для отрицательных чисел = наибольшие траты первыми), берем первые 7 записей
    result_df = (
        df[(~df['category'].isin(exclude_values)) & (df['amount'] < 0)]
        .sort_values('amount', ascending=True)  # ascending=True для отрицательных чисел
        .head(7)
    )

    # Преобразуем в список словарей и обрабатываем каждый элемент
    records = result_df.to_dict('records')
    result = []
    for record in records:
        formatted_record: Dict[str, Any] = {}
        for key, value in record.items():
            formatted_record[str(key)] = value
        formatted_record['amount'] = abs(formatted_record['amount'])
        result.append(formatted_record)

    # Логируем результат для отладки
    logger.debug(result)
    return result


@log_function
def get_other_category(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """Функция получает категории кроме исключенных, пропуская первые 7 наибольших по модулю"""

    # Проверка на пустые входные данные
    if not data:
        return None

    # Создание DataFrame из списка транзакций
    df = pd.DataFrame(data)

    # Категории для исключения (служебные операции)
    exclude_values = ['Переводы', 'Бонусы', 'Наличные', 'Пополнения']

    # Получаем все категории расходов, кроме исключенных, сортируем по убыванию суммы
    # и пропускаем первые 7 (топ-7) - берем все остальные начиная с 8-й позиции
    result_df = (
        df[~df['category'].isin(exclude_values) & (df['amount'] < 0)].sort_values('amount', ascending=True).iloc[7:]
    )

    # Суммируем абсолютные значения всех оставшихся расходов
    total_amount = result_df['amount'].abs().sum()

    # Создаем одну запись "Остальное" с общей суммой
    result = [{"category": "Остальное", "amount": int(total_amount)}]

    # Логируем результат для отладки
    logger.debug(result)
    return result


@log_function
def get_transfer_and_cash(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """Функция возвращает сумму расходов по категориям Переводы и Наличные"""

    # Проверка на пустые входные данные
    if not data:
        return None

    # Создание DataFrame из списка транзакций
    df = pd.DataFrame(data)

    # Категории для включения в результат
    include_values = ['Переводы', 'Наличные']

    # Создание маски для фильтрации по категориям (регистронезависимый поиск)
    mask = df['category'].str.contains('|'.join(include_values), case=False, na=False)

    # Логирование для отладки - найденные категории и количество отрицательных транзакций
    logger.debug(f"Найдено категорий по маске: {df[mask]['category'].unique().tolist()}")
    logger.debug(f"Отрицательные суммы: {df[df['amount'] < 0].shape[0]} транзакций")

    # Фильтрация данных: только выбранные категории и только расходы
    filtered_df = df[mask & (df['amount'] < 0)].copy()

    # Логирование количества оставшихся транзакций после фильтрации
    logger.debug(f"После фильтрации: {filtered_df.shape[0]} транзакций")

    # Группировка по категориям, суммирование, преобразование в абсолютные значения и округление
    result_series = filtered_df.groupby('category')['amount'].sum().abs().round(0).sort_values(ascending=False)

    # Преобразование результата в список словарей
    result = []
    for category, amount in result_series.items():
        result.append({'category': str(category), 'amount': int(amount)})

    # Логирование финального результата
    logger.debug(result)
    return result


@log_function
def get_income(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """Возвращает сумму доходов, сгруппированную по описанию операций"""

    # Проверка на пустые входные данные
    if not data:
        return None

    # Создание DataFrame из списка транзакций
    df = pd.DataFrame(data)

    # Фильтрация доходов (положительные суммы), группировка по описанию,
    # суммирование, округление и сортировка по убыванию
    result_series = df[(df['amount'] > 0)].groupby('description')['amount'].sum().round(0).sort_values(ascending=False)

    # Преобразование результата в список словарей с описанием и суммой дохода
    result = []
    for description, amount in result_series.items():
        result.append({'category': str(description), 'amount': int(amount)})

    # Логирование результата для отладки
    logger.debug(result)
    return result


@log_function
def get_total_amount(data: List[Dict[str, Any]]) -> int:
    """Вычисляет общую сумму расходов из списка транзакций"""

    # Проверка на пустые входные данные
    if not data:
        return 0

    try:
        # Создание DataFrame из списка транзакций
        df = pd.DataFrame(data)

        # Проверяем наличие необходимых колонок
        if 'amount' not in df.columns:
            logger.warning("Column 'amount' not found in data")
            return 0

        # Фильтрация расходов (отрицательные суммы) и вычисление общей суммы
        expense_df = df[df['amount'] < 0]
        if expense_df.empty:
            return 0

        total_expense = expense_df['amount'].sum().round(0)

        # Преобразование отрицательной суммы в положительное целое число
        result = int(abs(float(total_expense)))

        # Логирование результата для отладки
        logger.debug(f"Total expense calculated: {result}")
        return result

    except Exception as e:
        logger.error(f"Error calculating total amount: {e}")
        return 0


@log_function
def get_total_amount_income(data: List[Dict[str, Any]] | None) -> int:
    """Вычисляет общую сумму доходов из списка категорий доходов"""

    # Обработка случая, когда data равно None или пустой список
    if not data:
        return 0

    try:
        # Суммируем все amount из словарей
        total_income: int = sum(item['amount'] for item in data)

        # Логирование результата для отладки
        logger.debug(f"Total income calculated: {total_income}")
        return total_income

    except Exception as e:
        logger.error(f"Error calculating total income: {e}")
        return 0


@log_function
def get_cashback(data: List[Dict[str, Any]]) -> List[Dict[str, Any]] | None:
    """Возвращает сумму кэшбэка по операциям"""

    # Проверка на пустые входные данные
    if not data:
        return None

    # Создание DataFrame из списка транзакций
    df = pd.DataFrame(data)

    # Суммируем колонку 'cashback' (кэшбэк по операциям)
    total_cashback = df['cashback'].sum().round(0)

    # Преобразуем в целое число
    total_cashback = int(total_cashback)

    # Возвращаем в формате списка словарей с категорией "Кэшбэк"
    result = [{"category": "Кэшбэк", "amount": total_cashback}]

    # Логирование результата для отладки
    logger.debug(result)
    return result
