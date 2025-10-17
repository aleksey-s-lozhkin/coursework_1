import json
import os
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest
import requests

from src.utils import (
    exchange_rate,
    get_expense,
    greeting,
    log_function,
    read_user_setting,
    read_xlsx,
    sorted_by_date,
    sorted_by_range,
    stock_price,
    top_five,
    get_expense_by_category,
    get_top_seven_category,
    get_other_category,
    get_transfer_and_cash,
    get_income,
    get_total_amount,
    get_total_amount_income,
    get_cashback,
)


# ТЕСТЫ ДЛЯ ЛОГЕРА
def test_reports_log_function_decorator():
    """Тест декоратора логирования"""

    @log_function
    def test_function():
        return "success"

    result = test_function()
    assert result == "success"


def test_reports_log_function_decorator_with_exception():
    """Тест декоратора логирования с исключением"""

    @log_function
    def test_function():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        test_function()


# ТЕСТ ДЛЯ GREETING
@pytest.mark.parametrize(
    "hour,expected",
    [
        (0, "Доброй ночи"),
        (3, "Доброй ночи"),
        (5, "Доброй ночи"),
        (6, "Доброго утра"),
        (8, "Доброго утра"),
        (11, "Доброго утра"),
        (12, "Доброго дня"),
        (15, "Доброго дня"),
        (17, "Доброго дня"),
        (18, "Доброго вечера"),
        (20, "Доброго вечера"),
        (23, "Доброго вечера"),
    ],
)
def test_greeting_returns_correct_message_based_on_hour(hour, expected):
    """Проверяет возврат правильного приветствия в зависимости от часа"""
    with patch('src.utils.datetime') as mock_datetime:
        # Мокаем текущее время с нужным часом
        mock_datetime.now.return_value = datetime(2024, 1, 1, hour, 0, 0)

        result = greeting()

        assert result == expected


# ТЕСТ ДЛЯ READ_USER_SETTING
@patch('src.utils.logger')
@patch('src.utils.json.load')
@patch('builtins.open')
def test_read_user_currencies_success(mock_open, mock_json_load, mock_logger):
    """Проверяет успешное чтение валют пользователя"""
    mock_json_load.return_value = {'user_currencies': ['USD', 'EUR'], 'user_stocks': ['AAPL', 'TSLA']}

    result = read_user_setting('user_currencies')

    assert result == ['USD', 'EUR']
    mock_logger.info.assert_any_call('Чтение пользовательских настроек: user_currencies')
    mock_logger.info.assert_any_call("Валюта пользователя: ['USD', 'EUR']")

    result = read_user_setting('user_stocks')

    assert result == ['AAPL', 'TSLA']
    mock_logger.info.assert_any_call('Чтение пользовательских настроек: user_stocks')
    mock_logger.info.assert_any_call("Акции пользователя: ['AAPL', 'TSLA']")

    result = read_user_setting('unknown_setting')

    assert result is None


@patch('builtins.open', side_effect=FileNotFoundError)
def test_file_not_found_exception(mock_open):
    """Проверяет выброс исключения при отсутствии файла"""
    with pytest.raises(FileNotFoundError):
        read_user_setting('user_currencies')


@patch('builtins.open')
def test_json_decode_error(mock_open):
    """Проверяет выброс исключения при невалидном JSON"""
    # Создаем мок для файлового объекта, который вызывает JSONDecodeError при вызове json.load
    mock_file = MagicMock()
    mock_file.__enter__.return_value = mock_file
    mock_open.return_value = mock_file
    mock_json_load = MagicMock(side_effect=json.JSONDecodeError("Expecting value", "doc", 0))

    with patch('src.utils.json.load', mock_json_load):
        with pytest.raises(json.JSONDecodeError):
            read_user_setting('user_currencies')


# ТЕСТ ДЛЯ READ_XLSX
@patch('src.utils.pd.read_excel')
@patch('src.utils.os.path.exists')
def test_read_xlsx_success(mock_exists, mock_read_excel):
    """Тест успешного чтения файла"""
    # Мокируем данные
    mock_exists.return_value = True
    mock_df = MagicMock()
    mock_df.to_dict.return_value = [{'Дата операции': '2023-01-01', 'Сумма платежа': 100.0}]

    mock_df.rename.return_value = mock_df

    mock_read_excel.return_value = mock_df

    # Вызов функции
    result = read_xlsx('test.xlsx', sheet=0)

    # Проверки
    mock_read_excel.assert_called_once()
    mock_df.rename.assert_called_once()
    assert len(result) == 1


@patch('src.utils.os.path.exists')
def test_read_xlsx_file_not_found(mock_exists):
    """Тест обработки отсутствующего файла"""
    mock_exists.return_value = False

    with pytest.raises(FileNotFoundError):
        read_xlsx('nonexistent.xlsx')


@patch('src.utils.pd.read_excel')
@patch('src.utils.os.path.exists')
def test_read_xlsx_general_error(mock_exists, mock_read_excel):
    """Тест обработки общей ошибки"""
    mock_exists.return_value = True
    mock_read_excel.side_effect = Exception("Test error")

    with pytest.raises(ValueError):
        read_xlsx('test.xlsx')


