import numpy as np
from strategy.RSIStrategy import *
import sys
from util.notifier import *

app = QApplication(sys.argv)
# rsi_strategy = RSIStrategy()
# rsi_strategy.start()

kiwoom = Kiwoom()


kospi_code_list = kiwoom.get_code_list_by_market("0")
df = pd.DataFrame(columns=['종목명', '회계월', '자본금', '상장주식수(천주)', 'PER', 'EPS', 'ROE', 'PBR', '매출액', '영업이익', '당기순이익', '현재가'])
for code in kospi_code_list[:30]:
     df.loc[code] = kiwoom.get_stock_info(code)

df.replace('', 0, inplace=True)
df = df.astype({'자본금':'int64', '상장주식수(천주)':'int64', 'PER':'float', 'EPS':'float', 'ROE':'float', 'PBR':'float', '매출액':'int64', '영업이익':'int64', '당기순이익':'int64', '현재가':'int64'})

df['상장주식수(주)'] = df['상장주식수(천주)'] * 1000
df['영업이익(원)'] = df['영업이익'] * 100000000
df['당기순이익(원)'] = df['당기순이익'] * 100000000
df['EPS(재계산)'] = df['당기순이익(원)'] / df['상장주식수(주)']
df['PER(재계산)'] = df['현재가'] / df['EPS']
print(df.info())

df.to_excel('kospi.xlsx')

print('완료')

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


