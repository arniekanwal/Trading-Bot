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


API_KEY = "PK0540A4HFAVO0OBCVAJ"
SECRET_KEY = "EKbAw43LEyk0DNZGwAt46YpGKB9fwaQAm5SGoXpv"
ENDPOINT_URL = "https://paper-api.alpaca.markets"
HEADERS = {'APCA-API-KEY-ID': API_KEY, 'APCA-API-SECRET-KEY': SECRET_KEY}
ORDERS_URL = "{}/v2/orders".format(ENDPOINT_URL)

ALPHAVANTAGE_API_KEY = 'F37CT05APWZEDQB1'

STOCK_URL = "https://finance.yahoo.com/quote/{}/"


