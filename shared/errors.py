from fastapi.responses import JSONResponse


def error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"message": message})
