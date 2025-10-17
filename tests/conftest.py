import os
import tempfile
from datetime import datetime

import pandas as pd
import pytest


# Фикстуры
@pytest.fixture
def sample_transactions():
    """Фикстура с примером данных транзакций"""
    return pd.DataFrame(
        {
            'Дата платежа': ['01.01.2024', '15.01.2024', '01.02.2024', '15.02.2024', '01.03.2024', '15.03.2024'],
            'Категория': ['Еда', 'Транспорт', 'Еда', 'Развлечения', 'Еда', 'Транспорт'],
            'Сумма операции': [1000, 500, 1200, 2000, 800, 600],
        }
    )


@pytest.fixture
def sample_excel_file():
    """Создание временного Excel файла для тестов"""
    df = pd.DataFrame(
        {
            'Дата платежа': ['01.01.2024', '15.01.2024'],
            'Категория': ['Еда', 'Транспорт'],
            'Сумма операции': [1000, 500],
        }
    )

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df.to_excel(f.name, index=False, engine='openpyxl')
        yield f.name
    # Удаляем временный файл после теста
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
def empty_dataframe():
    return pd.DataFrame()


@pytest.fixture
def test_data():
    """Фикстура с тестовыми данными"""
    return [
        {'date': '01.01.2021 10:00:00', 'amount': 100},
        {'date': '15.01.2021 14:30:00', 'amount': 200},
        {'date': '31.01.2021 23:59:59', 'amount': 300},
        {'date': '01.02.2021 00:00:00', 'amount': 400},
        {'date': '01.01.2020 09:00:00', 'amount': 500},
        {'date': '15.01.2020 12:00:00', 'amount': 600},
        {'date': '01.01.2022 08:00:00', 'amount': 700},  # Будущая дата относительно 2021
        {'invalid_key': 'value'},
    ]

@pytest.fixture
def january_2021_date():
    """Фикстура с датой января 2021"""
    return datetime(2021, 1, 31, 23, 59, 59)

@pytest.fixture
def december_2021_date():
    """Фикстура с датой декабря 2021"""
    return datetime(2021, 12, 31, 23, 59, 59)

@pytest.fixture
def mid_january_2021_date():
    """Фикстура с датой середины января 2021"""
    return datetime(2021, 1, 15, 23, 59, 59)


@pytest.fixture
def expense_data():
    """Фикстура с тестовыми данными для тестирования расходов по категориям"""
    return [
        {'category': 'food', 'amount': -1500},
        {'category': 'transport', 'amount': -500},
        {'category': 'food', 'amount': -2000},
        {'category': 'entertainment', 'amount': -1000},
        {'category': 'transport', 'amount': -300},
        {'category': 'salary', 'amount': 10000},  # доход
        {'category': 'food', 'amount': -1000},
        {'category': 'investment', 'amount': 5000},  # доход
    ]

@pytest.fixture
def expense_data_with_positive_only():
    """Фикстура только с положительными суммами (доходами)"""
    return [
        {'category': 'salary', 'amount': 10000},
        {'category': 'bonus', 'amount': 5000},
        {'category': 'investment', 'amount': 3000},
    ]

@pytest.fixture
def expense_data_with_negative_only():
    """Фикстура только с отрицательными суммами (расходами)"""
    return [
        {'category': 'food', 'amount': -1500},
        {'category': 'transport', 'amount': -500},
        {'category': 'rent', 'amount': -30000},
    ]

@pytest.fixture
def expense_data_empty_category():
    """Фикстура с данными, где есть пустые категории"""
    return [
        {'category': 'food', 'amount': -1500},
        {'category': '', 'amount': -500},
        {'category': 'transport', 'amount': -300},
        {'category': None, 'amount': -1000},
    ]

@pytest.fixture
def expense_data_single_category():
    """Фикстура с данными одной категории"""
    return [
        {'category': 'food', 'amount': -1000},
        {'category': 'food', 'amount': -2000},
        {'category': 'food', 'amount': -1500},
    ]


