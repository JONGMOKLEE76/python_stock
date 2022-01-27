import sqlite3
import datetime
import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns

with sqlite3.connect('RSIStrategy.db') as con:
    # cur = con.cursor()
    table = '200130'
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
    current_price = df.loc[df['index'] == today.index, 'close']
    print('최저가일자:', min_date, min_price)
    print('최고가일자:', max_date, max_price)
    print('하락폭:', (max_price - current_price)/(max_price-min_price)*100, "%" )
    print(current_price)


    # sns.lineplot(x='index', y='close', data=df)
    # plt.show()

