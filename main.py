import sqlite3

from strategy.RSIStrategy import *
import sys
from util.notifier import *

app = QApplication(sys.argv)
rsi_strategy = RSIStrategy()
rsi_strategy.start()

# con = sqlite3.connect('RSIStrategy.db')
# cur = con.cursor()
#
# for code in rsi_strategy.universe.keys():
#     sql = "delete from `{}` where `index` = '20220118'".format(code)
#     cur.execute(sql)
#
# con.commit()
# cur.close()
# con.close()
app.exec_()


# rsi_strategy = RSIStrategy()
# rsi_strategy.start()

# 주식 일봉 데이타 가져와서 출력
# df = kiwoom.get_price_data("005930")
# print(df)

# 주문 가능 금액 확인
# deposit = kiwoom.get_deposit()

# 주문 정보 가져오기
# orders = kiwoom.get_order()
# print(orders)

# 잔고 정보 가져오기
# position = kiwoom.get_balance()
# print(position)

# 주문
# order_result = kiwoom.send_order('삼전매수', '1001', 1, '005930', 1, '75000', '00')
# print(order_result)

# 실시간 정보
# fids = get_fid("체결시간")
# codes = '005930;'
# kiwoom.set_real_reg("1000", "", get_fid("장운영구분"), '0')


