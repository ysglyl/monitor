import sqlite3


class DbHelper(object):
    conn = sqlite3.connect('db/db.db')
    cursor = conn.cursor()
    cursor.execute(
        'create table if not exists t_user (ID INTEGER PRIMARY KEY AUTOINCREMENT,name text)')
    conn.commit()

    @staticmethod
    def insert_user(name):
        DbHelper.cursor.execute('insert into t_user (name) values (?)', (name,))
        DbHelper.conn.commit()
        DbHelper.cursor.execute('select last_insert_rowid() from t_user')
        return DbHelper.cursor.fetchone()[0]

    @staticmethod
    def query_users():
        DbHelper.cursor.execute('select * from t_user')
        return DbHelper.cursor.fetchall()
