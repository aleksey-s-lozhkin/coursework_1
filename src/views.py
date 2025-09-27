import json
from datetime import datetime
from typing import Any, Dict, List


def greeting() -> str:
    """Функция возвращает приветствие в зависимости от текущего времени пользователя"""

    cur_hour = datetime.now().hour

    greet_message = ['Доброй ночи', 'Доброго утра', 'Доброго дня', 'Доброго вечера']
    time_of_day = cur_hour // 6
    return greet_message[time_of_day]


def read_user_setting() -> List[Dict[str, Any]] | None:

    user_setting_config = '../data/user_setting.json'

    try:
        with open(user_setting_config, 'r', encoding='utf-8') as user_setting:
            data = json.load(user_setting)
            return data.get('user_currencies')

    except FileNotFoundError:
        print(f"Файл {user_setting_config} не найден")
        return None

    except json.JSONDecodeError:
        print(f"Ошибка парсинга JSON в файле {user_setting_config}")
        return None


def exchange_rate(currency: List[str]) -> Dict[str, Any] | None:
    """Функция получает на вход словарь с перечнем валют, по которым надо получить текущий курс и возвращает словарь,
    где ключи - код валюты, а значения - текущий курс"""

    pass


def top_five(data: list[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Функция получает на вход список словарей с транзакциями и возвращает ТОП 5 транзакций по сумме платежа"""

    pass


def share_price(data: List[str]) -> List[Dict[str, Any]]:
    """Функция получает на вход список акций и возвращает список словарей, где ключи - код акций, а значение -
    стоимость акций"""

    pass


def general(data: List[Dict[str, Any]], date: str) -> json:
    pass
