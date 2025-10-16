import json
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

from src.services import (
    person_search,
    phone_search,
    services_log_function,
    simple_search,
    investment_bank,
    get_boosted_cashback_categories,
)


# ТЕСТЫ ДЛЯ ЛОГЕРА
def test_reports_log_function_decorator():
    """Тест декоратора логирования"""

    @services_log_function
    def test_function():
        return "success"

    result = test_function()
    assert result == "success"


def test_reports_log_function_decorator_with_exception():
    """Тест декоратора логирования с исключением"""

    @services_log_function
    def test_function():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        test_function()


# ТЕСТЫ ДЛЯ PERSON_SEARCH
def test_empty_input_returns_none():
    """Проверяет возврат None при пустом списке"""
    result = person_search([])
    assert result is None


# def test_none_input_returns_none():
#     """Проверяет возврат None при None входе"""
#     result = person_search(None)
#     assert result is None


def test_finds_transactions_with_fio_and_transfers_category():
    """Проверяет нахождение транзакций с ФИО и категорией Переводы"""
    test_data = [
        {'description': 'Перевод Иванов И.И.', 'category': 'Переводы', 'amount': 1000},
        {'description': 'Оплата в магазине', 'category': 'Покупки', 'amount': 500},
    ]

    result = person_search(test_data)
    parsed_result = json.loads(result)

    assert len(parsed_result) == 1
    assert parsed_result[0]['description'] == 'Перевод Иванов И.И.'


def test_no_matching_transactions_returns_empty_json_array():
    """Проверяет возврат пустого JSON массива при отсутствии подходящих транзакций"""
    test_data = [
        {'description': 'Оплата в магазине', 'category': 'Покупки'},
        {'description': 'Перевод банку', 'category': 'Банковские услуги'},
    ]

    result = person_search(test_data)
    assert result == '[]'


# ТЕСТЫ ДЛЯ PHONE_SEARCH
def test_empty_input_returns_none_phone_search():
    """Проверяет возврат None при пустом списке"""
    result = phone_search([])
    assert result is None


def test_no_phone_numbers_returns_empty_json_array():
    """Проверяет возврат пустого JSON массива при отсутствии номеров телефонов"""
    test_data = [
        {'description': 'Оплата в магазине', 'category': 'Покупки'},
        {'description': 'Перевод по карте', 'category': 'Переводы'},
    ]

    result = phone_search(test_data)
    assert result == '[]'  # Пустой JSON массив


def test_finds_transactions_with_phone_numbers():
    """Проверяет нахождение транзакций с номерами телефонов"""
    test_data = [
        {'description': 'Пополнение +79161234567', 'category': 'Мобильная связь', 'amount': 500},
        {'description': 'Оплата 8-916-123-45-68', 'category': 'Услуги', 'amount': 1000},
        {'description': 'Оплата в магазине', 'category': 'Покупки', 'amount': 300},
    ]

    result = phone_search(test_data)
    parsed_result = json.loads(result)

    assert len(parsed_result) == 2
    descriptions = [item['description'] for item in parsed_result]
    assert 'Пополнение +79161234567' in descriptions
    assert 'Оплата 8-916-123-45-68' in descriptions


# ТЕСТЫ ДЛЯ SIMPLE_SEARCH
def test_empty_transactions_returns_none():
    """Проверяет возврат None при пустом списке транзакций"""
    result = simple_search("запрос", [])
    assert result is None


def test_no_matching_transactions_simple_search():
    """Проверяет возврат пустого JSON массива при отсутствии совпадений"""
    test_data = [
        {'description': 'Оплата в магазине', 'category': 'Покупки'},
        {'description': 'Перевод другу', 'category': 'Переводы'},
    ]

    result = simple_search("несуществующий", test_data)
    assert result == '[]'  # Пустой JSON массив


def test_finds_transactions_by_description():
    """Проверяет поиск по описанию транзакций"""
    test_data = [
        {'description': 'Оплата такси', 'category': 'Транспорт', 'amount': 300},
        {'description': 'Покупка в магазине', 'category': 'Покупки', 'amount': 500},
        {'description': 'Оплата интернета', 'category': 'Услуги', 'amount': 700},
    ]

    result = simple_search("такси", test_data)
    parsed_result = json.loads(result)

    assert len(parsed_result) == 1
    assert parsed_result[0]['description'] == 'Оплата такси'


def test_finds_transactions_by_category():
    """Проверяет поиск по категории транзакций"""
    test_data = [
        {'description': 'Оплата такси', 'category': 'Транспорт', 'amount': 300},
        {'description': 'Покупка в магазине', 'category': 'Покупки', 'amount': 500},
        {'description': 'Оплата интернета', 'category': 'Услуги', 'amount': 700},
    ]

    result = simple_search("покупки", test_data)
    parsed_result = json.loads(result)

    assert len(parsed_result) == 1
    assert parsed_result[0]['category'] == 'Покупки'


