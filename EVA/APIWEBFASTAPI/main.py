import logging

import uvicorn
# from apscheduler.schedulers.background import BackgroundScheduler  # Comentado - no se usa
from database_async import db_type, get_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router as api_router
from utils import (
    # delete_expired_tokens_job,  # Comentado - función no disponible
    init_db,
)

app = FastAPI(title="API Migrada a FastAPI", version="1.0")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apiweb")

# Inicializar base de datos y programar job
init_db()
# SCHEDULER COMENTADO - AUTENTICACIÓN DESHABILITADA
# scheduler = BackgroundScheduler()
# scheduler.add_job(delete_expired_tokens_job, "interval", minutes=1)
# scheduler.start()


# Solo conectar/desconectar si es async
def _setup_async_events():
    @app.on_event("startup")
    async def startup():
        db = get_db()
        await db.connect()
        logger.info("Conexión a la base de datos establecida.")

    @app.on_event("shutdown")
    async def shutdown():
        db = get_db()
        await db.disconnect()
        logger.info("Conexión a la base de datos cerrada.")


if db_type == "async":
    _setup_async_events()


# Endpoint raíz
@app.get("/")
async def root():
    return {"message": "API FastAPI funcionando"}


# Importar y registrar rutas
app.include_router(api_router)