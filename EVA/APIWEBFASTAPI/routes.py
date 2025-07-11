import os
import secrets
from datetime import datetime, timedelta

# from auth import get_current_user  # Comentado para permitir acceso sin token
from database_async import db_type, get_db #
from fastapi import APIRouter, Depends, HTTPException, Request # 
from jose import jwt
from sqlalchemy import text #
from utils import ( #
    # deactivate_old_tokens,  # Comentado - función no disponible
    format_number, #
    hash_password, #
    logger, #
    # save_token,  # Comentado - función no disponible
    verify_password, #
)

router = APIRouter()

# --- Endpoints existentes (MANTENERLOS TAL CUAL) ---

@router.get("/CB")
async def cuentas_balance(request: Request):  # Removido user=Depends(get_current_user)
    # logger.info(
    #     f"Usuario '{user}' accedió a /CB con params: {dict(request.query_params)}"
    # )
    logger.info(f"Acceso a /CB con params: {dict(request.query_params)}") # 
    db = get_db() #
    cedula = request.query_params.get("cedula", "") # 
    if not cedula: # 
        raise HTTPException( # 
            status_code=400, detail="El parámetro cedula es obligatorio"
        )
    query = """
        SELECT cliente, nombre, banco, cuenta, Tele, balance, FechaUltimoMovimiento, FechaApertura, Moneda, Cedula
        FROM ListaProductosCliente
        WHERE Cedula = :cedula
    """
    if db_type == "async": #
        results = await db.fetch_all(query, {"cedula": cedula}) #
    else: #
        with db.connect() as conn: #
            result = conn.execute(text(query), {"cedula": cedula}) #
            results = result.fetchall() #
    if not results: # 
        raise HTTPException(status_code=404, detail="No se encontraron resultados") # 
    cliente_data = {
        "numero_socio": results[0][0],
        "nombre": results[0][1],
        "telefono": results[0][4],
        "cedula": results[0][9],
    }

    def format_date(date_value):
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d")
        return None

    productos_data = [
        {
            "banco": row[2],
            "cuenta": row[3],
            "balance": row[5],
            "fecha_ultimo_movimiento": format_date(row[6]),
            "fecha_apertura": format_date(row[7]),
            "moneda": row[8],
        }
        for row in results
    ]
    data = {"cliente": cliente_data, "productos": productos_data}
    return data


@router.get("/EF")
async def estados_fiscales(request: Request):  # Removido user=Depends(get_current_user)
    # logger.info(
    #     f"Usuario '{user}' accedió a /EF con params: {dict(request.query_params)}"
    # )
    logger.info(f"Acceso a /EF con params: {dict(request.query_params)}") # 
    db = get_db() #
    fecha_inicio = request.query_params.get("fecha_inicio", "") # 
    fecha_fin = request.query_params.get("fecha_fin", "") # 
    caja = request.query_params.get("caja", "TODAS") # 
    estado_fiscal = request.query_params.get("estado_fiscal", "TODOS") # 
    rncemisor = request.query_params.get("rncemisor", "TODOS") # 
    if not fecha_inicio or not fecha_fin: # 
        raise HTTPException( # 
            status_code=400,
            detail="Los parámetros 'fecha_inicio' y 'fecha_fin' son obligatorios",
        )
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Las fechas deben tener el formato 'YYYY-MM-DD'"
        )
    query = """
        SELECT TipoVenta, Factura, TipoECF, encf, EstadoFiscal, DescripcionEstadoFiscal, URLC, ResultadoEstadoFiscal, MontoFacturado, ITBISFacturado, MontoDGII, MontoITBISDGII
        FROM vMonitorSentences
        WHERE CONVERT(date, FechaEmision) BETWEEN :fecha_inicio AND :fecha_fin
    """
    params = {"fecha_inicio": fecha_inicio_dt, "fecha_fin": fecha_fin_dt}
    if caja != "TODAS":
        query += " AND caja = :caja"
        params["caja"] = caja
    if estado_fiscal and estado_fiscal != "TODOS":
        query += " AND EstadoFiscal = :estado_fiscal"
        params["estado_fiscal"] = estado_fiscal
    if rncemisor and rncemisor != "TODOS":
        query += " AND rncemisor = :rncemisor"
        params["rncemisor"] = rncemisor
    if db_type == "async": #
        results = await db.fetch_all(query, params) #
    else: #
        with db.connect() as conn: #
            result = conn.execute(text(query), params) #
            results = result.fetchall() #
    if not results: # 
        raise HTTPException( # 
            status_code=404,
            detail="No se encontraron resultados para los filtros especificados",
        )
    datos = []
    for row in results:
        datos.append(
            {
                "tipo_venta": str(row[0]).strip(),
                "factura": str(row[1]).strip(),
                "tipo_ecf": str(row[2]).strip(),
                "encf": str(row[3]).strip(),
                "estado_fiscal": row[4],
                "descripcion_estado_fiscal": str(row[5]).strip(),
                "urlc": str(row[6]).strip(),
                "resultado_estado_fiscal": str(row[7] or "").strip(),
                "monto_facturado": format_number(row[8] or 0.00),
                "itbis_facturado": format_number(row[9] or 0.00),
                "monto_dgii": format_number(row[10] or 0.0000),
                "monto_itbis_dgii": format_number(row[11] or 0.0000),
            }
        )
    return datos


