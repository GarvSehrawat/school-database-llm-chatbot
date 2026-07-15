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


async def _read_uploaded_file(file: UploadFile) -> bytes:
    """Read an uploaded file and guarantee that it is closed."""

    try:
        return await file.read()
    finally:
        await file.close()


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
    """Upload and import student records from a CSV file."""

    try:
        file_content = await _read_uploaded_file(file)

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


@router.post(
    "/subjects",
    response_model=UploadSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_subjects_csv(
    file: UploadFile = File(...),
    replace_existing: bool = Form(False),
    service: CSVService = Depends(get_csv_service),
) -> UploadSummaryResponse:
    """Upload and import subject records from a CSV file."""

    try:
        file_content = await _read_uploaded_file(file)

        return service.import_subjects(
            file_content=file_content,
            filename=file.filename,
            replace_existing=replace_existing,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/marks",
    response_model=UploadSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_marks_csv(
    file: UploadFile = File(...),
    replace_existing: bool = Form(False),
    service: CSVService = Depends(get_csv_service),
) -> UploadSummaryResponse:
    """Upload and import student mark records from a CSV file."""

    try:
        file_content = await _read_uploaded_file(file)

        return service.import_marks(
            file_content=file_content,
            filename=file.filename,
            replace_existing=replace_existing,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc