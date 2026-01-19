import psycopg2
#connection to databse
connection = psycopg2.connect(
    dbname="db_dictionary",
    user="postgres",
    password="PGS8!32_admin",
    host="localhost",
    port=5432
)