@router.post("/register") # 
async def register(request: Request): # 
    data = await request.json() # 
    username = data.get("username") # 
    logger.info(f"Intento de registro de usuario: {username}") # 
    db = get_db() #
    query = "SELECT * FROM usuariosj WHERE username = :username" # 
    if db_type == "async": #
        existing_user = await db.fetch_one(query, {"username": username}) #
    else: #
        with db.connect() as conn: #
            result = conn.execute(text(query), {"username": username}) #
            existing_user = result.fetchone() #
    if existing_user: # 
        raise HTTPException(status_code=400, detail="User already exists") # 
    hashed_password = hash_password(data.get("password")) #
    try:
        if db_type == "async": #
            await db.execute( #
                "INSERT INTO usuariosj (username, password, rnc) VALUES (:username, :password, :rnc)", # 
                {
                    "username": username, # 
                    "password": hashed_password, # 
                    "rnc": data.get("rnc"), # 
                },
            )
        else: #
            with db.connect() as conn: #
                conn.execute( #
                    text(
                        "INSERT INTO usuariosj (username, password, rnc) VALUES (:username, :password, :rnc)" # 
                    ),
                    {
                        "username": username, # 
                        "password": hashed_password, # 
                        "rnc": data.get("rnc"), # 
                    },
                )
    except Exception as e:
        logger.error(f"Error al registrar usuario: {e}") # 
        raise HTTPException(status_code=500, detail="Error al registrar usuario") # 
    logger.info(f"Nuevo usuario registrado: {username} con RNC: {data.get('rnc')}") # 
    return {"message": "User registered successfully"} # 


@router.post("/login") # 
async def login(request: Request): # 
    data = await request.json() # 
    username = data.get("username") # 
    logger.info(f"Intento de login de usuario: {username}") # 
    db = get_db() #
    query = "SELECT * FROM usuariosj WHERE username = :username" # 
    if db_type == "async": #
        user_data = await db.fetch_one(query, {"username": username}) #
    else: #
        with db.connect() as conn: #
            result = conn.execute(text(query), {"username": username}) #
            user_data = result.fetchone() #
    if user_data is None: # 
        raise HTTPException( # 
            status_code=401, detail="Invalid username or password or RNC"
        )
    db_password = user_data[1] # 
    db_rnc = user_data[2] # 
    if (
        not verify_password(db_password, data.get("password")) #
        or data.get("rnc") != db_rnc # 
    ):
        raise HTTPException( # 
            status_code=401, detail="Invalid username or password or RNC"
        )
    # FUNCIONES DE TOKEN COMENTADAS - AUTENTICACIÓN DESHABILITADA
    # await deactivate_old_tokens(username, db)
    hour1 = data.get("1hour", 0) # 
    min30 = data.get("30min", 0) # 
    min5 = data.get("5min", 0) # 
    expiration_time = None
    if hour1: # 
        expiration_time = datetime.utcnow() + timedelta(hours=1) # 
    elif min30: # 
        expiration_time = datetime.utcnow() + timedelta(minutes=30) # 
    elif min5: # 
        expiration_time = datetime.utcnow() + timedelta(minutes=5) # 
    token_data = {"username": username} # 
    if expiration_time: # 
        token_data["exp"] = int(expiration_time.timestamp()) # 
    token = jwt.encode(token_data, os.getenv("SECRET_KEY", "2016"), algorithm="HS256") # 
    # FUNCIONES DE TOKEN COMENTADAS - AUTENTICACIÓN DESHABILITADA
    # await save_token(username, token, hour1, min30, min5, db)
    return {"token": token} # 


