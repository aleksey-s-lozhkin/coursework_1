import logging
import os
import sys
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.reports import (
    decorator_output_to,
    get_data_by_range,
    get_dataframe_from_excel,
    reports_log_function,
    spending_by_category,
    spending_by_weekday,
    spending_by_workday,
)


# Тесты для декораторов
@patch('src.reports.os.makedirs')
@patch('src.reports.open')
def test_decorator_output_to_success(mock_open, mock_makedirs):
    """Тест декоратора записи в файл"""
    mock_file = MagicMock()
    mock_open.return_value.__enter__ = mock_file
    mock_open.return_value.__exit__ = MagicMock()

    test_df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})

    @decorator_output_to(filename='test.json')
    def test_function():
        return test_df

    result = test_function()

    # Проверяем, что функция возвращает правильный результат
    pd.testing.assert_frame_equal(result, test_df)

    # Проверяем, что файл был открыт для записи
    mock_open.assert_called_once()


def test_decorator_output_to_default_filename():
    """Тест декоратора записи в файл с именем по умолчанию"""
    test_df = pd.DataFrame({'A': [1, 2]})

    @decorator_output_to()
    def test_function():
        return test_df

    result = test_function()
    pd.testing.assert_frame_equal(result, test_df)


@patch('src.reports.open')
def test_decorator_output_to_write_error(mock_open):
    """Тест декоратора при ошибке записи в файл"""
    mock_open.side_effect = Exception("Write error")

    test_df = pd.DataFrame({'A': [1, 2]})

    @decorator_output_to(filename='test.json')
    def test_function():
        return test_df

    # Функция должна завершиться успешно, несмотря на ошибку записи
    result = test_function()
    pd.testing.assert_frame_equal(result, test_df)


def test_reports_log_function_decorator():
    """Тест декоратора логирования"""

    @reports_log_function
    def test_function():
        return "success"

    result = test_function()
    assert result == "success"


def test_reports_log_function_decorator_with_exception():
    """Тест декоратора логирования с исключением"""

    @reports_log_function
    def test_function():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        test_function()


# ТЕСТИРОВАНИЕ ФУНКЦИИ GET_DATA_FROM_EXCEL
def test_get_dataframe_from_excel_success(sample_excel_file):
    """Тест успешного чтения Excel файла"""
    result = get_dataframe_from_excel(sample_excel_file)

    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert 'Категория' in result.columns
    assert 'Сумма операции' in result.columns


def test_get_dataframe_from_excel_file_not_found():
    """Тест обработки отсутствующего файла"""
    result = get_dataframe_from_excel('nonexistent_file.xlsx')
    assert result is None


def test_get_dataframe_from_excel_empty_file():
    """Тест обработки пустого файла"""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        # Создаем пустой файл
        pass

    try:
        result = get_dataframe_from_excel(f.name)
        assert result is None
    finally:
        if os.path.exists(f.name):
            os.unlink(f.name)


# ТЕСТИРОВАНИЕ ФУНКЦИИ GET_DATA_BY_RANGE
def test_get_data_by_range_success(sample_transactions):
    """Тест успешной фильтрации по диапазону дат"""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 2, 1)

    result = get_data_by_range(sample_transactions, start_date, end_date)

    assert result is not None
    assert len(result) == 3  # 3 транзакции в январе-феврале 2024


def test_get_data_by_range_empty_dataframe(empty_dataframe):
    """Тест фильтрации пустого DataFrame"""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 2, 1)

    result = get_data_by_range(empty_dataframe, start_date, end_date)
    assert result is None


def test_get_data_by_range_invalid_dates(sample_transactions):
    """Тест фильтрации с некорректными датами"""
    start_date = datetime(2024, 2, 1)
    end_date = datetime(2024, 1, 1)  # start_date > end_date

    result = get_data_by_range(sample_transactions, start_date, end_date)
    assert result is None


def test_get_data_by_range_missing_date_column():
    """Тест фильтрации DataFrame без колонки даты"""
    df_without_date = pd.DataFrame({'Категория': ['Еда', 'Транспорт'], 'Сумма': [1000, 500]})

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 2, 1)

    result = get_data_by_range(df_without_date, start_date, end_date)
    assert result is None