# ТЕСТ ДЛЯ SORTED_BY_DATE
def test_sorted_by_date_empty_list():
    """Тест с пустым списком"""
    result = sorted_by_date([], datetime(2023, 5, 15))
    assert result == []


def test_sorted_by_date_no_date_key():
    """Тест с транзакциями без ключа 'date'"""
    data = [{'amount': 100, 'category': 'test'}, {'card': '1234', 'amount': 200}]
    result = sorted_by_date(data, datetime(2023, 5, 15))
    assert result == []


def test_sorted_by_date_correct():
    """Тест корректной фильтрации по дате"""
    test_date = datetime(2023, 5, 15, 23, 59, 59)
    data = [
        {'date': '01.05.2023 10:00:00', 'amount': 100},  # Должна попасть (начало месяца)
        {'date': '10.05.2023 14:30:00', 'amount': 200},  # Должна попасть
        {'date': '15.05.2023 23:59:59', 'amount': 300},  # Должна попасть
        {'date': '16.05.2023 00:00:00', 'amount': 400},  # Не должна попасть (после указанной даты)
        {'date': '30.04.2023 10:00:00', 'amount': 500},  # Не должна попасть (до начала месяца)
    ]

    result = sorted_by_date(data, test_date)

    assert len(result) == 3
    assert result[0]['amount'] == 100
    assert result[1]['amount'] == 200
    assert result[2]['amount'] == 300


# ТЕСТ ДЛЯ TOP_FIVE
def test_top_five_empty_list():
    """Тест с пустым списком"""
    result = top_five([])
    assert result is None


def test_top_five_less_than_five_items():
    """Тест с менее чем 5 транзакциями"""
    data = [
        {'amount': 100, 'date': '01.01.2023 10:00:00', 'category': 'A', 'description': 'Test1'},
        {'amount': 300, 'date': '02.01.2023 11:00:00', 'category': 'B', 'description': 'Test2'},
        {'amount': 200, 'date': '03.01.2023 12:00:00', 'category': 'C', 'description': 'Test3'},
    ]

    result = top_five(data)

    assert len(result) == 3
    # Проверяем сортировку по убыванию абсолютной суммы
    assert result[0]['amount'] == 300
    assert result[1]['amount'] == 200
    assert result[2]['amount'] == 100


def test_top_five_more_than_five_items():
    """Тест с более чем 5 транзакциями"""
    data = [
        {'amount': 100, 'date': '01.01.2023 10:00:00', 'category': 'A', 'description': 'Test1'},
        {'amount': 500, 'date': '02.01.2023 11:00:00', 'category': 'B', 'description': 'Test2'},
        {'amount': 200, 'date': '03.01.2023 12:00:00', 'category': 'C', 'description': 'Test3'},
        {'amount': 600, 'date': '04.01.2023 13:00:00', 'category': 'D', 'description': 'Test4'},
        {'amount': 300, 'date': '05.01.2023 14:00:00', 'category': 'E', 'description': 'Test5'},
        {'amount': 400, 'date': '06.01.2023 15:00:00', 'category': 'F', 'description': 'Test6'},
    ]

    result = top_five(data)

    assert len(result) == 5
    # Проверяем что взяты самые большие по абсолютной сумме
    assert result[0]['amount'] == 600
    assert result[1]['amount'] == 500
    assert result[2]['amount'] == 400
    assert result[3]['amount'] == 300
    assert result[4]['amount'] == 200


def test_top_five_date_formatting():
    """Тест форматирования даты"""
    data = [
        {'amount': 100, 'date': '01.01.2023 10:00:00', 'category': 'A', 'description': 'Test1'},
        {'amount': 200, 'date': '02.01.2023 11:00:00', 'category': 'B', 'description': 'Test2'},
    ]

    result = top_five(data)

    # Проверяем что время удалено из даты
    assert result[0]['date'] == '02.01.2023'
    assert result[1]['date'] == '01.01.2023'


def test_top_five_missing_fields():
    """Тест с отсутствующими полями"""
    data = [
        {'amount': 100, 'date': '01.01.2023 10:00:00'},
        {'amount': 200, 'category': 'B', 'description': 'Test2'},
        {'amount': 300, 'date': '03.01.2023 12:00:00', 'category': 'C'},
    ]

    result = top_five(data)

    assert len(result) == 3

    # Находим транзакции по сумме
    trans_100 = next(item for item in result if item['amount'] == 100)
    trans_200 = next(item for item in result if item['amount'] == 200)
    trans_300 = next(item for item in result if item['amount'] == 300)

    # Проверяем отсутствующие поля для каждой транзакции
    assert 'category' not in trans_100
    assert 'description' not in trans_100
    assert 'date' in trans_100

    assert 'date' not in trans_200
    assert 'category' in trans_200
    assert 'description' in trans_200

    assert 'description' not in trans_300
    assert 'date' in trans_300
    assert 'category' in trans_300


