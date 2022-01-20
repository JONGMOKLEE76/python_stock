import numpy as np
from strategy.RSIStrategy import *
import sys
from util.notifier import *
from util.opendart import *

app = QApplication(sys.argv)
rsi_strategy = RSIStrategy()
rsi_strategy.start()
app.exec_()