# ТЕСТЫ ДЛЯ INVESTMENT_BANK
@patch('src.services.services_logger')
@patch('src.services.get_last_day')
@patch('src.services.sorted_by_range')
def test_investment_logging_calls(mock_sorted, mock_last_day, mock_logger):
    """Проверяет корректность вызовов логирования и вспомогательных функций"""
    mock_last_day.return_value = datetime(2021, 1, 31)
    mock_sorted.return_value = [{'date': '2021-01-10', 'amount': -300, 'description': 'Тест'}]

    test_data = [{'date': '2021-01-10', 'amount': -300, 'description': 'Тест'}]

    result = investment_bank("2021-01", test_data, 100)

    # Проверяем вызов вспомогательных функций
    mock_last_day.assert_called_once_with(2021, 1)
    mock_sorted.assert_called_once()

    # Проверяем логирование
    assert mock_logger.debug.called
    assert mock_logger.info.called


def test_investment_empty_transactions_returns_none():
    """Проверяет расчет инвестиций при отсутствии транзакций"""
    result = investment_bank("2021-01", [], 100)
    assert result is None


def test_investment_filters_by_month_correctly():
    """Проверяет фильтрацию транзакций по указанному месяцу"""
    test_data = [
        {'date': '2021-01-10', 'amount': -550, 'description': 'Январь'},
        {'date': '2021-02-10', 'amount': -550, 'description': 'Февраль'},
        {'date': '2021-01-15', 'amount': -550, 'description': 'Январь'},
    ]

    # Мокаем sorted_by_range, чтобы он возвращал отфильтрованные данные
    with patch('src.services.sorted_by_range') as mock_sorted:
        # Возвращаем только январские транзакции
        mock_sorted.return_value = [
            {'date': '2021-01-10', 'amount': -550, 'description': 'Январь'},
            {'date': '2021-01-15', 'amount': -550, 'description': 'Январь'},
        ]

        result = investment_bank("2021-01", test_data, 100)

        # Проверяем, что sorted_by_range был вызван с правильными аргументами
        mock_sorted.assert_called_once()
        args = mock_sorted.call_args[0]

        # Первый аргумент - transactions
        assert args[0] == test_data
        # Второй аргумент - end_date (должен быть datetime)
        assert isinstance(args[1], datetime)
        # Третий аргумент - period_type (должен быть 'M')
        assert args[2] == 'M'

        # Проверяем результат расчета
        expected_json = json.dumps({"investment": 100}, indent=2, ensure_ascii=False)
        assert result == expected_json


# ТЕСТЫ ДЛЯ GET_BOOSTED_CASHBACK_CATEGORIES
def test_boosted_cashback_empty():
    """Проверяет возврат None при отсутствии данных после фильтрации"""
    with (
        patch('src.services.get_last_day') as mock_last_day,
        patch('src.services.read_xlsx') as mock_read_xlsx,
        patch('src.services.sorted_by_range') as mock_sorted,
    ):
        mock_last_day.return_value = MagicMock()
        mock_read_xlsx.return_value = [{'date': '2024-01-10', 'category': 'Еда', 'cashback': 100}]
        mock_sorted.return_value = []  # Пустой список после фильтрации

        result = get_boosted_cashback_categories("data.xlsx", "2024", "01")
        assert result is None


def test_boosted_cashback_calculates_correctly():
    """Проверяет корректный расчет кешбэка по категориям"""
    test_data = [
        {'date': '2024-01-10', 'category': 'Еда', 'cashback': 150.0},
        {'date': '2024-01-15', 'category': 'Еда', 'cashback': 250.0},
        {'date': '2024-01-20', 'category': 'Транспорт', 'cashback': 200.0},
        {'date': '2024-01-25', 'category': 'Развлечения', 'cashback': 0},
    ]

    with (
        patch('src.services.get_last_day') as mock_last_day,
        patch('src.services.read_xlsx') as mock_read_xlsx,
        patch('src.services.sorted_by_range') as mock_sorted,
    ):
        mock_last_day.return_value = MagicMock()
        mock_read_xlsx.return_value = test_data
        mock_sorted.return_value = test_data

        result = get_boosted_cashback_categories("data.xlsx", "2024", "01")
        parsed_result = json.loads(result)

        assert parsed_result["Еда"] == 400
        assert parsed_result["Транспорт"] == 200
        assert "Развлечения" not in parsed_result
