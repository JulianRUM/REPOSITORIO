import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        ssl_keyfile="C:/cert/llave_privada.pem",
        ssl_certfile="C:/cert/certificado.pem",
    )
