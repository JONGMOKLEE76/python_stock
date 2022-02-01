from datetime import date
import sqlite3
import numpy as np
from strategy.RSIStrategy import *
import sys
from util.notifier import *
from util.opendart import *
from tqdm import tqdm




app = QApplication(sys.argv)

rsi_strategy = RSIStrategy()

kosdaq_list = rsi_strategy.kiwoom.get_code_list_by_market(10)
today = date.today().strftime('%y%m%d')

for code in tqdm(kosdaq_list):
    with sqlite3.connect("stock.db") as con:
        cur = con.cursor()
        sql = "SELECT stock_code FROM code_info where stock_code = ?"
        cur.execute(sql, (code,))
        if cur.fetchone() == None:
            sql = "INSERT INTO code_info VALUES (?, ?, ?, ?)"
            cur.execute(sql, (code, rsi_strategy.kiwoom.get_master_code_name(code), 'kosdaq', today,))

app.exec_()






