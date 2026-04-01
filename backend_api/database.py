import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="root1234",
        database="sleep_optimizer"
    )