@router.post("/generate-api-key") # 
async def generate_api_key(request: Request):  # Removido user=Depends(get_current_user)
    # logger.info(f"Usuario '{user}' generó una API Key")
    logger.info("Generación de API Key") # 
    db = get_db() #
    # username = user  # Comentado
    username = "default_user"  # Usuario por defecto
    raw_key = secrets.token_urlsafe(64) # 
    hashed_key = hash_password(raw_key) #
    if db_type == "async": #
        await db.execute( #
            "INSERT INTO api_keys (username, hashed_key, expires_at) VALUES (:username, :hashed_key, :expires_at)", # 
            {
                "username": username, # 
                "hashed_key": hashed_key, # 
                "expires_at": datetime.utcnow() + timedelta(days=30), # 
            },
        )
    else: #
        with db.connect() as conn: #
            conn.execute( #
                text(
                    "INSERT INTO api_keys (username, hashed_key, expires_at) VALUES (:username, :hashed_key, :expires_at)" # 
                ),
                {
                    "username": username, # 
                    "hashed_key": hashed_key, # 
                    "expires_at": datetime.utcnow() + timedelta(days=30), # 
                },
            )
    logger.info(f"API Key generada para el usuario: {username}") # 
    return {"api_key": raw_key} # 


@router.get("/data") # 
async def protected_data(request: Request):  # Removido user=Depends(get_current_user)
    # logger.info(f"Usuario '{user}' accedió a /data")
    logger.info("Acceso a /data") # 
    db = get_db() #
    # username = user  # Comentado
    username = "default_user"  # Usuario por defecto
    query = "SELECT * FROM usuariosj WHERE username = :username" # 
    if db_type == "async": #
        user_data = await db.fetch_one(query, {"username": username}) #
    else: #
        with db.connect() as conn: #
            result = conn.execute(text(query), {"username": username}) #
            user_data = result.fetchone() #
    if not user_data: # 
        raise HTTPException(status_code=404, detail="Usuario no encontrado") # 
    return {"username": user_data[0], "additional_data": user_data[1]} # 


# --- NUEVOS ENDPOINTS PARA LA APLICACIÓN DE PRÉSTAMOS ---

# Endpoint para obtener todos los clientes
@router.get("/clientes")
async def get_clientes():
    db = get_db()
    query = "SELECT id, nombreCliente, cedula, codigoCliente, direccionCliente, telefonoCliente FROM Clientes"
    if db_type == "async":
        results = await db.fetch_all(query)
    else:
        with db.connect() as conn:
            result = conn.execute(text(query))
            results = result.fetchall()

    clientes = []
    for row in results:
        clientes.append({
            "id": row[0],
            "nombreCliente": row[1],
            "cedula": row[2],
            "codigoCliente": row[3],
            "direccionCliente": row[4],
            "telefonoCliente": row[5],
        })
    return clientes

