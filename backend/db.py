import os
import sqlite3
from typing import Optional, Any, Iterable
from pathlib import Path
from dotenv import load_dotenv

try:
    import mysql.connector
except Exception:
    mysql = None

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')
load_dotenv(dotenv_path=ROOT_DIR / '.env')


class RowProxy(dict):
    def __init__(self, data: dict, columns: Iterable[str]):
        super().__init__(data)
        self._columns = list(columns)

    def __getitem__(self, key):
        if isinstance(key, int):
            return super().__getitem__(self._columns[key])
        return super().__getitem__(key)


class DBCursor:
    def __init__(self, cursor, engine: str):
        self._cursor = cursor
        self._engine = engine

    @property
    def description(self):
        return self._cursor.description

    def execute(self, query: str, params: Optional[Iterable[Any]] = None):
        if self._engine == 'mysql':
            query = query.replace('?', '%s')
        if params is None:
            return self._cursor.execute(query)
        return self._cursor.execute(query, params)

    def executemany(self, query: str, params: Iterable[Iterable[Any]]):
        if self._engine == 'mysql':
            query = query.replace('?', '%s')
        return self._cursor.executemany(query, params)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self._engine == 'mysql':
            return RowProxy(row, self._cursor.column_names)
        return row

    def fetchall(self):
        rows = self._cursor.fetchall()
        if self._engine == 'mysql':
            return [RowProxy(row, self._cursor.column_names) for row in rows]
        return rows

    def __getattr__(self, name: str):
        return getattr(self._cursor, name)


class DBConnection:
    def __init__(self, conn, engine: str):
        self._conn = conn
        self._engine = engine

    def cursor(self):
        if self._engine == 'mysql':
            return DBCursor(self._conn.cursor(dictionary=True), self._engine)
        return DBCursor(self._conn.cursor(), self._engine)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    @property
    def engine(self):
        return self._engine


def get_engine(db_path: Optional[str] = None) -> str:
    if db_path:
        return 'sqlite'
    return os.getenv('DB_ENGINE', 'sqlite').lower()


def get_sqlite_path(default_path: str) -> str:
    return os.getenv('DB_PATH', default_path)


def get_mysql_config():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            return {
                'host': parsed.hostname or 'localhost',
                'port': int(parsed.port or 3306),
                'user': parsed.username or 'root',
                'password': parsed.password or '',
                'database': (parsed.path or '/cipa').lstrip('/'),
                'autocommit': False
            }
        except Exception:
            pass
    return {
        'host': os.getenv('MYSQL_HOST', os.getenv('DB_HOST', 'localhost')),
        'port': int(os.getenv('MYSQL_PORT', os.getenv('DB_PORT', '3306'))),
        'user': os.getenv('MYSQL_USER', os.getenv('DB_USER', 'root')),
        'password': os.getenv('MYSQL_PASSWORD', os.getenv('DB_PASS', '')),
        'database': os.getenv('MYSQL_DATABASE', os.getenv('DB_NAME', 'cipa')),
        'autocommit': False
    }


def get_connection(db_path: Optional[str] = None, default_sqlite_path: str = './data/notas_credito.db') -> DBConnection:
    engine = get_engine(db_path)
    if engine == 'mysql' and db_path is None:
        if mysql is None:
            raise RuntimeError('mysql-connector-python no instalado')
        config = get_mysql_config()
        try:
            conn = mysql.connector.connect(**config)
            return DBConnection(conn, engine)
        except Exception as e:
            error_code = getattr(e, 'errno', None)
            if error_code == 1049:
                base_config = {k: v for k, v in config.items() if k != 'database'}
                conn = mysql.connector.connect(**base_config)
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']}")
                conn.commit()
                conn.close()
                conn = mysql.connector.connect(**config)
                return DBConnection(conn, engine)
            raise
    sqlite_path = db_path or get_sqlite_path(default_sqlite_path)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    return DBConnection(conn, 'sqlite')
