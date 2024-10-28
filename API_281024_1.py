import gui, key, math
import pandas as pd
import PySimpleGUI as sg
from binance.client import Client
pd.options.display.expand_frame_repr = False
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)
client = Client(key.api_key, key.api_secret, testnet=True)
def Go():
    x = f"{values['-lc-']}USDT"
    y = values['-lc-']["free"]
    deptH = client.get_order_book(symbol=x)
    best_buy, best_sell = deptH['bids'][3][0], deptH['asks'][3][0]
    # Получаем значение из поля -LB1- и -LB2-
    parts = int(values['-LB1-'])  # количество частей на которые будет разбит ордер
    order_type = values['-LB2-']  # тип ордера, например, скользящий стоплосс
    if values['-BUY-']:
        q = float(values['-LB-']) * float(client.get_asset_balance(asset=y)) / parts
        q = round_quantity(x, q)
        for _ in range(parts):
            if order_type == "trailing_stop_loss":
                Print('client.order')
            else:
                Print(client.order_limit_buy( symbol = x , price=float(best_buy) , quantity=q))
    else:
        q = float(values['-LB-']) * float(client.get_asset_balance(asset=y)) / parts
        q = round_quantity(x , q)
        for _ in range(parts):
            if order_type == "trailing_stop_loss":
                Print('client.order')
            else:
                Print(client.order_limit_sell( symbol=x , price=float(best_sell) , quantity = q ))
def Bill():
    # Инициализация начальных значений балансов
    initial_btc_balance = 1
    initial_eth_balance = 5
    initial_usdt_balance = 5000

    # Функция для вычисления процентного изменения
    def calculate_percentage_change(initial, current):
        return ((current - initial) / initial) * 100

    # Получение текущих балансов активов
    btc_balance = float(client.get_asset_balance(asset='BTC')["free"])
    eth_balance = float(client.get_asset_balance(asset='ETH')["free"])
    usdt_balance = float(client.get_asset_balance(asset='USDT')["free"])

    # Вычисление процентного изменения
    btc_change = calculate_percentage_change(initial_btc_balance, btc_balance)
    eth_change = calculate_percentage_change(initial_eth_balance, eth_balance)
    usdt_change = calculate_percentage_change(initial_usdt_balance, usdt_balance)

    # Получение последних цен на активы
    btc_price = float(client.get_recent_trades(symbol='BTCUSDT')[-1]['price'])
    eth_price = float(client.get_recent_trades(symbol='ETHUSDT')[-1]['price'])

    # Вычисление общей стоимости активов
    total_value = btc_price * btc_balance + eth_price * eth_balance + usdt_balance

    # Обновление значений в графическом интерфейсе
    window['-billBTC-'].update(f"{btc_balance} ({btc_change:.2f}%)")
    window['-billETH-'].update(f"{eth_balance} ({eth_change:.2f}%)")
    window['-billUSDT-'].update(f"{usdt_balance} ({usdt_change:.2f}%)")
    window['-billALL-'].update(total_value)
def display_open_orders():
    orders = pd.DataFrame(client.get_open_orders(symbol=f"{values['-lc-']}USDT"),
                          columns=['orderId', 'symbol', 'price', 'side', 'origQty', 'status', 'type', 'time'])
    orderId = orders[['symbol','orderId']].values.tolist()
    window['-TABLE1-'].update(values=orders.values.tolist())
    window['-id-'].update(values=orderId)# Обновление значений в ComboBox
def display_all_orders():
    orders = pd.DataFrame(client.get_all_orders(symbol=f"{values['-lc-']}USDT"),
                          columns=['orderId', 'symbol', 'price', 'side', 'origQty', 'status', 'type', 'time'])

    order_ = orders[orders['status'] == 'FILLED']# Выбираем строки где 'status'='FILLED'
    orderId =  order_[['symbol','orderId']].values.tolist()#значения 'symbol','orderId' в список
    window['-TABLE1-'].update(values=orders[orders['status'] == 'FILLED'].values.tolist())# Обновление значений в ComboBox
    window['-id-'].update(values=orderId)# Обновление значен��й в ComboBox
def Print(*x):
    window['-ML-'].print('\n', x, sep='')
def delete_order():
    if values['-id-']:
        symbol, order_id = values['-id-']
        Print(client.cancel_order(symbol=symbol, orderId=order_id))
def get_depth():
    x = client.get_order_book(symbol=f"{values['-lc-']}USDT")
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
    with open('log.txt','wt') as f: f.write(x)#.to_string()#x.to_csv(f"{x}.csv")
    f.close()
def log_data(*data):
    with open('log.txt', 'wt') as f:
        f.write('\n')
        for item in data:
            f.write(str(item))
def round_quantity(symbol, quantity):
    # Получаем информацию о символе
    info = client.get_symbol_info(symbol)
    step_size = float(info['filters'][1]['stepSize'])

    # Округляем количество до допустимого числа знаков после запятой
    precision = int(round(-math.log(step_size, 10), 0))
    return round(quantity, precision)
dictL = {
'Bill': lambda: Bill(),
'ВСЕ ОРДЕРА': lambda: display_all_orders(),
'ОТКРЫТЫЕ ОРДЕРА': lambda: display_open_orders(),
'Go': lambda: Go(),
'Delete': lambda: delete_order(),
'Do_it': lambda: Print(eval(values['-LIST_DOIT-'])),
'Save':  lambda: Save_txt(values['-ML-']),
'Clear': lambda: window['-ML-'].update('')}
window = gui.create_window()
while True:
    event, values = window.read()
    try:
        if event in dictL.keys():
            dictL[event]()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
    except Exception as e:
        sg.popup(e, no_titlebar=True, background_color='#e22bc7')
window.close()