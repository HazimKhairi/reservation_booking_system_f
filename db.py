import mysql.connector
from mysql.connector import pooling
from config import Config

class Database:
    _pool = None
    
    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            cls._pool = pooling.MySQLConnectionPool(
                pool_name="library_pool",
                pool_size=5,
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE,
                port=Config.MYSQL_PORT
            )
        return cls._pool
    
    @classmethod
    def get_connection(cls):
        return cls.get_pool().get_connection()


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute a query with prepared statements to prevent SQL injection."""
    conn = None
    cursor = None
    try:
        conn = Database.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
        
        return result
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def execute_many(query, data_list):
    """Execute multiple inserts/updates."""
    conn = None
    cursor = None
    try:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, data_list)
        conn.commit()
        return cursor.rowcount
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
