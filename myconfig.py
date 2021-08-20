# from configparser import ConfigParser

# config = ConfigParser()

# config.add_section('main')
# config.set('main', 'ALPACA_API_KEY', '')
# config.set('main', 'SECRET_KEY', '')
# config.set('main', 'ENDPOINT_URL', '')
# config.set('main', 'HEADERS', '')
# config.set('main', 'STOCK_URL', '')

# with open('config.ini', 'w+') as f:
#     config.write(f)


API_KEY = "your-alpaca-api-key"
SECRET_KEY = "your-alpaca-secret-key"
ENDPOINT_URL = "https://paper-api.alpaca.markets"
HEADERS = {'APCA-API-KEY-ID': API_KEY, 'APCA-API-SECRET-KEY': SECRET_KEY}
ORDERS_URL = "{}/v2/orders".format(ENDPOINT_URL)

ALPHAVANTAGE_API_KEY = 'your-alpha-vantage-api-key'

STOCK_URL = "https://finance.yahoo.com/quote/{}/"


