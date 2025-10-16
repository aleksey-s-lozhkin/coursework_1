import logging
import os
from datetime import datetime
from functools import wraps
from typing import Optional, Union

import pandas as pd
from dateutil.relativedelta import relativedelta

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
            os.makedirs(data_path, exist_ok=True)
            # Определяем имя файла для записи
            output_filename = (
                os.path.join(data_path, filename) if filename else os.path.join(data_path, f"{func.__name__}.json")
            )

            try:
                # Записываем json_result в файл именем output_filename
                with open(output_filename, 'w', encoding='utf-8') as f:
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
    """Читает данные из Excel файла и возвращает в виде DataFrame"""

    # Проверка существования файла
    if not os.path.exists(path):
        reports_logger.error(f'Файл {path} не найден')
        return None

    # Проверка, что файл не пустой
    if os.path.getsize(path) == 0:
        reports_logger.error(f'Файл {path} пустой')
        return None

    try:
        # Чтение Excel файла
        df = pd.read_excel(
            path, sheet_name=sheet, engine='openpyxl', na_values=['', ' ', 'NULL', 'null'], keep_default_na=True
        )

        # Логируем успешное чтение
        reports_logger.debug(f'Успешно прочитан файл {path}, строк: {len(df)}')
        return df

    except FileNotFoundError:
        reports_logger.error(f'Файл {path} не найден')
        return None
    except ValueError as e:
        reports_logger.error(f"Ошибка в данных файла или лист '{sheet}' не найден: {e}")
        return None
    except PermissionError:
        reports_logger.error(f"Нет прав доступа к файлу {path}")
        return None
    except ImportError as e:
        reports_logger.error(f"Отсутствуют необходимые библиотеки: {e}")
        return None
    except Exception as e:
        reports_logger.error(f"Неизвестная ошибка при чтении файла: {e}")
        return None


