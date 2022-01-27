import sqlite3
import datetime
import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns

# 특정 구간의 주가의 저가/고가와 고가대비 현재가의 하락폭

with sqlite3.connect('RSIStrategy.db') as con:
    # cur = con.cursor()
    table = '005930'
    start_date = '20200101'
    today = datetime.datetime.now().strftime('%Y%m%d')
    sql = "select * from `{}` where `index` > {} and `index` <= {}".format(table, start_date, today)

    # cur.execute(sql)

    df = pd.read_sql(sql, con)
    df_min = df[df['close'] == df['close'].min()].iloc[0].to_list()
    min_date = df_min[0]
    min_price = df_min[4]
    df_max = df[df['close'] == df['close'].max()].iloc[0].to_list()
    max_date = df_max[0]
    max_price = df_max[4]
    current_price = df.loc[df['index'] == today, 'close'].values[0]
    print('최저가일자:', min_date, min_price)
    print('최고가일자:', max_date, max_price)
    print('하락폭:', (current_price - min_price)/(max_price-min_price)*100, "%" )
    print(current_price)


    # sns.lineplot(x='index', y='close', data=df)
    # plt.show()

