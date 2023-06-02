#Collection of database oriented python functions

import psycopg2
from dotenv import load_dotenv
import os


load_dotenv()
#Create libpq connection string from env.
LOGIN_HOST = os.getenv('DB_HOST')
LOGIN_DBNAME = os.getenv('DB_NAME')
LOGIN_USER = os.getenv('DB_USER')
LOGIN_PASS = os.getenv('DB_PASS')
LOGIN_PORT = os.getenv('DB_PORT')
db_login = f"host={LOGIN_HOST} port={LOGIN_PORT} dbname={LOGIN_DBNAME}

#Establish event table variables in global scope
TABLE_NAME=""
GAME_TYPE=""
GAME_DATE=""
GAME_TIME=""

def create_connection()
    connection = None

    try:
        print('Connecting to postgreSQL database...')
        with psycopg2.connect(db_login) as connection:
            print('Establishing SQL cursor')
            with connection.cursor() as cursor:
                print('Connected!')
                cursor.execute('SELECT version()')
                db_version = cursor.fetchone()
                print('PostgreSQL version: ')
                print(db_version)
                cursor.close()
    except (Exception, psycopg2.DatabaseError) as err
        print(err)
    return connection

def create_table_sql_query(table_name)
    sql_table = f"""CREATE TABLE IF NOT EXISTS {table_name} (
        game_id SERIAL PRIMARY KEY,
        game_type VARCHAR(255) NOT NULL,
        game_date DATE NOT NULL,
        game_time TIME NOT NULL);
        """
        return sql_table

def create_session_table(connection, sql_table)
    try:
        c = connection.cursor()
        c.execute(create_table_sql_query)

    except psycopg2.Error as errErr:
        print("An error has occured...")
        print(errErr)

    except psycopg2.OperationalError as errOp:
        print("An operational error has occured...")
        print(errOp)
        
    except Exception as errExc:
        print("A general exception has occured...")
        print(errExc)
    finally:
        c.close()

def create_session()