@reports_log_function
def get_data_by_range(transactions: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame | None:
    """Функция возвращает DataFrame за определенный период из переданного ей DataFrame"""

    # Проверка входных данных
    if transactions.empty:
        reports_logger.debug('Передан пустой DataFrame')
        return None

    if not start_date or not end_date:
        reports_logger.debug('Начальная или конечная дата для фильтрации отсутствуют')
        return None

    if start_date > end_date:
        reports_logger.debug('Начальная дата больше конечной')
        return None

    try:
        transactions_copy = transactions.copy()
        transactions_copy['Дата платежа'] = pd.to_datetime(
            transactions_copy['Дата платежа'], dayfirst=True, errors='coerce'
        )
        result_df = transactions_copy[
            (transactions_copy['Дата платежа'] >= start_date) & (transactions_copy['Дата платежа'] <= end_date)
        ]
        return result_df

    except KeyError as err:
        reports_logger.debug(f'Отсутствует необходимый столбец: {err}')
        return None
    except Exception as err:
        reports_logger.debug(f'Ошибка при фильтрации DataFrame: {err}')
        return None


@reports_log_function
@decorator_output_to(filename=None)
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame | None:
    """Возвращает траты по указанной категории за последние три месяца от указанной даты"""

    # Проверка входных данных
    if transactions is None or transactions.empty:
        reports_logger.error('Передан пустой DataFrame или None')
        return pd.DataFrame()

    if not category:
        reports_logger.error('Категория затрат не введена')
        return pd.DataFrame()

    # Установка даты по умолчанию
    if not date:
        date_obj = datetime.now()
    else:
        try:
            date_obj = datetime.strptime(date, '%d.%m.%Y')
        except ValueError:
            reports_logger.error(f'Указана некорректная дата: {date}')
            return pd.DataFrame()

    # Вычисляем дату 3 месяца назад
    try:
        target_date = date_obj - relativedelta(months=3)
    except NameError as err:
        reports_logger.error(f'Ошибка вычисления начальной даты: {err}')
        return None

    reports_logger.debug(f'Получаем данные в диапазоне дат от {target_date} до {date_obj}')

    # Фильтруем по дате
    try:
        filtered_df = get_data_by_range(transactions, target_date, date_obj)

        if filtered_df is None or filtered_df.empty:
            reports_logger.info(f'Нет данных за указанный период для категории "{category}"')
            return pd.DataFrame()

        # Фильтруем по категории
        if 'Категория' not in filtered_df.columns:
            reports_logger.error('В данных отсутствует столбец "Категория"')
            return None

        result_df = filtered_df[filtered_df['Категория'] == category]

        reports_logger.info(f'Найдено {len(result_df)} записей по категории "{category}"')
        return result_df

    except Exception as e:
        reports_logger.error(f'Ошибка при фильтрации данных: {e}')
        return None


@reports_log_function
@decorator_output_to(filename=None)
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame | None:
    """Возвращает средние траты в каждый из дней недели за последние три месяца от переданной даты"""

    # Проверка входных данных
    if transactions is None or transactions.empty:
        reports_logger.error('Передан пустой DataFrame или None')
        return pd.DataFrame()

    # Установка даты по умолчанию
    if not date:
        date_obj = datetime.now()
    else:
        try:
            date_obj = datetime.strptime(date, '%d.%m.%Y')
        except ValueError:
            reports_logger.error(f'Указана некорректная дата: {date}')
            return pd.DataFrame()

    # Вычисляем дату 3 месяца назад
    try:
        target_date = date_obj - relativedelta(months=3)
    except NameError as err:
        reports_logger.error(f'Ошибка вычисления начальной даты: {err}')
        return pd.DataFrame()

    reports_logger.debug(f'Получаем данные в диапазоне дат от {target_date} до {date_obj}')

    # Фильтруем по дням недели
    try:
        filtered_df = get_data_by_range(transactions, target_date, date_obj)

        if filtered_df is None or filtered_df.empty:
            reports_logger.info('Нет данных за указанный период')
            return pd.DataFrame()

        filtered_df['Дата платежа'] = pd.to_datetime(filtered_df['Дата платежа'], dayfirst=True, errors='coerce')
        filtered_df['День недели'] = filtered_df['Дата платежа'].dt.day_name()

        result_df = filtered_df.groupby('День недели', as_index=False)['Сумма операции'].mean().round(2)

        # Упорядочим дни недели
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        result_df['День недели'] = pd.Categorical(result_df['День недели'], categories=days_order, ordered=True)
        result_df = result_df.sort_values('День недели').reset_index(drop=True)

        reports_logger.info(f'Найдено {len(filtered_df)} транзакций, сгруппировано в {len(result_df)} дней недели')
        return result_df

    except Exception as e:
        reports_logger.error(f'Ошибка при при работе с данными: {e}')
        return None


@reports_log_function
@decorator_output_to(filename=None)  # Поправить после реализации partial
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame | None:
    """Функция выводит средние траты в рабочий и в выходной день за последние три месяца (от переданной даты)."""

    # Проверка входных данных
    if transactions is None or transactions.empty:
        reports_logger.error('Передан пустой DataFrame или None')
        return pd.DataFrame()

    # Установка даты по умолчанию
    if not date:
        date_obj = datetime.now()
    else:
        try:
            date_obj = datetime.strptime(date, '%d.%m.%Y')
        except ValueError:
            reports_logger.error(f'Указана некорректная дата: {date}')
            return pd.DataFrame()

    # Вычисляем дату 3 месяца назад
    try:
        target_date = date_obj - relativedelta(months=3)
    except NameError as err:
        reports_logger.error(f'Ошибка вычисления начальной даты: {err}')
        return pd.DataFrame()

    reports_logger.debug(f'Получаем данные в диапазоне дат от {target_date} до {date_obj}')

    # Фильтруем по дням недели
    try:
        filtered_df = get_data_by_range(transactions, target_date, date_obj)

        if filtered_df is None or filtered_df.empty:
            reports_logger.info('Нет данных за указанный период')
            return pd.DataFrame()

        filtered_df['Дата платежа'] = pd.to_datetime(filtered_df['Дата платежа'], dayfirst=True, errors='coerce')
        filtered_df['Номер для недели'] = filtered_df['Дата платежа'].dt.dayofweek
        filtered_df['Тип дня'] = filtered_df['Номер для недели'].apply(
            lambda item: 'Выходной' if item >= 5 else 'Рабочий'
        )

        result_df = filtered_df.groupby('Тип дня', as_index=False)['Сумма операции'].mean().round(2)

        # Упорядочим дни недели
        type_order = ['Рабочий', 'Выходной']
        result_df['Тип дня'] = pd.Categorical(result_df['Тип дня'], categories=type_order, ordered=True)
        result_df = result_df.sort_values('Тип дня').reset_index(drop=True)

        reports_logger.info(f'Найдено {len(filtered_df)} транзакций, сгруппировано в {len(result_df)} типа дней')
        return result_df

    except Exception as e:
        reports_logger.error(f'Ошибка при при работе с данными: {e}')
        return None
