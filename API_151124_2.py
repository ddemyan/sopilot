
import gui141124, key, math, threading, os, time
from datetime import datetime
import pandas as pd
import PySimpleGUI as sg
from binance.client import Client
from binance import ThreadedWebsocketManager
from telegram import Bot
import logging
from logging.handlers import RotatingFileHandler
# Create 'Log' folder if it doesn't exist
if not os.path.exists('Log'):
    os.makedirs('Log')

# Configure logging
log_filename = datetime.now().strftime("Log/app_%Y-%m-%d_%H-%M-%S.log")
handler = RotatingFileHandler(log_filename, maxBytes=30*1024*1024, backupCount=5)
logging.basicConfig(level=logging.INFO, handlers=[handler])
#logging.info(f"Condition met: {condition}")
pd.options.mode.copy_on_write = True
client = Client(key.api_key, key.api_secret, testnet=True)
df,d = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume', 'num']), []
bot_token = '7772169803:AAFOT0hDlbBkiC2vVv5fYMGpjgQeQRMAm78'  # Вставьте ваш токен доступа
chat_id = '740355937'
bot = Bot(token=bot_token)
hours=2
# Отправка сообщения
def Tg(*message):
    bot.send_message(chat_id=chat_id, text=message)
def Run():
    logging.info("Starting websocket manager")
    twm = ThreadedWebsocketManager(api_key=key.api_key, api_secret=key.api_secret)
    twm.start()
    twm.start_kline_socket(symbol=values['-trading_pairs-'], callback=Di, interval='1m')
    twm.join()
def Di(msg):
    conditions = values['-conditions-']
    ma = int(values['-ma-'])
    delta_ma = float(values['-delta_ma-'])
    delta_num = float(values['-delta_num-'])
    d.append(msg)
    if len(d) == 11:
        del d[0]
    if len(d) >= 10:
        for y in range(-10, -1):
            event_time = pd.to_datetime(d[y]['E'], unit='ms') + pd.Timedelta(hours=hours)
            df.loc[y] = [event_time, float(d[y]['k']['o']), float(d[y]['k']['h']),
                         float(d[y]['k']['l']), float(d[y]['k']['c']),
                         float(d[y]['k']['v']), int(d[y]['k']['n'])]
        for condition in conditions:
            condition_eval = eval(gui141124.Dict_query[condition])
            if condition_eval.any():
                logging.info(f"Condition met: {condition}")
                Tg(f'{condition}/n{df.iloc[-1].open}')
        window.write_event_value('-UPDATE_TABLE-', df.values.tolist())
def Trade():
    is_buy = values['-BUY-']
    action = 'buy' if is_buy else 'sell'
    symbol = values['-trading_pairs-']
    asset = symbol[0:3]
    if action == 'buy':
        price = float(client.get_recent_trades(symbol=symbol)[-1]['price'])
        q = float(values['-cut-']) * float(client.get_asset_balance(asset='FDUSD')["free"])/price
    else :
        q = float(values['-cut-']) * float(client.get_asset_balance(asset=asset)["free"])
    target_quantity = round_quantity(symbol, q)
    accumulated_quantity = 0
    while accumulated_quantity < target_quantity:
        deptH = client.get_order_book(symbol=symbol)
        logging.info(f"target_quantity:{target_quantity}")
        logging.info(f"Order book (top 5 {'bids' if is_buy else 'asks'}): {deptH['bids' if is_buy else 'asks'][0:5]}")
        for order in deptH['bids' if is_buy else 'asks']:
            price = float(order[0])
            available_quantity = float(order[1])
            if accumulated_quantity + available_quantity >= target_quantity:
                quantity_to_trade = target_quantity
            else:
                quantity_to_trade = available_quantity
            try:
                if is_buy:
                    response = client.order_limit_buy(symbol=symbol, price=price, quantity=quantity_to_trade)
                else:
                    response = client.order_limit_sell(symbol=symbol, price=price, quantity=quantity_to_trade)
                Print(f"Placing limit {action} order: {symbol}, {price}, {response['origQty']},{response['status']}")
                time.sleep(1)
                if response['status'] == 'PARTIALLY_FILLED' or 'FILLED':
                    accumulated_quantity += float(response['origQty'])
                    logging.info(f"Placing limit {action} order: {symbol}, {price}, {response['origQty']},{response['status']}")
                    logging.info(f"accumulated_quantity: {accumulated_quantity}")
                    Print(f"Placing limit {action} order: {symbol}, {price}, {response['origQty']},{response['status']}")
                    Print(f"accumulated_quantity: {accumulated_quantity}")
                else:
                    client.cancel_order(symbol=symbol, orderId=response['order_id'])

            except Exception as e:
                logging.error(f"Failed to place order: {e}")
                Print(f"Failed to place order: {e}")
            if accumulated_quantity >= target_quantity:
                logging.info(f"Target quantity of {target_quantity} ETH {'bought' if is_buy else 'sold'}")
                Print(f"Target quantity of {target_quantity} ETH {'bought' if is_buy else 'sold'}")
            break
