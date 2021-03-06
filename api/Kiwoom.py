import sys
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time
import pandas as pd
from datetime import date
import sqlite3
from util.const import *
from util.db_helper import *
from tqdm import tqdm

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._make_kiwoom_instance()
        self._set_signal_slot()
        self.comm_connect()
        self.account_number = self.get_account_number()

        self.tr_event_loop = QEventLoop()
        self.order = {}
        self.balance = {}
        self.universe_realtime_transaction_info = {}

    def _make_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slot(self):
        self.OnEventConnect.connect(self._login_slot)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.OnReceiveMsg.connect(self._on_receive_msg)
        self.OnReceiveChejanData.connect(self._on_chejan_slot)
        self.OnReceiveRealData.connect(self._on_receive_real_data)

    def _login_slot(self, err_code):
        if err_code == 0:
            print("연결 성공")
        elif err_code == 100:
            print("사용자 정보 교환 실패")
        elif err_code == 101:
            print("서버 접속 실패")
        elif err_code == 102:
            print("버전 처리 실패")
        else:
            print("연결 실패")
        self.login_event_loop.exit()

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def get_account_number(self, tag="ACCNO"):
        account_list = self.dynamicCall("GetLoginInfo(QString)", tag)
        account_number = account_list.split(';')[0]
        print(account_number)
        return account_number

    def get_code_list_by_market(self, market_type):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_type)
        code_list = code_list.split(';')[:-1]
        return code_list

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        # print("[Kiwoom] _on_receive_tr_data is called {} / {} / {}".format(screen_no, rqname, trcode))
        tr_data_cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

        if next == '2':
            self.has_next_tr_data = True
        else:
            self.has_next_tr_data = False

        if rqname == 'opt10081_req':
            ohlcv = {'date':[], 'open':[], 'high':[], 'low':[], 'close':[], 'volume':[]}

            for i in range(tr_data_cnt):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, '일자')
                open = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, '시가')
                high = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, '고가')
                low = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, '저가')
                close = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, '현재가')
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, '거래량')

                ohlcv['date'].append(date.strip())
                ohlcv['open'].append(int(open))
                ohlcv['high'].append(int(high))
                ohlcv['low'].append(int(low))
                ohlcv['close'].append(int(close))
                ohlcv['volume'].append(int(volume))

            self.tr_data = ohlcv

        elif rqname == 'opw00001_req':
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "주문가능금액")
            # print("수익증권증거금현금:", self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "수익증권증거금현금"))
            # print("예수금:", self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "예수금"))
            # print("주식증거금현금:", self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "주식증거금현금"))
            # print("출금가능금액:", self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "출금가능금액"))
            # print("주문가능금액:", self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "주문가능금액"))
            # print("30%종목주문가능금액:", self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "30%종목주문가능금액"))
            # print("100%종목주문가능금액:", self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "100%종목주문가능금액"))
            # print("d+1추정예수금:", self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "d+1추정예수금"))
            # print("d+2추정예수금:", self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "d+2추정예수금"))
            # print("d+1매도매수정산금:", self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "d+1매도매수정산금"))
            # print("d+2출금가능금액:", self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "d+2출금가능금액"))

            self.tr_data = int(deposit)
            # print(self.tr_data)

        elif rqname == "opt10075_req":
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목코드")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명")
                order_number = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문상태")
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문가격")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가")
                order_type = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문구분")
                left_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "미체결수량")
                executed_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "체결량")
                ordered_at = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시간")
                fee = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "당일매매수수료")
                tax = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "당일매매세금")
                code = code.strip()
                code_name = code_name.strip()
                order_number = str(int(order_number.strip()))
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())

                current_price = int(current_price.strip().lstrip('+').lstrip('-'))
                order_type = order_type.strip().lstrip('+').lstrip('-')
                left_quantity = int(left_quantity.strip())
                executed_quantity = int(executed_quantity.strip())
                ordered_at = ordered_at.strip()
                fee = int(fee)
                tax = int(tax)

                self.order[code] = {
                    '종목코드':code,
                    '종목명':code_name,
                    '주분번호':order_number,
                    '주문상태':order_status,
                    '주문수량':order_quantity,
                    '주문가격':order_price,
                    '현재가':current_price,
                    '주문구분':order_type,
                    '미체결수량':left_quantity,
                    '체결량':executed_quantity,
                    '주문시간':ordered_at,
                    '당일매매수수료':fee,
                    '당일매매세금':tax
                }
            self.tr_data = self.order

        elif rqname == "opw00018_req":
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목번호")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명")
                quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "보유수량")
                purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "매입가")
                return_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i,"수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가")
                total_purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "매입금액")
                available_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname,i, "매매가능수량")

                code = code.strip()[1:]
                code_name = code_name.strip()
                quantity = int(quantity)
                purchase_price = int(purchase_price)
                return_rate = float(return_rate)/100
                current_price = int(current_price)
                total_purchase_price = int(total_purchase_price)
                available_quantity = int(available_quantity)

                self.balance[code] = {
                    '종목명':code_name,
                    '보유수량':quantity,
                    '매입가':purchase_price,
                    '수익률':return_rate,
                    '현재가':current_price,
                    '매입금액':total_purchase_price,
                    '매매가능수량':available_quantity
                }
            self.tr_data = self.balance

        elif rqname == "opt10001_req":
            name = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "종목명")
            accnting_month = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "결산월")
            capital = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "자본금")
            listed_qty = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "상장주식")
            PER = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "PER")
            EPS = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "EPS")
            ROE = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "ROE")
            PBR = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "PBR")
            sales_amt = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "매출액")
            sales_income = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "영업이익")
            net_income = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "당기순이익")
            price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "현재가")

            self.tr_data = [name.strip(), accnting_month.strip(), capital.strip(), listed_qty.strip(), PER.strip(), EPS.strip(), ROE.strip(), PBR.strip(), sales_amt.strip(), sales_income.strip(), net_income.strip(), price.strip().lstrip('+').lstrip('-')]

        elif rqname == 'opt10086_req':
            date = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, 0, '날짜')
            open = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, 0, '시가')
            high = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, 0, '고가')
            low = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, 0, '저가')
            close = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, 0, '종가')
            volume = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, 0, '거래량')

            self.tr_data = [date.strip(), open.strip().lstrip('+').lstrip('-'), high.strip().lstrip('+').lstrip('-'), low.strip().lstrip('+').lstrip('-'), close.strip().lstrip('+').lstrip('-'), volume.strip().lstrip('+').lstrip('-')]

        self.tr_event_loop.exit()
        time.sleep(0.5)

    def get_stock_info(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10001_req", "opt10001", "0", "0001")
        self.tr_event_loop.exec_()
        return self.tr_data


    def get_price_data(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        # self.dynamicCall("SetInputValue(QString, QString)", "기준일자", "20220113")
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 0, "0001")
        self.tr_event_loop.exec_()

        ohlcv = self.tr_data

        while self.has_next_tr_data:
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            # self.dynamicCall("SetInputValue(QString, QString)", "기준일자", "20220113")
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 2, "0001")
            self.tr_event_loop.exec_()

            for key, val in self.tr_data.items():
                ohlcv[key] += val

        df = pd.DataFrame(ohlcv, columns=["open", "high", "low", "close", "volume"], index=ohlcv['date'])
        return df[::-1]

    def get_price_data_2(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        # self.dynamicCall("SetInputValue(QString, QString)", "기준일자", "20220125")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 0, "0001")
        self.tr_event_loop.exec_()

        df = pd.DataFrame(self.tr_data, columns=["open", "high", "low", "close", "volume"], index=self.tr_data['date'])
        return df

    def get_deposit(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QSTring)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00001_req", "opw00001", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    def send_order(self, rqname, screen_no, order_type, code, order_quantity, order_price, order_classification, origin_order_number = ""):
        order_result = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)", [rqname, screen_no, self.account_number, order_type, code, order_quantity, order_price, order_classification, origin_order_number])
        return order_result

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        print("[Kiwoom] _on_receive_msg is called {} / {} / {} / {}".format(screen_no, rqname, trcode,msg))

    def _on_chejan_slot(self, s_gubun, n_item_cnt, s_fid_list):
        print("[Kiwoom] _on_chejan_slot is called {} / {} / {}".format(s_gubun, n_item_cnt, s_fid_list))

        for fid in s_fid_list.split(";"):
            if fid in FID_CODES:
                code = self.dynamicCall("GetChejanData(int)", '9001')[1:]
                data = self.dynamicCall("GetChejanData(int)", fid)
                data = data.strip().lstrip('+').lstrip('-')
                if data.isdigit():
                    data = int(data)
                item_name = FID_CODES[fid]
                print("{}: {}".format(item_name, data))
                if int(s_gubun) == 0:
                    if code not in self.order.keys():
                        self.order[code] = {}
                    self.order[code].update({item_name:data})
                elif int(s_gubun) == 1:
                    if code not in self.balance.keys():
                        self.balance[code] = {}
                    self.balance[code].update({item_name:data})
        if int(s_gubun) == 0:
            print("*주문 출력(self.order)")
            print(self.order)
        elif int(s_gubun) == 1:
            print("* 잔고 출력(self.balance)")
            print(self.balance)

    def get_order(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10075_req", "opt10075", 0, "0002")
        self.tr_event_loop.exec_()

        while self.has_next_tr_data:
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
            self.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")
            self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "0")
            self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10075_req", "opt10075", 2, "0002")
            self.tr_event_loop.exec_()

        return self.tr_data

    def get_balance(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00018_req", "opw00018", 0, "0002")
        self.tr_event_loop.exec_()

        while self.has_next_tr_data:
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
            self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00018_req", "opw00018", 2, "0002")
            self.tr_event_loop.exec_()

        return self.tr_data

    def set_real_reg(self, str_screen_no, str_code_list, str_fid_list, str_opt_type):
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", str_screen_no, str_code_list, str_fid_list, str_opt_type)

        time.sleep(0.5)

    def _on_receive_real_data(self, s_code, real_type, real_data):
        if real_type == "장시작시간":
            pass

        elif real_type == "주식체결":
            signed_at = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("체결시간"))

            close = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('현재가'))
            close = abs(int(close))

            high = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('고가'))
            high = abs(int(high))

            open = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('시가'))
            open = abs(int(open))

            low = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('저가'))
            low = abs(int(low))

            top_priority_ask = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('(최우선)매도호가'))
            top_priority_ask = abs(int(top_priority_ask))

            top_priority_bid = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('(최우선)매수호가'))
            top_priority_bid = abs(int(top_priority_bid))

            accum_volume = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('누적거래량'))
            accum_volume = abs(int(accum_volume))

            # print(s_code, signed_at, close, high, open, low, top_priority_ask, top_priority_bid, accum_volume)

            if s_code not in self.universe_realtime_transaction_info:
                self.universe_realtime_transaction_info.update({s_code: {}})

            self.universe_realtime_transaction_info[s_code].update({
                "체결시간":signed_at,
                "시가":open,
                "고가":high,
                "저가":low,
                "현재가":close,
                "(최우선)매도호가":top_priority_ask,
                "(최우선)매수호가":top_priority_bid,
                "누적거래량":accum_volume
            })

    def get_stock_qty(self, code):
        stock_qty = self.dynamicCall("KOA_Functions(QString, QString)", "GetMasterListedStockCntEx", code)
        return stock_qty

    def get_today_price_data(self, code, date):
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "조회일자", date)
        self.dynamicCall("SetInputValue(QString, QString)", "표시구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10086_req", "opt10086", 0, "0001")
        self.tr_event_loop.exec_()
        return self.tr_data

    def update_all_stock_price(self, date):
        kospi_list = self.get_code_list_by_market(0)
        kosdaq_list = self.get_code_list_by_market(10)

        for code in tqdm(kospi_list+kosdaq_list):
            if check_table_exist('RSIStrategy', code):
                sql = "select max(`index`) from `{}`".format(code)
                cur = execute_sql('RSIStrategy', sql)
                last_date = cur.fetchone()
                if last_date[0] != date:
                    data = self.get_today_price_data(code, date)
                    if data[0] != '':
                        sql = "insert into `{}` values (?, ?, ?, ?, ?, ?)".format(code)
                        execute_sql('RSIStrategy', sql, data)
                    else:
                        print('값이 없음', code, data)
                continue
            price_df = self.get_price_data(code)
            insert_df_to_db('RSIStrategy', code, price_df)

    def update_stock_code_db(self):
        kospi_list = self.get_code_list_by_market(0)
        today = date.today().strftime('%y%m%d')

        for code in tqdm(kospi_list):
            with sqlite3.connect("stock.db") as con:
                cur = con.cursor()
                sql = "SELECT stock_code FROM code_info where stock_code = ?"
                cur.execute(sql, (code,))
                if cur.fetchone() == None:
                    sql = "INSERT INTO code_info VALUES (?, ?, ?, ?)"
                    cur.execute(sql, (code, self.get_master_code_name(code), 'kospi', today,))

        kosdaq_list = self.get_code_list_by_market(10)
        today = date.today().strftime('%y%m%d')

        for code in tqdm(kosdaq_list):
            with sqlite3.connect("stock.db") as con:
                cur = con.cursor()
                sql = "SELECT stock_code FROM code_info where stock_code = ?"
                cur.execute(sql, (code,))
                if cur.fetchone() == None:
                    sql = "INSERT INTO code_info VALUES (?, ?, ?, ?)"
                    cur.execute(sql, (code, self.get_master_code_name(code), 'kosdaq', today,))

    def get_stock_status(self, code):
        status = self.dynamicCall("[GetMasterConstruction(QString)", code)
        return status