# ТЕСТ ДЛЯ EXCHANGE_RATE


@patch('src.utils.requests.get')
@patch('src.utils.load_dotenv')
@patch('src.utils.os.getenv')
def test_exchange_rate_success(mock_getenv, mock_load_dotenv, mock_get):
    """Тест успешного получения курсов валют"""
    mock_getenv.return_value = 'test_api_key'
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'rate': 90.5}
    mock_get.return_value = mock_response

    result = exchange_rate(['USD', 'EUR'])

    mock_load_dotenv.assert_called_once()
    mock_getenv.assert_called_with('API_KEY')
    assert mock_get.call_count == 2
    assert len(result) == 2
    assert result[0] == {'currency': 'USD', 'rate': 90.5}
    assert result[1] == {'currency': 'EUR', 'rate': 90.5}


@patch('src.utils.requests.get')
@patch('src.utils.load_dotenv')
@patch('src.utils.os.getenv')
def test_exchange_rate_no_api_key_or_empty_list(mock_getenv, mock_load_dotenv, mock_get):
    """Тест отсутствия API ключа или пустого списка валют"""
    # Тест 1: отсутствие API ключа
    mock_getenv.return_value = None
    result = exchange_rate(['USD'])

    assert result is None

    mock_getenv.return_value = 'test_key'
    mock_get.reset_mock()

    result = exchange_rate([])
    assert result is None
    mock_get.assert_not_called()


@patch('src.utils.requests.get')
@patch('src.utils.load_dotenv')
@patch('src.utils.os.getenv')
@pytest.mark.parametrize(
    "error",
    [
        ("request_exception", None),
        ("http_error", None),
        ("no_rate", [{'currency': 'USD', 'rate': None}]),
        ("json_error", None),
    ],
)
def test_exchange_rate_error_scenarios(mock_getenv, mock_load_dotenv, mock_get, error):
    """Тест различных сценариев ошибок"""
    mock_getenv.return_value = 'test_api_key'

    error_scenario, expected_result = error

    # Настраиваем мок в зависимости от сценария
    if error_scenario == "request_exception":
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
    elif error_scenario == "http_error":
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
    elif error_scenario == "no_rate":
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'error': 'Invalid currency'}  # Нет поля 'rate'
        mock_get.return_value = mock_response
    elif error_scenario == "json_error":
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

    # Вызываем функцию
    result = exchange_rate(['USD'])

    # Проверяем результат
    assert result == expected_result


# ТЕСТ ДЛЯ STOCK_PRICE
@patch('src.utils.requests.get')
@patch('src.utils.load_dotenv')
@patch('src.utils.os.getenv')
def test_stock_price_success(mock_getenv, mock_load_dotenv, mock_get):
    """Тест успешного получения цен акций"""
    mock_getenv.return_value = 'test_api_key'

    # Мокируем успешный ответ API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'AAPL': {'price': '150.50'},
        'GOOGL': {'price': '2800.75'},
        'TSLA': {'price': '250.30'},
    }
    mock_get.return_value = mock_response

    result = stock_price(['AAPL', 'GOOGL', 'TSLA'])

    # Проверки
    mock_load_dotenv.assert_called_once()
    mock_getenv.assert_called_with('API_KEY')
    mock_get.assert_called_once()

    assert len(result) == 3
    assert result == [
        {'stock': 'AAPL', 'price': 150.50},
        {'stock': 'GOOGL', 'price': 2800.75},
        {'stock': 'TSLA', 'price': 250.30},
    ]


@patch('src.utils.requests.get')
@patch('src.utils.load_dotenv')
@patch('src.utils.os.getenv')
def test_stock_price_no_api_key_or_empty_list(mock_getenv, mock_load_dotenv, mock_get):
    """Тест отсутствия API ключа или пустого списка акций"""
    # Тест 1: отсутствие API ключа
    mock_getenv.return_value = None
    result = stock_price(['AAPL'])
    assert result is None

    # Тест 2: пустой список акций
    mock_getenv.return_value = 'test_api_key'
    result = stock_price([])
    assert result is None

    # Убеждаемся что запросы не отправлялись
    mock_get.assert_not_called()


@patch('src.utils.requests.get')
@patch('src.utils.load_dotenv')
@patch('src.utils.os.getenv')
@pytest.mark.parametrize(
    "error_scenario, expected_result",
    [
        # (сценарий ошибки, ожидаемый результат)
        ("request_exception", None),
        ("http_error", None),
        ("json_error", None),
    ],
)
def test_stock_price_errors_returning_none(mock_getenv, mock_load_dotenv, mock_get, error_scenario, expected_result):
    """Тест ошибок, которые приводят к возврату None"""
    mock_getenv.return_value = 'test_api_key'

    if error_scenario == "request_exception":
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
    elif error_scenario == "http_error":
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
    elif error_scenario == "json_error":
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

    result = stock_price(['AAPL'])
    assert result == expected_result


