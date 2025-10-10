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

    date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    project_dir = os.path.dirname(os.path.dirname(__file__))
    data_file = os.path.join(project_dir, 'data', 'operations.xlsx')
    raw_data = read_xlsx(data_file, 0)

    filtered_data = sorted_by_date(raw_data, date_obj)
    card_expense = get_expense(filtered_data)
    top_five_list = top_five(filtered_data)

    greeting_str = greeting()

    user_currencies = read_user_setting('user_currencies')
    user_stocks = read_user_setting('user_stocks')
    currency_rates = exchange_rate(user_currencies)
    stock_prices = stock_price(user_stocks)

    result = {
        'greeting': greeting_str,
        'cards': card_expense,
        'top_transaction': top_five_list,
        'currency_rates': currency_rates,
        'stock_prices': stock_prices,
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


def events(date: str, date_range: str = 'M') -> str:
    """Функция, принимающая на вход строку с датой и второй необязательный параметр — диапазон данных (W — неделя,
    на которую приходится дата; M — месяц, на который приходится дата; Y — год, на который приходится дата; ALL — все
    данные до указанной даты). По умолчанию диапазон равен одному месяцу (с начала месяца, на который выпадает дата,
    по саму дату). Возвращаемый JSON-ответ содержит следующие данные: Расходы по категориям, Поступления, Курс валют,
    Стоимость акций"""

    date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    project_dir = os.path.dirname(os.path.dirname(__file__))
    data_file = os.path.join(project_dir, 'data', 'operations.xlsx')
    raw_data = read_xlsx(data_file, 0)

    filtered_data = sorted_by_range(raw_data, date_obj, date_range)
    category_amount = get_expense_by_category(filtered_data)

    total_amount = get_total_amount(category_amount)
    main_category = get_top_seven_category(category_amount)
    other_category = get_other_category(category_amount)
    transfer_and_cash_category = get_transfer_and_cash(category_amount)
    income_category = get_income(filtered_data)
    cashback_category = get_cashback(filtered_data)

    if income_category and cashback_category:
        combined_income = income_category + cashback_category
    elif income_category:
        combined_income = income_category
    elif cashback_category:
        combined_income = cashback_category
    else:
        combined_income = None

    total_amount_income = get_total_amount_income(combined_income)

    user_currencies = read_user_setting('user_currencies')
    user_stocks = read_user_setting('user_stocks')

    currency_rates = exchange_rate(user_currencies)

    stock_prices = stock_price(user_stocks)

    # currency_rates = []
    # stock_prices =[]

    main_category.extend(other_category)
    expenses = {
        'total_amount': total_amount,
        'main': main_category,
        'transfers_and_cash': transfer_and_cash_category,
    }

    income_category.extend(cashback_category)

    income = {
        'total_amount': total_amount_income,
        'main': income_category,
    }

    result = {
        'expenses': expenses,
        'income': income,
        'currency_rates': currency_rates,
        'stock_prices': stock_prices,
    }

    return json.dumps(result, ensure_ascii=False, indent=2)
