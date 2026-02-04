import json
import os
from datetime import datetime

from src.utils import (
    exchange_rate,
    get_cashback,
    get_expense,
    get_expense_by_category,
    get_income,
    get_other_category,
    get_top_seven_category,
    get_total_amount,
    get_total_amount_income,
    get_transfer_and_cash,
    greeting,
    read_user_setting,
    read_xlsx,
    sorted_by_date,
    sorted_by_range,
    stock_price,
    top_five,
)


def general(date: str) -> str:
    """Функция, принимает на вход строку с датой и временем в формате YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ
    содержащий: Приветствие в зависимости от текущего системного времени, По каждой карте: последние 4 цифры, общую
    сумму расходов, кэшбэк (1 рубль на каждые 100 рублей), Топ-5 транзакций по сумме платежа, Курс валют, Стоимость
    акций"""

    # Парсим строку даты в объект datetime
    date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    # Формируем путь к файлу с данными об операциях
    project_dir = os.path.dirname(os.path.dirname(__file__))
    data_file = os.path.join(project_dir, 'data', 'operations.xlsx')

    # Читаем данные из Excel файла
    raw_data = read_xlsx(data_file, 0)

    # Фильтруем данные по указанной дате
    filtered_data = sorted_by_date(raw_data, date_obj)

    # Получаем информацию о расходах по картам
    card_expense = get_expense(filtered_data)

    # Получаем топ-5 транзакций по сумме
    top_five_list = top_five(filtered_data)

    # Генерируем приветствие в зависимости от времени суток
    greeting_str = greeting()

    # Получаем настройки пользователя для валют и акций
    user_currencies = read_user_setting('user_currencies')
    user_stocks = read_user_setting('user_stocks')

    # Получаем актуальные курсы валют и цены акций
    currency_rates = exchange_rate(user_currencies)
    stock_prices = stock_price(user_stocks)

    # Формируем итоговый словарь с результатами
    result = {
        'greeting': greeting_str,  # Приветствие
        'cards': card_expense,  # Данные по картам
        'top_transaction': top_five_list,  # Топ-5 транзакций
        'currency_rates': currency_rates,  # Курсы валют
        'stock_prices': stock_prices,  # Цены акций
    }

    # Возвращаем результат в формате JSON
    return json.dumps(result, ensure_ascii=False, indent=2)


def events(date: str, date_range: str = 'M') -> str:
    """Функция, принимающая на вход строку с датой и второй необязательный параметр — диапазон данных (W — неделя,
    на которую приходится дата; M — месяц, на который приходится дата; Y — год, на который приходится дата; ALL — все
    данные до указанной даты). По умолчанию диапазон равен одному месяцу (с начала месяца, на который выпадает дата,
    по саму дату). Возвращаемый JSON-ответ содержит следующие данные: Расходы по категориям, Поступления, Курс валют,
    Стоимость акций"""

    # Парсим строку даты в объект datetime
    date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    # Формируем путь к файлу с данными об операциях
    project_dir = os.path.dirname(os.path.dirname(__file__))
    data_file = os.path.join(project_dir, 'data', 'operations.xlsx')

    # Читаем исходные данные из Excel файла
    raw_data = read_xlsx(data_file, 0)

    # Фильтруем данные по указанному диапазону (неделя/месяц/год/все)
    filtered_data = sorted_by_range(raw_data, date_obj, date_range)

    # Получаем расходы по категориям
    category_amount = get_expense_by_category(filtered_data)

    # Рассчитываем общую сумму расходов
    total_amount = get_total_amount(category_amount)

    # Получаем топ-7 категорий по расходам
    main_category = get_top_seven_category(category_amount)

    # Получаем остальные категории (кроме топ-7)
    other_category = get_other_category(category_amount)

    # Получаем категории переводов и наличных
    transfer_and_cash_category = get_transfer_and_cash(category_amount)

    # Получаем данные о доходах
    income_category = get_income(filtered_data)

    # Получаем данные о кэшбэке
    cashback_category = get_cashback(filtered_data)

    # Объединяем доходы и кэшбэк в один список
    combined_income = []
    if income_category is not None:
        combined_income.extend(income_category)

    if cashback_category is not None:
        combined_income.extend(cashback_category)

    # Рассчитываем общую сумму доходов
    total_amount_income = get_total_amount_income(combined_income)

    # Получаем настройки пользователя для валют и акций
    user_currencies = read_user_setting('user_currencies')
    user_stocks = read_user_setting('user_stocks')

    # Получаем актуальные курсы валют
    currency_rates = exchange_rate(user_currencies)

    # Получаем актуальные цены акций
    stock_prices = stock_price(user_stocks)

    # Объединяем основные и остальные категории расходов
    if main_category is None:
        main_category = []
    if other_category is not None:
        if isinstance(other_category, list):
            main_category.extend(other_category)
        else:
            main_category.append(other_category)

    # Формируем структуру расходов
    expenses = {
        'total_amount': total_amount,  # Общая сумма расходов
        'main': main_category,  # Основные категории
        'transfers_and_cash': transfer_and_cash_category,  # Переводы и наличные
    }

    # Формируем структуру доходов
    income = {
        'total_amount': total_amount_income,  # Общая сумма доходов
        'main': combined_income,  # Категории доходов
    }

    # Формируем итоговый результат
    result = {
        'expenses': expenses,  # Данные о расходах
        'income': income,  # Данные о доходах
        'currency_rates': currency_rates,  # Курсы валют
        'stock_prices': stock_prices,  # Цены акций
    }

    # Возвращаем результат в формате JSON
    return json.dumps(result, ensure_ascii=False, indent=2)