# ТЕСТИРОВАНИЕ ФУНКЦИИ SPENDING_BY_CATEGORY
def test_spending_by_category_success(sample_transactions):
    """Тест успешного получения трат по категории"""
    result = spending_by_category(sample_transactions, 'Еда', '15.03.2024')

    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert all(result['Категория'] == 'Еда')


def test_spending_by_category_empty_transactions(empty_dataframe):
    """Тест получения трат по категории с пустыми данными"""
    result = spending_by_category(empty_dataframe, 'Еда')

    # Проверяем, что возвращается пустой DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_spending_by_category_no_category(sample_transactions):
    """Тест получения трат без указания категории"""
    result = spending_by_category(sample_transactions, '')

    # Проверяем, что возвращается пустой DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_spending_by_category_invalid_date(sample_transactions):
    """Тест получения трат с некорректной датой"""
    result = spending_by_category(sample_transactions, 'Еда', 'invalid_date')

    # Проверяем, что возвращается пустой DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_spending_by_category_no_data_in_period(sample_transactions):
    """Тест получения трат по категории, когда нет данных за период"""
    # Используем дату из далекого будущего, когда данных нет
    result = spending_by_category(sample_transactions, 'Еда', '01.01.2030')
    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


# ТЕСТИРОВАНИЕ ФУНКЦИИ SPENDING_BY_WEEKDAY
def test_spending_by_weekday_success(sample_transactions):
    """Тест успешного получения средних трат по дням недели"""
    result = spending_by_weekday(sample_transactions, '15.03.2024')

    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert 'День недели' in result.columns
    assert 'Сумма операции' in result.columns
    assert len(result) > 0


def test_spending_by_weekday_empty_transactions(empty_dataframe):
    """Тест получения трат по дням недели с пустыми данными"""
    result = spending_by_weekday(empty_dataframe)

    # Проверяем, что возвращается пустой DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_spending_by_weekday_invalid_date(sample_transactions):
    """Тест получения трат по дням недели с некорректной датой"""
    result = spending_by_weekday(sample_transactions, 'invalid_date')

    # Проверяем, что возвращается пустой DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty


# ТЕСТИРОВАНИЕ ФУНКЦИИ SPENDING_BY_WORKDAY
def test_spending_by_workday_success(sample_transactions):
    """Тест успешного получения средних трат по рабочим/выходным дням"""
    result = spending_by_workday(sample_transactions, '15.03.2024')

    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert 'Тип дня' in result.columns
    assert 'Сумма операции' in result.columns
    assert len(result) == 1  # Рабочий и Выходной


def test_spending_by_workday_empty_transactions(empty_dataframe):
    """Тест получения трат по рабочим/выходным с пустыми данными"""
    result = spending_by_workday(empty_dataframe)

    # Проверяем, что возвращается пустой DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_spending_by_workday_invalid_date(sample_transactions):
    """Тест получения трат по рабочим/выходным с некорректной датой"""
    result = spending_by_workday(sample_transactions, 'invalid_date')

    # Проверяем, что возвращается пустой DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty


# ТЕСТ С ПАРАМЕТРИЗАЦИЕЙ ДЛЯ ПРОВЕРКИ ОБРАБОТКИ ОШИБОК
@pytest.mark.parametrize(
    "exception,expected_log_part",
    [
        (FileNotFoundError(), "не найден"),
        (ValueError("Sheet error"), "Ошибка в данных файла или лист"),
        (PermissionError(), "Нет прав доступа"),
        (ImportError("No module"), "Отсутствуют необходимые библиотеки"),
        (Exception("Any error"), "Неизвестная ошибка"),
    ],
)
def test_all_exceptions_parametrized(exception, expected_log_part, caplog):
    """Параметризованный тест всех исключений"""
    with (
        patch('os.path.exists', return_value=True),
        patch('os.path.getsize', return_value=100),
        patch('pandas.read_excel', side_effect=exception),
    ):
        result = get_dataframe_from_excel('test_file.xlsx')

    assert result is None
    assert expected_log_part in caplog.text
