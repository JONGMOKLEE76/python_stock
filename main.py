from api.Kiwoom import *
import sys

app = QApplication(sys.argv)
kiwoom = Kiwoom()


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
fids = get_fid("체결시간")
codes = '005930;'
kiwoom.set_real_reg("1000", "", get_fid("장운영구분"), '0')

app.exec_()
