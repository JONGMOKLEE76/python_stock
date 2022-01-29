import requests
import zipfile
import xml.etree.ElementTree as ET # xml 자료를 처리하기 위한 모듈
import pandas as pd
import sqlite3
import re

key = "5aa91e225ab588004e05be4c7385998c59b42d00"

def make_dart_corpcode_db():
    url = "https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={key}".format(key = key)
    res = requests.get(url)
    f = open('고유번호.zip', 'wb')
    f.write(res.content)
    f.close()
    with zipfile.ZipFile("고유번호.zip", "r") as zip_ref:
        zip_ref.extractall()
    tree = ET.parse('CORPCODE.xml')
    root = tree.getroot()

    record = []  # 회사 정보를 담을 빈 리스트 생성

    for list in root.iter('list'):  # 리스트 tag 를 돌면서 정보를 추출
        dic = {}  # 특정 리스트 1개에서 정보를 취합하기 위한 빈 딕셔너리 생성
        for item in list:  # 특정 회사 리스트 1개에서 하위의 회사 정보를 돌면서 정보를 추출
            dic[item.tag] = item.text  # 각 정보의 tag와 text를 key 와 value로 저장하는 딕셔너리 자료 생성
        record.append(dic)  # 취합된 딕셔너리 1개를 빈 리스트의 첫번째 element로 저장

    df = pd.DataFrame(record)

    with sqlite3.connect('RSIStrategy.db') as con:  # 데이타베이스 접속을 위한 con 객체 생성
        df.to_sql('opendart_company_list', con, if_exists='replace', index=None)  # 데이티프레임을 sqlite로 저장, 만약 해당 table이 이미 저장되어 있으면 덮어쓰기하고, index는 추가하지 않는 옵션)

def conv_stock_code_to_name(code):
    with sqlite3.connect('RSIStrategy.db') as con:
        cur = con.cursor()
        sql = "SELECT corp_name FROM opendart_company_list where stock_code = ?"
        cur.execute(sql, (code,))
        name = cur.fetchone()
        return name[0]

def conv_stock_code_to_dartcode(code):
    with sqlite3.connect('RSIStrategy.db') as con:
        df = pd.read_sql("SELECT * FROM opendart_company_list", con, index_col = None) # db에서 회사정보를 불러와 데이타프레임으로 만듬
        if (df['stock_code'] == code).sum() != 0:
            return df[df['stock_code'] == code].iloc[0, 0]
        else:
            return False

# OpenDart에서 회사코드로 주식의 총수를 구해서 Series로 반환하는 함수
# reprt_code : 1분기보고서 : 11013 반기보고서 : 11012 3분기보고서 : 11014 사업보고서 : 11011

def get_stock_qty(code, year, reprt_code):
    base_url = "https://opendart.fss.or.kr/api/stockTotqySttus.json"
    params = {'crtfc_key':key, 'corp_code':code, 'bsns_year':year, 'reprt_code':reprt_code}
    res = requests.get(base_url, params=params)
    if res.json().get('status') == '000': # 특정 년도에는 보고서가 없을수도 있기 때문에 상태가 '000' 일때만 데이타 추출
        df = pd.DataFrame.from_dict(res.json().get('list'))
        corp_name = df['corp_name'][0]
        common_share_qty = df[df['se'].str.contains('보통')]['istc_totqy'].sum()
        self_common_share_qty = df[df['se'].str.contains('보통')]['tesstk_co'].sum()
        distributed_common_share_qty = df[df['se'].str.contains('보통')]['distb_stock_co'].sum()
        preferred_share_qty = df[df['se'].str.contains('우선')]['istc_totqy'].sum()
        self_preferred_share_qty = df[df['se'].str.contains('우선')]['tesstk_co'].sum()
        distributed_preferred_share_qty = df[df['se'].str.contains('우선')]['distb_stock_co'].sum()
        return pd.Series([corp_name, common_share_qty, self_common_share_qty, distributed_common_share_qty, preferred_share_qty, self_preferred_share_qty, distributed_preferred_share_qty], name = code, index = ['corp_name', 'common_share_qty', 'self_common_share_qty', 'distributed_common_share_qty', 'preferred_share_qty', 'self_preferred_share_qty', 'distributed_preferred_share_qty'])
    else:
        print(res.json()['message'])


