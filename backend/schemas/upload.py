"""Pydantic schemas for CSV upload responses."""

from pydantic import BaseModel, Field


class UploadRowError(BaseModel):
    """Describes an error found in one CSV row."""

    row: int = Field(ge=1)
    field: str | None = None
    message: str


class UploadSummaryResponse(BaseModel):
    """Summary returned after processing a CSV upload."""

    file_type: str
    total_rows: int = Field(ge=0)
    inserted_rows: int = Field(ge=0)
    updated_rows: int = Field(ge=0)
    skipped_rows: int = Field(ge=0)
    failed_rows: int = Field(ge=0)
    errors: list[UploadRowError]