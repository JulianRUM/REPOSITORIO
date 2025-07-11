import asyncio
import hashlib
import json
import logging
import os
import secrets
import sys
from configparser import ConfigParser
from datetime import datetime, timedelta

# import jwt  # Comentado - no se usa para autenticación
from database_async import db_type, get_db
from fastapi import HTTPException
from passlib.hash import pbkdf2_sha256
from sqlalchemy import text

# Configuración de logging
base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
log_file = os.path.join(base_path, "data", "api.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def format_number(number):
    return "{:,.2f}".format(number)


def validate_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        raise ValueError("Formato de fecha inválido. Use 'YYYYMMDD'.")


def hash_password(password):
    return pbkdf2_sha256.hash(password)


def verify_password(stored_password, provided_password):
    return pbkdf2_sha256.verify(provided_password, stored_password)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def rotate_log_file(log_file):
    if os.path.exists(log_file):
        base_name, extension = os.path.splitext(log_file)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_log_file = f"{base_name}{timestamp}.{extension}"
        try:
            os.rename(log_file, new_log_file)
            print(f"Archivo de log renombrado a: {new_log_file}")
        except Exception as e:
            print(f"Error al renombrar el archivo de log: {e}")


# --- Funciones adicionales migradas de api.py ---
async def get_data_from_database(username, db):
    query = "SELECT * FROM usuariosj WHERE username = :username"
    return await db.fetch_one(query, {"username": username})


async def get_active_token(username, db):
    query = "SELECT token FROM tokenjwt WHERE username = :username AND active = 1"
    result = await db.fetch_one(query, {"username": username})
    return result


# FUNCIONES DE TOKEN COMENTADAS - AUTENTICACIÓN DESHABILITADA
# async def deactivate_old_tokens(username, db=None):
#     db = db or get_db()
#     if db_type == "async":
#         await db.connect()
#         await db.execute(
#             "UPDATE tokenjwt SET active = 0 WHERE username = :username",
#             {"username": username},
#         )
#         await db.disconnect()
#     else:

#         def sync_deactivate():
#             with db.connect() as conn:
#                 conn.execute(
#                     text("UPDATE tokenjwt SET active = 0 WHERE username = :username"),
#                     {"username": username},
#                 )

#         loop = asyncio.get_running_loop()
#         await loop.run_in_executor(None, sync_deactivate)


# async def save_token(username, token, hour1, min30, min5, db=None):
#     db = db or get_db()
#     if db_type == "async":
#         await db.connect()
#         await db.execute(
#             "INSERT INTO tokenjwt (username, token, active, [1hour], [30min], [5min], creation_time) VALUES (:username, :token, 1, :hour1, :min30, :min5, :creation_time)",
#             {
#                 "username": username,
#                 "token": token,
#                 "hour1": hour1,
#                 "min30": min30,
#                 "min5": min5,
#                 "creation_time": datetime.utcnow(),
#             },
#         )
#         await db.disconnect()
#     else:

#         def sync_save():
#             with db.connect() as conn:
#                 conn.execute(
#                     text(
#                         "INSERT INTO tokenjwt (username, token, active, [1hour], [30min], [5min], creation_time) VALUES (:username, :token, 1, :hour1, :min30, :min5, :creation_time)"
#                     ),
#                     {
#                         "username": username,
#                         "token": token,
#                         "hour1": hour1,
#                         "min30": min30,
#                         "min5": min5,
#                         "creation_time": datetime.utcnow(),
#                     },
#                 )

#         loop = asyncio.get_running_loop()
#         await loop.run_in_executor(None, sync_save)


async def save_api_key(username, hashed_key, expiry_hours, db):
    expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
    await db.execute(
        "INSERT INTO api_keys (username, hashed_key, expires_at) VALUES (:username, :hashed_key, :expires_at)",
        {"username": username, "hashed_key": hashed_key, "expires_at": expires_at},
    )


async def get_hashed_api_key(hashed_key, db):
    query = "SELECT username FROM api_keys WHERE hashed_key = :hashed_key AND expires_at > :now"
    result = await db.fetch_one(
        query, {"hashed_key": hashed_key, "now": datetime.utcnow()}
    )
    return result[0] if result else None


async def deactivate_old_api_keys(username, db):
    await db.execute(
        "UPDATE api_keys SET expires_at = :now WHERE username = :username",
        {"now": datetime.utcnow(), "username": username},
    )


# FUNCIÓN DE ELIMINACIÓN DE TOKENS COMENTADA - AUTENTICACIÓN DESHABILITADA
# async def delete_expired_tokens(db):
#     logger.info(
#         "[Depuración] Usando lógica de expiración igual a la API original (Flask) + active=0"
#     )
#     if db_type == "async":
#         await db.connect()
#         # Mostrar todos los tokens para depuración
#         all_tokens = await db.fetch_all(
#             "SELECT username, token, active, [1hour], [30min], [5min], creation_time FROM tokenjwt ORDER BY creation_time DESC"
#         )
#         logger.info(f"[Depuración] Todos los tokens en la tabla:")
#         for t in all_tokens:
#             logger.info(f"[Depuración] Token: {t}")
#         # Mostrar candidatos a eliminar
#         tokens = await db.fetch_all(
#             "SELECT username, token, active, [1hour], [30min], [5min], creation_time FROM tokenjwt WHERE ([1hour]=1 AND creation_time <= :h1) OR ([30min]=1 AND creation_time <= :m30) OR ([5min]=1 AND creation_time <= :m5) OR (active=0)",
#             {
#                 "h1": datetime.utcnow() - timedelta(hours=1),
#                 "m30": datetime.utcnow() - timedelta(minutes=30),
#                 "m5": datetime.utcnow() - timedelta(minutes=5),
#             },
#         )
#         logger.info(f"[Depuración] Tokens candidatos a eliminar: {len(tokens)}")
#         for t in tokens:
#             logger.info(f"[Depuración] Token: {t}")
#         count = len(tokens)
#         await db.execute(
#             "DELETE FROM tokenjwt WHERE ([1hour]=1 AND creation_time <= :h1) OR ([30min]=1 AND creation_time <= :m30) OR ([5min]=1 AND creation_time <= :m5) OR (active=0)",
#             {
#                 "h1": datetime.utcnow() - timedelta(hours=1),
#                 "m30": datetime.utcnow() - timedelta(minutes=30),
#                 "m5": datetime.utcnow() - timedelta(minutes=5),
#             },
#         )
#         await db.disconnect()
#         logger.info(f"Tokens eliminados: {count}")
#         return count
#     else:

#         def sync_delete():
#             with db.connect() as conn:
#                 # Mostrar todos los tokens para depuración
#                 result_all = conn.execute(
#                     text(
#                         "SELECT username, token, active, [1hour], [30min], [5min], creation_time FROM tokenjwt ORDER BY creation_time DESC"
#                     )
#                 )
#                 all_tokens = result_all.fetchall()
#                 logger.info(f"[Depuración] Todos los tokens en la tabla:")
#                 for t in all_tokens:
#                     logger.info(f"[Depuración] Token: {t}")
#                 # Mostrar candidatos a eliminar
#                 result = conn.execute(
#                     text(
#                         "SELECT username, token, active, [1hour], [30min], [5min], creation_time FROM tokenjwt WHERE ([1hour]=1 AND creation_time <= :h1) OR ([30min]=1 AND creation_time <= :m30) OR ([5min]=1 AND creation_time <= :m5) OR (active=0)"
#                     ),
#                     {
#                         "h1": datetime.utcnow() - timedelta(hours=1),
#                         "m30": datetime.utcnow() - timedelta(minutes=30),
#                         "m5": datetime.utcnow() - timedelta(minutes=5),
#                     },
#                 )
#                 tokens = result.fetchall()
#                 logger.info(f"[Depuración] Tokens candidatos a eliminar: {len(tokens)}")
#                 for t in tokens:
#                     logger.info(f"[Depuración] Token: {t}")
#                 count = len(tokens)
#                 conn.execute(
#                     text(
#                         "DELETE FROM tokenjwt WHERE ([1hour]=1 AND creation_time <= :h1) OR ([30min]=1 AND creation_time <= :m30) OR ([5min]=1 AND creation_time <= :m5) OR (active=0)"
#                     ),
#                     {
#                         "h1": datetime.utcnow() - timedelta(hours=1),
#                         "m30": datetime.utcnow() - timedelta(minutes=30),
#                         "m5": datetime.utcnow() - timedelta(minutes=5),
#                     },
#                 )
#                 return count

#         loop = asyncio.get_running_loop()
#         count = await loop.run_in_executor(None, sync_delete)
#         logger.info(f"Tokens eliminados: {count}")
#         return count


# --- Creación de tablas si no existen (híbrido) ---
def init_db():
    db = get_db()
    if db_type == "async":
        async def _init():
            await db.connect()
            # ... tus tablas existentes (usuariosj, api_keys) ...

            # AÑADIR ESTAS TABLAS NUEVAS
            await db.execute("""
            CREATE TABLE IF NOT EXISTS Clientes (
                id INT IDENTITY(1,1) PRIMARY KEY, -- Para SQL Server, o SERIAL para PostgreSQL/INTEGER PRIMARY KEY AUTOINCREMENT para SQLite
                nombreCliente VARCHAR(100) NOT NULL,
                cedula VARCHAR(20) UNIQUE NOT NULL,
                codigoCliente VARCHAR(50) UNIQUE NOT NULL,
                direccionCliente VARCHAR(200),
                telefonoCliente VARCHAR(20) NOT NULL
            )
            """)
            print("[init_db] Tabla 'Clientes' creada o ya existía.")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS Prestamos (
                id INT IDENTITY(1,1) PRIMARY KEY,
                cliente_id INT NOT NULL,
                monto_principal DECIMAL(18, 2) NOT NULL,
                tasa_interes DECIMAL(5, 4) NOT NULL,
                plazo_meses INT NOT NULL,
                fecha_inicio DATETIME DEFAULT GETDATE(),
                estado VARCHAR(20) DEFAULT 'activo',
                FOREIGN KEY (cliente_id) REFERENCES Clientes(id)
            )
            """)
            print("[init_db] Tabla 'Prestamos' creada o ya existía.")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS Cuotas (
                id INT IDENTITY(1,1) PRIMARY KEY,
                prestamo_id INT NOT NULL,
                numero_cuota INT NOT NULL,
                monto_cuota DECIMAL(18, 2) NOT NULL,
                fecha_vencimiento DATETIME NOT NULL,
                pagada BIT DEFAULT 0,
                fecha_pago DATETIME,
                FOREIGN KEY (prestamo_id) REFERENCES Prestamos(id)
            )
            """)
            print("[init_db] Tabla 'Cuotas' creada o ya existía.")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS RecibosIngreso (
                id INT IDENTITY(1,1) PRIMARY KEY,
                cliente_id INT, -- Puede ser nulo si el recibo no es de un cliente específico
                monto DECIMAL(18, 2) NOT NULL,
                concepto VARCHAR(200) NOT NULL,
                fecha_ingreso DATETIME DEFAULT GETDATE(),
                FOREIGN KEY (cliente_id) REFERENCES Clientes(id)
            )
            """)
            print("[init_db] Tabla 'RecibosIngreso' creada o ya existía.")

            await db.disconnect()

        import asyncio
        asyncio.run(_init())
    else: # db_type == "sqlserver"
        with db.connect() as conn:
            # ... tus tablas existentes (usuariosj, api_keys) ...

            # AÑADIR ESTAS TABLAS NUEVAS
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM sysobjects WHERE name='Clientes' AND xtype='U'"))
                if result.scalar() == 0:
                    conn.execute(text("""
                        CREATE TABLE Clientes (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            nombreCliente VARCHAR(100) NOT NULL,
                            cedula VARCHAR(20) UNIQUE NOT NULL,
                            codigoCliente VARCHAR(50) UNIQUE NOT NULL,
                            direccionCliente VARCHAR(200),
                            telefonoCliente VARCHAR(20) NOT NULL
                        )
                    """))
                    print("[init_db] Tabla 'Clientes' creada (SQL Server)")
            except Exception as e:
                print(f"[init_db] ERROR creando tabla 'Clientes': {e}")

            try:
                result = conn.execute(text("SELECT COUNT(*) FROM sysobjects WHERE name='Prestamos' AND xtype='U'"))
                if result.scalar() == 0:
                    conn.execute(text("""
                        CREATE TABLE Prestamos (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            cliente_id INT NOT NULL,
                            monto_principal DECIMAL(18, 2) NOT NULL,
                            tasa_interes DECIMAL(5, 4) NOT NULL,
                            plazo_meses INT NOT NULL,
                            fecha_inicio DATETIME DEFAULT GETDATE(),
                            estado VARCHAR(20) DEFAULT 'activo',
                            FOREIGN KEY (cliente_id) REFERENCES Clientes(id)
                        )
                    """))
                    print("[init_db] Tabla 'Prestamos' creada (SQL Server)")
            except Exception as e:
                print(f"[init_db] ERROR creando tabla 'Prestamos': {e}")

            try:
                result = conn.execute(text("SELECT COUNT(*) FROM sysobjects WHERE name='Cuotas' AND xtype='U'"))
                if result.scalar() == 0:
                    conn.execute(text("""
                        CREATE TABLE Cuotas (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            prestamo_id INT NOT NULL,
                            numero_cuota INT NOT NULL,
                            monto_cuota DECIMAL(18, 2) NOT NULL,
                            fecha_vencimiento DATETIME NOT NULL,
                            pagada BIT DEFAULT 0,
                            fecha_pago DATETIME,
                            FOREIGN KEY (prestamo_id) REFERENCES Prestamos(id)
                        )
                    """))
                    print("[init_db] Tabla 'Cuotas' creada (SQL Server)")
            except Exception as e:
                print(f"[init_db] ERROR creando tabla 'Cuotas': {e}")

            try:
                result = conn.execute(text("SELECT COUNT(*) FROM sysobjects WHERE name='RecibosIngreso' AND xtype='U'"))
                if result.scalar() == 0:
                    conn.execute(text("""
                        CREATE TABLE RecibosIngreso (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            cliente_id INT,
                            monto DECIMAL(18, 2) NOT NULL,
                            concepto VARCHAR(200) NOT NULL,
                            fecha_ingreso DATETIME DEFAULT GETDATE(),
                            FOREIGN KEY (cliente_id) REFERENCES Clientes(id)
                        )
                    """))
                    print("[init_db] Tabla 'RecibosIngreso' creada (SQL Server)")
            except Exception as e:
                print(f"[init_db] ERROR creando tabla 'RecibosIngreso': {e}")


# --- Job para eliminar tokens/API keys expirados (híbrido) ---
# FUNCIÓN COMENTADA - AUTENTICACIÓN DESHABILITADA
# def delete_expired_tokens_job():
#     db = get_db()
#     import asyncio

#     async def _job():
#         await delete_expired_tokens(db)

#     asyncio.run(_job())
