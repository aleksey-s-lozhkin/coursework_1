import json
import os
import time
import traceback

from src.reports import get_dataframe_from_excel, spending_by_category, spending_by_weekday, spending_by_workday
from src.services import get_boosted_cashback_categories, investment_bank, person_search, phone_search, simple_search
from src.utils import read_xlsx
from src.views import events, general


def web():
    """Демонстрация функций веб-отчетов из модуля views"""
    try:
        print("=" * 60)
        print("ВЕБ-ОТЧЕТЫ (VIEWS)")
        print("=" * 60)

        # Определяем корневую директорию проекта
        project_root = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(project_root, 'data', 'operations.xlsx')

        # Проверяем существование файла
        if not os.path.exists(data_file):
            print(f"Файл данных не найден: {data_file}")
            return

        # Используем фиксированную дату 20.02.2020
        demo_date_str = '2020-05-20 12:00:00'
        print("Демонстрационная дата: 20.05.2020")

        print("\n--- ОБЩИЙ ОТЧЕТ ---")
        try:
            general_report = general(demo_date_str)
            print(general_report)
        except Exception as e:
            print(f"Ошибка при формировании общего отчета: {e}")

        # Задержка для избежания лимитов API
        time.sleep(5)

        print("\n--- ОТЧЕТ ПО СОБЫТИЯМ (МЕСЯЦ) ---")
        try:
            events_report = events(demo_date_str, 'M')
            print(events_report)
        except Exception as e:
            print(f"Ошибка при формировании отчета по событиям: {e}")

    except Exception as e:
        print(f"Ошибка в функции web: {e}")


def services():
    """Демонстрация сервисных функций из модуля services"""
    try:
        print("=" * 60)
        print("СЕРВИСНЫЕ ФУНКЦИИ (SERVICES)")
        print("=" * 60)

        # Определяем корневую директорию проекта
        project_root = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(project_root, 'data', 'operations.xlsx')

        # Проверяем существование файла
        if not os.path.exists(data_file):
            print(f"Файл данных не найден: {data_file}")
            return

        # Загружаем данные
        transactions_data = read_xlsx(data_file, 0)

        if not transactions_data:
            print("Не удалось загрузить данные для сервисных функций")
            return

        # Используем фиксированную дату 20.02.2020
        demo_year = 2020
        demo_month = 5
        print("Демонстрационная дата: 20.02.2020")

        print("\n--- ВЫГОДНЫЕ КАТЕГОРИИ ПОВЫШЕННОГО КЭШБЭКА ---")
        try:
            profitable_cats = get_boosted_cashback_categories(data_file, str(demo_year), str(demo_month))
            if profitable_cats:
                result_data = json.loads(profitable_cats)
                print(f"Найдено категорий с кэшбэком: {len(result_data)}")
                top_categories = dict(list(result_data.items())[:3])
                print("Топ-3 категории по кэшбэку:")
                print(json.dumps(top_categories, ensure_ascii=False, indent=2))
            else:
                print("Нет данных по кэшбэку за указанный период")
        except Exception as e:
            print(f"Ошибка: {e}")

        print("\n--- ИНВЕСТКОПИЛКА ---")
        try:
            month_str = f"{demo_year}-{demo_month:02d}"
            investment = investment_bank(month_str, transactions_data, 100)
            print(investment)
        except Exception as e:
            print(f"Ошибка: {e}")

        print("\n--- ПРОСТОЙ ПОИСК ---")
        try:
            search_terms = ["кафе", "ресторан", "магазин"]
            for term in search_terms:
                search_result = simple_search(term, transactions_data)
                if search_result:
                    result_list = json.loads(search_result)
                    print(f"По запросу '{term}' найдено транзакций: {len(result_list)}")
                    if result_list:
                        print("Пример транзакции:")
                        print(json.dumps(result_list[0], ensure_ascii=False, indent=2))
                        break
            else:
                print("Транзакции не найдены по любым запросам")
        except Exception as e:
            print(f"Ошибка: {e}")

        print("\n--- ПОИСК ПО ТЕЛЕФОННЫМ НОМЕРАМ ---")
        try:
            phone_result = phone_search(transactions_data)
            if phone_result:
                result_list = json.loads(phone_result)
                print(f"Найдено транзакций с номерами: {len(result_list)}")
                if result_list:
                    print("Пример транзакции:")
                    print(json.dumps(result_list[0], ensure_ascii=False, indent=2))
            else:
                print("Транзакции с номерами не найдены")
        except Exception as e:
            print(f"Ошибка: {e}")

        print("\n--- ПОИСК ПЕРЕВОДОВ ФИЗИЧЕСКИМ ЛИЦАМ ---")
        try:
            person_result = person_search(transactions_data)
            if person_result:
                result_list = json.loads(person_result)
                print(f"Найдено переводов физлицам: {len(result_list)}")
                if result_list:
                    print("Пример перевода:")
                    print(json.dumps(result_list[0], ensure_ascii=False, indent=2))
            else:
                print("Переводы физлицам не найдены")
        except Exception as e:
            print(f"Ошибка: {e}")

    except Exception as e:
        print(f"Ошибка в функции services: {e}")