# Endpoint para agregar un nuevo cliente
@router.post("/clientes")
async def add_cliente(request: Request):
    data = await request.json()
    db = get_db()

    required_fields = ["nombreCliente", "cedula", "codigoCliente", "telefonoCliente"]
    if not all(field in data for field in required_fields):
        raise HTTPException(status_code=400, detail="Faltan datos requeridos para el cliente.")

    # Opcional: Verificar si el cliente ya existe por cédula o código
    query_check = "SELECT id FROM Clientes WHERE cedula = :cedula OR codigoCliente = :codigoCliente"
    params_check = {"cedula": data["cedula"], "codigoCliente": data["codigoCliente"]}

    if db_type == "async":
        existing_client = await db.fetch_one(query_check, params_check)
    else:
        with db.connect() as conn:
            result_check = conn.execute(text(query_check), params_check)
            existing_client = result_check.fetchone()

    if existing_client:
        raise HTTPException(status_code=409, detail="Un cliente con esa cédula o código ya existe.")

    query = """
        INSERT INTO Clientes (nombreCliente, cedula, codigoCliente, direccionCliente, telefonoCliente)
        VALUES (:nombreCliente, :cedula, :codigoCliente, :direccionCliente, :telefonoCliente)
    """
    params = {
        "nombreCliente": data["nombreCliente"],
        "cedula": data["cedula"],
        "codigoCliente": data["codigoCliente"],
        "direccionCliente": data.get("direccionCliente", None), # Puede ser nulo
        "telefonoCliente": data["telefonoCliente"]
    }

    try:
        if db_type == "async":
            await db.execute(query, params)
        else:
            with db.connect() as conn:
                conn.execute(text(query), params)
                conn.commit() # Importante para commits en modo síncrono si no es autocommit

        # Opcional: Recuperar el ID del cliente recién insertado si la DB lo soporta
        # Para MSSQL con SQLALCHEMY, a menudo no necesitas esto si usas un ORM.
        # Si necesitas el ID, la lógica puede variar. Para fines de esta prueba, no lo haremos.

        return {"message": "Cliente agregado exitosamente", "cliente": data}
    except Exception as e:
        logger.error(f"Error al agregar cliente: {e}")
        raise HTTPException(status_code=500, detail=f"Error al agregar cliente: {e}")

# Endpoint para obtener préstamos (todos o por cliente)
@router.get("/prestamos")
async def get_prestamos(cliente_id: int = None):
    db = get_db()
    query = "SELECT id, cliente_id, monto_principal, tasa_interes, plazo_meses, fecha_inicio, estado FROM Prestamos"
    params = {}
    if cliente_id:
        query += " WHERE cliente_id = :cliente_id"
        params["cliente_id"] = cliente_id

    if db_type == "async":
        results = await db.fetch_all(query, params)
    else:
        with db.connect() as conn:
            result = conn.execute(text(query), params)
            results = result.fetchall()

    prestamos = []
    for row in results:
        prestamos.append({
            "id": row[0],
            "clienteId": row[1],
            "montoPrincipal": row[2],
            "tasaInteres": row[3],
            "plazoMeses": row[4],
            "fechaInicio": row[5].isoformat() if isinstance(row[5], datetime) else row[5],
            "estado": row[6],
        })
    return prestamos

