from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

def json_ok(data=None):
    return JSONResponse(content=jsonable_encoder({"success": True, "data": data}))

def json_error(message, status=400):
    return JSONResponse(
        status_code=status,
        content=jsonable_encoder({"success": False, "error": message})
    )
