import json
from unittest.mock import MagicMock, patch

import pytest

from src.views import events, general


def test_general():
    # Мокаем все импортированные функции, которые используются в `general`
    with (
        patch('src.views.datetime') as mock_datetime,
        patch('src.views.os.path.dirname') as mock_dirname,
        patch('src.views.read_xlsx') as mock_read_xlsx,
        patch('src.views.sorted_by_date') as mock_sorted_by_date,
        patch('src.views.get_expense') as mock_get_expense,
        patch('src.views.top_five') as mock_top_five,
        patch('src.views.greeting') as mock_greeting,
        patch('src.views.read_user_setting') as mock_read_user_setting,
        patch('src.views.exchange_rate') as mock_exchange_rate,
        patch('src.views.stock_price') as mock_stock_price,
    ):

        # Настраиваем моки
        mock_datetime.strptime.return_value = MagicMock()
        mock_dirname.return_value = '/fake/path'
        mock_read_xlsx.return_value = [{'some': 'data'}]
        mock_sorted_by_date.return_value = [{'transaction': 'data'}]
        mock_get_expense.return_value = [{'card': 'data'}]
        mock_top_five.return_value = [{'top': 'transaction'}]
        mock_greeting.return_value = 'Добрый день'
        mock_read_user_setting.side_effect = lambda x: ['USD', 'EUR'] if x == 'user_currencies' else ['AAPL', 'TSLA']
        mock_exchange_rate.return_value = [{'currency': 'USD', 'rate': 75.0}]
        mock_stock_price.return_value = [{'stock': 'AAPL', 'price': 150.0}]

        # Вызываем функцию
        result = general('2023-10-15 12:00:00')

        # Проверяем, что результат - валидный JSON
        data = json.loads(result)

        # Проверяем наличие ожидаемых ключей
        assert 'greeting' in data
        assert 'cards' in data
        assert 'top_transaction' in data
        assert 'currency_rates' in data
        assert 'stock_prices' in data

        # Проверяем, что моки были вызваны
        mock_read_xlsx.assert_called_once()
        mock_sorted_by_date.assert_called_once()
        mock_get_expense.assert_called_once()
        mock_top_five.assert_called_once()
        mock_greeting.assert_called_once()
        assert mock_read_user_setting.call_count == 2
        mock_exchange_rate.assert_called_once_with(['USD', 'EUR'])
        mock_stock_price.assert_called_once_with(['AAPL', 'TSLA'])


def test_events():
    with (
        patch('src.views.datetime') as mock_datetime,
        patch('src.views.os.path.dirname') as mock_dirname,
        patch('src.views.read_xlsx') as mock_read_xlsx,
        patch('src.views.sorted_by_range') as mock_sorted_by_range,
        patch('src.views.get_expense_by_category') as mock_get_expense_by_category,
        patch('src.views.get_total_amount') as mock_get_total_amount,
        patch('src.views.get_top_seven_category') as mock_get_top_seven_category,
        patch('src.views.get_other_category') as mock_get_other_category,
        patch('src.views.get_transfer_and_cash') as mock_get_transfer_and_cash,
        patch('src.views.get_income') as mock_get_income,
        patch('src.views.get_cashback') as mock_get_cashback,
        patch('src.views.get_total_amount_income') as mock_get_total_amount_income,
        patch('src.views.read_user_setting') as mock_read_user_setting,
        patch('src.views.exchange_rate') as mock_exchange_rate,
        patch('src.views.stock_price') as mock_stock_price,
    ):

        # Настраиваем моки
        mock_datetime.strptime.return_value = MagicMock()
        mock_dirname.return_value = '/fake/path'
        mock_read_xlsx.return_value = [{'some': 'data'}]
        mock_sorted_by_range.return_value = [{'transaction': 'data'}]
        mock_get_expense_by_category.return_value = [{'category': 'food', 'amount': 100}]
        mock_get_total_amount.return_value = 1000
        mock_get_top_seven_category.return_value = [{'category': 'food', 'amount': 100}]
        mock_get_other_category.return_value = [{'category': 'other', 'amount': 50}]
        mock_get_transfer_and_cash.return_value = [{'category': 'transfer', 'amount': 200}]
        mock_get_income.return_value = [{'category': 'salary', 'amount': 500}]
        mock_get_cashback.return_value = [{'category': 'cashback', 'amount': 10}]
        mock_get_total_amount_income.return_value = 510
        mock_read_user_setting.side_effect = lambda x: ['USD'] if x == 'user_currencies' else ['AAPL']
        mock_exchange_rate.return_value = [{'currency': 'USD', 'rate': 75.0}]
        mock_stock_price.return_value = [{'stock': 'AAPL', 'price': 150.0}]

        # Вызываем функцию
        result = events('2023-10-15 12:00:00', 'M')

        # Проверяем, что результат - валидный JSON
        data = json.loads(result)

        # Проверяем наличие ожидаемых ключей
        assert 'expenses' in data
        assert 'income' in data
        assert 'currency_rates' in data
        assert 'stock_prices' in data

        # Проверяем структуру expenses
        expenses = data['expenses']
        assert 'total_amount' in expenses
        assert 'main' in expenses
        assert 'transfers_and_cash' in expenses

        # Проверяем структуру income
        income = data['income']
        assert 'total_amount' in income
        assert 'main' in income

        # Проверяем, что моки были вызваны
        mock_read_xlsx.assert_called_once()
        mock_sorted_by_range.assert_called_once()
        mock_get_expense_by_category.assert_called_once()
        mock_get_total_amount.assert_called_once()
        mock_get_top_seven_category.assert_called_once()
        mock_get_other_category.assert_called_once()
        mock_get_transfer_and_cash.assert_called_once()
        mock_get_income.assert_called_once()
        mock_get_cashback.assert_called_once()
        mock_get_total_amount_income.assert_called_once()
        assert mock_read_user_setting.call_count == 2
        mock_exchange_rate.assert_called_once_with(['USD'])
        mock_stock_price.assert_called_once_with(['AAPL'])
