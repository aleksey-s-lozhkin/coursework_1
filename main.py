from src.views import exchange_rate, stock_price, read_user_setting


user_currencies = read_user_setting('user_currencies')
user_stocks = read_user_setting('user_stocks')

print(exchange_rate(user_currencies))

print(stock_price(user_stocks))
