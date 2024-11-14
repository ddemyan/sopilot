import gui141124, key, math, threading, os
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

pd.options.mode.copy_on_write = True
client = Client(key.api_key, key.api_secret, testnet=True)
df,d = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume', 'num']), []
bot_token = '7772169803:AAFOT0hDlbBkiC2vVv5fYMGpjgQeQRMAm78'  # Вставьте ваш токен доступа
chat_id = '740355937'
bot = Bot(token=bot_token)

# Отправка сообщения
def Tg(*message):
    bot.send_message(chat_id=chat_id, text=message)
    logging.info(f"Sent message: {message}")

def Run():
    logging.info("Starting websocket manager")
    twm = ThreadedWebsocketManager(api_key=key.api_key, api_secret=key.api_secret)
    twm.start()
    twm.start_kline_socket(symbol=values['-trading_pairs-'], callback=Di, interval='1m')
    twm.join()

def Di(msg, hours=2):
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

def Go():
    symbol = values['-trading_pairs-']
    asset = symbol[0:3]
    deptH = client.get_order_book(symbol=symbol)
    best_buy, best_sell = deptH['bids'][3][0], deptH['asks'][3][0]
    parts = int(values['-gap-'])  # количество частей на которые будет разбит ордер
    order_type = values['-clause-']  # тип ордера, например, скользящий стоплосс
    if values['-BUY-']:
        q = float(values['-cut-']) * float(client.get_asset_balance(asset=asset)["free"]) / parts
        q = round_quantity(symbol, q)
        for _ in range(parts):
            if order_type == "trailing_stop_loss":
                logging.info("Placing trailing stop loss order")
                Print('client.order')
            else:
                logging.info(f"Placing limit buy order: {symbol}, {best_buy}, {q}")
                Print(client.order_limit_buy(symbol=symbol, price=float(best_buy), quantity=q))
    else:
        q = float(values['-cut-']) * float(client.get_asset_balance(asset=asset)["free"]) / parts
        q = round_quantity(symbol, q)
        for _ in range(parts):
            if order_type == "trailing_stop_loss":
                logging.info("Placing trailing stop loss order")
                Print('client.order')
            else:
                logging.info(f"Placing limit sell order: {symbol}, {best_sell}, {q}")
                Print(client.order_limit_sell(symbol=symbol, price=float(best_sell), quantity=q))

def Bill():
    logging.info("Calculating balances")
    initial_btc_balance = 1
    initial_eth_balance = 5
    initial_usdt_balance = 5000

    def calculate_percentage_change(initial, current):
        return ((current - initial) / initial) * 100

    btc_balance = float(client.get_asset_balance(asset='BTC')["free"])
    eth_balance = float(client.get_asset_balance(asset='ETH')["free"])
    usdt_balance = float(client.get_asset_balance(asset='USDT')["free"])

    btc_change = calculate_percentage_change(initial_btc_balance, btc_balance)
    eth_change = calculate_percentage_change(initial_eth_balance, eth_balance)
    usdt_change = calculate_percentage_change(initial_usdt_balance, usdt_balance)

    btc_price = float(client.get_recent_trades(symbol='BTCUSDT')[-1]['price'])
    eth_price = float(client.get_recent_trades(symbol='ETHUSDT')[-1]['price'])

    total_value = btc_price * btc_balance + eth_price * eth_balance + usdt_balance

    window['-billBTC-'].update(f"{btc_balance} ({btc_change:.2f}%)")
    window['-billETH-'].update(f"{eth_balance} ({eth_change:.2f}%)")
    window['-billUSDT-'].update(f"{usdt_balance} ({usdt_change:.2f}%)")
    window['-billALL-'].update(total_value)

def display_open_orders():
    orders = pd.DataFrame(client.get_open_orders(symbol=values['-trading_pairs-']),
                          columns=['orderId', 'symbol', 'price', 'side', 'origQty', 'status', 'type', 'time'])
    orderId = orders[['symbol','orderId']].values.tolist()
    window['-TABLE1-'].update(values=orders.values.tolist())
    window['-id-'].update(values=orderId)

