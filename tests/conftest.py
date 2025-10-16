import os
import tempfile

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
    """Фикстура с пустым DataFrame"""
    return pd.DataFrame()
