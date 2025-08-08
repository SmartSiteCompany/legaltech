import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="emmanuel_admin",
        password="smartsite",
        database="asistente_db"
    )

def get_dict_cursor():
    return get_db_connection().cursor(dictionary=True)