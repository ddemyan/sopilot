import gui, key, time
import pandas as pd
import PySimpleGUI as sg
from binance.client import Client
pd.options.display.expand_frame_repr = False
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)
client = Client(key.api_key, key.api_secret, testnet=True)
def Go():
    deptH = client.get_order_book(symbol=values['-ltp-'])
    best_buy, best_sell = deptH['bids'][3][0], deptH['asks'][3][0]
    if values['-BUY-'] == True:
        Print(client.order_limit_buy(symbol=values['-ltp-'], quantity=0.1, price=best_buy))
    else:
        Print(client.order_limit_sell(symbol=values['-ltp-'], quantity=float(values['-LB-']), price=best_sell))
def display_all_orders():
    orders = pd.DataFrame(client.get_open_orders(symbol=values['-ltp-']),
                          columns=['orderId', 'symbol', 'price', 'side', 'origQty', 'status', 'type', 'time'])
    orderId = orders[['symbol','orderId']].values.tolist()
    window['-TABLE1-'].update(values=orders.values.tolist())
    window['-id-'].update(values=orderId)# Обновление значений в ComboBox
def Print(*x):
    window['-ML-'].print('\n', x)
"""
def Print(x, start_time):
    end_time = time.time()
    elapsed_time = end_time - start_time
    window['-ML-'].print(f"\n{x}\nElapsed time: {elapsed_time:.2f} seconds")
"""
def delete_order():
    if values['-id-']:
        symbol, order_id = values['-id-']
        Print(client.cancel_order(symbol=symbol, orderId=order_id))
def get_depth():
    x = client.get_order_book(symbol=values['-ltp-'])
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
def log_data(*data):
    with open('log.txt', 'wt') as f:
        f.write('\n')
        for item in data:
            f.write(str(item))
#def Win():
#    current_data = window['-TABLE1-'].get() # Получение текущих данных из таблицы
#    updated_data = current_data + orders.values.tolist()# Добавление новых данных к текущим
#    window['-TABLE1-'].update(values=updated_data)# Обновление таблицы
dictL = {'Bill': lambda: window['-bill-'].update(values['-lc-']),
         'ОТКРЫТЫЕ ПОЗИЦИИ': lambda: display_all_orders(),
         'Go': lambda: Go(),
         'Delete': lambda: delete_order()}
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