# ТЕСТ ДЛЯ GET_EXPENSE
def test_get_expense_empty_list():
    """Тест с пустым списком"""
    result = get_expense([])
    assert result == []


def test_get_expense_no_negative_amounts():
    """Тест без трат (только доходы)"""
    data = [
        {'card': '1234567890123456', 'amount': 100.0},
        {'card': '6543210987654321', 'amount': 200.0},
    ]
    result = get_expense(data)
    assert result == []


def test_get_expense_single_card():
    """Тест с одной картой"""
    data = [
        {'card': '1234567890123456', 'amount': -100.0},
        {'card': '1234567890123456', 'amount': -200.50},
        {'card': '1234567890123456', 'amount': 300.0},  # доход - игнорируется
    ]
    result = get_expense(data)

    assert len(result) == 1
    assert result[0]['last_digits'] == '234567890123456'
    assert result[0]['total_spent'] == 300.5
    assert result[0]['cashback'] == 3.0


# ТЕСТ ДЛЯ SORTED_BY_RANGE
def test_sorted_by_range_empty():
    """Тест с пустым списком транзакций"""
    test_date = datetime(2023, 5, 15)
    data = []

    result = sorted_by_range(data, test_date, 'M')
    assert result == []


def test_month_range(test_data, january_2021_date):
    """Тест фильтрации по месяцу"""
    result = sorted_by_range(test_data, january_2021_date, 'M')

    result_dates = [item['date'] for item in result]
    expected_dates = ['01.01.2021 10:00:00', '15.01.2021 14:30:00', '31.01.2021 23:59:59']

    assert result_dates == expected_dates


def test_year_range(test_data, december_2021_date):
    """Тест фильтрации по году"""
    result = sorted_by_range(test_data, december_2021_date, 'Y')

    result_dates = [item['date'] for item in result]
    expected_dates = ['01.01.2021 10:00:00', '15.01.2021 14:30:00', '31.01.2021 23:59:59', '01.02.2021 00:00:00']

    assert result_dates == expected_dates


def test_all_range(test_data, mid_january_2021_date):
    """Тест фильтрации за весь период"""
    result = sorted_by_range(test_data, mid_january_2021_date, 'ALL')

    result_dates = [item['date'] for item in result]
    expected_dates = [
        '01.01.2021 10:00:00',
        '15.01.2021 14:30:00',
        '01.01.2020 09:00:00',
        '15.01.2020 12:00:00'
    ]

    assert result_dates == expected_dates


def test_week_range(test_data):
    """Тест фильтрации по неделе"""
    date = datetime(2021, 1, 15, 12, 0, 0)  # Пятница
    result = sorted_by_range(test_data, date, 'W')

    result_dates = [item['date'] for item in result]

    expected_dates = []

    assert result_dates == expected_dates


# ТЕСТ ДЛЯ GET_EXPENSE_BY_CATEGORY
def test_expense_by_category_basic(expense_data):
    """Тест базовой функциональности группировки расходов по категориям"""
    result = get_expense_by_category(expense_data)

    expected = [
        {"category": "transport", "amount": -800},  # -500 + -300
        {"category": "entertainment", "amount": -1000},
        {"category": "food", "amount": -4500},  # -1500 + -2000 + -1000
    ]

    assert result == expected


def test_expense_by_category_positive(expense_data_with_positive_only):
    """Тест с данными, содержащими только положительные суммы (доходы)"""
    result = get_expense_by_category(expense_data_with_positive_only)

    assert result == []


def test_expense_by_category_negative(expense_data_with_negative_only):
    """Тест с данными, содержащими только отрицательные суммы (расходы)"""
    result = get_expense_by_category(expense_data_with_negative_only)

    expected = [
        {"category": "transport", "amount": -500},
        {"category": "food", "amount": -1500},
        {"category": "rent", "amount": -30000},
    ]

    assert result == expected


def test_expense_by_category_empty_input():
    """Тест с пустым входным списком"""
    result = get_expense_by_category([])

    assert result is None


def test_expense_by_category_single_category(expense_data_single_category):
    """Тест с данными одной категории"""
    result = get_expense_by_category(expense_data_single_category)

    expected = [
        {"category": "food", "amount": -4500},  # -1000 + -2000 + -1500
    ]

    assert result == expected


def test_expense_by_category_sorting_order():
    """Тест правильности сортировки по убыванию суммы"""
    data = [
        {'category': 'A', 'amount': -100},
        {'category': 'B', 'amount': -500},
        {'category': 'C', 'amount': -300},
    ]

    result = get_expense_by_category(data)

    # Проверяем порядок сортировки: от наибольшей суммы к наименьшей
    expected = [
        {"category": "A", "amount": -100},
        {"category": "C", "amount": -300},
        {"category": "B", "amount": -500},
    ]

    assert result == expected


def test_expense_by_category_rounding():
    """Тест округления сумм"""
    data = [
        {'category': 'food', 'amount': -1499.4},
        {'category': 'food', 'amount': -1000.6},
        {'category': 'transport', 'amount': -500.4},
    ]

    result = get_expense_by_category(data)

    expected = [
        {"category": "transport", "amount": -500},
        {"category": "food", "amount": -2500},
    ]

    assert result == expected


