import sqlite3
import numpy as np
from strategy.RSIStrategy import *
import sys
from util.notifier import *
from util.opendart import *
from tqdm import tqdm

app = QApplication(sys.argv)

rsi_strategy = RSIStrategy()
rsi_strategy.kiwoom.update_all_stock_price('20220128')

app.exec_()






