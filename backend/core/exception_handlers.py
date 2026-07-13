"""Global FastAPI exception handlers."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from backend.utils.exceptions import StudentNotFoundError


def register_exception_handlers(app: FastAPI) -> None:
    """Register all application-level exception handlers."""

    @app.exception_handler(StudentNotFoundError)
    async def handle_student_not_found(
        request: Request,
        exc: StudentNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": str(exc),
                    "details": {
                        "student_id": exc.student_id,
                    },
                }
            },
        )