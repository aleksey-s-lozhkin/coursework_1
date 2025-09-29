import json
import os
from datetime import datetime

from src.utils import (
    exchange_rate,
    get_expense,
    greeting,
    read_user_setting,
    read_xlsx,
    sorted_by_date,
    stock_price,
    top_five,
)


def general(date: str) -> str:
    """Функция, принимает на вход строку с датой и временем в формате YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ"""

    result = {}
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
