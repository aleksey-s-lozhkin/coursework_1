import pytest
import json
import os
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

from src.utils import log_function, greeting, read_user_setting



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
@pytest.mark.parametrize("hour,expected", [
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
])
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
    mock_json_load.return_value = {
        'user_currencies': ['USD', 'EUR'],
        'user_stocks': ['AAPL', 'TSLA']
    }

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

