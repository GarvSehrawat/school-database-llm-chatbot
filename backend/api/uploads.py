"""FastAPI routes for CSV data uploads."""

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from backend.dependencies import get_csv_service
from backend.schemas.upload import UploadSummaryResponse
from backend.services.csv_service import CSVService


router = APIRouter(
    prefix="/api/v1/uploads",
    tags=["Uploads"],
)


@router.post(
    "/students",
    response_model=UploadSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_students_csv(
    file: UploadFile = File(...),
    replace_existing: bool = Form(False),
    service: CSVService = Depends(get_csv_service),
) -> UploadSummaryResponse:
    """
    Upload and import student records from a CSV file.

    Existing students are skipped unless `replace_existing` is true.
    """

    try:
        file_content = await file.read()

        return service.import_students(
            file_content=file_content,
            filename=file.filename,
            replace_existing=replace_existing,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()