import logging
import os
import re
import sys
import urllib.parse
from configparser import ConfigParser

from databases import Database
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


# Leer el connection_string desde config.ini
def get_database_url():
    # Determinar la ruta base. Priorizar el directorio del ejecutable.
    if getattr(sys, "frozen", False):
        # Entorno de producción (PyInstaller)
        base_path = os.path.dirname(sys.executable)
    else:
        # Entorno de desarrollo
        base_path = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(base_path, "data", "config.ini")

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"El archivo de configuración no se encuentra en la ruta esperada: {config_path}"
        )

    config = ConfigParser(interpolation=None)
    config.read(config_path)
    connection_string = config.get("database", "connection_string", fallback=None)

    if connection_string is None:
        raise ValueError(
            "El connection_string no está configurado correctamente en el archivo config.ini"
        )
    return connection_string.strip()


DATABASE_URL = get_database_url()

# Detectar tipo de base de datos
if DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("mysql"):
    database = Database(DATABASE_URL)
    db_type = "async"
elif DATABASE_URL.startswith("mssql+pyodbc") or DATABASE_URL.startswith("mssql"):
    # Formato SQLAlchemy nativo, no se necesita hacer nada.
    db_type = "sqlserver"
    engine = create_engine(
        DATABASE_URL, fast_executemany=True, isolation_level="AUTOCOMMIT"
    )
else:
    # Si no es un dialecto conocido, podría ser una cadena DSN para pyodbc.
    if "DRIVER=" in DATABASE_URL and "SERVER=" in DATABASE_URL:
        # Adaptar la cadena DSN para SQLAlchemy.
        adapted_url = (
            f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(DATABASE_URL)}"
        )
        db_type = "sqlserver"
        engine = create_engine(
            adapted_url, fast_executemany=True, isolation_level="AUTOCOMMIT"
        )
    else:
        # Si no es un formato reconocible, lanzar el error.
        raise ValueError("Tipo de base de datos no soportado por la solución híbrida.")


# Función para obtener la conexión adecuada
def get_db():
    if db_type == "async":
        return database
    elif db_type == "sqlserver":
        return engine
    else:
        raise RuntimeError("Tipo de base de datos no soportado.")


# Ejemplo de uso en endpoints:
# from database_async import get_db
# db = get_db()
# if db_type == "async":
#     await db.fetch_all(...)
# else:
#     with db.connect() as conn:
#         result = conn.execute(text("SELECT ..."), params)
#         rows = result.fetchall()