def test_expense_by_category_missing_fields():
    """Тест с данными, где отсутствуют необходимые поля"""
    data = [
        {'category': 'food', 'amount': -100},
        {'amount': -200},  # отсутствует category
        {'category': 'transport'},  # отсутствует amount
        {'invalid': 'data'},  # отсутствуют оба поля
    ]

    result = get_expense_by_category(data)

    # Должен обработать только корректные записи
    expected = [
        {"category": "food", "amount": -100},
    ]

    assert result == expected


# ТЕСТ ДЛЯ GET_TOP_SEVEN_CATEGORY
def test_top_seven_category_basic(top_category_data):
    """Тест базовой функциональности топа 7 категорий"""
    result = get_top_seven_category(top_category_data)

    # Проверяем что вернулось 7 транзакций (не категорий)
    assert len(result) == 7

    # Проверяем что транзакции отсортированы по убыванию суммы расхода (наибольшие сначала)
    # Функция возвращает отдельные транзакции, а не суммарные по категориям
    expected_categories_order = ['Жилье', 'Образование', 'Путешествия', 'Техника', 'Одежда', 'Спорт', 'Здоровье']
    result_categories = [item['category'] for item in result]

    assert result_categories == expected_categories_order

    # Проверяем что суммы положительные
    for item in result:
        assert item['amount'] > 0

    # Проверяем конкретные суммы (абсолютные значения исходных отрицательных сумм)
    expected_amounts = [30000, 15000, 12000, 8000, 4000, 3000, 2500]
    result_amounts = [item['amount'] for item in result]

    assert result_amounts == expected_amounts


def test_top_seven_category_less_than_seven(top_category_data_less_than_seven):
    """Тест с количеством категорий меньше 7"""
    result = get_top_seven_category(top_category_data_less_than_seven)

    # Должны вернуться все 5 категорий
    assert len(result) == 5

    # Проверяем порядок и суммы
    expected_categories = ['Жилье', 'Здоровье', 'Еда', 'Развлечения', 'Транспорт']
    result_categories = [item['category'] for item in result]

    assert result_categories == expected_categories


def test_top_seven_category_empty_input():
    """Тест с пустым входным списком"""
    result = get_top_seven_category([])

    # Должен вернуть None для пустых входных данных
    assert result is None


def test_top_seven_category_only_excluded(top_category_data_with_excluded_only):
    """Тест только с исключаемыми категориями"""
    result = get_top_seven_category(top_category_data_with_excluded_only)

    # Должен вернуть пустой список, так как все категории исключены
    assert result == []


def test_top_seven_category_only_positive(top_category_data_with_positive_only):
    """Тест только с положительными суммами (доходами)"""
    result = get_top_seven_category(top_category_data_with_positive_only)

    # Должен вернуть пустой список, так как нет расходов
    assert result == []


def test_top_seven_category_single_large_expense(top_category_data_single_large_expense):
    """Тест с одним большим расходом"""
    result = get_top_seven_category(top_category_data_single_large_expense)

    expected = [
        {'category': 'Жилье', 'amount': 50000},
        {'category': 'Транспорт', 'amount': 200},
        {'category': 'Еда', 'amount': 100},
    ]

    assert result == expected


def test_top_seven_category_exact_seven():
    """Тест с точно 7 категориями (без исключаемых)"""
    data = [
        {'category': 'Категория1', 'amount': -7000},
        {'category': 'Категория2', 'amount': -6000},
        {'category': 'Категория3', 'amount': -5000},
        {'category': 'Категория4', 'amount': -4000},
        {'category': 'Категория5', 'amount': -3000},
        {'category': 'Категория6', 'amount': -2000},
        {'category': 'Категория7', 'amount': -1000},
    ]

    result = get_top_seven_category(data)

    assert len(result) == 7

    # Проверяем порядок от наибольшей суммы к наименьшей
    expected_categories = ['Категория1', 'Категория2', 'Категория3', 'Категория4', 'Категория5', 'Категория6',
                           'Категория7']
    result_categories = [item['category'] for item in result]

    assert result_categories == expected_categories


def test_top_seven_category_mixed_excluded():
    """Тест со смесью исключаемых и обычных категорий"""
    data = [
        {'category': 'Еда', 'amount': -1000},
        {'category': 'Переводы', 'amount': -5000},  # исключаемая
        {'category': 'Транспорт', 'amount': -2000},
        {'category': 'Бонусы', 'amount': -100},  # исключаемая
        {'category': 'Жилье', 'amount': -30000},
        {'category': 'Наличные', 'amount': -50},  # исключаемая
        {'category': 'Развлечения', 'amount': -1500},
        {'category': 'Пополнения', 'amount': -10},  # исключаемая
    ]

    result = get_top_seven_category(data)

    # Должны остаться только обычные категории
    expected_categories = ['Жилье', 'Транспорт', 'Развлечения', 'Еда']
    result_categories = [item['category'] for item in result]

    assert result_categories == expected_categories


