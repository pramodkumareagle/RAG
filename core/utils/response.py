from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

def json_ok(data=None):
    return JSONResponse(content=jsonable_encoder({"success": True, "data": data}))

def json_error(message: str, status_code: int = 400):
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"success": False, "error": message})
    )
