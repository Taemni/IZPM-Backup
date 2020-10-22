import pymysql

# MySQL Connection 연결
def ExecuteWriteSQL(sql, sql_data) : #insert db
    conn = pymysql.connect(host='', user='', password='', db='', charset='utf8')
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, sql_data)
        conn.commit()
    finally:
        conn.close()

def ExecuteReadSQL(sql) : #select db
    conn = pymysql.connect(host='', user='', password='', db='', charset='utf8')
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
    finally:
        conn.close()