# Endpoint para agregar un nuevo préstamo
@router.post("/prestamos")
async def add_prestamo(request: Request):
    data = await request.json()
    db = get_db()

    required_fields = ["clienteId", "montoPrincipal", "tasaInteres", "plazoMeses"]
    if not all(field in data for field in required_fields):
        raise HTTPException(status_code=400, detail="Faltan datos requeridos para el préstamo.")

    # Verificar si el cliente existe
    query_cliente = "SELECT id FROM Clientes WHERE id = :cliente_id"
    if db_type == "async":
        cliente_exists = await db.fetch_one(query_cliente, {"cliente_id": data["clienteId"]})
    else:
        with db.connect() as conn:
            result_cliente = conn.execute(text(query_cliente), {"cliente_id": data["clienteId"]})
            cliente_exists = result_cliente.fetchone()

    if not cliente_exists:
        raise HTTPException(status_code=404, detail="El cliente especificado no existe.")

    query = """
        INSERT INTO Prestamos (cliente_id, monto_principal, tasa_interes, plazo_meses, fecha_inicio, estado)
        VALUES (:cliente_id, :monto_principal, :tasa_interes, :plazo_meses, :fecha_inicio, :estado)
    """
    params = {
        "cliente_id": data["clienteId"],
        "monto_principal": data["montoPrincipal"],
        "tasa_interes": data["tasaInteres"],
        "plazo_meses": data["plazoMeses"],
        "fecha_inicio": datetime.utcnow(), # Usar la fecha actual UTC
        "estado": data.get("estado", "activo") # Valor por defecto 'activo'
    }

    try:
        if db_type == "async":
            await db.execute(query, params)
        else:
            with db.connect() as conn:
                conn.execute(text(query), params)
                conn.commit()
        return {"message": "Préstamo agregado exitosamente", "prestamo": data}
    except Exception as e:
        logger.error(f"Error al agregar préstamo: {e}")
        raise HTTPException(status_code=500, detail=f"Error al agregar préstamo: {e}")

# Endpoint para obtener recibos de ingreso
@router.get("/recibos_ingreso")
async def get_recibos_ingreso(cliente_id: int = None):
    db = get_db()
    query = "SELECT id, cliente_id, monto, concepto, fecha_ingreso FROM RecibosIngreso"
    params = {}
    if cliente_id:
        query += " WHERE cliente_id = :cliente_id"
        params["cliente_id"] = cliente_id

    if db_type == "async":
        results = await db.fetch_all(query, params)
    else:
        with db.connect() as conn:
            result = conn.execute(text(query), params)
            results = result.fetchall()

    recibos = []
    for row in results:
        recibos.append({
            "id": row[0],
            "clienteId": row[1],
            "monto": row[2],
            "concepto": row[3],
            "fechaIngreso": row[4].isoformat() if isinstance(row[4], datetime) else row[4],
        })
    return recibos

# Endpoint para agregar un nuevo recibo de ingreso
@router.post("/recibos_ingreso")
async def add_recibo_ingreso(request: Request):
    data = await request.json()
    db = get_db()

    required_fields = ["monto", "concepto"]
    if not all(field in data for field in required_fields):
        raise HTTPException(status_code=400, detail="Faltan datos requeridos para el recibo de ingreso.")

    cliente_id = data.get("clienteId")
    if cliente_id:
        # Verificar si el cliente existe
        query_cliente = "SELECT id FROM Clientes WHERE id = :cliente_id"
        if db_type == "async":
            cliente_exists = await db.fetch_one(query_cliente, {"cliente_id": cliente_id})
        else:
            with db.connect() as conn:
                result_cliente = conn.execute(text(query_cliente), {"cliente_id": cliente_id})
                cliente_exists = result_cliente.fetchone()

        if not cliente_exists:
            raise HTTPException(status_code=404, detail="El cliente asociado no existe.")

    query = """
        INSERT INTO RecibosIngreso (cliente_id, monto, concepto, fecha_ingreso)
        VALUES (:cliente_id, :monto, :concepto, :fecha_ingreso)
    """
    params = {
        "cliente_id": cliente_id,
        "monto": data["monto"],
        "concepto": data["concepto"],
        "fecha_ingreso": datetime.utcnow()
    }

    try:
        if db_type == "async":
            await db.execute(query, params)
        else:
            with db.connect() as conn:
                conn.execute(text(query), params)
                conn.commit()
        return {"message": "Recibo de ingreso agregado exitosamente", "recibo": data}
    except Exception as e:
        logger.error(f"Error al agregar recibo de ingreso: {e}")
        raise HTTPException(status_code=500, detail=f"Error al agregar recibo de ingreso: {e}")

