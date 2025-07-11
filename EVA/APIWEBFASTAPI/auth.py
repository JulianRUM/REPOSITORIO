# ARCHIVO COMENTADO - AUTENTICACIÓN DESHABILITADA
# import os
# from datetime import datetime, timedelta

# from database_async import get_db
# from fastapi import Depends, HTTPException, Request, status
# from jose import JWTError, jwt
# from utils import hash_api_key, logger

# SECRET_KEY = os.getenv("SECRET_KEY", "2016")
# ALGORITHM = "HS256"


# async def get_current_user(request: Request, db=Depends(get_db)):
#     token = request.headers.get("Authorization")
#     api_key = request.headers.get("x-api-key")
#     if not token and not api_key:
#         raise HTTPException(status_code=401, detail="Token o API key requerido")
#     if token:
#         try:
#             token = token.split(" ")[-1]
#             payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#             username = payload["username"]
#             # Aquí puedes validar el token en la base de datos si lo deseas
#             return username
#         except JWTError:
#             raise HTTPException(status_code=401, detail="Token inválido o expirado")
#     if api_key:
#         hashed_key = hash_api_key(api_key)
#         # Aquí deberías validar la API key en la base de datos
#         # Por simplicidad, se acepta cualquier valor
#         return "api_key_user"