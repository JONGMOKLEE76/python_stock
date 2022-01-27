import datetime
import time

import pandas as pd

from api.Kiwoom import *
from util.make_up_universe import *
from util.db_helper import *
from util.time_helper import *
from util.notifier import *
import math
import traceback

class RSIStrategy(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.strategy_name = "RSIStrategy"
        self.kiwoom = Kiwoom()
        self.universe = {}
        self.deposit = 0
        self.is_init_success = False
        self.init_strategy()

    def init_strategy(self):
        try:
            self.check_and_get_universe()
            self.check_and_get_price_data()
            self.kiwoom.get_order()
            self.kiwoom.get_balance()
            self.deposit = self.kiwoom.get_deposit()
            self.set_universe_real_time()
            self.is_init_success = True
        except Exception as e:
            print(traceback.format_exc())
            send_message(traceback.format_exc(), RSI_STRATEGY_MESSAGE_TOKEN)

    def check_and_get_universe(self):
        if not check_table_exist(self.strategy_name, 'universe'):
            universe_list = get_universe()
            # print(universe_list)
            universe = {}
            now = datetime.now().strftime("%Y%m%d")

            kospi_code_list = self.kiwoom.get_code_list_by_market("0")
            kosdaq_code_list = self.kiwoom.get_code_list_by_market("10")

            for code in kospi_code_list + kosdaq_code_list:
                code_name = self.kiwoom.get_master_code_name(code)

                if code_name in universe_list:
                    universe[code] = code_name

            universe_df = pd.DataFrame({
                'code': universe.keys(),
                'code_name': universe.values(),
                'created_at': [now] * len(universe.keys())
                })

            insert_df_to_db(self.strategy_name, 'universe', universe_df)

        sql = "select * from universe"
        cur = execute_sql(self.strategy_name, sql)
        universe_list = cur.fetchall()
        for item in universe_list:
            idx, code, code_name, created_at = item
            self.universe[code] = {
                'code_name': code_name
            }
        # print(self.universe)

    def check_and_get_price_data(self):
        for idx, code in enumerate(self.universe.keys()):
            print("({}/{}) {}".format(idx+1, len(self.universe), code))

            if check_transaction_closed() and not check_table_exist(self.strategy_name, code):
                price_df = self.kiwoom.get_price_data(code)
                insert_df_to_db(self.strategy_name, code, price_df)
            else:
                if check_transaction_closed():
                    sql = "select max(`{}`) from `{}`".format('index', code)
                    cur = execute_sql(self.strategy_name, sql)

                    last_date = cur.fetchone()

                    now = datetime.now().strftime("%Y%m%d")

                    if last_date[0] != now:
                        price_df = self.kiwoom.get_price_data_2(code)
                        price_df = price_df[price_df.index > last_date[0]]
                        price_df = price_df[::-1]
                        insert_df_to_db(self.strategy_name, code, price_df, 'append')
                else:
                    sql = "select * from `{}`".format(code)
                    cur = execute_sql(self.strategy_name, sql)
                    cols = [column[0] for column in cur.description]
                    price_df = pd.DataFrame.from_records(data=cur.fetchall(), columns=cols)
                    price_df = price_df.set_index('index')
                    self.universe[code]['price_df'] = price_df

    def set_universe_real_time(self):
        fids = get_fid('체결시간')
        codes = list(self.universe.keys())
        first_half = codes[:100]
        first_half = ";".join(map(str, first_half))
        second_half = codes[100:]
        second_half = ";".join(map(str, second_half))
        self.kiwoom.set_real_reg("9999", first_half, fids, "0")
        self.kiwoom.set_real_reg("9998", second_half, fids, "0")

    def check_sell_signal(self, code):
        universe_item = self.universe[code]
        # print(universe_item)
        # print(universe_item.keys())

        if code not in self.kiwoom.universe_realtime_transaction_info.keys():
            print("매도대상 확인 과정에서 아직 체결정보가 없습니다.")
            return

        open = self.kiwoom.universe_realtime_transaction_info[code]['시가']
        high = self.kiwoom.universe_realtime_transaction_info[code]['고가']
        low = self.kiwoom.universe_realtime_transaction_info[code]['저가']
        close = self.kiwoom.universe_realtime_transaction_info[code]['현재가']
        volume = self.kiwoom.universe_realtime_transaction_info[code]['누적거래량']

        today_price_data = [open, high, low, close, volume]

        df = universe_item['price_df'].copy()
        df.loc[datetime.now().strftime('%Y%m%d')] = today_price_data
        # print(df)

        period = 2
        date_index = df.index.astype('str')
        U = np.where(df['close'].diff(1) > 0, df['close'].diff(1), 0)
        D = np.where(df['close'].diff(1) < 0, df['close'].diff(1) * (-1), 0)
        AU = pd.DataFrame(U, index = date_index).rolling(window=period).mean()
        AD = pd.DataFrame(D, index = date_index).rolling(window=period).mean()
        RSI = AU / (AD + AU) * 100
        df['RSI(2)'] = RSI

        purchase_price = self.kiwoom.balance[code]['매입가']
        rsi = df[-1:]['RSI(2)'].values[0]

        if rsi > 80 and close > purchase_price:
            print('매도 대상임')
            return True
        else:
            print('RSI:', rsi)
            return False

    def order_sell(self, code):
        quantity = self.kiwoom.balance[code]['보유수량']
        ask = self.kiwoom.universe_realtime_transaction_info[code]['(최우선)매도호가']
        order_result = self.kiwoom.send_order('send_sell_order', '1001', 2, code, quantity, ask, '00')

    def check_buy_signal_and_order(self, code):
        if not check_adjacent_transaction_closed_for_buying():
            return False
        univese_item = self.universe[code]

        if code not in self.kiwoom.universe_realtime_transaction_info.keys():
            print("매수대상 확인 과정에서 아직 체결정보가 없습니다.")
            return

        open = self.kiwoom.universe_realtime_transaction_info[code]['시가']
        high = self.kiwoom.universe_realtime_transaction_info[code]['고가']
        low = self.kiwoom.universe_realtime_transaction_info[code]['저가']
        close = self.kiwoom.universe_realtime_transaction_info[code]['현재가']
        volume = self.kiwoom.universe_realtime_transaction_info[code]['누적거래량']

        today_price_data = [open, high, low, close, volume]
        df = univese_item['price_df'].copy()
        df.loc[datetime.now().strftime("%Y%m%d")] = today_price_data

        period = 2
        date_index = df.index.astype('str')
        U = np.where(df['close'].diff(1) > 0, df['close'].diff(1), 0)
        D = np.where(df['close'].diff(1) < 0, df['close'].diff(1) * (-1), 0)
        AU = pd.DataFrame(U, index=date_index).rolling(window=period).mean()
        AD = pd.DataFrame(D, index=date_index).rolling(window=period).mean()
        RSI = AU / (AD + AU) * 100
        df['RSI(2)'] = RSI

        df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean()
        df['ma60'] = df['close'].rolling(window=60, min_periods=1).mean()

        rsi = df[-1:]['RSI(2)'].values[0]
        ma20 = df[-1:]['ma20'].values[0]
        ma60 = df[-1:]['ma60'].values[0]

        idx = df.index.get_loc(datetime.now().strftime('%Y%m%d')) - 2
        close_2days_ago = df.iloc[idx]['close']
        price_diff = (close - close_2days_ago) / close_2days_ago * 100

        if ma20 > ma60 and rsi < 5 and price_diff < -3:
            print('일단 매수 조건에 걸림')
            if (self.get_balance_count() + self.get_buy_order_count()) >= 30:
                return
            budget = self.deposit / (30 - (self.get_balance_count() + self.get_buy_order_count()))
            bid = self.kiwoom.universe_realtime_transaction_info[code]['(최우선)매수호가']

            quantity = math.floor(budget / bid)

            if quantity < 1:
                print('살수 있는 수량이 아님', bid)
                return

            amount = quantity * bid
            self.deposit = math.floor(self.deposit - amount * 1.00015)

            if self.deposit < 0:
                print('예수금 부족함')
                return

            order_result = self.kiwoom.send_order('send_buy_order', '1001', 1, code, quantity, bid, '00')
            self.kiwoom.order[code] = {'주문구분':'매수', '미체결수량':quantity}
        else:
            print('아직 매수타이밍 아님')
            return

    def get_balance_count(self):
        balance_count = len(self.kiwoom.balance)
        for code in self.kiwoom.order.keys():
            if code in self.kiwoom.balance and self.kiwoom.order[code]['주문구분'] == '매도' and self.kiwoom.order[code]['미체결수량'] == 0:
                balance_count = balance_count - 1
        return balance_count

    def get_buy_order_count(self):
        buy_order_count = 0
        for code in self.kiwoom.order.keys():
            if code not in self.kiwoom.balance and self.kiwoom.order[code]['주문구분'] == '매수':
                buy_order_count = buy_order_count + 1
        return buy_order_count

    def run(self):
        while self.is_init_success:
            try:
                if not check_transaction_open():
                    print('장시간이 아니므로 5분간 대기합니다.')
                    time.sleep(5 * 60)
                    continue

                for idx, code in enumerate(self.universe.keys()):
                    print('[{}/{}_{}]'.format(idx+1, len(self.universe), self.universe[code]['code_name']),
                          '보유종목개수:', self.get_balance_count(), '주문종목개수:', self.get_buy_order_count(), '주문가능금액:', self.deposit)
                    time.sleep(0.5)

                    if code in self.kiwoom.order.keys():
                        print('접수 주문', self.kiwoom.order[code])

                        if self.kiwoom.order[code]['미체결수량'] > 0:
                            pass

                    elif code in self.kiwoom.balance.keys():
                        print('보유 종목임. 수익률은 :', self.kiwoom.balance[code]['수익률']*100, '%')
                        if self.check_sell_signal(code):
                            self.order_sell(code)
                    else:
                        self.check_buy_signal_and_order(code)

            except Exception as e:
                print(traceback.format_exc())
                send_message(traceback.format_exc(), RSI_STRATEGY_MESSAGE_TOKEN)
