import sqlite3

with sqlite3.connect('universe_price.db') as conn:
    cur = conn.cursor()
    # sql = 'delete from balance where will_clear_at=:will_clear_at'
    cur.execute('select * from balance')
    rows = cur.fetchall()
    print(rows)

# cur.execute('''CREATE TABLE balance
#             (code varchar(6) PRIMARY KEY,
#             bid_price int(20) NOT NULL,
#             quantity int(20) NOT NULL,
#             created_at varchar(14) NOT NULL,
#             will_clear_at varchar(14)
#             )''')

# sql = "insert into balance(code, bid_price, quantity, created_at, will_clear_at) values(?, ?, ?, ?, ?)"