@pytest.fixture
def top_category_data():
    """Фикстура с тестовыми данными для тестирования топа категорий"""
    return [
        {'category': 'Еда', 'amount': -1500},
        {'category': 'Транспорт', 'amount': -500},
        {'category': 'Еда', 'amount': -2000},
        {'category': 'Развлечения', 'amount': -1000},
        {'category': 'Транспорт', 'amount': -300},
        {'category': 'Переводы', 'amount': -5000},  # исключаемая категория
        {'category': 'Бонусы', 'amount': -100},     # исключаемая категория
        {'category': 'Наличные', 'amount': -200},   # исключаемая категория
        {'category': 'Пополнения', 'amount': -50},  # исключаемая категория
        {'category': 'Жилье', 'amount': -30000},
        {'category': 'Здоровье', 'amount': -2500},
        {'category': 'Одежда', 'amount': -4000},
        {'category': 'Образование', 'amount': -15000},
        {'category': 'Путешествия', 'amount': -12000},
        {'category': 'Техника', 'amount': -8000},
        {'category': 'Красота', 'amount': -2000},
        {'category': 'Спорт', 'amount': -3000},
        {'category': 'salary', 'amount': 10000},    # доход - должен игнорироваться
    ]

@pytest.fixture
def top_category_data_less_than_seven():
    """Фикстура с данными, где категорий меньше 7"""
    return [
        {'category': 'Еда', 'amount': -1500},
        {'category': 'Транспорт', 'amount': -500},
        {'category': 'Развлечения', 'amount': -1000},
        {'category': 'Жилье', 'amount': -30000},
        {'category': 'Здоровье', 'amount': -2500},
    ]

@pytest.fixture
def top_category_data_with_excluded_only():
    """Фикстура только с исключаемыми категориями"""
    return [
        {'category': 'Переводы', 'amount': -5000},
        {'category': 'Бонусы', 'amount': -100},
        {'category': 'Наличные', 'amount': -200},
        {'category': 'Пополнения', 'amount': -50},
    ]

@pytest.fixture
def top_category_data_with_positive_only():
    """Фикстура только с положительными суммами"""
    return [
        {'category': 'Еда', 'amount': 1500},
        {'category': 'Транспорт', 'amount': 500},
        {'category': 'Развлечения', 'amount': 1000},
    ]

@pytest.fixture
def top_category_data_single_large_expense():
    """Фикстура с одним большим расходом"""
    return [
        {'category': 'Еда', 'amount': -100},
        {'category': 'Жилье', 'amount': -50000},
        {'category': 'Транспорт', 'amount': -200},
    ]


@pytest.fixture
def other_category_data():
    """Фикстура с тестовыми данными для тестирования остальных категорий"""
    return [
        {'category': 'Еда', 'amount': -1500},
        {'category': 'Транспорт', 'amount': -500},
        {'category': 'Еда', 'amount': -2000},
        {'category': 'Развлечения', 'amount': -1000},
        {'category': 'Транспорт', 'amount': -300},
        {'category': 'Переводы', 'amount': -5000},  # исключаемая категория
        {'category': 'Бонусы', 'amount': -100},     # исключаемая категория
        {'category': 'Наличные', 'amount': -200},   # исключаемая категория
        {'category': 'Пополнения', 'amount': -50},  # исключаемая категория
        {'category': 'Жилье', 'amount': -30000},
        {'category': 'Здоровье', 'amount': -2500},
        {'category': 'Одежда', 'amount': -4000},
        {'category': 'Образование', 'amount': -15000},
        {'category': 'Путешествия', 'amount': -12000},
        {'category': 'Техника', 'amount': -8000},
        {'category': 'Красота', 'amount': -2000},
        {'category': 'Спорт', 'amount': -3000},
        {'category': 'Книги', 'amount': -1500},
        {'category': 'Подарки', 'amount': -1200},
        {'category': 'Рестораны', 'amount': -1800},
        {'category': 'salary', 'amount': 10000},    # доход - должен игнорироваться
    ]

@pytest.fixture
def other_category_data_less_than_eight():
    """Фикстура с данными, где транзакций меньше 8"""
    return [
        {'category': 'Еда', 'amount': -1500},
        {'category': 'Транспорт', 'amount': -500},
        {'category': 'Развлечения', 'amount': -1000},
        {'category': 'Жилье', 'amount': -30000},
        {'category': 'Здоровье', 'amount': -2500},
        {'category': 'Одежда', 'amount': -4000},
        {'category': 'Образование', 'amount': -15000},
    ]

@pytest.fixture
def other_category_data_exactly_seven():
    """Фикстура с точно 7 транзакциями"""
    return [
        {'category': 'Еда', 'amount': -1000},
        {'category': 'Транспорт', 'amount': -500},
        {'category': 'Развлечения', 'amount': -1500},
        {'category': 'Жилье', 'amount': -30000},
        {'category': 'Здоровье', 'amount': -2500},
        {'category': 'Одежда', 'amount': -4000},
        {'category': 'Образование', 'amount': -15000},
    ]

