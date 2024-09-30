import alpaca_trade_api as tradeapi
import requests, json
import time, schedule

from alpha_vantage.techindicators import TechIndicators
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from myconfig import *
import configparser

class PyRobot:

    # Initialize the trading robot and connect to the Alpaca API
    def __init__(self):
        self.api_key = API_KEY 
        self.secret_key = SECRET_KEY
        self.endpoint = ENDPOINT_URL
        self.alpaca_api = tradeapi.REST(self.api_key, self.secret_key, self.endpoint)
        self.alpha_indicators = TechIndicators(key=ALPHAVANTAGE_API_KEY)
        
        self.assets: dict = {
            "GUSH": {}, # Oil/Gas Leveraged ETF
            "SOXL": {}, # Semiconductor Leveraged ETF
            "TECL": {}, # Technology Leveraged ETF
        }

        for symbol in self.assets:
            stock_data = {
                'current_price': None,
                'percent_change': None,
                'prev_close': None,
                'RSI(2)': None,
                'next_purchase_allowed_at': None
            }
            self.assets[symbol] = stock_data

        # Get historical data
        self.get_historical_data()


    def get_orders(self):
        r = requests.get(ORDERS_URL, headers = HEADERS)
        return json.loads(r.content)

    def cancel_all_orders(self):
        self.alpaca_api.cancel_all_orders()

    # This function is intended to run once upon initializing bot
    # Gathers previous closing price and 2-period RSI
    def get_historical_data(self):
        print("Gathering historical stock data and indicators...")

        for symbol in self.assets:
            r = requests.get(url=STOCK_URL.format(symbol))
            soup = BeautifulSoup(r.text, 'html.parser')

            previous_close = float(soup.find('span', {'class': "Trsdu(0.3s)", "data-reactid": "43"}).text)

            
            indicator = self.alpha_indicators.get_rsi(symbol, time_period='2')
            last_refreshed = str(indicator[1]["3: Last Refreshed"])
            rsi_2 = float(indicator[0][last_refreshed]["RSI"])

            # Add the information to self.assets
            self.assets[symbol]['prev_close'] = previous_close
            self.assets[symbol]['RSI(2)'] = rsi_2
    
        return self.assets

    # Returns current price and percent-change
    def get_current_prices(self) -> dict:
        for symbol in self.assets:
            r = requests.get(url=STOCK_URL.format(symbol))
            soup = BeautifulSoup(r.text, 'html.parser')

            current_price = float(soup.find('div', {'class': "D(ib) Mend(20px)", 'data-reactid': "48"}).find_all('span')[0].text)
            self.assets[symbol]['current_price'] = current_price

            prev_close = self.assets[symbol]['prev_close']

            # Calculate percentage-change if we have previous closing price
            if prev_close is not None:
                percent_change = ((current_price - prev_close) / prev_close) * 100
                self.assets[symbol]['percent_change'] = percent_change

            print(symbol, "current price @:", current_price)
            time.sleep(1)
        print()
        return self.assets

    # Generates a unique order id for every purchase
    def generate_order_id(self, symbol):
        # Open trade_history.json and 
        # count number of times an asset has been bought/sold
        # in order t
        num_trades = 0
        with open('trade_history.json') as file:
            data = json.load(file)
            for buys in data['Bought']:
                if buys[0:4] == symbol:
                    num_trades += 1

            for sells in data['Sold']:
                if sells[0:4] == symbol:
                    num_trades +=1

        order_id = symbol + ' ' + str(num_trades)
        return order_id

    # Buys shares of indicated stock
    # Updates trade_history.json
    def market_buy(self, symbol: str):
        order = self.alpaca_api.submit_order(symbol=symbol, qty=100, side="buy")
        client_order_id = order.client_order_id
        time.sleep(5)
        get_order = self.alpaca_api.get_order_by_client_order_id(client_order_id)
        purchase_price = get_order.filled_avg_price

        print("\nBuying 100 shares of", symbol, "@ avg_price:", purchase_price)
        order_id = self.generate_order_id(symbol)
        
        # Get date of purchase
        date_time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        # Allow the same asset to be purchased again (if conditions are met) 
        # after waiting 3 hours
        self.assets[symbol]['next_purchase_allowed_at'] = datetime.now() + timedelta(hours=3)

        new_trade = {
            "symbol": symbol,
            "purchase_price": purchase_price,
            "qty": 100,
            "prev_close": self.assets[symbol]["prev_close"],
            "purchase_date": date_time,
            "client_order_id": client_order_id
        }

        with open("trade_history.json", "r+") as file:
            data = json.load(file)
            data["Bought"][order_id] = new_trade
            file.seek(0)
            json.dump(data, file, indent = 4)

    # Sells shares of indicated stock
    # Updates trade_history.json
    def market_sell(self, order_id: str):
        print("Selling", order_id + "...")
        with open("trade_history.json", "r+") as file:
            data = json.load(file)
            
            purchase_price = float(data['Bought'][order_id]['purchase_price'])
            symbol = data['Bought'][order_id]['symbol']

            order = self.alpaca_api.submit_order(symbol=symbol, qty=100, side="sell")
            client_order_id = order.client_order_id
            time.sleep(5)
            get_order = self.alpaca_api.get_order_by_client_order_id(client_order_id)
            sold_at = float(get_order.filled_avg_price)

            date_time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            percent_profit = round(((sold_at / purchase_price) - 1) * 100, 4)

            sale_info = {
                "symbol": symbol,
                "sold_at": sold_at,
                "purchase_price": purchase_price,
                "percent_profit": percent_profit,
                "purchase_date": data['Bought'][order_id]['purchase_date'],
                "sale_date": date_time,
                "qty": 100
            }

            del data['Bought'][order_id]

            data["Sold"][order_id] = sale_info
            file.seek(0)
            json.dump(data, file, indent = 4)

    # Looks for buying opportunities
    def create_new_trade(self):
        print("\nLooking for trading opportunities...")
        for symbol in self.assets:
            percent_change = self.assets[symbol]['percent_change']
            rsi_2 = self.assets[symbol]['RSI(2)']

            current_time = datetime.now()
            delay = self.assets[symbol]['next_purchase_allowed_at']

            if delay is None or current_time > delay:
                if (percent_change < -2 or rsi_2 < 15):
                    self.market_buy(symbol=symbol)

    # Looks to fill/sell orders and take profit
    def take_profit(self):
        with open("trade_history.json", "r+") as file:
            data = json.load(file)

            for order in data['Bought']:
                symbol = data['Bought'][order]['symbol']
                purchase_price = float(data['Bought'][order]['purchase_price'])
                current_price = float(self.assets[symbol]['current_price'])

                if purchase_price is None:
                    pass
                else:
                    percent_profit = ((current_price - purchase_price) / purchase_price) * 100
                    if percent_profit >= 2.5:
                        self.market_sell(order_id=order)


    def run_strategy(self):
        self.get_current_prices()
        self.create_new_trade()
        self.take_profit()
        

if __name__ == "__main__":
    robot = PyRobot()
    schedule.every(15).seconds.do(robot.run_strategy)

    while True:
        schedule.run_pending()
        time.sleep(1)