def test_top_seven_category_amount_conversion():
    """Тест преобразования отрицательных сумм в положительные"""
    data = [
        {'category': 'Еда', 'amount': -1500.75},
        {'category': 'Транспорт', 'amount': -500.25},
    ]

    result = get_top_seven_category(data)

    # Суммы должны быть положительными
    for item in result:
        assert item['amount'] > 0

    # Проверяем конкретные значения (функция берет абсолютное значение)
    expected_amounts = [1500.75, 500.25]
    result_amounts = [item['amount'] for item in result]

    assert result_amounts == expected_amounts


def test_top_seven_category_sorting_logic():
    """Тест логики сортировки (ascending=True для отрицательных чисел)"""
    data = [
        {'category': 'A', 'amount': -100},  # наименьший расход
        {'category': 'B', 'amount': -500},  # наибольший расход
        {'category': 'C', 'amount': -300},  # средний расход
    ]

    result = get_top_seven_category(data)

    expected = [
        {'category': 'B', 'amount': 500},
        {'category': 'C', 'amount': 300},
        {'category': 'A', 'amount': 100},
    ]

    assert result == expected


# ТЕСТ ДЛЯ GET_OTHER_CATEGORY
def test_other_category_basic(other_category_data):
    """Тест базовой функциональности остальных категорий"""
    result = get_other_category(other_category_data)

    # Должен вернуть список с одним элементом "Остальное"
    assert len(result) == 1
    assert result[0]['category'] == 'Остальное'

    # Сумма должна быть положительной
    assert result[0]['amount'] > 0

    # Проверяем вычисленную сумму
    expected_amount = 2000 + 2000 + 1800 + 1500 + 1500 + 1200 + 1000 + 500 + 300
    assert result[0]['amount'] == expected_amount


def test_other_category_less_than_eight(other_category_data_less_than_eight):
    """Тест с количеством транзакций меньше 8"""
    result = get_other_category(other_category_data_less_than_eight)

    # Должен вернуть сумму 0, так как нет транзакций после топ-7
    assert result == [{"category": "Остальное", "amount": 0}]


def test_other_category_exactly_seven(other_category_data_exactly_seven):
    """Тест с точно 7 транзакциями"""
    result = get_other_category(other_category_data_exactly_seven)

    # Должен вернуть сумму 0, так как все транзакции входят в топ-7
    assert result == [{"category": "Остальное", "amount": 0}]


def test_other_category_empty_input():
    """Тест с пустым входным списком"""
    result = get_other_category([])

    # Должен вернуть None для пустых входных данных
    assert result is None


def test_other_category_only_excluded(other_category_data_with_excluded_only):
    """Тест только с исключаемыми категориями"""
    result = get_other_category(other_category_data_with_excluded_only)

    # Должен вернуть сумму 0, так как все категории исключены
    assert result == [{"category": "Остальное", "amount": 0}]


def test_other_category_only_positive(other_category_data_with_positive_only):
    """Тест только с положительными суммами (доходами)"""
    result = get_other_category(other_category_data_with_positive_only)

    # Должен вернуть сумму 0, так как нет расходов
    assert result == [{"category": "Остальное", "amount": 0}]


def test_other_category_single_category_multiple(other_category_data_single_category_multiple):
    """Тест с одной категорией, но множеством транзакций"""
    result = get_other_category(other_category_data_single_category_multiple)

    expected_amount = 300 + 200 + 100
    assert result == [{"category": "Остальное", "amount": expected_amount}]


# ТЕСТ ДЛЯ GET_TRANSFER_AND_CASH
def test_transfer_and_cash_basic(transfer_cash_data):
    """Тест базовой функциональности переводов и наличных"""
    result = get_transfer_and_cash(transfer_cash_data)

    # Проверяем что вернулось 2 категории
    assert len(result) == 2

    # Проверяем что категории отсортированы по убыванию суммы
    expected_categories = ['Переводы', 'Наличные']
    result_categories = [item['category'] for item in result]

    assert result_categories == expected_categories

    # Проверяем суммы (абсолютные значения отрицательных сумм)
    expected_amounts = [3500, 800]
    result_amounts = [item['amount'] for item in result]

    assert result_amounts == expected_amounts


def test_transfer_and_cash_only_transfers(transfer_cash_data_only_transfers):
    """Тест только с переводами"""
    result = get_transfer_and_cash(transfer_cash_data_only_transfers)

    assert len(result) == 1
    assert result[0]['category'] == 'Переводы'
    assert result[0]['amount'] == 4500


def test_transfer_and_cash_only_cash(transfer_cash_data_only_cash):
    """Тест только с наличными"""
    result = get_transfer_and_cash(transfer_cash_data_only_cash)

    assert len(result) == 1
    assert result[0]['category'] == 'Наличные'
    assert result[0]['amount'] == 1000