# Puedes añadir más endpoints para Cuotas (GET, POST, PUT para marcar como pagada)
# Ejemplo para obtener cuotas de un préstamo
@router.get("/prestamos/{prestamo_id}/cuotas")
async def get_cuotas_by_prestamo(prestamo_id: int):
    db = get_db()
    query = "SELECT id, prestamo_id, numero_cuota, monto_cuota, fecha_vencimiento, pagada, fecha_pago FROM Cuotas WHERE prestamo_id = :prestamo_id"
    params = {"prestamo_id": prestamo_id}

    if db_type == "async":
        results = await db.fetch_all(query, params)
    else:
        with db.connect() as conn:
            result = conn.execute(text(query), params)
            results = result.fetchall()

    cuotas = []
    for row in results:
        cuotas.append({
            "id": row[0],
            "prestamoId": row[1],
            "numeroCuota": row[2],
            "montoCuota": row[3],
            "fechaVencimiento": row[4].isoformat() if isinstance(row[4], datetime) else row[4],
            "pagada": bool(row[5]),
            "fechaPago": row[6].isoformat() if isinstance(row[6], datetime) else row[6],
        })
    return cuotas

# Ejemplo para agregar una cuota (útil si las cuotas se generan por separado)
@router.post("/cuotas")
async def add_cuota(request: Request):
    data = await request.json()
    db = get_db()

    required_fields = ["prestamoId", "numeroCuota", "montoCuota", "fechaVencimiento"]
    if not all(field in data for field in required_fields):
        raise HTTPException(status_code=400, detail="Faltan datos requeridos para la cuota.")

    # Verificar si el préstamo existe
    query_prestamo = "SELECT id FROM Prestamos WHERE id = :prestamo_id"
    if db_type == "async":
        prestamo_exists = await db.fetch_one(query_prestamo, {"prestamo_id": data["prestamoId"]})
    else:
        with db.connect() as conn:
            result_prestamo = conn.execute(text(query_prestamo), {"prestamo_id": data["prestamoId"]})
            prestamo_exists = result_prestamo.fetchone()

    if not prestamo_exists:
        raise HTTPException(status_code=404, detail="El préstamo especificado no existe.")

    query = """
        INSERT INTO Cuotas (prestamo_id, numero_cuota, monto_cuota, fecha_vencimiento, pagada, fecha_pago)
        VALUES (:prestamo_id, :numero_cuota, :monto_cuota, :fecha_vencimiento, :pagada, :fecha_pago)
    """
    params = {
        "prestamo_id": data["prestamoId"],
        "numero_cuota": data["numeroCuota"],
        "monto_cuota": data["montoCuota"],
        "fecha_vencimiento": datetime.strptime(data["fechaVencimiento"], "%Y-%m-%d"), # Asume formato YYYY-MM-DD
        "pagada": data.get("pagada", False),
        "fecha_pago": datetime.utcnow() if data.get("pagada", False) else None
    }

    try:
        if db_type == "async":
            await db.execute(query, params)
        else:
            with db.connect() as conn:
                conn.execute(text(query), params)
                conn.commit()
        return {"message": "Cuota agregada exitosamente", "cuota": data}
    except Exception as e:
        logger.error(f"Error al agregar cuota: {e}")
        raise HTTPException(status_code=500, detail=f"Error al agregar cuota: {e}")


# Endpoint para marcar una cuota como pagada (PUT)
@router.put("/cuotas/{cuota_id}/mark_paid")
async def mark_cuota_paid(cuota_id: int):
    db = get_db()

    query = "UPDATE Cuotas SET pagada = 1, fecha_pago = :fecha_pago WHERE id = :cuota_id AND pagada = 0"
    params = {"fecha_pago": datetime.utcnow(), "cuota_id": cuota_id}

    try:
        if db_type == "async":
            result = await db.execute(query, params)
        else:
            with db.connect() as conn:
                result = conn.execute(text(query), params)
                conn.commit()
        
        if (db_type == "async" and result == 0) or (db_type != "async" and result.rowcount == 0):
            raise HTTPException(status_code=404, detail="Cuota no encontrada o ya pagada.")
        
        return {"message": "Cuota marcada como pagada exitosamente"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al marcar cuota como pagada: {e}")
        raise HTTPException(status_code=500, detail=f"Error al marcar cuota como pagada: {e}")