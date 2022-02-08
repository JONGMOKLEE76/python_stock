from datetime import date
import sqlite3
import numpy as np
import pandas as pd

from strategy.RSIStrategy import *
import sys
from util.notifier import *
from util.opendart import *
from tqdm import tqdm

# RSI 전략 운영
# app = QApplication(sys.argv)
# rsi_strategy = RSIStrategy()
# rsi_strategy.start()
# app.exec_()

# 전체 주식의 오늘자 일봉데이타 UPDATE
app = QApplication(sys.argv)
kiwoom = Kiwoom()
kiwoom.update_all_stock_price('20220208')

# kospi_list = kiwoom.get_code_list_by_market(0)
# kosdaq_list = kiwoom.get_code_list_by_market(10)
# ELW_list = kiwoom.get_code_list_by_market(3)
# ETF_list = kiwoom.get_code_list_by_market(8)
# KONEX_list = kiwoom.get_code_list_by_market(50)
# mutual_fund = kiwoom.get_code_list_by_market(4)
# new_stock_list = kiwoom.get_code_list_by_market(5)
# ritz_list = kiwoom.get_code_list_by_market(6)
# hiel_fund = kiwoom.get_code_list_by_market(9)
# KOTC_list = kiwoom.get_code_list_by_market(30)
#
# kospi_name = []
# for code in kospi_list:
#     kospi_name.append(kiwoom.get_master_code_name(code))
#
# kosdaq_name = []
# for code in kosdaq_list:
#     kosdaq_name.append(kiwoom.get_master_code_name(code))
#
# ELW_name = []
# for code in ELW_list:
#     ELW_name.append(kiwoom.get_master_code_name(code))
#
# ETF_name = []
# for code in ETF_list:
#     ETF_name.append(kiwoom.get_master_code_name(code))
#
# KONEX_name = []
# for code in KONEX_list:
#     KONEX_name.append(kiwoom.get_master_code_name(code))
#
# mutual_name = []
# for code in mutual_fund:
#     mutual_name.append(kiwoom.get_master_code_name(code))
#
# kospi_dic = {'code':kospi_list, 'name':kospi_name}
# kosdaq_dic = {'code':kosdaq_list, 'name':kosdaq_name}
# ELW_dic = {'code':ELW_list, 'name':ELW_name}
# ETF_dic = {'code':ETF_list, 'name':ETF_name}
# KONEX_dic = {'code':KONEX_list, 'name':KONEX_name}
# mutual_dic = {'code':mutual_fund, 'name':mutual_name}
#
# pd.DataFrame(kospi_dic).to_excel('kospi.xlsx')
# pd.DataFrame(kosdaq_dic).to_excel('kosdaq.xlsx')
# pd.DataFrame(ELW_dic).to_excel('ELW.xlsx')
# pd.DataFrame(ETF_dic).to_excel('ETF.xlsx')
# pd.DataFrame(KONEX_dic).to_excel('KONEX.xlsx')
# pd.DataFrame(mutual_dic).to_excel('mutual.xlsx')

app.exec_()






