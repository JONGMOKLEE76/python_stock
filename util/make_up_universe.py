import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from datetime import datetime

BASE_URL = 'https://finance.naver.com/sise/sise_market_sum.naver'
CODES = [0, 1]
fields = []

def execute_crawler():
        df_total = []
        for code in CODES:
                res = requests.get(BASE_URL + str(code))
                page_soup = BeautifulSoup(res.text, 'lxml')
                total_page_num = page_soup.select_one('td.pgRR > a')
                total_page_num = int(total_page_num.get('href').split('=')[-1])
                ipt_html = page_soup.select_one('div.subcnt_sise_item_top')
                global fields
                fields = [item.get('value') for item in ipt_html.select('input')]
                result = [crawler(code, page) for page in range(1, total_page_num + 1)]
                df = pd.concat(result, axis=0, ignore_index=0)
                df_total.append(df)

        df_total = pd.concat(df_total)
        df_total.reset_index(drop=True, inplace=True)
        return df_total

def crawler(code, page):
        global fields
        data = {'menu': 'market_sum', 'fieldIds': fields, 'returnUrl': BASE_URL + str(code) + '&page=' + str(page)}
        res = requests.post('https://finance.naver.com/sise/field_submit.nhn', data=data)
        df = pd.read_html(res.text)[1].drop(columns='토론실').dropna(how='all').set_index('N')
        return df
