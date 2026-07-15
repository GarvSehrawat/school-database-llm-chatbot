"""API endpoint for safe natural-language school queries."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from backend.dependencies import get_query_service
from backend.llm.query_service import QueryService
from backend.llm.schemas import NaturalLanguageQueryRequest, QueryResult


router = APIRouter(
    prefix="/api/v1",
    tags=["Natural Language Query"],
)


@router.post(
    "/query",
    response_model=QueryResult,
    status_code=status.HTTP_200_OK,
)
def execute_natural_language_query(
    request: NaturalLanguageQueryRequest,
    service: QueryService = Depends(get_query_service),
) -> QueryResult:
    """Parse and safely execute a supported natural-language query."""

    try:
        return service.execute(request.query)

    except ValidationError as exc:
        error_message = exc.errors()[0].get(
            "msg",
            "The query is missing required information.",
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc