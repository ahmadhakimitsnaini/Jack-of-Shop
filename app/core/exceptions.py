"""
Mendefinisikan global exception handlers untuk FastAPI.
Agar response error seragam untuk 400, 404, dan 422.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class APIException(Exception):
    """
    Custom Base Exception.
    Bisa dilempar (raise) di dalam endpoint atau service:
    raise APIException(status_code=404, detail="User not found")
    """
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        """Handler untuk error bisnis atau resource not found (custom)."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handler untuk error validasi skema (Pydantic). Merapikan format default."""
        # Ambil semua pesan error dari exception Pydantic
        errors = []
        for error in exc.errors():
            # Gabungkan field lokasi error menjadi string
            loc = " -> ".join([str(x) for x in error.get("loc", [])])
            msg = error.get("msg", "")
            errors.append(f"{loc}: {msg}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "detail": "Validation Error",
                "errors": errors,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handler untuk menangkap unhandled exception (Internal Server Error)."""
        # Di production, sebaiknya tidak mengembalikan exception langsung, melainkan
        # di-log dan mengembalikan pesan generik.
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal Server Error",
                "error_msg": str(exc)  # Bisa disembunyikan di production
            },
        )