def reports():
    """Демонстрация функций отчетов из модуля reports"""
    try:
        print("=" * 60)
        print("ФУНКЦИИ ОТЧЕТОВ (REPORTS)")
        print("=" * 60)

        # Определяем корневую директорию проекта
        project_root = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(project_root, 'data', 'operations.xlsx')

        # Проверяем существование файла
        if not os.path.exists(data_file):
            print(f"Файл данных не найден: {data_file}")
            return

        # Загружаем данные
        transactions_df = get_dataframe_from_excel(data_file, 0)
        if transactions_df is None or transactions_df.empty:
            print("Не удалось загрузить данные из файла")
            return

        # Используем фиксированную дату 20.02.2020
        demo_date_dd_mm_yyyy = '20.05.2020'
        print(f"Демонстрационная дата: {demo_date_dd_mm_yyyy}")

        # Используем фиксированные категории для демонстрации
        fixed_categories = ["Супермаркеты", "Каршеринг", "Фастфуд"]

        print("\n--- ТРАТЫ ПО КАТЕГОРИИ ---")
        try:
            category_found = False
            for category in fixed_categories:
                category_result = spending_by_category(transactions_df, category, demo_date_dd_mm_yyyy)
                if category_result is not None and not category_result.empty:
                    print(f"Найдено {len(category_result)} транзакций по категории '{category}':")
                    if len(category_result) > 3:
                        print(category_result.head(3).to_string(index=False))
                        print(f"... и еще {len(category_result) - 3} транзакций")
                    else:
                        print(category_result.to_string(index=False))
                    category_found = True
                    break

            if not category_found:
                print("Не найдено транзакций по указанным категориям")
        except Exception as e:
            print(f"Ошибка: {e}")

        print("\n--- ТРАТЫ ПО ДНЯМ НЕДЕЛИ ---")
        try:
            weekday_result = spending_by_weekday(transactions_df, demo_date_dd_mm_yyyy)
            if weekday_result is not None and not weekday_result.empty:
                print("Средние траты по дням недели:")
                print(weekday_result.to_string(index=False))
            else:
                print("Нет данных для анализа трат по дням недели")
        except Exception as e:
            print(f"Ошибка: {e}")

        print("\n--- ТРАТЫ ПО ТИПУ ДНЯ (РАБОЧИЙ/ВЫХОДНОЙ) ---")
        try:
            workday_result = spending_by_workday(transactions_df, demo_date_dd_mm_yyyy)
            if workday_result is not None and not workday_result.empty:
                print("Средние траты по типу дня:")
                print(workday_result.to_string(index=False))
            else:
                print("Нет данных для анализа трат по типу дня")
        except Exception as e:
            print(f"Ошибка: {e}")

    except Exception as e:
        print(f"Ошибка в функции reports: {e}")


def main():
    """
    Основная функция для демонстрации работы финансовой аналитики.
    Вызывает три независимые функции для демонстрации разных модулей.
    """
    try:
        print("=" * 60)
        print("ФИНАНСОВАЯ АНАЛИТИКА")
        print("=" * 60)

        # Демонстрация веб-отчетов
        web()

        # Разделитель между модулями
        print("\n" + "=" * 60)

        # Демонстрация сервисных функций
        services()

        # Разделитель между модулями
        print("\n" + "=" * 60)

        # Демонстрация функций отчетов
        reports()

        print("\n" + "=" * 60)
        print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
        print("=" * 60)

    except Exception as e:
        print(f"Критическая ошибка при выполнении демонстрации: {e}")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