def test_transfer_and_cash_case_insensitive(transfer_cash_data_case_insensitive):
    """Тест регистронезависимости категорий"""
    result = get_transfer_and_cash(transfer_cash_data_case_insensitive)

    # Функция находит категории без учета регистра, но группирует с учетом регистра
    # Поэтому разные варианты написания считаются разными категориями
    assert len(result) == 4

    # Проверяем что все варианты регистра найдены и суммы посчитаны правильно
    result_dict = {item['category']: item['amount'] for item in result}

    assert result_dict['переводы'] == 1000
    assert result_dict['ПЕРЕВОДЫ'] == 2000
    assert result_dict['НаличныЕ'] == 500
    assert result_dict['наличные'] == 300


def test_transfer_and_cash_empty_input():
    """Тест с пустым входным списком"""
    result = get_transfer_and_cash([])
    assert result is None


def test_transfer_and_cash_no_matching(transfer_cash_data_no_matching):
    """Тест без подходящих категорий"""
    result = get_transfer_and_cash(transfer_cash_data_no_matching)

    # Должен вернуть пустой список
    assert result == []


# ТЕСТ ДЛЯ GET_INCOME
def test_income_basic(income_data):
    """Тест базовой функциональности доходов"""
    result = get_income(income_data)

    # Проверяем количество элементов
    assert len(result) == 4

    # Проверяем сортировку по убыванию суммы
    expected_descriptions = ['Зарплата', 'Фриланс', 'Инвестиции', 'Подарок']
    result_descriptions = [item['category'] for item in result]

    assert result_descriptions == expected_descriptions

    # Проверяем суммы
    expected_amounts = [25000, 5000, 3000, 2000]
    result_amounts = [item['amount'] for item in result]

    assert result_amounts == expected_amounts


def test_income_only_expenses(income_data_only_expenses):
    """Тест только с расходами"""
    result = get_income(income_data_only_expenses)

    # Должен вернуть пустой список, так как нет доходов
    assert result == []


def test_income_empty_input():
    """Тест с пустым входным списком"""
    result = get_income([])

    # Должен вернуть None для пустых входных данных
    assert result is None


def test_income_single_description(income_data_single_description):
    """Тест с одним описанием доходов"""
    result = get_income(income_data_single_description)

    assert len(result) == 1
    assert result[0]['category'] == 'Зарплата'
    assert result[0]['amount'] == 18000


def test_income_case_sensitive(income_data_mixed_case):
    """Тест чувствительности к регистру описаний"""
    result = get_income(income_data_mixed_case)

    # Функция группирует с учетом регистра, поэтому разные варианты считаются разными категориями
    assert len(result) == 3

    # Проверяем что все варианты регистра найдены
    result_dict = {item['category']: item['amount'] for item in result}

    assert result_dict['зарплата'] == 10000
    assert result_dict['Зарплата'] == 5000
    assert result_dict['ЗАРПЛАТА'] == 3000


def test_income_rounding():
    """Тест округления сумм доходов"""
    data = [
        {'description': 'Зарплата', 'amount': 10000.4},
        {'description': 'Зарплата', 'amount': 5000.6},
        {'description': 'Фриланс', 'amount': 3000.5},
    ]

    result = get_income(data)

    # Суммы должны быть округлены до целых
    result_dict = {item['category']: item['amount'] for item in result}

    assert result_dict['Зарплата'] == 15001
    assert result_dict['Фриланс'] == 3000


# ТЕСТ ДЛЯ GET_TOTAL_AMOUNT
def test_total_amount_basic(total_amount_data):
    """Тест базовой функциональности общей суммы расходов"""
    result = get_total_amount(total_amount_data)

    # Сумма расходов: 1500 + 500 + 2000 = 4000
    expected = 4000
    assert result == expected


def test_total_amount_only_income(total_amount_data_only_income):
    """Тест только с доходами"""
    result = get_total_amount(total_amount_data_only_income)

    # Должен вернуть 0, так как нет расходов
    assert result == 0


def test_total_amount_empty_input():
    """Тест с пустым входным списком"""
    result = get_total_amount([])

    # Должен вернуть 0 для пустых входных данных
    assert result == 0


def test_total_amount_mixed(total_amount_data_mixed):
    """Тест со смешанными доходами и расходами"""
    result = get_total_amount(total_amount_data_mixed)

    # Сумма только расходов: 1000 + 500 + 1500 = 3000
    expected = 3000
    assert result == expected


def test_total_amount_decimals(total_amount_data_with_decimals):
    """Тест с десятичными числами"""
    result = get_total_amount(total_amount_data_with_decimals)

    # Сумма с округлением: 1000.4 + 500.6 + 1500.8 = 3001.8 → 3002
    expected = 3002
    assert result == expected


def test_total_amount_single_expense(total_amount_data_single_expense):
    """Тест с одним расходом"""
    result = get_total_amount(total_amount_data_single_expense)

    assert result == 5000


