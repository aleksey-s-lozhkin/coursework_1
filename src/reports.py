import os
import re
import logging
import json

from functools import wraps
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import pandas as pd


# Создаем путь к директории логов (два уровня выше от текущего файла)
logs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
# Создаем директорию, если она не существует
os.makedirs(logs_path, exist_ok=True)

# Создаем логгер для отчетов
reports_logger = logging.getLogger('reports')
# Устанавливаем уровень логирования - DEBUG и выше
reports_logger.setLevel(logging.DEBUG)

# Создаем форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Файловый обработчик - пишет все логи в файл
file_handler = logging.FileHandler(os.path.join(logs_path, 'reports.log'), encoding='utf-8', mode='w')
file_handler.setLevel(logging.DEBUG)  # Все уровни (DEBUG и выше)
file_handler.setFormatter(formatter)

# Консольный обработчик - выводит только предупреждения и ошибки
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Только WARNING и выше
console_handler.setFormatter(formatter)

# Добавляем обработчики к логгеру
reports_logger.addHandler(file_handler)
reports_logger.addHandler(console_handler)


def reports_log_function(func):
    """Декоратор для логирования вызовов функций."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Логируем начало вызова
        reports_logger.info(f'Вызов функции {func.__name__}')

        try:
            # Выполняем функцию
            result = func(*args, **kwargs)
            # Логируем успешное завершение
            reports_logger.info(f'Функция {func.__name__} успешно завершилась')
            return result

        except Exception as err:
            # Логируем ошибку
            reports_logger.error(f"Ошибка в функции {func.__name__}: {err}")
            raise

    return wrapper


def check_filename(filename: str) -> str | None:
    """Вспомогательная функция для проверки корректного ввода имени файла. Проверяет имя файла на наличие запрещенных
    символов и длину"""

    # Проверяем, что filename не пустой
    if filename:
        # Паттерн для поиска запрещенных символов в именах файлов
        wrong_chars = r'[<>:"/\\|?*\x00-\x1F]'

        # Если найдены запрещенные символы - вызываем исключение
        if re.search(wrong_chars, filename):
            return None

    # Проверяем длину имени файла (максимум 255 символов)
    if len(filename) > 255:
        return None

    # Дополнительная проверка. Имя файла не должно быть только точками
    if filename in ('.', '..'):
        return None

    # Возвращаем проверенное имя файла
    return filename


def decorator_output_to(filename: str = None):
    """Декоратор для функций-отчетов, записывающий в файл результат (в формате json), который возвращает функция,
    формирующая отчет. Декоратор без параметра — записывает данные отчета в файл с названием
    имя_декорируемой_функции.json в папку data проекта. Декоратор с параметром — принимает имя файла
    в качестве параметра (файл сохраняется также в папку data проекта"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            json_str = result.to_json(orient='records', indent=2, force_ascii=False)

            # Создаем путь к директории вывода файла (два уровня выше от текущего файла)
            data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            # Создаем директорию, если она не существует
            os.makedirs(logs_path, exist_ok=True)
            # Определяем имя файла для записи
            output_filename = (
                os.path.join(data_path, filename) if filename else os.path.join(data_path, f"{func.__name__}.json")
            )

            try:
                # Записываем json_result в файл именем output_filename
                with open(output_filename, 'a', encoding='utf-8') as f:
                    f.write(json_str + '\n')

            except Exception as e:
                # Записываем ошибку в лог
                logging.error(f"Ошибка записи в {output_filename}: {e}")
                # Программа продолжает работу

            return result

        return wrapper

    return decorator


@reports_log_function
def get_dataframe_from_excel(path: str, sheet: Union[int, str] = 0) -> pd.DataFrame | None:
    """Читает данные из Excel файла и возвращает в виде списка словарей"""

    try:
        # Читаем все данные
        df = pd.read_excel(path, sheet_name=sheet)
        return df
    # В случае ошибки пишем лог уровня error и возвращаем None
    except FileNotFoundError:
        reports_logger.error(f'Файл {path} не найден')
        return None
    except ValueError as e:
        reports_logger.error(f"Ошибка в данных файла: {e}")
        return None
    except PermissionError:
        reports_logger.error(f"Нет прав доступа к файлу {path}")
        return None
    except Exception as e:
        reports_logger.error(f"Неизвестная ошибка при чтении файла: {e}")
        return None


@reports_log_function
def get_data_by_range(transactions: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Функция возвращает DataFrame за определенный период из переданного ей DataFrame"""


@reports_log_function
@decorator_output_to()  # Поправить после реализации partial
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    if not date:
        date = datetime.now().strftime("%d-%m-%Y")

    if not transactions:
        reports_logger.error(f'Отсутствуют данные для отчета за последние три месяца от переданной даты {date}')
        return None

    if not category:
        reports_logger.info(f'Категория затрат не введена. Будет выведены все транзакции без учета категории')

    try:
        transactions['Дата платежа'] = pd.to_datetime(transactions['Дата платежа'])
        result_df = transactions[(transactions['date'] >= start_date) & (df['date'] <= end_date)]




@reports_log_function
@decorator_output_to()  # Поправить после реализации partial
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    pass


@reports_log_function
@decorator_output_to()  # Поправить после реализации partial
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    pass
