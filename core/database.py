from contextlib import contextmanager

from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

from config import DATABASE_URL

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=10,
    kwargs={
        "autocommit": False,
        "row_factory": dict_row
    }
)


@contextmanager
def get_connection():
    with pool.connection() as conn:
        yield conn


def execute(
    query,
    params=None,
    *,
    fetchone=False,
    fetchall=False,
    commit=False
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)

            if fetchone:
                return cur.fetchone()

            if fetchall:
                return cur.fetchall()

            if commit:
                conn.commit()

            return None


def transaction():
    return get_connection()