def display_all_orders():
    logging.info("Displaying all orders")
    start_date = datetime.strptime(values['-START_DATE-'], '%d/%m/%Y %H:%M:%S')
    end_date = datetime.strptime(values['-END_DATE-'], '%d/%m/%Y %H:%M:%S')
    orders = pd.DataFrame(client.get_all_orders(symbol=values['-trading_pairs-']),
                          columns=['orderId', 'symbol', 'price', 'side', 'origQty', 'status', 'type', 'time'])
    orders['time'] = pd.to_datetime(orders['time'], unit='ms')
    filtered_orders = orders[(orders['time'] >= start_date) & (orders['time'] <= end_date)]
    current_price = float(client.get_symbol_ticker(symbol=values['-trading_pairs-'])['price'])
    filtered_orders.loc[:, 'price_diff'] = filtered_orders.apply(
        lambda row: current_price - float(row['price']) if row['side'] == 'BUY'
        else float(row['price']) - current_price, axis=1)
    filtered_orders.loc[:,'price_diff'] = filtered_orders['price_diff'].round(2)
    filtered_orders.insert(0, 'price_diff', filtered_orders.pop('price_diff'))
    total_price_diff = filtered_orders['price_diff'].sum()
    window['-TABLE1-'].update(values=filtered_orders.values.tolist())
    window['-id-'].update(values=filtered_orders[['symbol', 'orderId']].values.tolist())
    window['-TOTAL_DIFF-'].update(total_price_diff)

def Print(*x):
    logging.info(f"Print: {x}")
    window['-ML-'].print('\n', x, sep='')

def Cancel_order():
    if values['-id-']:
        symbol, order_id = values['-id-']
        logging.info(f"Cancelling order: {symbol}, {order_id}")
        Print(client.cancel_order(symbol=symbol, orderId=order_id))

def Cancel_all_orders():
    logging.info("Cancelling all orders")
    a = client.get_open_orders(symbol=values['-trading_pairs-'])
    Print(a)
    for b in [a[x]['orderId'] for x in range(len(a))]:
        logging.info(f"Cancelling order: {b}")
        Print(client.cancel_order(symbol=values['-trading_pairs-'], orderId=b))

def get_depth():
    x = client.get_order_book(symbol=values['-trading_pairs-'])
    window['-ML-'].print(x)
    df_asks = pd.DataFrame(x['asks'], columns=['ask_price', 'ask_vol']).astype(float)
    df_bids = pd.DataFrame(x['bids'], columns=['bid_price', 'bid_vol']).astype(float)
    df_bids['depth'] = df_bids['bid_price'].apply(
        lambda x: '1%' if df_bids['bid_price'].max() / x > 1.001 else '0.1%' if df_bids['bid_price'].max() / x > 1.0001 else '0.01%')
    df_bids.loc[0, 'depth'] = '0%'
    df_asks['depth'] = df_asks['ask_price'].apply(
        lambda x: '1%' if df_asks['ask_price'].min() / x < 0.99 else '0.1%' if df_asks['ask_price'].max() / x < 0.999 else '0.01%')
    df_asks.loc[0, 'depth'] = '0%'
    depth = pd.concat([df_asks.groupby('depth')['ask_vol'].sum(),
                       df_bids.groupby('depth')['bid_vol'].sum()], axis=1).sort_values('depth')
    Print(depth)

def Save_txt(x):
    logging.info(f"Saving text to log.txt: {x}")
    with open('ML.txt', 'wt') as f:
        f.write(x)
    f.close()

def round_quantity(symbol, quantity):
    logging.info(f"Rounding quantity for {symbol}: {quantity}")
    info = client.get_symbol_info(symbol)
    step_size = float(info['filters'][1]['stepSize'])
    precision = int(round(-math.log(step_size, 10), 0))
    return round(quantity, precision)

window = gui141124.create_window()
while True:
    event, values = window.read()
    try:
        if event == '-UPDATE_TABLE-':
            logging.info("Updating table")
            window['-TABLE2-'].update(values=df.values.tolist())
        if event == '-PRINT-':
            logging.info("Print event")
            Print(values)
        if event == 'СИГНАЛЫ':
            logging.info("Starting signals thread")
            threading.Thread(target=Run).start()
        if event == 'Go':
            logging.info("Go event")
            Go()
        if event == 'Bill':
            logging.info("Bill event")
            Bill()
        if event == 'ВСЕ ОРДЕРА':
            logging.info("Displaying all orders")
            display_all_orders()
        if event == 'ОТКРЫТЫЕ ОРДЕРА':
            logging.info("Displaying open orders")
            display_open_orders()
        if event == 'Cancel':
            logging.info("Cancel order event")
            Cancel_order()
        if event == 'Cancel_all':
            logging.info("Cancel all orders event")
            Cancel_all_orders()
        if event == 'Do_it':
            logging.info(f"Executing: {values['-LIST_DOIT-']}")
            Print(eval(values['-LIST_DOIT-']))
        if event == 'Save':
            logging.info("Save event")
            Save_txt(values['-ML-'])
        if event == 'Clear':
            logging.info("Clear event")
            window['-ML-'].update('')
        if event == sg.WIN_CLOSED or event == 'Exit':
            logging.info("Exiting")
            break
    except Exception as e:
        logging.error(f"Exception: {e}")
        sg.popup(e, no_titlebar=True, background_color='#e22bc7')
window.close()