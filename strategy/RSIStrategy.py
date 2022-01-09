from api.Kiwoom import *
from util.make_up_universe import *
from util.db_helper import *
from util.time_helper import *
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

    def check_and_get_universe(self):
        if not check_table_exist(self.strategy_name, 'universe'):
            universe_list = get_universe()
            print(universe_list)
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
        print(self.universe)

    def check_and_get_price_data(self):
        for idx, code enumerate(self.universe.key()):
            print("({}/{}) {}".format(idx+1, len(self.universe), code))

            if check_transaction_closed() and not check_table_exist(self.strategy_name, code):
                price_df = self.kiwoom.get_price_data(code)
                insert_df_to_db(self.strategy_name, code, price_df)
            else:
                if check_transaction_closed():
                    sql = "select max({}) from {}".format('index', code)
                    cur = execute_sql(self.strategy_name, sql)

                    last_date = cur.fetchone()

                    now = datetime.now().strftime("%Y%m%d")

                    if last_date[0] != now:
                        price_df = self.kiwoom.get_price_data(code)
                        insert_df_to_db(self.strategy_name, code)
                else:
                    sql = "select * from {}".format(code)
                    cur = execute_sql(self.strategy_name, sql)
                    cols = [column[0] for column in cur.description]
                    price_df = pd.DataFrame.from_records(data=cur.fetchall(), columns=cols)
                    price_df = price_df.set_index('index')
                    self.universe[code]['price_df'] = price_df

    def set_universe_real_time(self):
        fids = get_fid('체결시간')
        codes = self.universe.keys()
        codes = ";".join(map(str, codes))
        self.kiwoom.set_real_reg("9999", codes, fids, "0")



    def run(self):
        pass