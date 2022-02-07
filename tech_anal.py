import sqlite3
import datetime
import pandas as pd
from tqdm import tqdm
from util.opendart import *
# import matplotlib.pyplot as plt
# import seaborn as sns

# 특정 구간의 주가의 저가/고가와 고가대비 현재가의 하락폭

def get_all_stock_fall_rate_for_certain_period(start_date, end_date):
    org_code_list = get_all_stock_table_from_DB()
    print(len(org_code_list))
    result_code_list = pick_stock_codes_in_opendart(org_code_list)
    print(len(result_code_list))

    dic = {'code':[], 'min_date': [], 'min_price': [], 'max_date': [], 'max_price': [], 'cur_price': []}

    for code in tqdm(result_code_list):
        with sqlite3.connect('RSIStrategy.db') as con:
            sql = "select * from `{}` where `index` > {} and `index` <= {}".format(code, start_date, end_date)

            df = pd.read_sql(sql, con)
            df_min = df[df['close'] == df['close'].min()].iloc[0].to_list()
            min_date = df_min[0]
            min_price = df_min[4]
            df_max = df[df['close'] == df['close'].max()].iloc[0].to_list()
            max_date = df_max[0]
            max_price = df_max[4]
            current_price = df.loc[df['index'] == end_date, 'close'].values[0]

            dic['code'].append(code)
            dic['min_date'].append(min_date)
            dic['min_price'].append(min_price)
            dic['max_date'].append(max_date)
            dic['max_price'].append(max_price)
            dic['cur_price'].append(current_price)

    df = pd.DataFrame(dic)

    df['min_date'] = pd.to_datetime(df['min_date'])
    df['max_date'] = pd.to_datetime(df['max_date'])
    df['min_year'] = df['min_date'].dt.year
    df['min_month'] = df['min_date'].dt.month
    df['max_year'] = df['max_date'].dt.year
    df['max_month'] = df['max_date'].dt.month
    df['fall_rate'] = (df['cur_price'] - df['min_price']) / (df['max_price'] - df['min_price']) * 100

    return df

def detect_minus_price(code):
    with sqlite3.connect('RSIStrategy.db') as con:
        cur = con.cursor()
        sql = "select `index`, close from `{}` where close < 0".format(code)
        cur.execute(sql)
        result = cur.fetchone()
    if result == None:
        return None
    else:
        return result

def get_all_stock_table_from_DB():
    with sqlite3.connect('RSIStrategy.db') as con:
        cur = con.cursor()
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        cur.execute(sql)
        stock_list  = []
        for code in cur.fetchall():
            if len(code[0]) == 6:
                stock_list.append(code[0])
    return stock_list

def check_stock_in_opendart(code):
    with sqlite3.connect('RSIStrategy.db') as con:
        cur = con.cursor()
        sql = "SELECT * FROM opendart_company_list where stock_code = ?"
        cur.execute(sql, (code,))
        result = cur.fetchone()
        if result == None:
            return False
        else:
            return True

def pick_stock_codes_in_opendart(code_list):
    result_list = []
    for code in tqdm(code_list):
        if check_stock_in_opendart(code):
            result_list.append(code)
    return result_list

def delete_record_for_certain_date(code_list, date):
    for code in tqdm(code_list):
        with sqlite3.connect("RSIStrategy.db") as con:
            cur = con.cursor()
            sql = "DELETE FROM `{}` where `index` = ?".format(code)
            cur.execute(sql, (date,))

if __name__ == '__main__':
    code_list = get_all_stock_table_from_DB()
    delete_record_for_certain_date(code_list, '20220204')






