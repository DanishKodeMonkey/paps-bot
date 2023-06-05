"Database related functions for use with paps-bot"

import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()
# Create libpq connection string from env.
LOGIN_HOST = os.getenv("DB_HOST")
LOGIN_DBNAME = os.getenv("DB_NAME")
LOGIN_USER = os.getenv("DB_USER")
LOGIN_PASS = os.getenv("DB_PASS")
LOGIN_PORT = os.getenv("DB_PORT")
db_login = f"host={LOGIN_HOST} port={LOGIN_PORT} dbname={LOGIN_DBNAME}"


def create_connection():
    """Function establishing connection to database"""
    conn = None

    try:
        conn = psycopg2.connect(db_login)

    except psycopg2.DatabaseError as err:
        print(err)
    return conn


def create_table_sql(conn):
    """Function creating a blank table, if it does not already exist, in postgreSQL"""
    sql_table = """CREATE TABLE IF NOT EXISTS paps_table (
        game_id SERIAL PRIMARY KEY,
        game_type VARCHAR(255) NOT NULL,
        game_date DATE NOT NULL,
        game_time TIME NOT NULL
        );
        """
    try:
        cur = conn.cursor()
        cur.execute(sql_table)
    except psycopg2.Error as err:
        print(err)


def create_session_sql(conn, input_type, input_date, input_time):
    """Function creating a session, to already established table"""
    game_type = input_type
    game_date = input_date
    game_time = input_time
    sql_query = f"""INSERT INTO paps_table (game_type, game_date, game_time)
                    VALUES {game_type}, {game_date}, {game_time}"""
    try:
        cur = conn.cursor()
        cur.execute(sql_query)
        conn.commit()
    except psycopg2.Error as err:
        print(err)
    event_id = cur.fetchone()[0]
    return event_id
