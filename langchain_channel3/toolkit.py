"""Both Channel3 tools with shared options."""

from __future__ import annotations

from typing import Optional

from langchain_core.tools import BaseTool, BaseToolkit
from pydantic import Field, SecretStr

from langchain_channel3.tools import Channel3GetProducts, Channel3SearchProducts


class Channel3Toolkit(BaseToolkit):
    """Channel3 product search and product detail tools.

    Setup:
        Install ``langchain-channel3`` and set ``CHANNEL3_API_KEY``.

    Instantiate:
        .. code-block:: python

            from langchain_channel3 import Channel3Toolkit

            toolkit = Channel3Toolkit(conversation_id=chat_id)
            tools = toolkit.get_tools()
    """

    api_key: Optional[SecretStr] = Field(default=None, exclude=True)
    """Channel3 API key. Defaults to the ``CHANNEL3_API_KEY`` environment variable."""
    base_url: Optional[str] = None
    """Overrides the API base URL."""
    conversation_id: Optional[str] = None
    """Groups one chat's calls together in your Channel3 analytics."""
    limit: int = Field(default=8, ge=1, le=30)
    """Maximum products per search."""

    def get_tools(self) -> list[BaseTool]:
        shared = {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "conversation_id": self.conversation_id,
        }
        return [Channel3SearchProducts(**shared, limit=self.limit), Channel3GetProducts(**shared)]
