"""LLM-powered query parser with deterministic fallback."""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI

from backend.config import Settings, settings
from backend.llm.parser import QueryParser
from backend.llm.prompts import (
    QUERY_PARSER_SYSTEM_PROMPT,
    build_query_parser_user_prompt,
)
from backend.llm.schemas import ParsedQuery


logger = logging.getLogger(__name__)


class HybridQueryParser:
    """
    Parse school queries using Azure OpenAI when available.

    If Azure is disabled, not configured, or returns an error, the safe
    deterministic parser is used automatically.
    """

    def __init__(
        self,
        app_settings: Settings = settings,
        fallback_parser: QueryParser | None = None,
    ) -> None:
        self.settings = app_settings
        self.fallback_parser = fallback_parser or QueryParser()
        self.structured_model = self._create_structured_model()

    def _create_structured_model(self):
        """Create the Azure structured-output model when configured."""

        if not self.settings.llm_enabled:
            return None

        if not self.settings.azure_openai_configured:
            return None

        model = AzureChatOpenAI(
            azure_deployment=self.settings.azure_openai_chat_deployment,
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            temperature=self.settings.llm_temperature,
            timeout=self.settings.llm_timeout_seconds,
            max_retries=self.settings.llm_max_retries,
        )

        return model.with_structured_output(ParsedQuery)

    @property
    def llm_active(self) -> bool:
        """Return whether Azure structured parsing is currently available."""

        return self.structured_model is not None

    def parse(self, query: str) -> ParsedQuery:
        """
        Parse a natural-language query.

        Azure is attempted first when enabled. Any Azure or validation failure
        falls back to the deterministic parser.
        """

        if self.structured_model is None:
            return self.fallback_parser.parse(query)

        try:
            parsed_query = self.structured_model.invoke(
                [
                    SystemMessage(
                        content=QUERY_PARSER_SYSTEM_PROMPT,
                    ),
                    HumanMessage(
                        content=build_query_parser_user_prompt(query),
                    ),
                ]
            )

            if not isinstance(parsed_query, ParsedQuery):
                raise TypeError(
                    "Azure returned an unexpected structured-output type."
                )

            return parsed_query

        except Exception as exc:
            logger.warning(
                "Azure query parsing failed; using deterministic fallback: %s",
                exc,
            )

            return self.fallback_parser.parse(query)