def Bill():
    initial_btc_balance = 1
    initial_eth_balance = 5
    initial_usdt_balance = 5000
    def calculate_percentage_change(initial, current):
        return ((current - initial) / initial) * 100
    btc_balance = float(client.get_asset_balance(asset='BNB')["free"])
    eth_balance = float(client.get_asset_balance(asset='ETH')["free"])
    usdt_balance = float(client.get_asset_balance(asset='FDUSD')["free"])

    btc_change = calculate_percentage_change(initial_btc_balance, btc_balance)
    eth_change = calculate_percentage_change(initial_eth_balance, eth_balance)
    usdt_change = calculate_percentage_change(initial_usdt_balance, usdt_balance)

    btc_price = float(client.get_recent_trades(symbol='BNBFDUSD')[-1]['price'])
    eth_price = float(client.get_recent_trades(symbol='ETHFDUSD')[-1]['price'])

    total_value = btc_price * btc_balance + eth_price * eth_balance + usdt_balance

    window['-billBTC-'].update(f"{btc_balance} ({btc_change:.2f}%)")
    window['-billETH-'].update(f"{eth_balance} ({eth_change:.2f}%)")
    window['-billUSDT-'].update(f"{usdt_balance} ({usdt_change:.2f}%)")
    window['-billALL-'].update(total_value)
def display_open_orders():
    orders = pd.DataFrame(client.get_open_orders(symbol=values['-trading_pairs-']),
                          columns=['time','orderId', 'symbol', 'price', 'side', 'origQty', 'status'])
    orders['time'] = pd.to_datetime(orders['time'],unit='ms')+pd.Timedelta(hours=hours)
    orderId = orders[['symbol','orderId']].values.tolist()
    window['-TABLE1-'].update(values=orders.values.tolist())
    window['-id-'].update(values=orderId)
def display_all_orders():
    start_date = datetime.strptime(values['-START_DATE-'] + pd.Timedelta(hours=hours),
                 '%d/%m/%Y %H:%M:%S')
    end_date = datetime.strptime(values['-END_DATE-'] + pd.Timedelta(hours=hours),
               '%d/%m/%Y %H:%M:%S')
    orders = pd.DataFrame(client.get_all_orders(symbol=values['-trading_pairs-']),
             columns=['time','orderId', 'symbol', 'price', 'side', 'origQty', 'status'])
    orders['time'] = pd.to_datetime(orders['time'], unit='ms')+pd.Timedelta(hours=hours)
    filtered_orders = orders[(orders['time']>=start_date) & (orders['time']<=end_date)]
    current_price=float(client.get_symbol_ticker(symbol=values['-trading_pairs-'])['price'])
    filtered_orders.loc[:, 'price_diff'] = filtered_orders.apply(
        lambda row: current_price - float(row['price']) if row['side'] == 'BUY'
        else float(row['price']) - current_price, axis=1)
    filtered_orders.loc[:,'price_diff'] = filtered_orders['price_diff'].round(2)
    total_price_diff = filtered_orders['price_diff'].sum()
    window['-TABLE1-'].update(values=filtered_orders.values.tolist())
    window['-id-'].update(values=filtered_orders[['symbol', 'orderId']].values.tolist())
    window['-TOTAL_DIFF-'].update(total_price_diff)
def Print(*x):
    window['-ML-'].print('\n', x, sep='')
    Tg(x)
def Cancel_order():
    if values['-id-']:
        symbol, order_id = values['-id-']
        logging.info(f"Cancelling order: {symbol}, {order_id}")
        Print(client.cancel_order(symbol=symbol, orderId=order_id))
def Cancel_all_orders():
    a = client.get_open_orders(symbol=values['-trading_pairs-'])
    Print(a)
    for b in [a[x]['orderId'] for x in range(len(a))]:
        logging.info(f"Cancelling order: {b}")
        Print(client.cancel_order(symbol=values['-trading_pairs-'], orderId=b))
def Save_txt(x):
    with open('ML.txt', 'wt') as f:
        f.write(x)
    f.close()
def round_quantity(symbol, quantity):
    info = client.get_symbol_info(symbol)
    step_size = float(info['filters'][1]['stepSize'])
    precision = int(round(-math.log(step_size, 10), 0))
    return round(quantity, precision)
dictL= {'-UPDATE_TABLE-':  lambda: window['-TABLE2-'].update(values=df.values.tolist()),
        '-PRINT-':         lambda: Print(values),
        'Bill':            lambda: Bill(),
        'ВСЕ ОРДЕРА':      lambda: display_all_orders(),
        'ОТКРЫТЫЕ ОРДЕРА': lambda: display_open_orders(),
        'Cancel':          lambda: Cancel_order(),
        'Cancel_all':      lambda: Cancel_all_orders(),
        'Do_it':           lambda: Print(eval(values['-LIST_DOIT-'])),
        'Save':            lambda: Save_txt(values['-ML-']),
        'Clear':           lambda: window['-ML-'].update('')}
window = gui141124.create_window()
while True:
    event, values = window.read()
    try:
        if event in dictL.keys():
            dictL[event]()
        if event == 'СИГНАЛЫ':
            threading.Thread(target=Run, daemon=True).start()
        if event == 'Go':
            threading.Thread(target=Trade, args=()).start()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
    except Exception as e:
        logging.error(f"Exception: {e}")
        sg.popup(e, no_titlebar=True, background_color='#e22bc7')
window.close()