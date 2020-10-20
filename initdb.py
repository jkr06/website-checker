from dynaconf import settings
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def create_db(user, password, host, port, dbname, default_db=None):
    # Only production DB needs default_db to connect
    conn = psycopg2.connect(
        user=user, password=password, host=host, port=port, dbname=default_db
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE {dbname}")
    cur.close()
    conn.close()


def destroy_db(user, password, host, port, dbname):
    conn = psycopg2.connect(user=user, password=password, host=host, port=port)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE {dbname}")
    cur.close()
    conn.close()


def initialize_db(cursor):
    cursor.execute(
        "CREATE TABLE events (id serial NOT NULL PRIMARY KEY,"
        "url varchar(256) NOT NULL, http_status integer NOT NULL, response_time numeric(9, 6) NOT NULL,"
        "event_time timestamp with time zone NOT NULL, search_results jsonb NOT NULL)"
    )


if __name__ == "__main__":
    print("creating database ", settings.DATABASE.dbname)
    create_db(**(dict(settings.DATABASE)))

    print("initializing database")
    conn = psycopg2.connect(**(dict(settings.DATABASE)))
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    initialize_db(cur)

    cur.close()
    conn.close()
