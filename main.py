import os

from src.services import (get_boosted_cashback_categories,
                          investment_bank,
                          simple_search,
                          phone_search,
                          person_search)
from src.utils import read_xlsx
from src.views import events, general

# print(general('2021-12-25 20:00:00'))

# print(events('2021-12-25 20:00:00', 'M'))


project_dir = os.path.dirname(__file__)
data_file = os.path.join(project_dir, 'data', 'operations.xlsx')

print(get_boosted_cashback_categories(data_file, 2020, 6))


raw_data = read_xlsx(data_file, 0)
print(investment_bank('2021-07', raw_data, 50))

request_str = 'кэшбэк'
print(simple_search(request_str, raw_data))

print(phone_search(raw_data))

print(person_search(raw_data))