# 함수 작성 중
def get_company_financial_data(code, year, reprt_code):
    base_url = 'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json'
    params = {'crtfc_key': key, 'corp_code': code, 'bsns_year': year, 'reprt_code': reprt_code, 'fs_div': 'CFS'}
    res = requests.get('https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json', params=params)
    if res.json().get('status') == '000':  # 특정 년도에는 보고서가 없을수도 있기 때문에 상태가 '000' 일때만 데이타 추출
        df = pd.DataFrame.from_dict(res.json().get('list'))
        df.replace('', 0, inplace=True)
        df = df.astype({'thstrm_amount': 'int64'})
        df1 = df[(df['sj_div'] == 'BS') & df['account_nm'].str.contains('자산총계|부채총계|자본금|^자본총계|^지배|^비지배', regex=True)]
        자산 = df1.loc[df1[df1['account_nm'] == '자산총계'].index[0], 'thstrm_amount']
        부채 = df1.loc[df1[df1['account_nm'] == '부채총계'].index[0], 'thstrm_amount']
        자본 = df1.loc[df1[df1['account_nm'] == '자본총계'].index[0], 'thstrm_amount']
        자본_지배 = df1.loc[df1[df1['account_nm'].str.contains('지배')].index[0], 'thstrm_amount']
        자본_비지배 = df1.loc[df1[df1['account_nm'].str.contains('비지배')].index[0], 'thstrm_amount']
        자본금 = df1.loc[df1[df1['account_nm'].str.contains('자본금')].index[0], 'thstrm_amount']
        if (df['sj_div'] == 'IS').sum() != 0:
            df2 = df[
                (df['sj_div'] == 'IS') & df['account_nm'].str.contains('매출액|영업이익|^당기순이익|^분기순이익|^반기순이익|보통주|우선주|^지배|^비지배',
                                                                       regex=True)]
            매출 = df2.loc[df2[df2['account_nm'].str.contains('매출액')].index[0], 'thstrm_amount']
            영업이익 = df2.loc[df2[df2['account_nm'].str.contains('영업이익')].index[0], 'thstrm_amount']
            순이익 = df2.loc[df2[df2['account_nm'].str.contains('순이익')].index[0], 'thstrm_amount']
            순이익_지배 = df2.loc[df2[df2['account_nm'].str.contains('지배')].index[0], 'thstrm_amount']
            순이익_비지배 = df2.loc[df2[df2['account_nm'].str.contains('비지배')].index[0], 'thstrm_amount']
            주당이익_보통주 = df2[df2['account_nm'].str.contains('보통')]['thstrm_amount'].sum()
            주당이익_우선주 = df2[df2['account_nm'].str.contains('우선')]['thstrm_amount'].sum()
            return pd.Series([자산, 부채, 자본, 자본_지배, 자본_비지배, 자본금, 매출, 영업이익, 순이익, 순이익_지배, 순이익_비지배, 주당이익_보통주, 주당이익_우선주],
                             name=code,
                             index=['자산', '부채', '자본', '자본_지배', '자본_비지배', '자본금', '매출', '영업이익', '순이익', '순이익_지배',
                                    '순이익_비지배', '주당이익_보통주', '주당이익_우선주'])
        else:
            df2 = df[(df['sj_div'] == 'CIS') & df['account_nm'].str.contains(
                '매출액|영업이익|^당기순이익|^분기순이익|^반기순이익|보통주|우선주|^지배|^비지배|주당이익', regex=True)]
            매출 = df2.loc[df2[df2['account_nm'].str.contains('매출액')].index[0], 'thstrm_amount']
            영업이익 = df2.loc[df2[df2['account_nm'].str.contains('영업이익')].index[0], 'thstrm_amount']
            순이익 = df2.loc[df2[df2['account_nm'].str.contains('순이익')].index[0], 'thstrm_amount']
            순이익_지배 = df2.loc[df2[df2['account_nm'].str.contains('지배')].index[0], 'thstrm_amount']
            순이익_비지배 = df2.loc[df2[df2['account_nm'].str.contains('비지배')].index[0], 'thstrm_amount']
            주당이익_보통주 = df2[df2['account_nm'].str.contains('기본주당이익')]['thstrm_amount'].sum()
            주당이익_우선주 = np.nan
            return pd.Series([자산, 부채, 자본, 자본_지배, 자본_비지배, 자본금, 매출, 영업이익, 순이익, 순이익_지배, 순이익_비지배, 주당이익_보통주, 주당이익_우선주],
                             name=code,
                             index=['자산', '부채', '자본', '자본_지배', '자본_비지배', '자본금', '매출', '영업이익', '순이익', '순이익_지배',
                                    '순이익_비지배', '주당이익_보통주', '주당이익_우선주'])
    else:
        print(res.json()['message'])
        return False


def get_company_financial_data_as_df(code, year, reprt_code):
    base_url = 'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json'
    params = {'crtfc_key': key, 'corp_code': code, 'bsns_year': year, 'reprt_code': reprt_code, 'fs_div': 'CFS'}
    res = requests.get('https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json', params=params)
    if res.json().get('status') == '000':  # 특정 년도에는 보고서가 없을수도 있기 때문에 상태가 '000' 일때만 데이타 추출
        df = pd.DataFrame.from_dict(res.json().get('list'))
        df.replace('', 0, inplace=True)
        #         df = df.astype({'thstrm_amount':'int64'})
        df = df[df['sj_div'].isin(['BS', 'IS', 'CIS'])]
        return df
    else:
        print(res.json()['message'])
        return ''