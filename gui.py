import PySimpleGUI as sg
# Настройки интерфейса
sizeW, sizeD, sizeML = (960, 670), (110, 23), (150, 30)
locationW, locationD = (5, 5), (7, 171)
font = ('Calibri', 14)
# Define the variables used in the GUI
gap = ['0.1', '0.25', '0.5', '0.75', '1']
gap1 = ['Все', 'по 3', 'по 5', 'по 10']
gap2 = ['Стоплосс', 'Тренд', 'Отскок']
list_trading_pairs = ['BTCUSDT', 'ETHUSDT', 'ETHBTC', 'BNBUSDT', 'BNBETH', 'BNBBTC']
list_coins = ['BTC', 'ETH', 'USDT', 'BNB']
orderId = []
# Определение макета интерфейса
c1 = sg.Column ([[ sg.Radio ('BUY', group_id=1, default=True, enable_events=True,
                             key='-BUY-')],
                  [sg.Radio ('SELL', group_id=1, enable_events=True, key='-SELL-')]])
c2 = sg.Column ([[ sg.Text ('ma'), sg.InputText ('7',key='-AVR-',size=(5,1))],
                  [sg.Text ('pa'), sg.InputText ('13',key='-AVR1-',size=(5,1))]])
c3 = sg.Column ([[ sg.Combo (list(gap), key='-LB-', default_value='0.1')]])
c4 = sg.Column ([[ sg.Combo (list(gap1), key='-LB1-', default_value='по 3')]])
c5 = sg.Column ([[ sg.Listbox (list(gap2), key='-LB12-', s=(15, 3),
                               select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE)]])
c6 = sg.Combo (list_trading_pairs,key='-ltp-',default_value='ETHUSDT',s=8,readonly=False)
c7 = sg.Column ([[sg.Button('Go')]])

layout = [
 [sg.Text ('БАЛАНС'),
  sg.Combo (list_coins, key='-lc-', default_value='USDT',readonly=False),
  sg.Button ('Bill'), sg.Input(key='-bill-', s=10, expand_x=True)],
 [[c7, sg.VerticalSeparator(), c1,sg.VerticalSeparator(), c2, sg.VerticalSeparator(),
 c3, sg.VerticalSeparator(), c4, sg.VerticalSeparator(), c5, sg.VerticalSeparator(),c6]],
 [sg.Text ('ОТКРЫТЫЕ ПОЗИЦИИ')],
 [sg.Table (values=[],
  headings=['orderId','symbol','price','side','origQty','status','type','time'],
  max_col_width=25, num_rows=5, auto_size_columns=True, justification='right',
  key='-TABLE1-', enable_events=True, expand_x=True)],
 [sg.Combo (orderId, key='-id-', s=10, readonly=False),
  sg.Button('Cancel'), sg.Button('Delete')],
 [sg.Table (values=[], headings=['ID','time','open','high','low','close','volume','num'],
  max_col_width=25, num_rows=5, auto_size_columns=True, justification='right',
  key='-TABLE-', enable_events=True, expand_x=True)],
 [sg.Button ('Exit'),sg.Text('СИГНАЛЫ')],
 [sg.Multiline (size=sizeML, key='-ML-', autoscroll=True)]
         ]
def create_window():
    return sg.Window('by Dandr11', layout, finalize=True, resizable=True,
                     location=locationW, size=sizeW)
if __name__ == "__main__":
    window = create_window()
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
    window.close()