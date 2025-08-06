import mysql.connector

conexion = mysql.connector.connect(
    host="localhost",
    user="paduk_admin",
    password="smartsite",
    database="asistente_db"
)
cursor = conexion.cursor(dictionary=True)