@pytest.fixture
def other_category_data_with_excluded_only():
    """Фикстура только с исключаемыми категориями"""
    return [
        {'category': 'Переводы', 'amount': -5000},
        {'category': 'Бонусы', 'amount': -100},
        {'category': 'Наличные', 'amount': -200},
        {'category': 'Пополнения', 'amount': -50},
    ]

@pytest.fixture
def other_category_data_with_positive_only():
    """Фикстура только с положительными суммами"""
    return [
        {'category': 'Еда', 'amount': 1500},
        {'category': 'Транспорт', 'amount': 500},
        {'category': 'Развлечения', 'amount': 1000},
    ]

@pytest.fixture
def other_category_data_single_category_multiple():
    """Фикстура с одной категорией, но множеством транзакций"""
    return [
        {'category': 'Еда', 'amount': -100},
        {'category': 'Еда', 'amount': -200},
        {'category': 'Еда', 'amount': -300},
        {'category': 'Еда', 'amount': -400},
        {'category': 'Еда', 'amount': -500},
        {'category': 'Еда', 'amount': -600},
        {'category': 'Еда', 'amount': -700},
        {'category': 'Еда', 'amount': -800},
        {'category': 'Еда', 'amount': -900},
        {'category': 'Еда', 'amount': -1000},
    ]


@pytest.fixture
def transfer_cash_data():
    """Фикстура с тестовыми данными для тестирования переводов и наличных"""
    return [
        {'category': 'Переводы', 'amount': -1500},
        {'category': 'Наличные', 'amount': -500},
        {'category': 'Переводы', 'amount': -2000},
        {'category': 'Наличные', 'amount': -300},
        {'category': 'Еда', 'amount': -1000},  # должна игнорироваться
        {'category': 'Транспорт', 'amount': -200},  # должна игнорироваться
        {'category': 'Переводы', 'amount': 1000},  # положительная - должна игнорироваться
        {'category': 'Наличные', 'amount': 500},  # положительная - должна игнорироваться
    ]

@pytest.fixture
def transfer_cash_data_only_transfers():
    """Фикстура только с переводами"""
    return [
        {'category': 'Переводы', 'amount': -1000},
        {'category': 'Переводы', 'amount': -2000},
        {'category': 'Переводы', 'amount': -1500},
    ]

@pytest.fixture
def transfer_cash_data_only_cash():
    """Фикстура только с наличными"""
    return [
        {'category': 'Наличные', 'amount': -500},
        {'category': 'Наличные', 'amount': -300},
        {'category': 'Наличные', 'amount': -200},
    ]

@pytest.fixture
def transfer_cash_data_case_insensitive():
    """Фикстура с разным регистром категорий"""
    return [
        {'category': 'переводы', 'amount': -1000},  # нижний регистр
        {'category': 'ПЕРЕВОДЫ', 'amount': -2000},  # верхний регистр
        {'category': 'НаличныЕ', 'amount': -500},   # смешанный регистр
        {'category': 'наличные', 'amount': -300},   # нижний регистр
    ]

@pytest.fixture
def transfer_cash_data_no_matching():
    """Фикстура без подходящих категорий"""
    return [
        {'category': 'Еда', 'amount': -1000},
        {'category': 'Транспорт', 'amount': -500},
        {'category': 'Развлечения', 'amount': -200},
    ]

@pytest.fixture
def income_data():
    """Фикстура с тестовыми данными для тестирования доходов"""
    return [
        {'description': 'Зарплата', 'amount': 10000},
        {'description': 'Фриланс', 'amount': 5000},
        {'description': 'Зарплата', 'amount': 15000},  # дублирующее описание
        {'description': 'Инвестиции', 'amount': 3000},
        {'description': 'Подарок', 'amount': 2000},
        {'description': 'Еда', 'amount': -1500},  # расход - должен игнорироваться
        {'description': 'Транспорт', 'amount': -500},  # расход - должен игнорироваться
    ]

@pytest.fixture
def income_data_only_expenses():
    """Фикстура только с расходами"""
    return [
        {'description': 'Еда', 'amount': -1500},
        {'description': 'Транспорт', 'amount': -500},
        {'description': 'Развлечения', 'amount': -1000},
    ]

@pytest.fixture
def income_data_single_description():
    """Фикстура с одним описанием доходов"""
    return [
        {'description': 'Зарплата', 'amount': 10000},
        {'description': 'Зарплата', 'amount': 5000},
        {'description': 'Зарплата', 'amount': 3000},
    ]

