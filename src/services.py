import json
import logging
import os
from calendar import monthrange
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List
from math import ceil

import pandas as pd

from src.utils import read_xlsx, sorted_by_range

logs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(logs_path, exist_ok=True)

services_logger = logging.getLogger('services')
services_logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler(os.path.join(logs_path, 'services.log'), encoding='utf-8', mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

services_logger.addHandler(file_handler)
services_logger.addHandler(console_handler)


def services_log_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        services_logger.info(f'Вызов функции {func.__name__}')
        try:
            result = func(*args, **kwargs)
            services_logger.info(f'Функция {func.__name__} успешно завершилась')
            return result
        except Exception as err:
            services_logger.error(f"Ошибка в функции {func.__name__}: {str(err)}")
            raise

    return wrapper


@services_log_function
def get_last_day(year: int, month: int) -> datetime:
    """Функция получает последний день указанного месяца и года. Возвращает значение даты в формате datetime."""

    # Получаем количество дней в месяце (последний день месяца)
    last_day_num = monthrange(year, month)[1]

    # Создаем объект datetime для последнего дня месяца
    # с временем 23:59:59 (конец дня)
    last_day = datetime(year, month, last_day_num, 23, 59, 59)

    return last_day


@services_log_function
def get_boosted_cashback_categories(data: str, year: str, month: str) -> str | None:
    """Функция для анализа выгодности категорий повышенного кешбэка. На вход функции поступают данные для анализа,
    год и месяц. На выходе — JSON с анализом, сколько на каждой категории можно заработать кешбэка в указанном месяце
    года."""

    # Получаем последний день указанного месяца
    date_value = get_last_day(int(year), int(month))

    # Читаем данные из Excel файла
    raw_data = read_xlsx(data, 0)

    # Фильтруем данные по указанному месяцу
    filtered_data = sorted_by_range(raw_data, date_value, 'M')

    # Если после фильтрации данных нет, возвращаем None
    if not filtered_data:
        return None

    # Создаем DataFrame из отфильтрованных данных
    df = pd.DataFrame(filtered_data)

    # Группируем по категориям, суммируем кешбэк, округляем и сортируем по убыванию
    result_series = df.groupby('category')['cashback'].sum().round(0).sort_values(ascending=False)

    # Создаем словарь {категория: сумма}, исключая нулевые значения
    result = {category: int(cashback) for category, cashback in result_series.items() if cashback > 0}

    # Логируем результат для отладки
    services_logger.debug(result)

    # Возвращаем результат в формате JSON
    return json.dumps(result, indent=2, ensure_ascii=False)


@services_log_function
def investment_bank(date: str, transactions: List[Dict[str, Any]], limit: int) -> str | None:
    """Функция, которая возвращает сумму, которую удалось бы отложить в «Инвесткопилку». Функция получает на вход
    три аргумента: month — месяц, для которого рассчитывается отложенная сумма (строка в формате 'YYYY-MM').
    transactions — список словарей, содержащий информацию о транзакциях, в которых содержатся следующие поля:
    Дата операции — дата, когда произошла транзакция (строка в формате 'YYYY-MM-DD').
    Сумма операции — сумма транзакции в оригинальной валюте (число).
    limit — предел, до которого нужно округлять суммы операций (целое число)."""

    # Парсим год и месяц из входной даты
    year = int(date.split('-')[0])
    month = int(date.split('-')[1])

    # Получаем последний день месяца для фильтрации
    date_value = get_last_day(int(year), int(month))

    # Проверяем, что есть данные для поиска
    if not transactions:
        return None

    # Фильтруем транзакции по указанному месяцу
    filtered_data = sorted_by_range(transactions, date_value, 'M')

    # Создаем DataFrame из отфильтрованных данных
    df = pd.DataFrame(filtered_data)

    # Оставляем только траты (отрицательные суммы)
    expenses_df = df[df['amount'] < 0]

    # Преобразуем в словарь {дата: сумма} для удобства
    result_df = expenses_df.set_index('date')['amount'].to_dict()
    services_logger.debug(f'Найдено {result_df} транзакций')

    # Вычисляем сумму для инвестирования
    investment = 0
    for amount in result_df.values():
        # Расчет суммы в копилку
        exp_sum = ceil(abs(amount) / limit) * limit
        investment += exp_sum - abs(amount)

    services_logger.info(investment)

    # Возвращаем результат в формате JSON
    return json.dumps({"investment": investment}, indent=2, ensure_ascii=False)


@services_log_function
def simple_search(request_str: str, transactions: List[Dict[str, Any]]) -> str | None:
    """Функция получает строку для поиска, возвращается JSON-ответ со всеми транзакциями, содержащими запрос
    в описании или категории."""

    # Проверяем, что есть данные для поиска
    if not transactions:
        return None

    # Преобразуем список транзакций в DataFrame для удобства обработки
    df = pd.DataFrame(transactions)

    # Разбиваем поисковый запрос на отдельные слова
    search_terms = request_str.split()

    # Создаем маску для фильтрации: ищем в столбцах category и description
    # Используем | (ИЛИ) для поиска по любому из столбцов
    # case=False для регистронезависимого поиска, na=False для игнорирования NaN
    mask = df['category'].str.contains('|'.join(search_terms), case=False, na=False) | df['description'].str.contains(
        '|'.join(search_terms), case=False, na=False
    )

    # Применяем маску для фильтрации DataFrame
    filtered_df = df[mask]

    # Конвертируем отфильтрованный DataFrame обратно в список словарей
    filtered_list = filtered_df.to_dict('records')

    # Логируем количество найденных транзакций
    services_logger.debug(f"Найдено {len(filtered_list)} транзакций")

    # Возвращаем результат в формате JSON
    return json.dumps(filtered_list, indent=2, ensure_ascii=False)


@services_log_function
def phone_search(data_list: List[Dict[str, Any]]) -> str | None:
    """Функция возвращает JSON со всеми транзакциями, содержащими в описании мобильные номера."""

    # Проверка на пустой список транзакций
    if not data_list:
        return None

    # Создаем DataFrame для удобства обработки данных
    df = pd.DataFrame(data_list)

    # Регулярное выражение для поиска российских номеров телефонов
    # Поддерживает форматы: +7, 8, с разными разделителями
    pattern = r'[\+]?[7-8]?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'

    # Создаем маску для фильтрации: ищем номера в описании транзакций
    mask = df['description'].str.contains(pattern, na=False)

    # Применяем маску для отбора транзакций с номерами телефонов
    filtered_df = df[mask]

    # Конвертируем результат обратно в список словарей
    filtered_list = filtered_df.to_dict('records')

    # Логируем количество найденных транзакций
    services_logger.debug(f"Найдено {len(filtered_list)} транзакций")

    # Возвращаем результат в формате JSON
    return json.dumps(filtered_list, indent=2, ensure_ascii=False)


@services_log_function
def person_search(data_list: List[Dict[str, Any]]) -> str | None:
    """Функция возвращает JSON со всеми транзакциями, которые относятся к переводам физлицам."""

    # Проверка на пустой список транзакций
    if not data_list:
        return None

    # Создаем DataFrame для обработки данных
    df = pd.DataFrame(data_list)

    # Регулярное выражение для поиска ФИО в формате "Фамилия И.О."
    # [А-ЯЁ][а-яё]+ - слово с заглавной буквы (фамилия)
    # \s+ - один или более пробелов
    # [А-ЯЁ]\. - инициал с точкой (например, "И.")
    pattern = r'[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.'

    # Создаем комбинированную маску: ищем ФИО в описании И переводы в категории
    mask = df['description'].str.contains(pattern, na=False) & df['category'].str.contains(
        'Переводы', case=False, na=False
    )

    # Применяем маску для фильтрации транзакций
    filtered_df = df[mask]

    # Конвертируем результат в список словарей
    filtered_list = filtered_df.to_dict('records')

    # Логируем количество найденных транзакций
    services_logger.debug(f"Найдено {len(filtered_list)} транзакций")

    # Возвращаем результат в формате JSON
    return json.dumps(filtered_list, indent=2, ensure_ascii=False)
