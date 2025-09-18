from fastapi import Header, HTTPException
from firebase_admin import auth

def verify_token(authorization: str = Header(...)) -> str:
    """
    Verifica el token de Firebase y devuelve el identificador
    único del usuario
    """
    if not authorization.startswith("Bearer "): # Verifica que sea de tipo bearer
        raise HTTPException(status_code=401, detail="Token inválido")
    id_token = authorization.split(" ")[1]
    try: # Intenta decodificar el token
        decoded_id_token = auth.verify_id_token(id_token)
        return decoded_id_token["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")