### Финансовая аналитика

Учебный проект на платформе SkyPro для анализа банковских операций и построения финансовых отчетов.

### Установка

#### Предварительные требования

- Python 3.8+
- Poetry (менеджер зависимостей)

### Установка Poetry

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# Linux/MacOS
curl -sSL https://install.python-poetry.org | python3 -
```

### Установка проекта

1. Клонируйте репозиторий:
```bash
git clone <https://github.com/aleksey-s-lozhkin/coursework_1/tree/master>
cd coursework_1
```

2. Установите зависимости через Poetry:
```bash
poetry install
```

3. Активируйте виртуальное окружение:
```bash
poetry shell
```

4. Настройте переменные окружения:
```bash
cp .env.example .env
```
Отредактируйте файл .env и добавьте необходимые API-ключи.

5. Подготовьте данные:
   - Поместите файл с операциями в `data/operations.xlsx`
   - Убедитесь, что формат данных соответствует ожидаемой структуре

### Запуск

```bash
# Запуск демонстрации всех функций
poetry run python main.py

# Или с активированным окружением:
python main.py
```

После запуска отобразятся демонстрационные отчеты за 20.05.2020.

### Функциональность

#### Веб-отчеты (`src/views`)
- **`general(date)`** - общая статистика по операциям на указанную дату
- **`events(date, period)`** - отчет по событиям за период (Y — год, M - месяц, W - неделя, ALL — все
    данные)

#### Сервисы (`src/services`) 
- **`get_boosted_cashback_categories(file, year, month)`** - анализ категорий с повышенным кэшбэком
- **`investment_bank(month, transactions, amount)`** - расчет инвестиционной копилки
- **`simple_search(term, transactions)`** - поиск операций по ключевому слову
- **`phone_search(transactions)`** - поиск операций с телефонными номерами
- **`person_search(transactions)`** - поиск переводов физическим лицам

#### Аналитические отчеты (`src/reports`)
- **`spending_by_category(df, category, date)`** - анализ трат по конкретной категории
- **`spending_by_weekday(df, date)`** - средние траты по дням недели
- **`spending_by_workday(df, date)`** - сравнение трат по типу дня (рабочий/выходной)

#### Утилиты (`src/utils`)
- **`read_xlsx(file, sheet_index)`** - чтение данных из Excel-файла
- **`get_dataframe_from_excel(file, sheet_index)`** - загрузка данных в pandas DataFrame

### Структура проекта

```
coursework_1/
├── src/
│   ├── views/           # Модуль веб-отчетов
│   ├── services/        # Сервисные функции поиска и анализа
│   ├── reports/         # Аналитические отчеты
│   └── utils/           # Вспомогательные функции
├── data/                # Директория для файлов с операциями
│   └── operations.xlsx  # Файл с банковскими операциями
├── logs/                # Директория для логов
├── tests/               # Дирректория для тестов
├── main.py              # Основной демонстрационный скрипт
├── pyproject.toml       # Конфигурация Poetry и зависимости
└── README.md
```

### Разработка

#### Добавление новых зависимостей
```bash
# Добавление production зависимости
poetry add package-name

# Добавление development зависимости
poetry add --group dev package-name
```

#### Запуск тестов
```bash
poetry run pytest
```

#### Форматирование кода
```bash
poetry run black .
poetry run isort .
```

### Демонстрация

Проект включает демонстрационный скрипт `main.py`, который показывает работу всех модулей:
- Веб-отчеты с общей статистикой и событиями
- Сервисные функции (поиск, кэшбэк, инвестиции)
- Аналитические отчеты по категориям и дням недели

### Примечания

- Для работы необходим файл с данными в формате Excel
- Проект использует фиксированную демонстрационную дату 20.05.2020
- Все модули независимы и могут использоваться отдельно

### Автор
aleksey.s.lozhkin@gmail.com

### Лицензия
Этот проект распространяется под лицензией MIT.