def test_total_amount_no_amount_column():
    """Тест с данными без колонки amount"""
    data = [
        {'category': 'Еда', 'description': 'Продукты'},
        {'category': 'Транспорт', 'description': 'Такси'},
    ]

    result = get_total_amount(data)

    # Должен вернуть 0 и залогировать предупреждение
    assert result == 0


def test_total_amount_negative_to_positive():
    """Тест преобразования отрицательной суммы в положительную"""
    data = [
        {'amount': -1000},
        {'amount': -2000},
    ]

    result = get_total_amount(data)

    # Сумма должна быть положительной
    assert result > 0
    assert result == 3000


# ТЕСТ ДЛЯ GET_TOTAL_AMOUNT_INCOME
def test_total_amount_income_basic(total_income_data):
    """Тест базовой функциональности общей суммы доходов"""
    result = get_total_amount_income(total_income_data)

    # Сумма доходов: 10000 + 5000 + 3000 = 18000
    expected = 18000
    assert result == expected


def test_total_amount_income_empty_input():
    """Тест с пустым входным списком"""
    result = get_total_amount_income([])

    # Должен вернуть 0 для пустых входных данных
    assert result == 0


def test_total_amount_income_none_input():
    """Тест с None входными данными"""
    result = get_total_amount_income(None)

    # Должен вернуть 0 для None
    assert result == 0


def test_total_amount_income_single(total_income_data_single):
    """Тест с одним доходом"""
    result = get_total_amount_income(total_income_data_single)

    assert result == 15000


def test_total_amount_income_with_negative(total_income_data_with_negative):
    """Тест с отрицательными суммами"""
    result = get_total_amount_income(total_income_data_with_negative)

    # Сумма: 10000 + (-500) = 9500
    expected = 9500
    assert result == expected


def test_total_amount_income_large_numbers(total_income_data_large_numbers):
    """Тест с большими числами"""
    result = get_total_amount_income(total_income_data_large_numbers)

    # Сумма: 100000 + 50000 + 75000 = 225000
    expected = 225000
    assert result == expected


def test_total_amount_income_zero_amounts():
    """Тест с нулевыми суммами"""
    data = [
        {'category': 'Зарплата', 'amount': 0},
        {'category': 'Фриланс', 'amount': 5000},
        {'category': 'Бонус', 'amount': 0},
    ]

    result = get_total_amount_income(data)

    expected = 5000
    assert result == expected


def test_total_amount_income_decimal_numbers():
    """Тест с десятичными числами"""
    data = [
        {'category': 'Зарплата', 'amount': 10000.50},
        {'category': 'Фриланс', 'amount': 5000.25},
        {'category': 'Бонус', 'amount': 3000.75},
    ]

    result = get_total_amount_income(data)

    # Сумма: 10000.50 + 5000.25 + 3000.75 = 18001.50
    expected = 18001.5
    assert result == expected


# ТЕСТ ДЛЯ GET_CASHBACK
def test_cashback_basic(cashback_data):
    """Тест базовой функциональности кэшбэка"""
    result = get_cashback(cashback_data)

    # Должен вернуть список с одним элементом
    assert len(result) == 1
    assert result[0]['category'] == 'Кэшбэк'

    # Сумма кэшбэка: 100 + 50 + 200 + 0 = 350
    expected_amount = 350
    assert result[0]['amount'] == expected_amount


def test_cashback_empty_input():
    """Тест с пустым входным списком"""
    result = get_cashback([])

    # Должен вернуть None для пустых входных данных
    assert result is None


def test_cashback_single(cashback_data_single):
    """Тест с одним элементом кэшбэка"""
    result = get_cashback(cashback_data_single)

    assert len(result) == 1
    assert result[0]['category'] == 'Кэшбэк'
    assert result[0]['amount'] == 500


def test_cashback_decimals(cashback_data_decimals):
    """Тест с десятичными числами кэшбэка"""
    result = get_cashback(cashback_data_decimals)

    # Сумма с округлением: 100.4 + 50.6 + 200.8 = 351.8 → 352
    expected_amount = 352
    assert result[0]['amount'] == expected_amount


def test_cashback_negative(cashback_data_negative):
    """Тест с отрицательным кэшбэком"""
    result = get_cashback(cashback_data_negative)

    # Сумма: 100 + (-50) + 200 = 250
    expected_amount = 250
    assert result[0]['amount'] == expected_amount


def test_cashback_no_cashback(cashback_data_no_cashback):
    """Тест без кэшбэка (все нули)"""
    result = get_cashback(cashback_data_no_cashback)

    # Должен вернуть 0
    assert result[0]['amount'] == 0


def test_cashback_large_numbers():
    """Тест с большими числами кэшбэка"""
    data = [
        {'cashback': 10000, 'amount': -150000, 'category': 'Еда'},
        {'cashback': 5000, 'amount': -50000, 'category': 'Транспорт'},
        {'cashback': 20000, 'amount': -200000, 'category': 'Развлечения'},
    ]

    result = get_cashback(data)

    # Сумма: 10000 + 5000 + 20000 = 35000
    expected_amount = 35000
    assert result[0]['amount'] == expected_amount