@pytest.fixture
def income_data_mixed_case():
    """Фикстура с разным регистром описаний"""
    return [
        {'description': 'зарплата', 'amount': 10000},  # нижний регистр
        {'description': 'Зарплата', 'amount': 5000},   # смешанный регистр
        {'description': 'ЗАРПЛАТА', 'amount': 3000},   # верхний регистр
    ]


@pytest.fixture
def total_amount_data():
    """Фикстура с тестовыми данными для тестирования общей суммы расходов"""
    return [
        {'amount': -1500},
        {'amount': -500},
        {'amount': -2000},
        {'amount': 1000},  # доход - должен игнорироваться
        {'amount': 500},   # доход - должен игнорироваться
    ]

@pytest.fixture
def total_amount_data_only_income():
    """Фикстура только с доходами"""
    return [
        {'amount': 1000},
        {'amount': 500},
        {'amount': 3000},
    ]

@pytest.fixture
def total_amount_data_mixed():
    """Фикстура со смешанными положительными и отрицательными суммами"""
    return [
        {'amount': -1000},
        {'amount': 2000},
        {'amount': -500},
        {'amount': 3000},
        {'amount': -1500},
    ]

@pytest.fixture
def total_amount_data_with_decimals():
    """Фикстура с десятичными числами"""
    return [
        {'amount': -1000.4},
        {'amount': -500.6},
        {'amount': -1500.8},
    ]

@pytest.fixture
def total_amount_data_single_expense():
    """Фикстура с одним расходом"""
    return [
        {'amount': -5000},
    ]

@pytest.fixture
def total_income_data():
    """Фикстура с тестовыми данными для тестирования общей суммы доходов"""
    return [
        {'category': 'Зарплата', 'amount': 10000},
        {'category': 'Фриланс', 'amount': 5000},
        {'category': 'Инвестиции', 'amount': 3000},
    ]

@pytest.fixture
def total_income_data_single():
    """Фикстура с одним доходом"""
    return [
        {'category': 'Зарплата', 'amount': 15000},
    ]

@pytest.fixture
def total_income_data_with_negative():
    """Фикстура с отрицательными суммами (нестандартный случай)"""
    return [
        {'category': 'Зарплата', 'amount': 10000},
        {'category': 'Штраф', 'amount': -500},  # отрицательный доход
    ]

@pytest.fixture
def total_income_data_empty_dicts():
    """Фикстура с пустыми словарями"""
    return [
        {},
        {'category': 'Зарплата', 'amount': 1000},
        {},
    ]

@pytest.fixture
def total_income_data_large_numbers():
    """Фикстура с большими числами"""
    return [
        {'category': 'Зарплата', 'amount': 100000},
        {'category': 'Бонус', 'amount': 50000},
        {'category': 'Инвестиции', 'amount': 75000},
    ]

@pytest.fixture
def cashback_data():
    """Фикстура с тестовыми данными для тестирования кэшбэка"""
    return [
        {'cashback': 100, 'amount': -1500, 'category': 'Еда'},
        {'cashback': 50, 'amount': -500, 'category': 'Транспорт'},
        {'cashback': 200, 'amount': -2000, 'category': 'Развлечения'},
        {'cashback': 0, 'amount': -1000, 'category': 'Жилье'},  # нулевой кэшбэк
    ]

@pytest.fixture
def cashback_data_single():
    """Фикстура с одним элементом кэшбэка"""
    return [
        {'cashback': 500, 'amount': -5000, 'category': 'Еда'},
    ]

@pytest.fixture
def cashback_data_decimals():
    """Фикстура с десятичными числами кэшбэка"""
    return [
        {'cashback': 100.4, 'amount': -1500, 'category': 'Еда'},
        {'cashback': 50.6, 'amount': -500, 'category': 'Транспорт'},
        {'cashback': 200.8, 'amount': -2000, 'category': 'Развлечения'},
    ]

@pytest.fixture
def cashback_data_negative():
    """Фикстура с отрицательным кэшбэком (нестандартный случай)"""
    return [
        {'cashback': 100, 'amount': -1500, 'category': 'Еда'},
        {'cashback': -50, 'amount': -500, 'category': 'Транспорт'},  # отрицательный кэшбэк
        {'cashback': 200, 'amount': -2000, 'category': 'Развлечения'},
    ]

@pytest.fixture
def cashback_data_no_cashback():
    """Фикстура без кэшбэка (все нули)"""
    return [
        {'cashback': 0, 'amount': -1500, 'category': 'Еда'},
        {'cashback': 0, 'amount': -500, 'category': 'Транспорт'},
        {'cashback': 0, 'amount': -2000, 'category': 'Развлечения'},
    ]
