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
rsi_strategy.start()

app.exec_()






